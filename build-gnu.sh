#!/bin/bash

cd ${HOME}/gittrees/embench
rootdir=$(pwd)

mkdir -p build/gnu/binutils-gdb
mkdir -p build/gnu/gcc-stage-1
mkdir -p build/gnu/gcc-stage-2
mkdir -p build/gnu/newlib

rm -f ${rootdir}/logs/gnu-build.log
touch ${rootdir}/logs/gnu-build.log

export PATH=${rootdir}/install/bin:${PATH}

# Binutils/GDB

cd ${rootdir}/build/gnu/binutils-gdb
echo "Starting at $(date)" >> ${rootdir}/logs/gnu-build.log 2>&1

echo -n "Configuring Binutils/GDB..."
echo "Configuring Binutils/GDB" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! ${rootdir}/gnu/binutils-gdb/configure \
     --prefix=${rootdir}/install \
     --sysconfdir=${rootdir}/install/etc \
     --localstatedir=${rootdir}/install/var \
     --disable-gtk-doc \
     --disable-gtk-doc-html \
     --disable-doc \
     --disable-docs \
     --disable-documentation \
     --with-xmlto=no \
     --with-fop=no \
     --disable-multilib \
     --enable-plugins \
     --target=riscv32-unknown-elf \
     --with-sysroot=${rootdir}/install/riscv32-unknown-elf/sysroot \
     --enable-poison-system-directories \
     --disable-tls \
     --disable-sim >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building Binutils/GDB..."
echo "Building Binutils/GDB" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! make -j 4 >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing Binutils/GDB..."
echo "Installing Binutils/GDB" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! make -j 4 install >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

# GCC stage 1

cd ${rootdir}/build/gnu/gcc-stage-1

echo -n "Configuring GCC Stage 1..."
echo "Configuring GCC Stage 1" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! ${rootdir}/gnu/gcc/configure \
     --prefix=${rootdir}/install \
     --sysconfdir=${rootdir}/install/etc \
     --localstatedir=${rootdir}/install/var \
     --disable-shared \
     --disable-static \
     --disable-gtk-doc \
     --disable-gtk-doc-html \
     --disable-doc \
     --disable-docs \
     --disable-documentation \
     --with-xmlto=no \
     --with-fop=no \
     --target=riscv32-unknown-elf \
     --with-sysroot=${rootdir}/install/riscv32-unknown-elf/sysroot \
     --disable-__cxa_atexit \
     --with-gnu-ld \
     --disable-libssp \
     --disable-multilib \
     --enable-target-optspace \
     --disable-libsanitizer \
     --disable-tls \
     --disable-libmudflap \
     --disable-threads \
     --disable-libquadmath \
     --disable-libgomp \
     --without-isl \
     --without-cloog \
     --disable-decimal-float \
     --with-arch=rv32imac \
     --with-abi=ilp32 \
     --enable-languages=c \
     --without-headers \
     --with-newlib \
     --disable-largefile \
     --enable-plugins \
     --disable-nls \
     --enable-checking=yes >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building GCC Stage 1..."
echo "Building GCC Stage 1" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! make -j 4 all-gcc >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing GCC Stage 1..."
echo "Installing GCC Stage 1" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! make -j 4 install-gcc >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

# Newlib

cd ${rootdir}/build/gnu/newlib

echo -n "Configuring Newlib..."
echo "Configuring Newlib" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! ${rootdir}/gnu/newlib/configure \
     --prefix=${rootdir}/install \
     --sysconfdir=${rootdir}/install/etc \
     --localstatedir=${rootdir}/install/var \
     --target=riscv32-unknown-elf \
     --with-sysroot=${rootdir}/install/riscv32-unknown-elf/sysroot \
     CFLAGS_FOR_TARGET="-DPREFER_SIZE_OVER_SPEED=1 -Os -march=rv32imc -mabi=ilp32" \
     --disable-newlib-fvwrite-in-streamio \
     --disable-newlib-fseek-optimization \
     --enable-newlib-nano-malloc \
     --disable-newlib-unbuf-stream-opt \
     --enable-target-optspace \
     --enable-newlib-reent-small \
     --disable-newlib-wide-orient \
     --disable-newlib-io-float \
     --enable-newlib-nano-formatted-io >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building Newlib..."
echo "Building Newlib" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! make -j 4 >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing Newlib..."
echo "Installing Newlib" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! make -j 4 install >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

# GCC Stage 2

cd ${rootdir}/build/gnu/gcc-stage-2

echo -n "Configuring GCC Stage 2..."
echo "Configuring GCC Stage 2" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! ${rootdir}/gnu/gcc/configure \
     --with-build-time-tools=${rootdir}/install/riscv32-unknown-elf/bin \
     --prefix=${rootdir}/install \
     --sysconfdir=${rootdir}/install/etc \
     --localstatedir=${rootdir}/install/var \
     --disable-shared \
     --enable-plugins \
     --enable-static \
     --disable-gtk-doc \
     --disable-gtk-doc-html \
     --disable-doc \
     --disable-docs \
     --disable-documentation \
     --with-xmlto=no \
     --with-fop=no \
     --target=riscv32-unknown-elf \
     --with-sysroot=${rootdir}/install/riscv32-unknown-elf/sysroot \
     --disable-__cxa_atexit \
     --with-gnu-ld \
     --disable-libssp \
     --disable-multilib \
     --enable-target-optspace \
     --disable-libsanitizer \
     --disable-tls \
     --disable-libmudflap \
     --disable-threads \
     --disable-libquadmath \
     --disable-libgomp \
     --without-isl \
     --without-cloog \
     --disable-decimal-float \
     --with-arch=rv32imac \
     --with-abi=ilp32 \
     --enable-languages=c,c++ \
     --with-newlib \
     --disable-largefile \
     --disable-nls \
     --enable-checking=yes >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building GCC Stage 2..."
echo "Building GCC Stage 2" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! make -j 4 all >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing GCC Stage 2..."
echo "Installing GCC Stage 2" >> ${rootdir}/logs/gnu-build.log 2>&1

if ! make -j 4 install >> ${rootdir}/logs/gnu-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo "Stopping at $(date)" >> ${rootdir}/logs/gnu-build.log 2>&1
