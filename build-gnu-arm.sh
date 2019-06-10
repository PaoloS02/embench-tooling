#!/bin/bash

progdir="$(dirname $0)"
topdir="$(cd ${progdir}/..; pwd)"

installdir=${topdir}/install-arm
builddir=${topdir}/build-arm
logdir=${topdir}/logs
logfile=${logdir}/gnu-arm-build.log

mkdir -p ${builddir}/gnu/binutils-gdb
mkdir -p ${builddir}/gnu/gcc-stage-1
mkdir -p ${builddir}/gnu/gcc-stage-2
mkdir -p ${builddir}/gnu/newlib

rm -f ${logfile}
touch ${logfile}

export PATH=${installdir}/bin:${PATH}

if [ "$(hostname)" = "longley" ]
then
    parallel="-j 4"
else
    parallel="-j $(nproc)"
fi

triplet=arm-none-eabi
cpu=cortex-m4
mode=thumb
float=soft
#arch=rv32emc
#abi=ilp32e
cflags_for_target="-DPREFER_SIZE_OVER_SPEED=1 -Os"

# Binutils/GDB

cd ${builddir}/gnu/binutils-gdb
echo "Starting at $(date)" >> ${logfile} 2>&1

echo -n "Configuring Binutils/GDB..."
echo "Configuring Binutils/GDB" >> ${logfile} 2>&1

if ! ${topdir}/gnu/binutils-gdb/configure \
     --prefix=${installdir} \
     --sysconfdir=${installdir}/etc \
     --localstatedir=${installdir}/var \
     --disable-gtk-doc \
     --disable-gtk-doc-html \
     --disable-doc \
     --disable-docs \
     --disable-documentation \
     --with-xmlto=no \
     --with-fop=no \
     --disable-multilib \
     --enable-plugins \
     --target=${triplet} \
     --with-sysroot=${installdir}/${triplet}/sysroot \
     --enable-poison-system-directories \
     --disable-tls \
     --disable-sim >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building Binutils/GDB..."
echo "Building Binutils/GDB" >> ${logfile} 2>&1

if ! make ${parallel} >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing Binutils/GDB..."
echo "Installing Binutils/GDB" >> ${logfile} 2>&1

if ! make ${parallel} install >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

# GCC stage 1

cd ${builddir}/gnu/gcc-stage-1

echo -n "Configuring GCC Stage 1..."
echo "Configuring GCC Stage 1" >> ${logfile} 2>&1

if ! ${topdir}/gnu/gcc/configure \
     --prefix=${installdir} \
     --sysconfdir=${installdir}/etc \
     --localstatedir=${installdir}/var \
     --disable-shared \
     --disable-static \
     --disable-gtk-doc \
     --disable-gtk-doc-html \
     --disable-doc \
     --disable-docs \
     --disable-documentation \
     --with-xmlto=no \
     --with-fop=no \
     --target=${triplet} \
     --with-sysroot=${installdir}/${triplet}/sysroot \
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
     --with-cpu=${cpu} \
     --with-mode=${mode} \
     --with-float=${float} \
     --enable-languages=c \
     --without-headers \
     --with-newlib \
     --disable-largefile \
     --enable-plugins \
     --disable-nls \
     --enable-checking=yes >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building GCC Stage 1..."
echo "Building GCC Stage 1" >> ${logfile} 2>&1

if ! make ${parallel} all-gcc >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing GCC Stage 1..."
echo "Installing GCC Stage 1" >> ${logfile} 2>&1

if ! make ${parallel} install-gcc >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

# Newlib

cd ${builddir}/gnu/newlib

echo -n "Configuring Newlib..."
echo "Configuring Newlib" >> ${logfile} 2>&1

if ! ${topdir}/gnu/newlib/configure \
     --prefix=${installdir} \
     --sysconfdir=${installdir}/etc \
     --localstatedir=${installdir}/var \
     --target=${triplet} \
     --with-sysroot=${installdir}/${triplet}/sysroot \
     CFLAGS_FOR_TARGET="${cflags_for_target}" \
     --disable-newlib-fvwrite-in-streamio \
     --disable-newlib-fseek-optimization \
     --enable-newlib-nano-malloc \
     --disable-newlib-unbuf-stream-opt \
     --enable-target-optspace \
     --enable-newlib-reent-small \
     --disable-newlib-wide-orient \
     --disable-newlib-io-float \
     --enable-newlib-nano-formatted-io >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building Newlib..."
echo "Building Newlib" >> ${logfile} 2>&1

if ! make ${parallel} >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing Newlib..."
echo "Installing Newlib" >> ${logfile} 2>&1

if ! make ${parallel} install >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

# GCC Stage 2

cd ${builddir}/gnu/gcc-stage-2

echo -n "Configuring GCC Stage 2..."
echo "Configuring GCC Stage 2" >> ${logfile} 2>&1

if ! ${topdir}/gnu/gcc/configure \
     --with-build-time-tools=${installdir}/${triplet}/bin \
     --prefix=${installdir} \
     --sysconfdir=${installdir}/etc \
     --localstatedir=${installdir}/var \
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
     --target=${triplet} \
     --with-sysroot=${installdir}/${triplet}/sysroot \
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
     --with-cpu=${cpu} \
     --with-mode=${mode} \
     --with-float=${float} \
     --enable-languages=c,c++ \
     --with-newlib \
     --disable-largefile \
     --disable-nls \
     --enable-checking=yes >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building GCC Stage 2..."
echo "Building GCC Stage 2" >> ${logfile} 2>&1

if ! make ${parallel} all >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing GCC Stage 2..."
echo "Installing GCC Stage 2" >> ${logfile} 2>&1

if ! make ${parallel} install >> ${logfile} 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo "Stopping at $(date)" >> ${logfile} 2>&1
