FROM mcr.microsoft.com/devcontainers/base:ubuntu

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential make git file \
    gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf \
    binutils-arm-linux-gnueabihf \
 && rm -rf /var/lib/apt/lists/*
