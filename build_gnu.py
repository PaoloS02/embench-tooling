#!/usr/bin/env python3

# Script to build GNU tool chains for 32-bit RISC-V

# Copyright (C) 2019 Embecosm Limited
#
# Contributor: Jeremy Bennett <jeremy.bennett@embecosm.com>
#
# This file is part of Embench.

# SPDX-License-Identifier: GPL-3.0-or-later

"""
Build a GNU tool chain for RISC-V
"""


import argparse
import datetime
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
from tooling_core import log_args


def build_parser():
    """Build a parser for all the arguments"""
    parser = argparse.ArgumentParser(
        description='Build a GNU tool chain for 32-bit RISC-V'
    )

    # The triplet is a mandatory positional argument
    parser.add_argument(
        'triplet',
        type=str,
        help='GNU triplet for the target',
    )

    # The next set have defaults
    parser.add_argument(
        '--builddir',
        type=str,
        default='build',
        help='Directory in which to build the tool chain',
    )
    parser.add_argument(
        '--installdir',
        type=str,
        default='install',
        help='Directory in which to install the tool chain',
    )
    parser.add_argument(
        '--logdir',
        type=str,
        default='logs',
        help='Directory in which to store logs',
    )

    # The next set have defaults dependent on the triplet, and so are set
    # later.
    parser.add_argument(
        '--arch',
        type=str,
        help='Target architecture',
    )
    parser.add_argument(
        '--abi',
        type=str,
        help='Target ABI',
    )
    parser.add_argument(
        '--cpu',
        type=str,
        help='Target CPU',
    )
    parser.add_argument(
        '--mode',
        type=str,
        help='Target mode (ARM only)',
    )
    parser.add_argument(
        '--float',
        type=str,
        help='Target float support',
    )
    parser.add_argument(
        '--endian',
        type=str,
        help='Target endianness',
    )
    parser.add_argument(
        '--libc',
        type=str,
        help='Target libc (newlib or avrlibc',
    )
    parser.add_argument(
        '--target-cflags',
        type=str,
        help='Compiler flags when building the target C library',
    )

    # Binary flag option
    parser.add_argument(
        '--clean', action='store_true', help='Rebuild everything'
    )

    return parser


def validate_args(args):
    """Validate and set default values of unspecified args"""

    # Only deal with certain triplets
    valid_triplets = {
        'riscv32-unknown-elf',
        'arm-none-eabi',
        'arc-elf32',
        'avr',
    }
    if args.triplet in valid_triplets:
        gp['triplet'] = args.triplet
    else:
        log.error(f'ERROR: Invalid target triplet {args.triplet}')
        sys.exit(1)

    # Dictionary of default values
    defaults = {
        'riscv32-unknown-elf' : {
            'arch' : 'rv32imc',
            'abi' : 'ilp32',
            'cpu' : None,
            'mode' : None,
            'float' : None,
            'endian' : None,
            'libc' : 'newlib',
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os',
        },
        'arm-none-eabi' : {
            'arch' : None,
            'abi' : None,
            'cpu' : 'cortex-m4',
            'mode' : 'thumb',
            'float' : 'soft',
            'endian' : None,
            'libc' : 'newlib',
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os',
        },
        'arc-elf32' : {
            'arch' : None,
            'abi' : None,
            'cpu' : 'em',
            'mode' : None,
            'float' : None,
            'endian' : 'little',
            'libc' : 'newlib',
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os',
        },
        'avr' : {
            'arch' : None,
            'abi' : None,
            'cpu' : None,
            'mode' : None,
            'float' : None,
            'endian' : None,
            'libc' : 'avrlibc',
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os',
        },
    }

    default = defaults[gp['triplet']]

    for arg in [
            'arch',
            'abi',
            'cpu',
            'mode',
            'float',
            'endian',
            'libc',
            'target_cflags']:
        val = getattr(args, arg)
        if val:
            gp[arg] = val
        else:
            gp[arg] = defaults[gp['triplet']][arg]


