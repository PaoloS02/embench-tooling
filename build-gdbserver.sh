#!/bin/bash

cd ${HOME}/gittrees/embench
rootdir=$(pwd)

mkdir -p build/gdbserver

rm -f ${rootdir}/logs/gdbserver-build.log
touch ${rootdir}/logs/gdbserver-build.log

if [ "$(hostname)" = "longley" ]
then
    parallel="-j 4"
    verilator_dir=/opt/verilator
else
    parallel="-j $(nproc)"
    verilator_dir=/usr
fi

# Model

cd ${rootdir}/ri5cy/verilator-model
echo "Starting at $(date)" >> ${rootdir}/logs/gdbserver-build.log 2>&1

echo -n "Building RI5CY..."
echo "Building RI5CY" >> ${rootdir}/logs/gdbserver-build.log 2>&1

if ! make >> ${rootdir}/logs/gdbserver-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

# GDBserver

cd ${rootdir}/build/gdbserver

echo -n "Configuring GDBserver..."
echo "Configuring GDBserver" >> ${rootdir}/logs/gdbserver-build.log 2>&1

if ! ${rootdir}/gdbserver/configure \
     --with-verilator-headers=${verilator_dir}/share/verilator/include \
     --with-ri5cy-modeldir=${rootdir}/ri5cy/verilator-model/obj_dir \
     --with-binutils-incdir= \
     --with-gdbsim-incdir= \
     --prefix=${rootdir}/install >> ${rootdir}/logs/gdbserver-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Building GDBserver..."
echo "Building GDBserver" >> ${rootdir}/logs/gdbserver-build.log 2>&1

if ! make ${parallel} >> ${rootdir}/logs/gdbserver-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo -n "Installing GDBserver..."
echo "Installing GDBserver" >> ${rootdir}/logs/gdbserver-build.log 2>&1

if ! make ${parallel} install >> ${rootdir}/logs/gdbserver-build.log 2>&1
then
    echo "failed"
    exit 1
else
    echo "succeeded"
fi

echo "Stopping at $(date)" >> ${rootdir}/logs/gdbserver-build.log 2>&1
