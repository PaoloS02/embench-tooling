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
    'gcc_10.0.0' : {
        'gcc' : 'a9d06ea05ab',
        'binutils-gdb' : 'ed7e9d0bda',
        'newlib' : 'edb1be4cc',
    },
    'gcc_9.2' : {
        'gcc' : 'gcc-9_2_0-release',
        'binutils-gdb' : 'binutils-2_32',
        'newlib' : 'newlib-3.1.0',
    },
    'gcc_9.1' : {
        'gcc' : 'gcc-9_1_0-release',
        'binutils-gdb' : 'binutils-2_32',
        'newlib' : 'newlib-3.1.0',
    },
    'gcc_8.3' : {
        'gcc' : 'gcc-8_3_0-release',
        'binutils-gdb' : 'binutils-2_32',
        'newlib' : 'newlib-3.1.0',
    },
    'gcc_8.2' : {
        'gcc' : 'gcc-8_2_0-release',
        'binutils-gdb' : 'binutils-2_31_1',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc_8.1' : {
        'gcc' : 'gcc-8_1_0-release',
        'binutils-gdb' : 'binutils-2_30',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc_7.5' : {
        'gcc' : '08e3e5fc33b',
        'binutils-gdb' : 'binutils-2_33_1',
        'newlib' : 'newlib-3.1.0',
    },
    'gcc_7.4' : {
        'gcc' : 'gcc-7_4_0-release',
        'binutils-gdb' : 'binutils-2_31_1',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc_7.3' : {
        'gcc' : 'gcc-7_3_0-release',
        'binutils-gdb' : 'binutils-2_29_1.1',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc_7.2' : {
        'gcc' : 'gcc-7_2_0-release',
        'binutils-gdb' : 'binutils-2_29',
        'newlib' : 'newlib-3.0.0',
    },
    'gcc_7.1' : {
        'gcc' : 'gcc-7_1_0-release',
        'binutils-gdb' : 'binutils-2_28',
        'newlib' : 'newlib-3.0.0',
    },
}


def checkout(src, tag):
    """Checkout a particular tag in a git source directoyr"""

    arglist = [
        'git',
        'checkout',
        tag,
    ]

    res = None
    succeeded = True

    try:
        res = subprocess.run(
            arglist,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.join(gp['rootdir'], 'gnu', src),
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


def build_toolchain(build):
    """Build a complete tool chain"""
    log.info(f'Building tool chain {build}')

    arglist = [
        f'./build_gnu.py',
        f'--builddir=build-rv32-{build}',
        f'--installdir=install-rv32-{build}',
        f'riscv32-unknown-elf',
    ]

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
            log.error(f'ERROR: Tool chain {build} failed')
            succeeded = False
    except subprocess.TimeoutExpired:
        log.error(f'ERROR: Tool chain {build} timed out after 900 seconds')
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
        for src in [ 'binutils-gdb', 'gcc', 'newlib', ]:
            checkout(src, tags[src])
        # Build the tool chain
        build_toolchain(build)


# Make sure we have new enough Python and only run if this is the main package

check_python_version(3, 6)
if __name__ == '__main__':
    sys.exit(main())
