"""
Example: Fake UART Device Model Integration

Demonstrates how to integrate UartTerminal with a simulated UART device.
Shows RX FIFO handling, interrupt simulation, and TX transmission.
"""

import time
import threading
from collections import deque
from typing import Optional
from uart_terminal import UartTerminal


class FakeUartDevice:
    """
    Simplified UART device model for demonstration.

    Features:
    - RX FIFO with configurable size
    - TX transmission via UartTerminal
    - Interrupt simulation for RX data
    - Simple echo functionality
    """

    def __init__(self, terminal: UartTerminal, fifo_size: int = 16):
        """
        Initialize fake UART device.

        Args:
            terminal: UartTerminal instance for actual I/O
            fifo_size: RX FIFO size in bytes
        """
        self.terminal = terminal
        self.fifo_size = fifo_size
        self.rx_fifo = deque()
        self.rx_interrupt_enabled = True
        self.running = False

        # Statistics
        self.rx_bytes_total = 0
        self.tx_bytes_total = 0
        self.interrupt_count = 0

        # Thread for processing
        self._process_thread = None

    def start(self) -> None:
        """Start the UART device processing."""
        if self.running:
            return

        self.running = True
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._process_thread.start()

        print("Fake UART Device started")

    def stop(self) -> None:
        """Stop the UART device processing."""
        self.running = False
        if self._process_thread and self._process_thread.is_alive():
            self._process_thread.join(timeout=1.0)
        print("Fake UART Device stopped")

    def on_rx_data(self, data: bytes) -> None:
        """
        Handle RX data from terminal (callback for UartTerminal).

        This simulates data arriving at the UART RX pin.
        """
        for byte in data:
            if len(self.rx_fifo) < self.fifo_size:
                self.rx_fifo.append(byte)
                self.rx_bytes_total += 1

                # Trigger RX interrupt if enabled and FIFO was empty
                if self.rx_interrupt_enabled and len(self.rx_fifo) == 1:
                    self._pend_rx_interrupt()
            else:
                print(f"RX FIFO overflow! Dropping byte: 0x{byte:02x}")

    def tx_byte(self, byte: int) -> None:
        """
        Transmit a byte via UART TX.

        This simulates writing to the UART TX register.
        """
        data = bytes([byte])
        self.terminal.write(data)
        self.tx_bytes_total += 1

    def tx_string(self, text: str) -> None:
        """Transmit a string via UART TX."""
        data = text.encode('utf-8')
        self.terminal.write(data)
        self.tx_bytes_total += len(data)

    def read_rx_byte(self) -> Optional[int]:
        """
        Read a byte from RX FIFO.

        Returns:
            Byte value or None if FIFO empty
        """
        if self.rx_fifo:
            return self.rx_fifo.popleft()
        return None

    def get_rx_count(self) -> int:
        """Get number of bytes in RX FIFO."""
        return len(self.rx_fifo)

    def _pend_rx_interrupt(self) -> None:
        """Simulate pending RX interrupt."""
        self.interrupt_count += 1
        # In real Cortex-M, this would call NVIC_SetPendingIRQ(UART_IRQn)
        print(f"RX Interrupt #{self.interrupt_count} (FIFO: {len(self.rx_fifo)} bytes)")

    def _process_loop(self) -> None:
        """
        Main processing loop (simulates interrupt service routine).

        Handles RX data and implements echo functionality.
        """
        while self.running:
            try:
                # Process RX FIFO (simulate ISR handling)
                while self.rx_fifo and self.running:
                    byte = self.read_rx_byte()
                    if byte is not None:
                        self._handle_rx_byte(byte)

                # Small delay to prevent busy-waiting
                time.sleep(0.01)

            except Exception as e:
                print(f"Process loop error: {e}")
                break

    def _handle_rx_byte(self, byte: int) -> None:
        """Handle a received byte (echo functionality)."""
        char = chr(byte) if 32 <= byte <= 126 else f'\\x{byte:02x}'
        print(f"Processing RX: 0x{byte:02x} ('{char}')")

        # Simple echo with newline handling
        if byte == ord('\r'):
            # Carriage return -> send CR+LF
            self.tx_string('\r\n')
        elif byte == ord('\n'):
            # Line feed -> send LF only
            self.tx_byte(ord('\n'))
        elif 32 <= byte <= 126:  # Printable ASCII
            # Echo the character
            self.tx_byte(byte)
        else:
            # Non-printable -> show hex
            self.tx_string(f'[0x{byte:02x}]')

    def get_stats(self) -> dict:
        """Get device statistics."""
        return {
            'rx_bytes_total': self.rx_bytes_total,
            'tx_bytes_total': self.tx_bytes_total,
            'interrupt_count': self.interrupt_count,
            'rx_fifo_count': len(self.rx_fifo),
            'rx_fifo_size': self.fifo_size
        }


def main():
    """Demo the fake UART device with UartTerminal."""
    import argparse

    parser = argparse.ArgumentParser(description='Fake UART Device Demo')
    parser.add_argument('--mode', choices=['pty', 'tcp', 'serial'],
                       default='pty', help='Terminal mode')
    parser.add_argument('--port', type=int, default=5555,
                       help='TCP port (tcp mode)')
    parser.add_argument('--serial-port', dest='serial_port',
                       help='Serial port (serial mode)')

    args = parser.parse_args()

    # Validate
    if args.mode == 'serial' and not args.serial_port:
        parser.error("--serial-port required for serial mode")

    print("Fake UART Device Demo")
    print("====================")
    print(f"Mode: {args.mode}")
    print("Connect to the terminal and type to see echo responses.")
    print("Press Ctrl+C to exit.\n")

    # Create fake device (temporary)
    fake_device = FakeUartDevice(None)

    try:
        # Create terminal with device's RX handler
        terminal = UartTerminal(
            on_rx=fake_device.on_rx_data,
            mode=args.mode,
            tcp_port=args.port,
            serial_port=args.serial_port
        )

        # Set terminal in device
        fake_device.terminal = terminal

        # Start everything
        terminal.start()
        fake_device.start()

        # Send welcome message
        time.sleep(0.2)  # Let terminal start
        fake_device.tx_string("=== Fake UART Device Ready ===\r\n")
        fake_device.tx_string("Type to see echo responses.\r\n")

        # Status reporting loop
        start_time = time.time()
        while True:
            time.sleep(5.0)  # Report every 5 seconds

            stats = fake_device.get_stats()
            elapsed = time.time() - start_time

            print(f"\n--- Stats (uptime: {elapsed:.1f}s) ---")
            print(
                f"RX: {stats['rx_bytes_total']} bytes, "
                f"{stats['interrupt_count']} interrupts"
            )
            print(f"TX: {stats['tx_bytes_total']} bytes")
            print(f"FIFO: {stats['rx_fifo_count']}/{stats['rx_fifo_size']} bytes")

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'fake_device' in locals():
            fake_device.stop()
        if 'terminal' in locals():
            terminal.stop()


if __name__ == '__main__':
    main()
