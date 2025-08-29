"""
UART Terminal for Unicorn Cortex-M Simulation

A thread-safe UART terminal component providing bidirectional communication
between a simulated UART device and various terminal interfaces (PTY, TCP, Serial).
"""

from .terminal import UartTerminal

__version__ = "1.0.0"
__all__ = ["UartTerminal"]
