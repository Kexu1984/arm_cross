#!/bin/bash
# check.sh - Verification script for ARM cross-compilation

set -e  # Exit on any error

echo "=== ARM Cross-Compilation Check Script ==="
echo ""

# Check if cross-compiler is available
CROSS=${CROSS:-arm-linux-gnueabihf-}
if ! command -v "${CROSS}gcc" &> /dev/null; then
    echo "Error: Cross-compiler ${CROSS}gcc not found!"
    echo "Please ensure ARM cross-compilation toolchain is installed."
    exit 1
fi

echo "✓ Cross-compiler found: $(which ${CROSS}gcc)"
echo "✓ Cross-compiler version:"
${CROSS}gcc --version | head -1

echo ""
echo "=== Building the sorting program ==="
make clean
make

echo ""
echo "=== Verifying the built ELF file ==="
if [ ! -f "build/sort.elf" ]; then
    echo "Error: build/sort.elf not found!"
    exit 1
fi

echo "✓ ELF file created: build/sort.elf"
echo ""

echo "=== ELF Header Analysis ==="
${CROSS}readelf -h build/sort.elf

echo ""
echo "=== ARM Architecture Verification ==="
if ${CROSS}readelf -h build/sort.elf | grep -q "Machine.*ARM"; then
    echo "✓ SUCCESS: ARM architecture confirmed!"
    ${CROSS}readelf -h build/sort.elf | grep "Machine"
else
    echo "✗ FAILURE: ARM architecture not found!"
    exit 1
fi

echo ""
echo "=== File Information ==="
file build/sort.elf
ls -lh build/sort.elf

echo ""
echo "=== All checks passed! ==="
echo "The sorting program has been successfully cross-compiled for ARM architecture."