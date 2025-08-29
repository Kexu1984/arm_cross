"""
Tests for PTY transport mode.

Tests PTY functionality on POSIX systems (skipped on Windows).
"""

import pytest
import asyncio
import os
import sys
import time
import threading
from uart_terminal import UartTerminal


@pytest.mark.skipif(sys.platform == 'win32', reason="PTY not supported on Windows")
class TestPTYTransport:
    """Test PTY transport functionality."""
    
    @pytest.mark.asyncio
    async def test_pty_creation(self):
        """Test PTY creation and basic properties."""
        terminal = UartTerminal(on_rx=lambda data: None, mode='pty')
        
        try:
            terminal.start()
            await asyncio.sleep(0.2)
            
            # Should have created a slave path
            slave_path = terminal.slave_path
            assert slave_path is not None
            assert slave_path.startswith('/dev/')
            assert os.path.exists(slave_path)
            
        finally:
            terminal.stop()
            
    @pytest.mark.asyncio
    async def test_pty_bidirectional_communication(self):
        """Test bidirectional PTY communication."""
        received_data = []
        event = asyncio.Event()
        
        def on_rx(data: bytes):
            received_data.append(data)
            event.set()
            
        terminal = UartTerminal(on_rx=on_rx, mode='pty')
        
        try:
            terminal.start()
            await asyncio.sleep(0.2)
            
            slave_path = terminal.slave_path
            assert slave_path is not None
            
            # Open slave device
            slave_fd = os.open(slave_path, os.O_RDWR | os.O_NOCTTY)
            
            try:
                # Test RX direction: slave -> on_rx callback
                test_data = b'Hello PTY RX!'
                os.write(slave_fd, test_data)
                
                # Wait for callback
                await asyncio.wait_for(event.wait(), timeout=2.0)
                
                assert len(received_data) == 1
                assert received_data[0] == test_data
                
                # Test TX direction: write() -> slave
                tx_data = b'Hello PTY TX!'
                terminal.write(tx_data)
                
                # Read from slave
                # Set slave to non-blocking for read
                import fcntl
                flags = fcntl.fcntl(slave_fd, fcntl.F_GETFL)
                fcntl.fcntl(slave_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                
                # Wait for data with timeout
                response = None
                for _ in range(50):  # 5 seconds max
                    try:
                        response = os.read(slave_fd, 1024)
                        if response:
                            break
                    except OSError:
                        # No data yet
                        pass
                    await asyncio.sleep(0.1)
                    
                assert response == tx_data
                
            finally:
                os.close(slave_fd)
                
        finally:
            terminal.stop()
            
    @pytest.mark.asyncio
    async def test_pty_slave_close_handling(self):
        """Test handling when slave side is closed."""
        rx_count = 0
        
        def on_rx(data: bytes):
            nonlocal rx_count
            rx_count += 1
            
        terminal = UartTerminal(on_rx=on_rx, mode='pty')
        
        try:
            terminal.start()
            await asyncio.sleep(0.2)
            
            slave_path = terminal.slave_path
            
            # Open, write, and close slave
            slave_fd = os.open(slave_path, os.O_RDWR)
            os.write(slave_fd, b'test before close')
            os.close(slave_fd)
            
            await asyncio.sleep(0.1)
            
            # Should have received the data
            assert rx_count > 0
            
            # Terminal should still be functional after slave close
            terminal.write(b'test after close')
            
            # Should be able to open slave again
            slave_fd2 = os.open(slave_path, os.O_RDWR)
            os.close(slave_fd2)
            
        finally:
            terminal.stop()
            
    def test_pty_sync_interface(self):
        """Test synchronous interface with PTY."""
        received_data = []
        
        def on_rx(data: bytes):
            received_data.append(data)
            
        terminal = UartTerminal(on_rx=on_rx, mode='pty')
        
        try:
            terminal.start()
            time.sleep(0.2)
            
            slave_path = terminal.slave_path
            assert slave_path is not None
            
            # Test in separate thread
            def pty_thread():
                fd = os.open(slave_path, os.O_RDWR)
                try:
                    # Send data
                    os.write(fd, b'sync pty test')
                    
                    # Wait for response
                    time.sleep(0.1)
                    import fcntl
                    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                    
                    response = None
                    for _ in range(50):
                        try:
                            response = os.read(fd, 1024)
                            if response:
                                break
                        except OSError:
                            pass
                        time.sleep(0.1)
                        
                    assert response == b'sync pty response'
                    
                finally:
                    os.close(fd)
                    
            thread = threading.Thread(target=pty_thread)
            thread.start()
            
            # Wait for data
            time.sleep(0.2)
            
            assert len(received_data) == 1
            assert received_data[0] == b'sync pty test'
            
            # Send response
            terminal.write(b'sync pty response')
            
            thread.join(timeout=2.0)
            assert not thread.is_alive()
            
        finally:
            terminal.stop()
            
    def test_pty_error_handling(self):
        """Test PTY error handling."""
        # Test starting multiple PTY terminals (should work)
        terminal1 = UartTerminal(on_rx=lambda data: None, mode='pty')
        terminal2 = UartTerminal(on_rx=lambda data: None, mode='pty')
        
        try:
            terminal1.start()
            terminal2.start()
            time.sleep(0.2)
            
            # Both should have different slave paths
            path1 = terminal1.slave_path
            path2 = terminal2.slave_path
            
            assert path1 != path2
            assert path1 is not None
            assert path2 is not None
            
        finally:
            terminal1.stop()
            terminal2.stop()