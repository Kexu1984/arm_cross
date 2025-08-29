"""
Command Line Interface for UART Terminal

Provides command-line entry point for testing and demonstration.
"""

import argparse
import sys
import time
import threading
from uart_terminal import UartTerminal


class TerminalDemo:
    """Demo application for UART Terminal."""

    def __init__(self, terminal: UartTerminal):
        self.terminal = terminal
        self.running = True
        self.tx_counter = 0

    def on_rx(self, data: bytes) -> None:
        """Handle received data from terminal."""
        try:
            text = data.decode('utf-8', errors='replace')
            print(f"RX: {repr(text)}")

            # Echo back the received data (demonstrate TX)
            echo_msg = f"Echo: {text}".encode('utf-8')
            self.terminal.write(echo_msg)

        except Exception as e:
            print(f"RX Error: {e}")

    def start_demo(self) -> None:
        """Start the demo."""
        print("UART Terminal Demo")
        print("==================")
        print("The terminal will periodically send demo messages.")
        print("Type in the terminal to see echo responses.")
        print("Press Ctrl+C to exit.\n")

        # Start terminal
        self.terminal.start()

        # Start demo TX thread
        tx_thread = threading.Thread(target=self._tx_demo_loop, daemon=True)
        tx_thread.start()

        try:
            # Main loop
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.running = False
            self.terminal.stop()

    def _tx_demo_loop(self) -> None:
        """Periodically send demo messages."""
        while self.running:
            try:
                self.tx_counter += 1
                demo_msg = (
                    f"Demo TX #{self.tx_counter} - "
                    f"{time.strftime('%H:%M:%S')}\r\n"
                )
                self.terminal.write(demo_msg.encode('utf-8'))

                # Wait 3 seconds between messages
                for _ in range(30):  # 30 * 0.1s = 3s
                    if not self.running:
                        break
                    time.sleep(0.1)

            except Exception as e:
                print(f"TX Demo Error: {e}")
                break


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='UART Terminal for Unicorn Cortex-M Simulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uart-term --mode pty
  uart-term --mode tcp --port 5555
  uart-term --mode serial --port /dev/ttyUSB0 --baud 115200
  uart-term --mode serial --port loop://  # Virtual loopback
        """
    )

    parser.add_argument('--mode', choices=['pty', 'tcp', 'serial'],
                       default='pty', help='Terminal mode')
    parser.add_argument('--host', default='127.0.0.1',
                       help='TCP host (tcp mode only)')
    parser.add_argument('--port', type=int, default=5555,
                       help='TCP port (tcp mode only)')
    parser.add_argument('--serial-port', dest='serial_port',
                       help='Serial port path (serial mode only)')
    parser.add_argument('--baud', type=int, default=115200,
                       help='Serial baudrate (serial mode only)')

    args = parser.parse_args()

    # Validate arguments
    if args.mode == 'serial' and not args.serial_port:
        parser.error("--serial-port required for serial mode")

    # Create demo instance
    demo = TerminalDemo(None)  # Temporary

    try:
        # Create terminal with demo's rx handler
        terminal = UartTerminal(
            on_rx=demo.on_rx,
            mode=args.mode,
            tcp_host=args.host,
            tcp_port=args.port,
            serial_port=args.serial_port,
            serial_baud=args.baud
        )

        # Set terminal in demo
        demo.terminal = terminal

        # Start demo
        demo.start_demo()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
