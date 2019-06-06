#!/bin/bash

cd ${HOME}/gittrees/embench
rootdir=$(pwd)

mkdir -p build/llvm

rm -f ${rootdir}/logs/llvm-build.log
touch ${rootdir}/logs/llvm-build.log

if [ "$(hostname)" = "longley" ]
then
    parallel="-j 4"
else
    parallel=""
fi

monorepo="monorepo/"

# Clang/LLVM

cd ${rootdir}/build/llvm
echo "Starting at $(date)" >> ${rootdir}/logs/llvm-build.log 2>&1

echo -n "Configuring Clang/LLVM..."
echo "Configuring Clang/LLVM" >> ${rootdir}/logs/llvm-build.log 2>&1

if ! cmake \
     -DCMAKE_BUILD_TYPE=Release \
     -DLLVM_OPTIMIZED_TABLEGEN=ON \
     -DLLVM_ENABLE_ASSERTIONS=ON \
     -DBUILD_SHARED_LIBS=ON \
     -DCMAKE_INSTALL_PREFIX=${rootdir}/install \
     -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=RISCV  \
     -DLLVM_BINUTILS_INCDIR=/${rootdir}/gnu/binutils-gdb/include \
     -DLLVM_ENABLE_THREADS=OFF \
     -G Ninja ${rootdir}/llvm/${monorepo}llvm \
     >> ${rootdir}/logs/llvm-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building and installing Clang/LLVM..."
echo "Building and installing Clang/LLVM" >> ${rootdir}/logs/llvm-build.log 2>&1

if ! ninja ${parallel} install >> ${rootdir}/logs/llvm-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Linking clang..."
echo "Linking clang" >> ${rootdir}/logs/llvm-build.log 2>&1

cd ${rootdir}/install/bin

if ! ln -sf clang riscv32-unknown-elf-clang
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Linking clang++..."
echo "Linking clang++" >> ${rootdir}/logs/llvm-build.log 2>&1

cd ${rootdir}/install/bin

if ! ln -sf clang++ riscv32-unknown-elf-clang++
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo "Stopping at $(date)" >> ${rootdir}/logs/llvm-build.log 2>&1
