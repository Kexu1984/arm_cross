# arm_cross

A repository demonstrating ARMv7 cross-compilation for embedded development, now featuring an interactive UART terminal for Unicorn Cortex-M simulation.

## Overview

This repository contains:

1. **ARM Cross-Compilation Demo**: A minimal sorting program demonstrating cross-compilation for ARM architecture using the ARM GNU Toolchain
2. **UART Terminal Component**: A thread-safe interactive UART terminal for Unicorn-based Cortex-M simulation with PTY, TCP, and Serial transport modes

## Features

### ARM Cross-Compilation
- **Sorting Algorithm**: Efficient quicksort implementation with O(n log n) average-case complexity
- **Cross-Compilation**: Configured for ARMv7 architecture using `arm-linux-gnueabihf-gcc`
- **Build System**: Makefile-based build system with customizable cross-compilation prefix
- **Verification**: Automated scripts to verify ARM ELF output

### UART Terminal
- **Three Transport Modes**: PTY (Linux/macOS), TCP (multi-client), and Serial (pyserial)
- **Thread-Safe Design**: Uses asyncio event loop in background thread
- **Simple API**: Easy integration with UART device models
- **Comprehensive Testing**: Full test coverage for all transport modes

## Prerequisites

### ARM Cross-Compilation
- ARM GNU Toolchain (`arm-linux-gnueabihf-gcc`, `arm-linux-gnueabihf-readelf`)
- GNU Make
- Standard C development tools

### UART Terminal
- Python 3.10+
- pyserial (for serial mode)
- pytest and pytest-asyncio (for testing)

## Quick Start

### ARM Cross-Compilation

#### Building the Program

```bash
# Build with default ARM toolchain
make

# Build with custom cross-compiler prefix
make CROSS=arm-linux-gnueabihf-

# Clean build artifacts
make clean
```

#### Verification

```bash
# Quick verification using Makefile
make check

# Comprehensive verification using script
./scripts/check.sh
```

#### Manual Verification

```bash
# Check ELF architecture
arm-linux-gnueabihf-readelf -h build/sort.elf | grep Machine

# Expected output: Machine: ARM
```

### UART Terminal

#### Installation

```bash
# Install UART terminal dependencies
pip install pyserial pytest pytest-asyncio

# Install package in development mode
pip install -e .
```

#### Command Line Usage

```bash
# PTY mode (Linux/macOS)
uart-term --mode pty

# TCP mode
uart-term --mode tcp --port 5555

# Serial mode
uart-term --mode serial --serial-port /dev/ttyUSB0 --baud 115200

# Or use Python module
python -m uart_terminal --mode pty
```

#### Python API

```python
from uart_terminal import UartTerminal

def on_rx_data(data: bytes):
    print(f"Received: {data}")
    
terminal = UartTerminal(on_rx=on_rx_data, mode='pty')
terminal.start()
terminal.write(b"Hello Terminal!\r\n")
terminal.stop()
```

## Project Structure

```
.
├── src/
│   └── sort.c               # ARM sorting program implementation
├── uart_terminal/           # UART terminal package
│   ├── __init__.py
│   ├── terminal.py          # UartTerminal implementation
│   └── cli.py              # Command line interface
├── examples/
│   └── fake_uart_device.py # UART device integration example
├── tests/                  # Test suite
│   ├── test_tcp.py         # TCP transport tests
│   ├── test_pty.py         # PTY transport tests
│   └── test_serial.py      # Serial transport tests
├── scripts/
│   └── check.sh            # ARM verification script
├── .github/workflows/
│   └── ci.yml              # CI configuration
├── Makefile                # ARM build configuration
├── pyproject.toml          # Python packaging
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Program Details

### ARM Sorting Program

The sorting program (`src/sort.c`) features:

- **Algorithm**: Quicksort with in-place partitioning
- **Input**: Static array of 10 integers
- **Output**: Console display of original and sorted arrays
- **Compliance**: Compiles cleanly with `-Wall -Wextra -O2`

#### Sample Output

```
ARM Cross-Compilation Sorting Demo
Algorithm: Quicksort
Array size: 10

Original array: 64, 34, 25, 12, 22, 11, 90, 88, 76, 50
Sorted array:   11, 12, 22, 25, 34, 50, 64, 76, 88, 90

Sorting completed successfully!
```

### UART Terminal Component

The UART terminal provides bidirectional communication for Cortex-M simulation:

#### Transport Modes

1. **PTY Mode** (Linux/macOS): Creates pseudo-terminal for `screen`/`picocom`
2. **TCP Mode**: TCP server for `telnet`/`nc` with multi-client support
3. **Serial Mode**: Real or virtual serial ports via pyserial

#### Integration Example

```python
from uart_terminal import UartTerminal

class UartDevice:
    def __init__(self):
        self.terminal = UartTerminal(on_rx=self.on_uart_rx, mode='pty')
        self.rx_fifo = []
        
    def on_uart_rx(self, data: bytes):
        """Handle RX data from terminal."""
        for byte in data:
            self.rx_fifo.append(byte)
            if len(self.rx_fifo) == 1:
                self.trigger_rx_interrupt()
                
    def uart_tx_write(self, byte: int):
        """Send TX data to terminal."""
        self.terminal.write(bytes([byte]))
        
    def trigger_rx_interrupt(self):
        """Trigger UART RX interrupt."""
        print("UART RX interrupt triggered")
```

#### Testing

```bash
# Run all tests
pytest

# Run specific transport tests
pytest tests/test_tcp.py
pytest tests/test_pty.py  
pytest tests/test_serial.py
```

## Build Configuration

The Makefile includes:

- **Target Architecture**: ARMv7-A (`-march=armv7-a`)
- **Optimization**: Level 2 (`-O2`)
- **Warning Flags**: Comprehensive warnings (`-Wall -Wextra`)
- **Cross-Compilation**: Configurable prefix (default: `arm-linux-gnueabihf-`)

## Development Environment

This project is designed to work with:

- **GitHub Codespaces**: Pre-configured development containers
- **GitHub Actions**: Automated build and verification
- **Local Development**: Standard ARM cross-compilation toolchain

## Contributing

When contributing:

1. Ensure code compiles without warnings
2. Run verification scripts before submitting
3. Update documentation for significant changes
4. Follow existing code style and structure

## License

This project serves as an educational example for ARM cross-compilation techniques and UART terminal integration with embedded simulation.
