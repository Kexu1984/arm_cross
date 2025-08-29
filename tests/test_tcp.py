"""
Tests for TCP transport mode.

Tests bidirectional communication via TCP sockets.
"""

import pytest
import asyncio
import threading
import time
from uart_terminal import UartTerminal


class TestTCPTransport:
    """Test TCP transport functionality."""

    @pytest.mark.asyncio
    async def test_tcp_bidirectional_communication(self):
        """Test bidirectional TCP communication."""
        received_data = []
        event = asyncio.Event()

        def on_rx(data: bytes):
            received_data.append(data)
            event.set()

        # Create terminal with random port
        terminal = UartTerminal(on_rx=on_rx, mode='tcp', tcp_port=0)

        try:
            # Start terminal
            terminal.start()

            # Give it time to start
            await asyncio.sleep(0.2)

            # Get actual port
            port = terminal.port
            assert port is not None and port > 0

            # Connect to the terminal
            reader, writer = await asyncio.open_connection('127.0.0.1', port)

            try:
                # Test RX direction: socket -> on_rx callback
                test_data = b'Hello UART RX!'
                writer.write(test_data)
                await writer.drain()

                # Wait for callback with timeout
                await asyncio.wait_for(event.wait(), timeout=2.0)

                assert len(received_data) == 1
                assert received_data[0] == test_data

                # Test TX direction: write() -> socket
                event.clear()
                received_data.clear()

                tx_data = b'Hello UART TX!'
                terminal.write(tx_data)

                # Read from socket
                response = await asyncio.wait_for(reader.read(1024), timeout=2.0)
                assert response == tx_data

            finally:
                writer.close()
                await writer.wait_closed()

        finally:
            terminal.stop()

    @pytest.mark.asyncio
    async def test_tcp_multiple_clients(self):
        """Test TCP with multiple clients."""
        terminal = UartTerminal(on_rx=lambda data: None, mode='tcp', tcp_port=0)

        try:
            terminal.start()
            await asyncio.sleep(0.2)

            port = terminal.port

            # Connect multiple clients
            clients = []
            for i in range(3):
                reader, writer = await asyncio.open_connection('127.0.0.1', port)
                clients.append((reader, writer))

            try:
                # Send data to all clients
                test_data = b'Broadcast message'
                terminal.write(test_data)

                # All clients should receive the data
                for reader, writer in clients:
                    response = await asyncio.wait_for(reader.read(1024), timeout=2.0)
                    assert response == test_data

            finally:
                for reader, writer in clients:
                    writer.close()
                    await writer.wait_closed()

        finally:
            terminal.stop()

    @pytest.mark.asyncio
    async def test_tcp_client_disconnect(self):
        """Test handling of client disconnection."""
        rx_data = []

        def on_rx(data: bytes):
            rx_data.append(data)

        terminal = UartTerminal(on_rx=on_rx, mode='tcp', tcp_port=0)

        try:
            terminal.start()
            await asyncio.sleep(0.2)

            port = terminal.port

            # Connect and immediately disconnect
            reader, writer = await asyncio.open_connection('127.0.0.1', port)
            writer.write(b'test')
            await writer.drain()
            writer.close()
            await writer.wait_closed()

            # Wait a bit for cleanup
            await asyncio.sleep(0.1)

            # Should still be able to connect new client
            reader2, writer2 = await asyncio.open_connection('127.0.0.1', port)

            try:
                terminal.write(b'after disconnect')
                response = await asyncio.wait_for(reader2.read(1024), timeout=2.0)
                assert response == b'after disconnect'

            finally:
                writer2.close()
                await writer2.wait_closed()

        finally:
            terminal.stop()

    def test_tcp_sync_interface(self):
        """Test synchronous interface from main thread."""
        received_data = []

        def on_rx(data: bytes):
            received_data.append(data)

        terminal = UartTerminal(on_rx=on_rx, mode='tcp', tcp_port=0)

        try:
            # Start from main thread
            terminal.start()
            time.sleep(0.2)

            port = terminal.port
            assert port is not None

            # Use a separate thread to test socket communication
            def client_thread():
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.connect(('127.0.0.1', port))

                    # Send data
                    sock.send(b'sync test')

                    # Wait for response
                    response = sock.recv(1024)
                    assert response == b'sync response'

                finally:
                    sock.close()

            client = threading.Thread(target=client_thread)
            client.start()

            # Give client time to connect and send
            time.sleep(0.2)

            # Check RX data received
            assert len(received_data) == 1
            assert received_data[0] == b'sync test'

            # Send response
            terminal.write(b'sync response')

            # Wait for client to finish
            client.join(timeout=2.0)
            assert not client.is_alive()

        finally:
            terminal.stop()
