"""
Tests for Serial transport mode.

Tests serial communication using loop:// virtual ports when available.
Falls back to xfail when loop:// is not supported.
"""

import pytest
import asyncio
import time
import threading
from uart_terminal import UartTerminal

# Check if pyserial is available and supports loop://
try:
    import serial
    HAS_SERIAL = True
    
    # Test if loop:// is supported
    try:
        test_port = serial.Serial('loop://', timeout=0.1)
        test_port.close()
        HAS_LOOP = True
    except Exception:
        HAS_LOOP = False
        
except ImportError:
    HAS_SERIAL = False
    HAS_LOOP = False


@pytest.mark.skipif(not HAS_SERIAL or not HAS_LOOP, reason="pyserial with loop:// support not available")
class TestSerialTransport:
    """Test Serial transport functionality."""
    
    @pytest.mark.asyncio
    async def test_serial_loop_creation(self):
        """Test loop:// serial port creation."""
        terminal = UartTerminal(
            on_rx=lambda data: None, 
            mode='serial', 
            serial_port='loop://'
        )
        
        try:
            terminal.start()
            await asyncio.sleep(0.2)
            
            # Should start without error
            # No specific properties to check for loop://
            
        finally:
            terminal.stop()
            
    @pytest.mark.asyncio
    async def test_serial_bidirectional_communication(self):
        """Test bidirectional serial communication with loop://."""
        received_data = []
        event = asyncio.Event()
        
        def on_rx(data: bytes):
            received_data.append(data)
            event.set()
            
        terminal = UartTerminal(
            on_rx=on_rx,
            mode='serial',
            serial_port='loop://',
            serial_baud=115200
        )
        
        try:
            terminal.start()
            await asyncio.sleep(0.2)
            
            # Open another connection to the same loop://
            ser = serial.Serial('loop://', 115200, timeout=1.0)
            
            try:
                # Test RX direction: serial -> on_rx callback
                test_data = b'Hello Serial RX!'
                ser.write(test_data)
                ser.flush()
                
                # Wait for callback
                await asyncio.wait_for(event.wait(), timeout=3.0)
                
                assert len(received_data) == 1
                assert received_data[0] == test_data
                
                # Test TX direction: write() -> serial
                tx_data = b'Hello Serial TX!'
                terminal.write(tx_data)
                
                # Read from serial port
                response = ser.read(len(tx_data))
                assert response == tx_data
                
            finally:
                ser.close()
                
        finally:
            terminal.stop()
            
    @pytest.mark.asyncio
    async def test_serial_multiple_writes(self):
        """Test multiple serial writes."""
        received_data = []
        
        def on_rx(data: bytes):
            received_data.append(data)
            
        terminal = UartTerminal(
            on_rx=on_rx,
            mode='serial', 
            serial_port='loop://'
        )
        
        try:
            terminal.start()
            await asyncio.sleep(0.2)
            
            ser = serial.Serial('loop://', 115200, timeout=1.0)
            
            try:
                # Send multiple messages
                messages = [b'msg1', b'msg2', b'msg3']
                
                for msg in messages:
                    terminal.write(msg)
                    await asyncio.sleep(0.1)  # Small delay between writes
                    
                # Read all responses
                responses = []
                for _ in messages:
                    data = ser.read(4)  # Each message is 4 bytes
                    if data:
                        responses.append(data)
                        
                assert responses == messages
                
            finally:
                ser.close()
                
        finally:
            terminal.stop()
            
    def test_serial_sync_interface(self):
        """Test synchronous interface with serial."""
        received_data = []
        
        def on_rx(data: bytes):
            received_data.append(data)
            
        terminal = UartTerminal(
            on_rx=on_rx,
            mode='serial',
            serial_port='loop://',
            serial_baud=9600  # Different baud rate
        )
        
        try:
            terminal.start()
            time.sleep(0.3)  # Longer wait for serial startup
            
            def serial_thread():
                ser = serial.Serial('loop://', 9600, timeout=2.0)
                try:
                    # Send data
                    ser.write(b'sync serial test')
                    ser.flush()
                    
                    # Wait for response  
                    response = ser.read(17)  # Length of expected response
                    assert response == b'sync serial resp'
                    
                finally:
                    ser.close()
                    
            thread = threading.Thread(target=serial_thread)
            thread.start()
            
            # Wait for data
            time.sleep(0.5)
            
            assert len(received_data) == 1
            assert received_data[0] == b'sync serial test'
            
            # Send response
            terminal.write(b'sync serial resp')
            
            thread.join(timeout=3.0)
            assert not thread.is_alive()
            
        finally:
            terminal.stop()
            
    def test_serial_error_handling(self):
        """Test serial error handling."""
        # Test invalid port - should handle gracefully  
        terminal = UartTerminal(
            on_rx=lambda data: None,
            mode='serial',
            serial_port='/dev/nonexistent'
        )
        terminal.start()
        try:
            time.sleep(0.1)
            # Error should be logged, terminal should handle gracefully
        finally:
            terminal.stop()
                
    @pytest.mark.asyncio
    async def test_serial_port_close_handling(self):
        """Test handling when serial port is closed.""" 
        rx_count = 0
        
        def on_rx(data: bytes):
            nonlocal rx_count
            rx_count += 1
            
        terminal = UartTerminal(
            on_rx=on_rx,
            mode='serial',
            serial_port='loop://'
        )
        
        try:
            terminal.start()
            await asyncio.sleep(0.2)
            
            # Open, send data, and close
            ser = serial.Serial('loop://', 115200, timeout=1.0)
            ser.write(b'test before close')
            ser.flush()
            ser.close()
            
            await asyncio.sleep(0.2)
            
            # Should have received the data
            assert rx_count > 0
            
            # Terminal should still be running
            terminal.write(b'test after close')
            
        finally:
            terminal.stop()

# Tests that don't require loop:// support 
@pytest.mark.skipif(not HAS_SERIAL, reason="pyserial not available")  
def test_serial_basic_initialization():
    """Test basic serial initialization without connection."""
    # Should not raise when creating terminal
    terminal = UartTerminal(
        on_rx=lambda data: None,
        mode='serial',
        serial_port='/dev/null'  # Won't work but shouldn't crash during init
    )
    # Don't start it since /dev/null won't work


@pytest.mark.skipif(HAS_SERIAL, reason="Testing missing pyserial")
def test_serial_missing_pyserial():
    """Test error when pyserial is not available."""
    with pytest.raises(RuntimeError, match="pyserial not available"):
        terminal = UartTerminal(
            on_rx=lambda data: None,
            mode='serial',
            serial_port='loop://'
        )
        terminal.start()
        try:
            time.sleep(0.1)
        finally:
            terminal.stop()