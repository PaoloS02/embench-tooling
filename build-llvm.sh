#!/bin/bash

cd ${HOME}/gittrees/embench
rootdir=$(pwd)

mkdir -p build/llvm

rm -f ${rootdir}/logs/llvm-build.log
touch ${rootdir}/logs/llvm-build.log

# Clang/LLVM

cd ${rootdir}/build/llvm
echo "Starting at $(date)" >> ${rootdir}/logs/llvm-build.log 2>&1

echo -n "Configuring Clang/LLVM..."

if ! cmake \
     -DCMAKE_BUILD_TYPE=Debug \
     -DBUILD_SHARED_LIBS=ON \
     -DCMAKE_INSTALL_PREFIX=${rootdir}/install \
     -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=RISCV  \
     -DLLVM_BINUTILS_INCDIR=/${rootdir}/gnu/binutils-gdb/include \
     -DLLVM_ENABLE_THREADS=OFF \
     -G Ninja ${rootdir}/llvm/llvm >> ${rootdir}/logs/llvm-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building Clang/LLVM..."

if ! ninja -j 4 install >> ${rootdir}/logs/llvm-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo "Stopping at $(date)" >> ${rootdir}/logs/llvm-build.log 2>&1
