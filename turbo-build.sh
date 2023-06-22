#!/bin/bash

TOPDIR="$(dirname $(cd $(dirname $0) && echo $PWD))"

echo "List of variations:"
echo ""

target_triple=(
"arm-none-eabi"
"riscv32-unknown-elf"
#"mips-elf"
)

gcc_vers=(
"7.5.0"
"8.5.0"
"9.2.0"
"9.5.0"
"10.4.0"
"11.3.0"
"12.3.0"
"13.1.0"
)

clang_vers=(
"15.0.0"
"14.0.0"
"13.0.0"
"12.0.0"
)

clang_newlib_arm_vers=(
"15.0.0-devel"  
"14.0.0-devel"  
"13.0.0-devel"  
"12.0.0-devel"  
)

build_gcc=false
build_clang=false

binutils_base="2_33_1"
binutils_latest="2_39"

binutils_vers=($binutils_base $binutils_latest)

newlib_base="3.3.0"
newlib_latest="4.3.0"

newlib_vers=($newlib_base $newlib_latest)

echo "GCC tags"
for gccv in ${gcc_vers[@]}
do
  echo "releases/gcc-$gccv"
done
echo ""

echo "Clang/LLVM tags"
for clangv in ${clang_vers[@]}
do
  echo "llvmorg-$clangv"
done
echo ""

echo "Binutils tags"
for binv in ${binutils_vers[@]}
do
  echo "binutils-$binv"
done
echo ""

echo "Newlib tags"
for newlv in ${newlib_vers[@]}
do
  echo "newlib-$newlv"
done
echo""

echo "Triples"
for triple in ${target_triple[@]}
do
  echo "$triple"
done

set +u
until
  opt="$1"
  case "${opt}" in    --gcc)
      build_gcc=true
      ;;
    --clang)
      build_clang=true
      ;;
  esac
[ "x${opt}" = "x" ]
do
  shift
done
set -u

