# Makefile for ARMv7 cross-compilation of sorting program
# Usage: make [CROSS=<prefix>]
# Example: make CROSS=arm-linux-gnueabihf-

# Cross-compilation prefix (can be overridden)
CROSS ?= arm-linux-gnueabihf-

# Compiler and tools
CC = $(CROSS)gcc
READELF = $(CROSS)readelf

# Directories
SRCDIR = src
BUILDDIR = build

# Source files
SOURCES = $(SRCDIR)/sort.c
TARGET = $(BUILDDIR)/sort.elf

# Compiler flags
CFLAGS += -O2 -Wall -Wextra -march=armv7-a
LDFLAGS = 

# Default target
.PHONY: all
all: $(TARGET)

# Create build directory if it doesn't exist
$(BUILDDIR):
	mkdir -p $(BUILDDIR)

# Build the target
$(TARGET): $(SOURCES) | $(BUILDDIR)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf $(BUILDDIR)

# Check the built ELF file
.PHONY: check
check: $(TARGET)
	@echo "=== ELF Header Information ==="
	$(READELF) -h $(TARGET) | grep -E "(Class|Data|Machine|Entry)"
	@echo ""
	@echo "=== Verifying ARM Architecture ==="
	$(READELF) -h $(TARGET) | grep "Machine.*ARM" && echo "✓ ARM architecture confirmed" || echo "✗ ARM architecture not found"

# Show help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all     - Build the sorting program (default)"
	@echo "  clean   - Remove build artifacts"
	@echo "  check   - Verify the built ELF file"
	@echo "  help    - Show this help message"
	@echo ""
	@echo "Variables:"
	@echo "  CROSS   - Cross-compilation prefix (default: arm-linux-gnueabihf-)"
	@echo ""
	@echo "Examples:"
	@echo "  make"
	@echo "  make CROSS=arm-linux-gnueabihf-"
	@echo "  make clean"
	@echo "  make check"