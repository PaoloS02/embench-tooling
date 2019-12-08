#!/usr/bin/env python3

# Script to build many GNU chains

# Copyright (C) 2019 Embecosm Limited
#
# Contributor: Jeremy Bennett <jeremy.bennett@embecosm.com>
#
# This file is part of Embench.

# SPDX-License-Identifier: GPL-3.0-or-later

"""
Build lots of GNU tool chains
"""

import argparse
import os
import shutil
import subprocess
import sys

sys.path.append(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pylib')
)

from tooling_core import arglist_to_str
from tooling_core import check_python_version
from tooling_core import log
from tooling_core import gp
from tooling_core import setup_logging

builds = {
    'llvm-master' : {
        'tool' : 'llvm',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'a9d06ea05ab',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
    'llvm-9.0.0' : {
        'tool' : 'llvm',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'a9d06ea05ab',
        'llvm-project' : 'llvmorg-9.0.0',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
    'llvm-8.0.1' : {
        'tool' : 'llvm',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'a9d06ea05ab',
        'llvm-project' : 'llvmorg-8.0.1',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
    'llvm-7.1.0' : {
        'tool' : 'llvm',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'a9d06ea05ab',
        'llvm-project' : 'llvmorg-7.1.0',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
    'llvm-6.0.1' : {
        'tool' : 'llvm',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'a9d06ea05ab',
        'llvm-project' : 'llvmorg-6.0.1',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
    'llvm-5.0.2' : {
        'tool' : 'llvm',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'a9d06ea05ab',
        'llvm-project' : 'llvmorg-5.0.2',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
    'llvm-4.0.1' : {
        'tool' : 'llvm',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'a9d06ea05ab',
        'llvm-project' : 'llvmorg-4.0.1',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
}

old_builds = {
    'gcc-10.0.0' : {
        'tool' : 'gnu',
        'arch' : ['arc-elf32', 'arm-none-eabi', 'avr', 'riscv32-unknown-elf'],
        'gcc' : 'a9d06ea05ab',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
    'gcc-9.2' : {
        'tool' : 'gnu',
        'arch' : ['arc-elf32', 'arm-none-eabi', 'avr'],
        'gcc' : 'gcc-9_2_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_32',
        'newlib' : 'newlib-3.1.0',
    },
    'gcc-9.1' : {
        'tool' : 'gnu',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'gcc-9_1_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_32',
        'newlib' : 'newlib-3.1.0',
    },
    'gcc-8.3' : {
        'tool' : 'gnu',
        'arch' : ['arc-elf32', 'arm-none-eabi', 'avr'],
        'gcc' : 'gcc-8_3_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_32',
        'newlib' : 'newlib-3.1.0',
    },
    'gcc-8.2' : {
        'tool' : 'gnu',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'gcc-8_2_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_31_1',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc-8.1' : {
        'tool' : 'gnu',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'gcc-8_1_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_30',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc-7.5' : {
        'tool' : 'gnu',
        'arch' : ['arc-elf32', 'arm-none-eabi', 'avr'],
        'gcc' : '08e3e5fc33b',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_33_1',
        'newlib' : 'newlib-3.1.0',
    },
    'gcc-7.4' : {
        'tool' : 'gnu',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'gcc-7_4_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_31_1',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc-7.3' : {
        'tool' : 'gnu',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'gcc-7_3_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_29_1.1',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc-7.2' : {
        'tool' : 'gnu',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'gcc-7_2_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_29',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc-7.1' : {
        'tool' : 'gnu',
        'arch' : ['riscv32-unknown-elf'],
        'gcc' : 'gcc-7_1_0-release',
        'llvm-project' : '008e65a7bfb',
        'binutils-gdb' : 'binutils-2_28',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc-6.5' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-6_5_0-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_31_1',
	'newlib' : 'newlib-2_4_0',
    },
    'gcc-5.5' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-5_5_0-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_29',
	'newlib' : 'newlib-2_4_0',
    },
    'gcc-4.9.4' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_9_4-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_27',
	'newlib' : 'newlib-2_4_0',
    },
    'gcc-4.8.5' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_8_5-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_26',
	'newlib' : 'newlib-2_2_0',
    },
    'gcc-4.7.4' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_7_4-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_24',
	'newlib' : 'newlib-2_1_0',
    },
    'gcc-4.6.4' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_6_4-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_23_2',
	'newlib' : 'newlib-2_0_0',
    },
    'gcc-4.5.4' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_5_4-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_22',
	'newlib' : 'newlib-1_20_0',
    },
    'gcc-4.4.7' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_4_7-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_22',
	'newlib' : 'newlib-1_20_0',
    },
    'gcc-4.3.6' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_3_6-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_21_1',
	'newlib' : 'newlib-1_19_0',
    },
    'gcc-4.2.4' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_2_4-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_18',
	'newlib' : 'newlib-1_16_0',
    },
    'gcc-4.1.2' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_1_2-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_17',
	'newlib' : 'newlib-1_15_0',
    },
    'gcc-4.0.4' : {
        'tool' : 'gnu',
        'arch' : ['arm-none-eabi'],
        'gcc' : 'gcc-4_0_4-release',
        'llvm-project' : '008e65a7bfb',
	'binutils-gdb' : 'binutils-2_17',
	'newlib' : 'newlib-1_15_0',
    },
}


