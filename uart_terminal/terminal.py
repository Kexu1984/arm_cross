"""
UART Terminal Implementation

Provides UartTerminal class with three transport modes:
- PTY: Creates pseudo-terminal for screen/picocom connection
- TCP: TCP server for telnet/nc connection  
- Serial: Real or virtual serial port via pyserial
"""

import asyncio
import os
import sys
import threading
import socket
from abc import ABC, abstractmethod
from typing import Callable, Optional
import logging

# Optional import for serial support
try:
    import serial
    import serial.threaded
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

logger = logging.getLogger(__name__)


class Transport(ABC):
    """Abstract base class for transport implementations."""
    
    def __init__(self, on_rx: Callable[[bytes], None]):
        self.on_rx = on_rx
        self._running = False
        
    @abstractmethod
    async def start(self) -> None:
        """Start the transport."""
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport."""
        pass
        
    @abstractmethod
    async def write(self, data: bytes) -> None:
        """Write data to the transport."""
        pass


class PTYTransport(Transport):
    """PTY transport for POSIX systems."""
    
    def __init__(self, on_rx: Callable[[bytes], None]):
        super().__init__(on_rx)
        self.master_fd = None
        self.slave_fd = None
        self.slave_path = None
        
    async def start(self) -> None:
        """Create PTY pair and start monitoring."""
        if sys.platform == 'win32':
            raise RuntimeError("PTY transport not supported on Windows")
            
        try:
            import pty
            self.master_fd, self.slave_fd = pty.openpty()
            self.slave_path = os.ttyname(self.slave_fd)
            
            # Set master fd to non-blocking
            os.set_blocking(self.master_fd, False)
            
            self._running = True
            
            # Add reader to event loop
            loop = asyncio.get_running_loop()
            loop.add_reader(self.master_fd, self._on_master_readable)
            
            print(f"PTY terminal ready: {self.slave_path}")
            print(f"Connect with: screen {self.slave_path} 115200")
            
        except Exception as e:
            logger.error(f"Failed to create PTY: {e}")
            raise
            
    async def stop(self) -> None:
        """Stop PTY monitoring and close resources."""
        if self._running:
            self._running = False
            
            if self.master_fd is not None:
                try:
                    loop = asyncio.get_running_loop()
                    loop.remove_reader(self.master_fd)
                    os.close(self.master_fd)
                except Exception as e:
                    logger.warning(f"Error closing PTY master: {e}")
                finally:
                    self.master_fd = None
                    
            if self.slave_fd is not None:
                try:
                    os.close(self.slave_fd)
                except Exception as e:
                    logger.warning(f"Error closing PTY slave: {e}")
                finally:
                    self.slave_fd = None
                    
    def _on_master_readable(self) -> None:
        """Handle data from PTY master."""
        try:
            data = os.read(self.master_fd, 1024)
            if data and self._running:
                self.on_rx(data)
        except OSError:
            # PTY closed or other error
            if self._running:
                logger.warning("PTY read error, stopping")
                asyncio.create_task(self.stop())
                
    async def write(self, data: bytes) -> None:
        """Write data to PTY."""
        if self.master_fd is not None and self._running:
            try:
                os.write(self.master_fd, data)
            except OSError as e:
                logger.warning(f"PTY write error: {e}")


class TCPTransport(Transport):
    """TCP transport with multi-client support."""
    
    def __init__(self, on_rx: Callable[[bytes], None], host: str = '127.0.0.1', port: int = 5555):
        super().__init__(on_rx)
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        
    async def start(self) -> None:
        """Start TCP server."""
        try:
            self.server = await asyncio.start_server(
                self._handle_client, self.host, self.port
            )
            self._running = True
            
            # Get actual port if port was 0 (random port)
            actual_port = self.server.sockets[0].getsockname()[1]
            print(f"TCP terminal ready on {self.host}:{actual_port}")
            print(f"Connect with: telnet {self.host} {actual_port}")
            
            # Store actual port for tests
            self.port = actual_port
            
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
            raise
            
    async def stop(self) -> None:
        """Stop TCP server and disconnect all clients."""
        self._running = False
        
        # Close all client connections
        for writer in list(self.clients):
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.warning(f"Error closing client: {e}")
        self.clients.clear()
        
        # Close server
        if self.server:
            try:
                self.server.close()
                await self.server.wait_closed()
            except Exception as e:
                logger.warning(f"Error closing TCP server: {e}")
            finally:
                self.server = None
                
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle a new TCP client connection."""
        addr = writer.get_extra_info('peername')
        logger.info(f"Client connected from {addr}")
        
        self.clients.add(writer)
        
        try:
            while self._running:
                data = await reader.read(1024)
                if not data:
                    break
                    
                # Forward received data to UART RX
                self.on_rx(data)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Client {addr} error: {e}")
        finally:
            self.clients.discard(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.info(f"Client {addr} disconnected")
            
    async def write(self, data: bytes) -> None:
        """Write data to all connected TCP clients."""
        if not self._running:
            return
            
        # Send to all connected clients
        for writer in list(self.clients):
            try:
                writer.write(data)
                await writer.drain()
            except Exception as e:
                logger.warning(f"Failed to write to client: {e}")
                self.clients.discard(writer)


class SerialTransport(Transport):
    """Serial transport using pyserial."""
    
    def __init__(self, on_rx: Callable[[bytes], None], port: str, baudrate: int = 115200):
        super().__init__(on_rx)
        self.port = port
        self.baudrate = baudrate
        self.serial_port = None
        self._read_task = None
        
    async def start(self) -> None:
        """Open serial port and start reading."""
        if not HAS_SERIAL:
            raise RuntimeError("pyserial not available. Install with: pip install pyserial")
            
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1  # Non-blocking reads
            )
            
            self._running = True
            self._read_task = asyncio.create_task(self._read_loop())
            
            print(f"Serial terminal ready on {self.port} @ {self.baudrate} baud")
            
        except Exception as e:
            logger.error(f"Failed to open serial port {self.port}: {e}")
            raise
            
    async def stop(self) -> None:
        """Stop serial monitoring and close port."""
        self._running = False
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
            self._read_task = None
            
        if self.serial_port:
            try:
                self.serial_port.close()
            except Exception as e:
                logger.warning(f"Error closing serial port: {e}")
            finally:
                self.serial_port = None
                
    async def _read_loop(self) -> None:
        """Async loop to read from serial port."""
        while self._running and self.serial_port:
            try:
                # Check for available data
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        self.on_rx(data)
                
                # Small delay to prevent busy-waiting
                await asyncio.sleep(0.01)
                
            except Exception as e:
                if self._running:
                    logger.warning(f"Serial read error: {e}")
                    break
                    
    async def write(self, data: bytes) -> None:
        """Write data to serial port."""
        if self.serial_port and self._running:
            try:
                self.serial_port.write(data)
                self.serial_port.flush()
            except Exception as e:
                logger.warning(f"Serial write error: {e}")


