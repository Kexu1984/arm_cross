# arm_cross

A repository demonstrating ARMv7 cross-compilation for embedded development.

## Overview

This repository contains a minimal sorting program that demonstrates cross-compilation for ARM architecture using the ARM GNU Toolchain. The program implements a quicksort algorithm and is designed to be compiled for ARMv7 targets.

## Features

- **Sorting Algorithm**: Efficient quicksort implementation with O(n log n) average-case complexity
- **Cross-Compilation**: Configured for ARMv7 architecture using `arm-linux-gnueabihf-gcc`
- **Build System**: Makefile-based build system with customizable cross-compilation prefix
- **Verification**: Automated scripts to verify ARM ELF output

## Prerequisites

- ARM GNU Toolchain (`arm-linux-gnueabihf-gcc`, `arm-linux-gnueabihf-readelf`)
- GNU Make
- Standard C development tools

## Quick Start

### Building the Program

```bash
# Build with default ARM toolchain
make

# Build with custom cross-compiler prefix
make CROSS=arm-linux-gnueabihf-

# Clean build artifacts
make clean
```

### Verification

```bash
# Quick verification using Makefile
make check

# Comprehensive verification using script
./scripts/check.sh
```

### Manual Verification

```bash
# Check ELF architecture
arm-linux-gnueabihf-readelf -h build/sort.elf | grep Machine

# Expected output: Machine: ARM
```

## Project Structure

```
.
├── src/
│   └── sort.c          # Sorting program implementation
├── scripts/
│   └── check.sh        # Verification script
├── Makefile            # Build configuration
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Program Details

The sorting program (`src/sort.c`) features:

- **Algorithm**: Quicksort with in-place partitioning
- **Input**: Static array of 10 integers
- **Output**: Console display of original and sorted arrays
- **Compliance**: Compiles cleanly with `-Wall -Wextra -O2`

### Sample Output

```
ARM Cross-Compilation Sorting Demo
Algorithm: Quicksort
Array size: 10

Original array: 64, 34, 25, 12, 22, 11, 90, 88, 76, 50
Sorted array:   11, 12, 22, 25, 34, 50, 64, 76, 88, 90

Sorting completed successfully!
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

This project serves as an educational example for ARM cross-compilation techniques.