def create_builddirs(builddir, clean):
    """Create the build directory and its subdirectories, which can be
       relative to the current directory or absolute. If the "clean" is True,
       delete any existing build directory

    """

    # Sort out absolute/relative directory name
    if os.path.isabs(builddir):
        gp['bd'] = builddir
    else:
        gp['bd'] = os.path.join(gp['rootdir'], builddir)

    # Clean the build directory if appropriate
    if os.path.isdir(gp['bd']) and clean:
        try:
            shutil.rmtree(gp['bd'])
        except PermissionError:
            log.error(
                'ERROR: Unable to clean build directory %s: exiting',
                gp['bd']
            )
            sys.exit(1)

    # Create the directory and subdirectories. Usually the same, except if we
    # are AVR
    if 'avr' in gp['triplet']:
        # AVR
        bdlist = [
            gp['bd'],
            os.path.join(gp['bd'], 'gnu'),
            os.path.join(gp['bd'], 'gnu', 'binutils-gdb'),
            os.path.join(gp['bd'], 'gnu', 'gcc-stage-1'),
            os.path.join(gp['bd'], 'gnu', 'avr-libc'),
        ]
    else:
        # Everything non-AVR
        bdlist = [
            gp['bd'],
            os.path.join(gp['bd'], 'gnu'),
            os.path.join(gp['bd'], 'gnu', 'binutils-gdb'),
            os.path.join(gp['bd'], 'gnu', 'gcc-stage-1'),
            os.path.join(gp['bd'], 'gnu', 'gcc-stage-2'),
            os.path.join(gp['bd'], 'gnu', 'newlib'),
    ]
    for subdir in bdlist:
        if not os.path.isdir(subdir):
            try:
                os.makedirs(subdir)
            except PermissionError:
                log.error(
                    f'ERROR: Unable to create build directory {subdir}: exiting'
                )
                sys.exit(1)

        if not os.access(subdir, os.W_OK):
            log.error(
                f'ERROR: Unable to write to build directory {subdir}, exiting'
            )
            sys.exit(1)


def create_installdir(installdir):
    """Create the install directory, which can be relative to the current
       directory or absolute.  The GNU tool chain build scripts will do this,
       but only after they have built the component, so this finds a problem
       earlier."""

    # Sort out absolute/relative directory name
    if os.path.isabs(installdir):
        gp['id'] = installdir
    else:
        gp['id'] = os.path.join(gp['rootdir'], installdir)

    # Create the directory if it does not exist
    if not os.path.isdir(gp['id']):
        try:
            os.makedirs(gp['id'])
        except PermissionError:
            log.error(
                f'ERROR: Unable to create build directory {gp["id"]}: exiting'
            )
            sys.exit(1)

    if not os.access(gp['bd'], os.W_OK):
        log.error(
            f'ERROR: Unable to write to build directory {gp["id"]}, exiting'
        )
        sys.exit(1)


def build_tool_stage(arglist, timeout, builddir, stage, tool, env=None):
    """Carry out one stage of building a tool"""
    log.info(f'{stage} {tool}...')

    res = None
    succeeded = True

    try:
        res = subprocess.run(
            arglist,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=builddir,
            timeout=timeout,
            env=env
        )
        if res.returncode != 0:
            log.error(f'ERROR: {stage} {tool} failed')
            succeeded = False
    except subprocess.TimeoutExpired:
        log.error(f'ERROR: {stage} {tool} timed out after {timeout} seconds')
        succeeded = False

    if not succeeded:
        log.debug('Command was:')
        log.debug(arglist_to_str(arglist))
        if res:
            log.debug(res.stdout.decode('utf-8'))
            log.debug(res.stderr.decode('utf-8'))
        sys.exit(1)


def build_tool(conf_arglist, timeouts, bdir, tool, make_targs=None, env=None):
    """Configure, build and install a tool"""

    # Configure
    build_tool_stage(
        arglist=conf_arglist,
        timeout=timeouts['config'],
        builddir=bdir,
        stage='Configuring',
        tool=tool,
        env=env
    )

    # Build
    arglist = ['make', '-j']
    if make_targs:
        for targ in make_targs:
            arglist.append(f'all-{targ}')
    else:
        arglist.append('all')

    build_tool_stage(
        arglist=arglist,
        timeout=timeouts['build'],
        builddir=bdir,
        stage='Building',
        tool=tool,
        env=env
    )

    # Install
    arglist = ['make', '-j']
    if make_targs:
        for targ in make_targs:
            arglist.append(f'install-{targ}')
    else:
        arglist.append('install')

    build_tool_stage(
        arglist=arglist,
        timeout=timeouts['install'],
        builddir=bdir,
        stage='Installing',
        tool=tool,
        env=env
    )