class UartTerminal:
    """
    UART Terminal with multiple transport options.
    
    Provides bidirectional communication between simulated UART and terminal interfaces.
    Runs asyncio event loop in background thread for thread-safe operation.
    """
    
    def __init__(self, 
                 on_rx: Callable[[bytes], None],
                 mode: str = 'pty',
                 tcp_host: str = '127.0.0.1',
                 tcp_port: int = 5555,
                 serial_port: Optional[str] = None,
                 serial_baud: int = 115200):
        """
        Initialize UART Terminal.
        
        Args:
            on_rx: Callback for received data from terminal
            mode: Transport mode ('pty', 'tcp', 'serial')
            tcp_host: TCP server host for TCP mode
            tcp_port: TCP server port for TCP mode  
            serial_port: Serial port path for serial mode
            serial_baud: Serial port baudrate for serial mode
        """
        self.on_rx = on_rx
        self.mode = mode
        self._thread = None
        self._loop = None
        self._transport = None
        self._stop_event = None
        
        # Create transport based on mode
        if mode == 'pty':
            self._transport = PTYTransport(on_rx)
        elif mode == 'tcp':
            self._transport = TCPTransport(on_rx, tcp_host, tcp_port)
        elif mode == 'serial':
            if not serial_port:
                raise ValueError("serial_port required for serial mode")
            self._transport = SerialTransport(on_rx, serial_port, serial_baud)
        else:
            raise ValueError(f"Unknown mode: {mode}")
            
    def start(self) -> None:
        """Start the terminal in background thread."""
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Terminal already started")
            
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()
        
        # Wait a moment for startup
        import time
        time.sleep(0.1)
        
    def stop(self) -> None:
        """Stop the terminal and clean up resources."""
        if self._stop_event:
            self._stop_event.set()
            
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            
        self._thread = None
        self._loop = None
        self._transport = None
        self._stop_event = None
        
    def write(self, data: bytes) -> None:
        """Write data to terminal (thread-safe)."""
        if self._loop and self._transport:
            # Schedule coroutine in the background loop
            asyncio.run_coroutine_threadsafe(
                self._transport.write(data), self._loop
            )
            
    def _run_async_loop(self) -> None:
        """Run asyncio event loop in background thread."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            self._loop.run_until_complete(self._async_main())
            
        except Exception as e:
            logger.error(f"Terminal loop error: {e}")
        finally:
            try:
                self._loop.close()
            except Exception:
                pass
                
    async def _async_main(self) -> None:
        """Main async function running in background thread."""
        try:
            await self._transport.start()
            
            # Run until stop requested
            while not self._stop_event.is_set():
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Transport error: {e}")
        finally:
            try:
                await self._transport.stop()
            except Exception as e:
                logger.warning(f"Transport stop error: {e}")

    @property 
    def port(self) -> Optional[int]:
        """Get actual TCP port (for tests with random port)."""
        if self.mode == 'tcp' and self._transport:
            return getattr(self._transport, 'port', None)
        return None

    @property
    def slave_path(self) -> Optional[str]:
        """Get PTY slave path (for tests)."""
        if self.mode == 'pty' and self._transport:
            return getattr(self._transport, 'slave_path', None)
        return None