def checkout(src, tag):
    """Checkout a particular tag in a git source directory"""

    arglist = [
        'git',
        'checkout',
        tag,
    ]

    res = None
    succeeded = True

    if src in ['llvm-project']:
        srcbasedir = os.path.join(gp['rootdir'], 'llvm')
    else:
        srcbasedir = os.path.join(gp['rootdir'], 'gnu')

    try:
        res = subprocess.run(
            arglist,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.join(srcbasedir, src),
            timeout=30
        )
        if res.returncode != 0:
            log.error(f'ERROR: Failed to check out tag {tag} of {src}')
            succeeded = False
    except subprocess.TimeoutExpired:
        log.error(f'ERROR: Check out of tag {tag} of {src} ' +
                  f'timed out after 30 seconds')
        succeeded = False

    if not succeeded:
        log.debug('Command was:')
        log.debug(arglist_to_str(arglist))
        if res:
            log.debug(res.stdout.decode('utf-8'))
            log.debug(res.stderr.decode('utf-8'))
        sys.exit(1)


def build_toolchain(build, triplet, tool):
    """Build a complete tool chain"""
    arch = triplet.split('-')[0]
    arglist = [
        f'./build_gnu.py',
        f'--build-' + tool,
        f'--builddir=build-{arch}-{build}',
        f'--installdir=install-{arch}-{build}',
        f'{triplet}',
        f'--clean',
    ]

    log.info(f'Building tool chain {arch}-{build}')

    res = None
    succeeded = True

    try:
        res = subprocess.run(
            arglist,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=900
        )
        if res.returncode != 0:
            log.error(f'ERROR: Tool chain {build} for {arch} failed')
            succeeded = False
    except subprocess.TimeoutExpired:
        log.error(
            f'ERROR: Tool chain {build} for {arch} timed out after 900 seconds'
        )
        succeeded = False

    if not succeeded:
        log.debug('Command was:')
        log.debug(arglist_to_str(arglist))
        if res:
            log.debug(res.stdout.decode('utf-8'))
            log.debug(res.stderr.decode('utf-8'))
        sys.exit(1)


def main():
    """Main program to drive building of lots of tool chains"""
    # Establish the root directory of the repository, since we know this file is
    # in that directory.
    gp['rootdir'] = os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.pardir
        ))
    gp['tooldir'] = os.path.join(gp['rootdir'], 'tooling')
    gp['logdir'] = os.path.join(gp['rootdir'], 'logs')

    # Establish logging, using "build" as the log file prefix.
    setup_logging(gp['logdir'], 'build-many')

    for build, tags in builds.items():
        # Check out the correct sources
        log.info(f'Checking out source for tool chain {build}')
        for src in [ 'binutils-gdb', 'gcc', 'llvm-project', 'newlib', ]:
            checkout(src, tags[src])
        # Build the tool chain
        for triplet in tags['arch']:
            build_toolchain(build, triplet, tags['tool'])


# Make sure we have new enough Python and only run if this is the main package

check_python_version(3, 6)
if __name__ == '__main__':
    sys.exit(main())