def build_all_tools():
    """Configure, build and install binutils, GDB, GCC and newlib."""

    # Binutils/GDB
    config_arglist = [
        os.path.join(gp['rootdir'], 'gnu', 'binutils-gdb', 'configure'),
        '--prefix=' + gp['id'],
        '--target=' + gp['triplet'],
        '--sysconfdir=' + os.path.join(gp['id'], 'etc'),
        '--localstatedir=' + os.path.join(gp['id'], 'var'),
        '--with-sysroot=' + os.path.join(gp['id'], gp['triplet'], 'sysroot'),
        '--disable-gtk-doc',
        '--disable-gtk-doc-html',
        '--disable-doc',
        '--disable-docs',
        '--disable-documentation',
        '--with-xmlto=no',
        '--with-fop=no',
        '--disable-multilib',
        '--enable-plugins',
        '--enable-poison-system-directories',
        '--disable-tls',
        '--disable-sim',
    ]

    # Add target specific options
    for arg in ['arch', 'abi', 'cpu', 'mode', 'float', 'endian']:
        if gp[arg]:
            config_arglist.append(f'--with-{arg}={gp[arg]}')

    build_tool(
        conf_arglist=config_arglist,
        timeouts={
            'config' : 30,
            'build' : 300,
            'install' : 10,
        },
        bdir=os.path.join(gp['bd'], 'gnu', 'binutils-gdb'),
        tool='Binutils/GDB',
        make_targs=['binutils', 'ld', 'gas']
    )

    # GCC stage 1
    config_arglist = [
        os.path.join(gp['rootdir'], 'gnu', 'gcc', 'configure'),
        '--prefix=' + gp['id'],
        '--target=' + gp['triplet'],
        '--sysconfdir=' + os.path.join(gp['id'], 'etc'),
        '--localstatedir=' + os.path.join(gp['id'], 'var'),
        '--with-sysroot=' + os.path.join(gp['id'], gp['triplet'], 'sysroot'),
        '--disable-shared',
        '--disable-static',
        '--disable-gtk-doc',
        '--disable-gtk-doc-html',
        '--disable-doc',
        '--disable-docs',
        '--disable-documentation',
        '--with-xmlto=no',
        '--with-fop=no',
        '--disable-__cxa_atexit',
        '--with-gnu-ld',
        '--disable-libssp',
        '--disable-multilib',
        '--enable-target-optspace',
        '--disable-libsanitizer',
        '--disable-tls',
        '--disable-libmudflap',
        '--disable-threads',
        '--disable-libquadmath',
        '--disable-libgomp',
        '--without-isl',
        '--without-cloog',
        '--disable-decimal-float',
        '--enable-languages=c',
        '--without-headers',
        '--with-newlib',
        '--disable-largefile',
        '--enable-plugins',
        '--disable-nls',
        '--enable-checking=yes',
    ]

    # Add target specific options
    for arg in ['arch', 'abi', 'cpu', 'mode', 'float', 'endian']:
        if gp[arg]:
            config_arglist.append(f'--with-{arg}={gp[arg]}')

    for arg in ['libc']:
        if gp[arg]:
            config_arglist.append(f'--with-{gp[arg]}')

    build_tool(
        conf_arglist=config_arglist,
        timeouts={
            'config' : 30,
            'build' : 900,
            'install' : 10,
        },
        bdir=os.path.join(gp['bd'], 'gnu', 'gcc-stage-1'),
        tool='GCC Stage 1'
    )

    # C library. Usually newlib, unless we are AVR
    # Need to extend the environment to access the new tool chain
    oldpath = os.environ['PATH']
    os.environ['PATH'] = (os.path.join(gp['id'], 'bin') + os.pathsep +
                          os.environ['PATH'])

    if 'avr' in gp['triplet']:
        # AVR Libc
        # Need to explicitly configure the build architecture
        succeeded = True

        try:
            res = subprocess.run(
                [os.path.join(
                    gp['rootdir'],
                    'gnu',
                    'avr-libc',
                    'avr-libc',
                    'config.guess'
                 )],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1
            )
            if res.returncode != 0:
                log.error(
                    f'ERROR: Failed to find build architecture for AVR LibC'
                )
                succeeded = False
        except subprocess.TimeoutExpired:
            log.error(f'ERROR: Finding build archicture for AVR LibC timed ' +
                      f'out after 1 second')
            succeeded = False

        if succeeded:
            buildmc = res.stdout.decode('utf-8').rstrip()
        else:
            log.debug('Command was:')
            log.debug(arglist_to_str(arglist))
            if res in locals():
                log.debug(res.stdout.decode('utf-8'))
                log.debug(res.stderr.decode('utf-8'))
                sys.exit(1)

        config_arglist = [
            os.path.join(
                gp['rootdir'], 'gnu', 'avr-libc', 'avr-libc', 'configure'
            ),
            '--prefix=' + gp['id'],
            '--build=' + buildmc,
            '--host=avr'
        ]

        build_tool(
            conf_arglist=config_arglist,
            timeouts={
                'config' : 120,
                'build' : 300,
                'install' : 60,
            },
            bdir=os.path.join(gp['bd'], 'gnu', 'avr-libc'),
            tool='AVR LibC',
            env=os.environ
        )
    else:
        # Newlib.
        config_arglist = [
            os.path.join(gp['rootdir'], 'gnu', 'newlib', 'configure'),
            '--prefix=' + gp['id'],
            '--target=' + gp['triplet'],
            '--sysconfdir=' + os.path.join(gp['id'], 'etc'),
            '--localstatedir=' + os.path.join(gp['id'], 'var'),
            '--with-sysroot=' + os.path.join(gp['id'], gp['triplet'], 'sysroot'),
            'CFLAGS_FOR_TARGET=' + gp['target_cflags'],
            '--disable-newlib-fvwrite-in-streamio',
            '--disable-newlib-fseek-optimization',
            '--enable-newlib-nano-malloc',
            '--disable-newlib-unbuf-stream-opt',
            '--enable-target-optspace',
            '--enable-newlib-reent-small',
            '--disable-newlib-wide-orient',
            '--disable-newlib-io-float',
            '--enable-newlib-nano-formatted-io',
        ]

        build_tool(
            conf_arglist=config_arglist,
            timeouts={
                'config' : 30,
                'build' : 300,
                'install' : 10,
            },
            bdir=os.path.join(gp['bd'], 'gnu', 'newlib'),
            tool='Newlib',
            env=os.environ
        )

    # Restore path
    os.environ['PATH'] = oldpath

    # GCC stage 2. Not needed for AVR
    if not 'avr' in gp['triplet']:
        config_arglist = [
            os.path.join(gp['rootdir'], 'gnu', 'gcc', 'configure'),
            '--prefix=' + gp['id'],
            '--target=' + gp['triplet'],
            '--sysconfdir=' + os.path.join(gp['id'], 'etc'),
            '--localstatedir=' + os.path.join(gp['id'], 'var'),
            '--with-sysroot=' + os.path.join(gp['id'], gp['triplet'], 'sysroot'),
            '--with-build-time-tools=' + os.path.join(
                gp['id'], gp['triplet'], 'bin'),
            '--disable-shared',
            '--enable-plugins',
            '--enable-static',
            '--disable-gtk-doc',
            '--disable-gtk-doc-html',
            '--disable-doc',
            '--disable-docs',
            '--disable-documentation',
            '--with-xmlto=no',
            '--with-fop=no',
            '--disable-__cxa_atexit',
            '--with-gnu-ld',
            '--disable-libssp',
            '--disable-multilib',
            '--enable-target-optspace',
            '--disable-libsanitizer',
            '--disable-tls',
            '--disable-libmudflap',
            '--disable-threads',
            '--disable-libquadmath',
            '--disable-libgomp',
            '--without-isl',
            '--without-cloog',
            '--disable-decimal-float',
            '--enable-languages=c,c++',
            '--with-newlib',
            '--disable-largefile',
            '--disable-nls',
            '--enable-checking=yes',
        ]

        # Add target specific options
        for arg in ['arch', 'abi', 'cpu', 'mode', 'float', 'endian']:
            if gp[arg]:
                config_arglist.append(f'--with-{arg}={gp[arg]}')

        for arg in ['libc']:
            if gp[arg]:
                config_arglist.append(f'--with-{gp[arg]}')

        build_tool(
            conf_arglist=config_arglist,
            timeouts={
                'config' : 30,
                'build' : 900,
                'install' : 10,
            },
            bdir=os.path.join(gp['bd'], 'gnu', 'gcc-stage-2'),
            tool='GCC Stage 2'
        )


def main():
    """Main program to drive building of benchmarks."""
    # Establish the root directory of the repository, since we know it is the
    # parent directory of the directory in which we find this file.
    gp['rootdir'] = os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.pardir
        ))

    # Parse arguments using standard technology
    parser = build_parser()
    args = parser.parse_args()

    # Establish logging, using "build" as the log file prefix.
    setup_logging(args.logdir, 'build')

    # Validate and record the args
    validate_args(args)
    log_args(args)

    # Establish build directory
    create_builddirs(args.builddir, args.clean)

    # Create install directory.
    create_installdir(args.installdir)

    # Configure, build and install the components
    now = datetime.datetime.now().strftime('%a %d %b %Y %H:%M:%S')
    log.info(f'Starting at {now}')

    build_all_tools()

    now = datetime.datetime.now().strftime('%a %d %b %Y %H:%M:%S')
    log.info(f'Ending at {now}')


# Make sure we have new enough Python and only run if this is the main package

check_python_version(3, 6)
if __name__ == '__main__':
    sys.exit(main())