if $build_gcc
then
  i=0
  for triple in ${target_triple[@]}
  do
    for gccv in ${gcc_vers[@]}
    do
      binv=$binutils_base
      newlv=$newlib_base

      echo ""
      echo "Building:"
      echo "GCC $gccv"
      echo "Binutils $binv"
      echo "Newlib $newlv"
      echo "Triple $triple"
      echo ""

      echo "cd $TOPDIR/gnu/gcc"
      cd $TOPDIR/gnu/gcc
      echo "git checkout releases/gcc-$gccv"
      git checkout releases/gcc-$gccv

      echo "cd $TOPDIR/gnu/binutils-gdb"  
      cd $TOPDIR/gnu/binutils-gdb
      echo "git checkout binutils-$binv"
      git checkout binutils-$binv
      echo "cd $TOPDIR/libs/newlib"
      cd $TOPDIR/libs/newlib
      echo "git checkout newlib-$newlv"
      git checkout newlib-$newlv
  
      echo "cd $TOPDIR/tooling"
      cd $TOPDIR/tooling
  
      echo "$i: ./build_toolchain.py --builddir $TOPDIR/build-turbo --installdir $TOPDIR/install-turbo/gcc-$gccv-binutils-$binv-newlib-$newlv-$triple --logdir $TOPDIR/log-turbo/gcc-$gccv-binutils-$binv-newlib-$newlv-$triple --build-gnu $triple"
      ./build_toolchain.py --builddir $TOPDIR/build-turbo --installdir $TOPDIR/install-turbo/gcc-$gccv-binutils-$binv-newlib-$newlv-$triple --logdir $TOPDIR/log-turbo/gcc-$gccv-binutils-$binv-newlib-$newlv-$triple --build-gnu $triple || true
  
      rm -rf $TOPDIR/build-turbo/*
      #mkdir -p $TOPDIR/build-turbo/newlib-nano
  
      let "i+=1"
  
      binv=$binutils_latest
      newlv=$newlib_latest
  
      echo ""
      echo "Building:"
      echo "GCC $gccv"
      echo "Binutils $binv"
      echo "Newlib $newlv"
      echo "Triple $triple"
      echo ""

      echo "cd $TOPDIR/gnu/gcc"
      cd $TOPDIR/gnu/gcc
      echo "git checkout releases/gcc-$gccv"
      git checkout releases/gcc-$gccv

      echo "cd $TOPDIR/gnu/binutils-gdb"  
      cd $TOPDIR/gnu/binutils-gdb
      echo "git checkout binutils-$binv"
      git checkout binutils-$binv
      echo "cd $TOPDIR/libs/newlib"
      cd $TOPDIR/libs/newlib
      echo "git checkout newlib-$newlv"
      git checkout newlib-$newlv
  
      echo "cd $TOPDIR/tooling"
      cd $TOPDIR/tooling
  
      echo "$i: ./build_toolchain.py --builddir $TOPDIR/build-turbo --installdir $TOPDIR/install-turbo/gcc-$gccv-binutils-$binv-newlib-$newlv-$triple --logdir $TOPDIR/log-turbo/gcc-$gccv-binutils-$binv-newlib-$newlv-$triple --build-gnu $triple"
      ./build_toolchain.py --builddir $TOPDIR/build-turbo --installdir $TOPDIR/install-turbo/gcc-$gccv-binutils-$binv-newlib-$newlv-$triple --logdir $TOPDIR/log-turbo/gcc-$gccv-binutils-$binv-newlib-$newlv-$triple --build-gnu $triple || true
      let "i+=1"
      echo ""
  
      rm -rf $TOPDIR/build-turbo/*
  
    done
  done
fi


if $build_clang
then
  clang_list=$clang_vers
  if [[ $triple == "arm-none-eabi" ]]; then
    clang_list=$clang_newlib_arm_vers
  fi
  i=0
  for triple in ${target_triple[@]}
  do
    for clangv in ${clang_list[@]}
    do
      binv=$binutils_base

      # ARM Clang needs a fix in newlib to build as
      # Clang being more pedantic than GCC would
      # error.
      if [[ $triple == "arm-none-eabi" ]]; then
        newlv="3.3.0-devel"
      else
        newlv=$newlib_base
      fi

      echo ""
      echo "Building:"
      echo "Clang/LLVM $clangv"
      echo "Binutils $binv"
      echo "Newlib $newlv"
      echo "Triple $triple"
      echo ""

      echo "cd $TOPDIR/llvm/llvm-project"
      cd $TOPDIR/llvm/llvm-project
      echo "git checkout llvmorg-$clangv"
      git checkout llvmorg-$clangv

      echo "cd $TOPDIR/gnu/binutils-gdb"
      cd $TOPDIR/gnu/binutils-gdb
      echo "git checkout binutils-$binv"
      git checkout binutils-$binv
      echo "cd $TOPDIR/libs/newlib"
      cd $TOPDIR/libs/newlib
      echo "git checkout newlib-$newlv"
      git checkout newlib-$newlv
  
      echo "cd $TOPDIR/tooling"
      cd $TOPDIR/tooling

      mkdir -p $TOPDIR/build-turbo/compiler-rt  
      #cat /home/paolo/EMBENCH/patterson/libs/newlib/newlib/libc/machine/arm/strlen-thumb2-Os.S
  
      echo "$i: ./build_toolchain.py --builddir $TOPDIR/build-turbo --installdir $TOPDIR/install-turbo/clang-$clangv-binutils-$binv-newlib-$newlv-$triple --logdir $TOPDIR/log-turbo/clang-$clangv-binutils-$binv-newlib-$newlv-$triple --build-llvm $triple"
      ./build_toolchain.py --builddir $TOPDIR/build-turbo --installdir $TOPDIR/install-turbo/clang-$clangv-binutils-$binv-newlib-$newlv-$triple --logdir $TOPDIR/log-turbo/clang-$clangv-binutils-$binv-newlib-$newlv-$triple --build-llvm $triple --verbose || true
  
      rm -rf $TOPDIR/build-turbo/*
  
      let "i+=1"
  
      binv=$binutils_latest

      # ARM Clang needs a fix in newlib to build as
      # Clang being more pedantic than GCC would
      # error.
      if [[ $triple == "arm-none-eabi" ]]; then
        newlv="4.3.0-devel"
      else
        newlv=$newlib_latest
      fi

      echo ""
      echo "Building:"
      echo "Clang/LLVM $clangv"
      echo "Binutils $binv"
      echo "Newlib $newlv"
      echo "Triple $triple"
      echo ""

      echo "cd $TOPDIR/gnu/binutils-gdb"
      cd $TOPDIR/gnu/binutils-gdb
      echo "git checkout binutils-$binv"
      git checkout binutils-$binv
      echo "cd $TOPDIR/libs/newlib"
      cd $TOPDIR/libs/newlib
      echo "git checkout newlib-$newlv"
      git checkout newlib-$newlv
  
      echo "cd $TOPDIR/tooling"
      cd $TOPDIR/tooling

      mkdir -p $TOPDIR/build-turbo/compiler-rt  
  #    cat /home/paolo/EMBENCH/patterson/libs/newlib/newlib/libc/machine/arm/strlen-thumb2-Os.S
  
      echo "$i: ./build_toolchain.py --builddir $TOPDIR/build-turbo --installdir $TOPDIR/install-turbo/clang-$clangv-binutils-$binv-newlib-$newlv-$triple --logdir $TOPDIR/log-turbo/clang-$clangv-binutils-$binv-newlib-$newlv-$triple --build-llvm $triple"
      ./build_toolchain.py --builddir $TOPDIR/build-turbo --installdir $TOPDIR/install-turbo/clang-$clangv-binutils-$binv-newlib-$newlv-$triple --logdir $TOPDIR/log-turbo/clang-$clangv-binutils-$binv-newlib-$newlv-$triple --build-llvm $triple --verbose || true
      let "i+=1"
  
      rm -rf $TOPDIR/build-turbo/*
 
    done
  done
fi
