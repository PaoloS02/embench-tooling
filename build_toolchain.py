#!/usr/bin/env python3

# Script to build a tool chain

# Copyright (C) 2019 Embecosm Limited
#
# Contributor: Jeremy Bennett <jeremy.bennett@embecosm.com>
#
# This file is part of Embench.

# SPDX-License-Identifier: GPL-3.0-or-later

"""
Build all Embench programs.
"""


import argparse
import datetime
import logging
import os
import re
import shutil
import subprocess
import sys
import time


# Handle for the logger
log = logging.getLogger()

# All the global parameters
gp = dict()


# Make sure we have new enough python
def check_python_version(major, minor):
    """Check the python version is at least {major}.{minor}."""
    if ((sys.version_info[0] < major)
            or ((sys.version_info[0] == major)
                and (sys.version_info[1] < minor))):
        log.error(f'ERROR: Requires Python {major}.{minor} or later')
        sys.exit(1)


def get_args():
    """Build a parser for all the arguments, parse them and return the parsed
       argments."""

    parser = argparse.ArgumentParser(description='Build a tool chain')

    # The mandatory positonal argument
    parser.add_argument(
        'triplet',
        help='The triplet for which to build the tool chain',
    )

    # Optional arguments
    parser.add_argument(
        '--builddir',
        default='build',
        help='Directory in which to build the tool chain',
    )
    # Optional arguments
    parser.add_argument(
        '--installdir',
        default='install',
        help='Directory in which to install the tool chain',
    )
    parser.add_argument(
        '--logdir',
        default='logs',
        help='Directory in which to store logs',
    )
    parser.add_argument(
        '--build-llvm',
        action='store_true',
        help='Build a LLVM compiler',
    )
    parser.add_argument(
        '--build-gnu',
        dest='build_llvm',
        action='store_false',
        help='Build a GNU compiler (the default)',
    )

    # Arguments which are passed to GNU configuration using --with-<xxx> and
    # so their destination name must match <xxx>'
    parser.add_argument(
        '--gnu-arch',
        dest='arch',
        help='The GNU architecture name (argment to --with-arch)',
    )
    parser.add_argument(
        '--abi',
        help='The ABI to use (argument to --with-abi)',
    )
    parser.add_argument(
        '--cpu',
        help='The CPU to use (argument to --with-cpu)',
    )
    parser.add_argument(
        '--isa-spec',
        type=str,
        help='The ISA version to use (RISC-V specific) (argument to --with-isa-spec)',
    )
    parser.add_argument(
        '--mode',
        help='The mode to use (argument to --with-mode for Arm)',
    )
    parser.add_argument(
        '--float',
        help='The type of floatinng point (argument to --with-float)',
    )
    parser.add_argument(
        '--endian',
        type=str,
        help='Target endianness',
    )

    # Timeout arguments, which all have defaults suitable for a reasonable
    # modern x86 laptop.

    parser.add_argument(
        '--timeout-config',
        type=int,
        default=120,
        help='Timeout for configuration steps in seconds',
    )
    parser.add_argument(
        '--timeout-build',
        type=int,
        default=3600,
        help='Timeout for build steps in seconds',
    )
    parser.add_argument(
        '--timeout-install',
        type=int,
        default=120,
        help='Timeout for install steps in seconds',
    )
    parser.add_argument(
        '--timeout-build-install',
        type=int,
        default=3600,
        help='Timeout for combined build-install steps in seconds',
    )

    # Other aguments controlling the build
    parser.add_argument(
        '--llvm-arch',
        help='The LLVM architecture name (directory in llvm/lib/Target)',
    )
    parser.add_argument(
        '--experimental',
        const=True,
        action='store_const',
        help='Built experimental LLVM target'
    )
    parser.add_argument(
        '--libc',
        choices={'newlib', 'avr-libc', 'newlib-nano'},
        help='Which C library to build',
    )
    parser.add_argument(
        '--target-cflags', help='CFLAGS to use when building for the target',
    )
    parser.add_argument(
        '--num-cpus',
        type=int,
        help='Number of CPUs to use when building (default all)',
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='More detailed logging'
    )
    parser.add_argument(
        '--clean', action='store_true', help='Rebuild everything'
    )

    return parser.parse_args()


def create_logdir(logdir):
    """Create the log directory, which can be relative to the root directory
       or absolute"""
    if not os.path.isabs(logdir):
        logdir = os.path.join(gp['rootdir'], logdir)

    if not os.path.isdir(logdir):
        try:
            os.makedirs(logdir)
        except PermissionError:
            raise PermissionError(f'Unable to create log directory {logdir}')

    if not os.access(logdir, os.W_OK):
        raise PermissionError(f'Unable to write to log directory {logdir}')

    return logdir


def setup_logging(logdir, prefix):
    """Set up logging in the directory specified by "logdir".

       The log file name is the "prefix" argument followed by a timestamp.

       Debug messages only go to file, everything else also goes to the
       console."""

    # Create the log directory first if necessary.
    logdir_abs = create_logdir(logdir)
    logfile = os.path.join(
        logdir_abs, time.strftime(f'{prefix}-%Y-%m-%d-%H%M%S.log')
    )

    # Set up logging
    log.setLevel(logging.DEBUG)
    cons_h = logging.StreamHandler(sys.stdout)
    cons_h.setLevel(logging.INFO)
    log.addHandler(cons_h)
    file_h = logging.FileHandler(logfile)
    file_h.setLevel(logging.DEBUG)
    log.addHandler(file_h)

    # Log where the log file is
    log.debug(f'Log file: {logfile}\n')
    log.debug('')


def log_args(args):
    """Record all the argument values"""
    log.debug('Supplied arguments')
    log.debug('==================')

    for arg in vars(args):
        realarg = re.sub('_', '-', arg)
        val = getattr(args, arg)
        log.debug(f'--{realarg:20}: {val}')

    log.debug('')


def validate_args(args):
    """Check that supplied args are all valid and fill in defaults. By definition
       logging is working when we get here.

       Update the gp dictionary with all the useful info """

    defaults = {
        'riscv32-unknown-elf' : {
            'arch' : 'rv32imc',
            'abi' : 'ilp32',
            'cpu' : None,
            'isa_spec' : '2.2',
            'mode' : None,
            'float' : None,
            'endian' : None,
            'llvm_arch' : 'RISCV',
            'libc' : 'newlib',
            'experimental' : False,
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os'
        },
        'riscv64-unknown-elf' : {
            'arch' : 'rv64imc',
            'abi' : 'lp64',
            'cpu' : None,
            'isa_spec' : None,
            'mode' : None,
            'float' : None,
            'endian' : None,
            'llvm_arch' : 'RISCV',
            'libc' : 'newlib',
            'experimental' : False,
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os'
        },
        'arm-none-eabi' : {
            'arch' : None,
            'llvm_arch' : 'ARM',
            'abi' : None,
            'cpu' : 'cortex-m4',
            'isa_spec' : None,
            'mode' : 'thumb',
            'float' : 'soft',
            'endian' : None,
            'libc' : 'newlib',
            'experimental' : False,
            'target_cflags' : '-DHAVE_GNU_LD -DPREFER_SIZE_OVER_SPEED=1 -Os'
        },
        'arc-elf32' : {
            'arch' : None,
            'llvm_arch' : 'ARC',
            'abi' : None,
            'cpu' : 'em',
            'isa_spec' : None,
            'mode' : None,
            'float' : None,
            'endian' : 'little',
            'libc' : 'newlib',
            'experimental' : False,
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os',
        },
        'avr' : {
            'arch' : None,
            'llvm_arch' : 'AVR',
            'abi' : None,
            'cpu' : None,
            'isa_spec' : None,
            'mode' : None,
            'float' : None,
            'endian' : None,
            'libc' : 'avr-libc',
            'experimental' : True,
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os',
        },
        'mips-elf' : {
            'arch' : 'mips32r2',
            'abi' : '32',
            'cpu' : None,
            'isa_spec' : None,
            'mode' : None,
            'float' : None,
            'endian' : None,
            'llvm_arch' : 'Mips',
            'libc' : 'newlib',
            'experimental' : False,
            'target_cflags' : '-DPREFER_SIZE_OVER_SPEED=1 -Os -D__GLIBC_USE\(...\)=0'
        },
    }

    if not args.triplet in defaults.keys():
        log.error(f'ERROR: Unrecognized triplet {args.triplet}')
        sys.exit(1)

    # Set default values
    gp['triplet'] = args.triplet
    argdict = args.__dict__
    default = defaults[args.triplet]

    for key in default.keys():
        gp[key] = argdict[key] if argdict[key] else default[key]

    gp['timeouts'] = {
        'config' : args.timeout_config,
        'build' : args.timeout_build,
        'install' : args.timeout_install,
        'build/install' : args.timeout_build_install,
    }

    gp['llvm'] = args.build_llvm
    gp['verbose'] = args.verbose
    gp['cpus'] = args.num_cpus if args.num_cpus else os.cpu_count()

    # Make the installdir absolute
    if os.path.isabs(args.installdir):
        gp['id'] = args.installdir
    else:
        gp['id'] = os.path.join(gp['rootdir'], args.installdir)


def create_one_builddir(abs_bd):
    """Create a single build directory if it does not exist and ensure it it
       writable."""

    if not os.path.isdir(abs_bd):
        try:
            os.makedirs(abs_bd)
        except PermissionError:
            log.error(
                f'ERROR: Unable to create build directory {abs_bd}: exiting'
            )
            sys.exit(1)

    if not os.access(abs_bd, os.W_OK):
        log.error(
            f'ERROR: Unable to write to build directory {abs_bd}, exiting'
        )
        sys.exit(1)


def create_builddirs(builddir, clean):
    """Create the build directory and sub-drectories, which can be relative to
       the current directory or absolute. If the "clean" argument is True,
       first delete any existing build directory."""

    # Make builddir absolute
    if os.path.isabs(builddir):
        gp['bd'] = builddir
    else:
        gp['bd'] = os.path.join(gp['rootdir'], builddir)

    # Clean the builddirectory if needed.
    if os.path.isdir(gp['bd']) and clean:
        try:
            shutil.rmtree(gp['bd'])
        except PermissionError:
            log.error(
                f'ERROR: Unable to clean build directory "{gp["bd"]}: '
                + 'exiting'
            )
            sys.exit(1)

    # Create the build directories we need
    create_one_builddir(gp['bd'])
    create_one_builddir(os.path.join(gp['bd'], 'binutils'))
    create_one_builddir(os.path.join(gp['bd'], 'gcc-stage-1'))

    if gp['llvm']:
        create_one_builddir(os.path.join(gp['bd'], 'llvm'))

    # Neither AVR LibC, nor LLVM need a second GCC build
    if not ((gp['libc'] == 'avr-libc') or gp['llvm']):
        create_one_builddir(os.path.join(gp['bd'], 'gcc-stage-2'))

    # Appropriate C library build directory
    create_one_builddir(os.path.join(gp['bd'], gp['libc']))


def log_parameters():
    """Record all the global parameters in the log"""
    log.debug('Global parameters')
    log.debug('=================')

    for key, val in gp.items():
        log.debug(f'{key:<21}: {val}')

    log.debug('')


def arg_to_str(arg):
    """Convert a single argument to a string. If it is of the form parm=val
       and val has spaces, then surround val by single quotation marks."""

    # If no = then just return the same string
    if not '=' in arg:
        return arg

    # Split after first =
    argparts = arg.split('=', 1)

    # If no spaces in the second part, then we can still just use the plain
    # string.
    if len(argparts[1].split()) == 1:
        return arg

    # We have spaces in the second part, so surround it with quotes
    return f'{argparts[0]}="{argparts[1]}"'


def arglist_to_str(arglist):
    """Convert a subprocess arglist to a command string."""

    cmd = ''

    for arg in arglist:
        if arg != arglist[0]:
            cmd = cmd + ' '
        cmd = cmd + arg_to_str(arg)

    return cmd


def run_command(arglist, builddir, timeout):
    """Run a single command in a specified directory and with specified
       timeout. If successful return stdout, else die"""

    succeeded = True

    try:
        if gp['verbose']:
            log.debug(arglist_to_str(arglist))

        res = subprocess.run(
            arglist,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=builddir,
            timeout=timeout,
        )
        if res.returncode != 0:
            log.error(f'ERROR: failed')
            succeeded = False
    except subprocess.TimeoutExpired:
        log.error(f'ERROR: timed out after {timeout} seconds')
        succeeded = False

    if succeeded:
        return res.stdout.decode('utf-8')
    else:
        log.debug(f'Running in directory {builddir}')
        log.debug('Command was:')
        log.debug(arglist_to_str(arglist))
        if 'res' in locals():
            log.debug(res.stdout.decode('utf-8'))
            log.debug(res.stderr.decode('utf-8'))
        sys.exit(1)


def create_gnu_component(config_arglist, tool_name, builddir, make_targs=None):
    """Build and install a single tool chain component, which uses a GNU style
       configure-build-install sequence."""

    # Config
    log.info(f'Configuring {tool_name}...')
    run_command(
        arglist=config_arglist,
        builddir=builddir,
        timeout=gp['timeouts']['config'],
    )

    # Build, appending targets
    log.info(f'Building {tool_name}...')
    arglist = ['make', '-j', str(gp['cpus']),]

    if make_targs:
        for targ in make_targs:
            arglist.append(f'all-{targ}')
    else:
        arglist.append('all')

    run_command(
        arglist=arglist,
        builddir=builddir,
        timeout=gp['timeouts']['build'],
    )

    # Install, appending targets
    log.info(f'Installing {tool_name}...')
    arglist = ['make', '-j', str(gp['cpus']),]

    if make_targs:
        for targ in make_targs:
            arglist.append(f'install-{targ}')
    else:
        arglist.append('install')

    run_command(
        arglist=arglist,
        builddir=builddir,
        timeout=gp['timeouts']['install'],
    )

    if tool_name == 'Newlib nano':
        arglist = [
                'cp',
                os.path.join(gp['id'], gp['triplet'], 'lib', 'libc.a'),
                os.path.join(gp['id'], gp['triplet'], 'lib', 'libc_nano.a'),
                ]

        run_command(
            arglist=arglist,
            builddir=builddir,
            timeout=gp['timeouts']['install'],
        )

        arglist = [
                'cp',
                os.path.join(gp['id'], gp['triplet'], 'lib', 'libm.a'),
                os.path.join(gp['id'], gp['triplet'], 'lib', 'libm_nano.a'),
                ]

        run_command(
            arglist=arglist,
            builddir=builddir,
            timeout=gp['timeouts']['install'],
        )

        arglist = [
                'cp',
                os.path.join(gp['id'], gp['triplet'], 'lib', 'libg.a'),
                os.path.join(gp['id'], gp['triplet'], 'lib', 'libg_nano.a'),
                ]

        run_command(
            arglist=arglist,
            builddir=builddir,
            timeout=gp['timeouts']['install'],
        )

        arglist = [
                'cp',
                os.path.join(gp['id'], gp['triplet'], 'lib', 'libgloss.a'),
                os.path.join(gp['id'], gp['triplet'], 'lib', 'libgloss_nano.a'),
                ]

        run_command(
            arglist=arglist,
            builddir=builddir,
            timeout=gp['timeouts']['install'],
        )

        arglist = [
                'mkdir',
                '-p',
                os.path.join(gp['id'], gp['triplet'], 'include', 'newlib-nano'),
                ]

        run_command(
            arglist=arglist,
            builddir=builddir,
            timeout=gp['timeouts']['install'],
        )

        arglist = [
                'cp',
                os.path.join(gp['id'], gp['triplet'], 'include', 'newlib.h'),
                os.path.join(gp['id'], gp['triplet'], 'include', 'newlib-nano'),
                ]

        run_command(
            arglist=arglist,
            builddir=builddir,
            timeout=gp['timeouts']['install'],
        )


def create_llvm(conf_arglist, tool_name, builddir):
    """Configure, build and install Clang/LLVM"""

    # Configure
    log.info(f'Configuring {tool_name}...')
    run_command(
        arglist=conf_arglist,
        builddir=builddir,
        timeout=gp['timeouts']['config'],
    )

    # Build and install
    log.info(f'Building and installing {tool_name}...')
    arglist=['ninja', '-j', str(gp['cpus']), 'install']
    run_command(
        arglist=arglist,
        builddir=builddir,
        timeout=gp['timeouts']['build/install'],
    )

    # Link clang and clang++. This has to be relative to be useful, so needs
    # directory file descrptors.
    if tool_name == 'Clang/LLVM':
        log.info(f'Linking shortcuts to {tool_name}...')
        if os.symlink in os.supports_dir_fd:
            bindir = os.path.join(gp['id'], 'bin')
            ifd = os.open(bindir, os.O_RDONLY)

            if os.path.exists(os.path.join(bindir, gp['triplet'] + '-clang')):
                os.remove(gp['triplet'] + '-clang', dir_fd=ifd)
            if os.path.exists(os.path.join(bindir, gp['triplet'] + '-clang++')):
                os.remove(gp['triplet'] + '-clang++', dir_fd=ifd)

            os.symlink('clang', gp['triplet'] + '-clang', dir_fd=ifd)
            os.symlink('clang++', gp['triplet'] + '-clang++', dir_fd=ifd)
        else:
            log.warning(
                'Warning: Unable to create symbolic links for clang/clang++'
            )


def create_libc():
    """Create the C library to support the tool chain."""

    # Need to pick up newly installed library
    oldpath = os.environ['PATH']
    os.environ['PATH'] = (
        os.path.join(gp['id'], 'bin') + os.path.pathsep + oldpath
    )

    if gp['libc'] == 'avr-libc':
        # AVR LibC, for which we need to explicitly configure the build
        # architeture.
        arglist = [
            os.path.join(gp['rootdir'], 'libs', 'avr-libc', 'config.guess',),
        ]
        avr_builddir = os.path.join(gp['bd'], 'avr-libc')
        buildmc = run_command(
            arglist=arglist,
            builddir=avr_builddir,
            timeout=gp['timeouts']['config'],
        ).rstrip()

        # Build and install the library
        arglist = [
            os.path.join(gp['rootdir'], 'libs', 'avr-libc', 'configure',),
            '--prefix=' + gp['id'],
            '--build=' + buildmc,
            '--host=avr',
        ]

        create_gnu_component(
            config_arglist=arglist,
            tool_name='AVR LibC',
            builddir=avr_builddir,
        )

    elif gp['libc'] == 'newlib-nano':
#        # Newlib nano
#        arglist = [
#            os.path.join(gp['rootdir'], 'libs', 'newlib', 'configure'),
#            '--target=' + gp['triplet'],
#            '--prefix=' + gp['id'],
#            '--disable-newlib-fvwrite-in-streamio',
#            '--disable-newlib-fseek-optimization',
#            '--enable-newlib-nano-malloc',
#            '--disable-newlib-unbuf-stream-opt',
#            '--enable-newlib-reent-small',
#            '--disable-newlib-wide-orient',
#            '--enable-newlib-nano-formatted-io',
#            '--enable-lite-exit',
#            '--enable-newlib-global-atexit',
#            '--disable-newlib-supplied-syscalls',
#            '--disable-nls',
#            'CFLAGS_FOR_TARGET=-Os -ffunction-sections -fdata-sections -mcmodel=medany',
#            'CXXFLAGS_FOR_TARGET=-Os -ffunction-sections -fdata-sections -mcmodel=medany',
#        ]
        arglist = [
            os.path.join(gp['rootdir'], 'libs', 'newlib', 'configure'),
            '--target=' + gp['triplet'],
            '--prefix=' + gp['id'],
            '--sysconfdir=' + os.path.join(gp['id'], 'etc'),
            '--localstatedir=' + os.path.join(gp['id'], 'var'),
            '--with-sysroot=' + os.path.join(gp['id'], gp['triplet'], 'sysroot'),
            '--disable-newlib-fvwrite-in-streamio',
            '--disable-newlib-fseek-optimization',
            '--enable-newlib-nano-malloc',
            '--disable-newlib-unbuf-stream-opt',
            '--enable-target-optspace',
            '--enable-newlib-reent-small',
            '--disable-newlib-wide-orient',
            '--disable-newlib-io-float',
            '--enable-newlib-nano-formatted-io',
            '--enable-lite-exit',
            '--disable-newlib-supplied-syscalls',
        ]

        # For LLVM need to specify clang when configuring.
        if gp['llvm']:
            arglist.append('CC_FOR_TARGET=' + gp['triplet'] + '-clang')
            arglist.append('GCC_FOR_TARGET=' + gp['triplet'] + '-clang')
            arglist.append('LD_FOR_TARGET=' + gp['triplet'] + '-clang')

        # Construct the target C flags. How these map as target flags is in
        # some cases target specific.
        cflags = gp['target_cflags']
        for opt_arg in ['arch', 'abi', 'cpu', 'endian',]:
            if gp[opt_arg]:
                if cflags:
                    cflags = cflags + ' '
                cflags = cflags + '-m' + opt_arg + '=' + gp[opt_arg]

        # Should be only on arm, and only "arm" or "thumb"
        if gp['mode']:
            if cflags:
                cflags = cflags + ' '
            cflags = cflags + '-m' + gp['mode']

        # Should be only on arm
        if gp['float']:
            if cflags:
                cflags = cflags + ' '
            cflags = cflags + '-mfloat-abi=' + gp['float']

        # This is necessary for riscv32-unknown-elf 12.2.0 GCC compiler
        cflags = cflags + ' -Wno-int-conversion -Wno-implicit-function-declaration'

        # We must not surround the flags with quote. That's a shell syntactic
        # delimiter, but we are already delimited.
        arglist.append(f'CFLAGS_FOR_TARGET={cflags}')

        # Build and install it
        create_gnu_component(
            config_arglist=arglist,
            tool_name='Newlib nano',
            builddir=os.path.join(gp['bd'], 'newlib-nano')
        )

    else:
        # Newlib
        arglist = [
            os.path.join(gp['rootdir'], 'libs', 'newlib', 'configure'),
            '--target=' + gp['triplet'],
            '--prefix=' + gp['id'],
            '--sysconfdir=' + os.path.join(gp['id'], 'etc'),
            '--localstatedir=' + os.path.join(gp['id'], 'var'),
            '--with-sysroot=' + os.path.join(gp['id'], gp['triplet'], 'sysroot'),
            '--disable-newlib-fvwrite-in-streamio',
            '--disable-newlib-fseek-optimization',
            '--enable-newlib-nano-malloc',
            '--disable-newlib-unbuf-stream-opt',
            '--enable-target-optspace',
            '--enable-newlib-reent-small',
            '--disable-newlib-wide-orient',
            '--disable-newlib-io-float',
            '--enable-newlib-nano-formatted-io',
            '--enable-lite-exit',
            '--disable-newlib-supplied-syscalls',
        ]

        # For LLVM need to specify clang when configuring.
        if gp['llvm']:
            arglist.append('CC_FOR_TARGET=' + gp['triplet'] + '-clang')
            arglist.append('GCC_FOR_TARGET=' + gp['triplet'] + '-clang')
            arglist.append('LD_FOR_TARGET=' + gp['triplet'] + '-clang')

        # Construct the target C flags. How these map as target flags is in
        # some cases target specific.
        cflags = gp['target_cflags']
        for opt_arg in ['arch', 'abi', 'cpu', 'endian',]:
            if gp[opt_arg]:
                if cflags:
                    cflags = cflags + ' '
                cflags = cflags + '-m' + opt_arg + '=' + gp[opt_arg]

        # Should be only on arm, and only "arm" or "thumb"
        if gp['mode']:
            if cflags:
                cflags = cflags + ' '
            cflags = cflags + '-m' + gp['mode']

        # Should be only on arm
        if gp['float']:
            if cflags:
                cflags = cflags + ' '
            cflags = cflags + '-mfloat-abi=' + gp['float']

        # This is necessary for riscv32-unknown-elf 12.2.0 GCC compiler
        cflags = cflags + ' -Wno-int-conversion -Wno-implicit-function-declaration'

        # We must not surround the flags with quote. That's a shell syntactic
        # delimiter, but we are already delimited.
        arglist.append(f'CFLAGS_FOR_TARGET={cflags}')

        # Build and install it
        create_gnu_component(
            config_arglist=arglist,
            tool_name='Newlib',
            builddir=os.path.join(gp['bd'], 'newlib')
        )

    if (gp['llvm']):
        # Build compiler-rt
        config_arglist = [
            'cmake',
            '-DCMAKE_INSTALL_PREFIX=' + subprocess.check_output([gp['id'] + '/bin/clang', '-print-resource-dir']).decode("utf-8"),
            '-DCMAKE_C_COMPILER=' + gp['id'] + '/bin/clang',
            '-DCMAKE_CXX_COMPILER=' + gp['id'] + '/bin/clang',
            '-DCMAKE_AR=' + gp['id'] + '/bin/llvm-ar',
            '-DCMAKE_NM=' + gp['id'] + '/bin/llvm-nm',
            '-DCMAKE_RANLIB=' + gp['id'] + '/bin/llvm-ranlib',
            '-DCMAKE_C_COMPILER_TARGET=' + gp['triplet'],
            '-DCMAKE_CXX_COMPILER_TARGET=' + gp['triplet'],
            '-DCMAKE_ASM_COMPILER_TARGET=' + gp['triplet'],
            '-DCMAKE_C_FLAGS=' + cflags,
            '-DCMAKE_CXX_FLAGS=' + cflags,
            '-DCMAKE_ASM_FLAGS=' + cflags,
            '-DCOMPILER_RT_BAREMETAL_BUILD=ON',
            '-DCOMPILER_RT_DEFAULT_TARGET_ONLY=ON',
            '-DLLVM_CONFIG_PATH=' + gp['bd'] + '/llvm/bin/llvm-config',
            '../../llvm-project/compiler-rt',
            '-G',
            'Ninja',
            os.path.join(gp['rootdir'], 'llvm', 'llvm-project', 'compiler-rt'),
        ]

        create_llvm(
            conf_arglist=config_arglist,
            tool_name='compiler-rt',
            builddir=os.path.join(gp['bd'], 'compiler-rt'),
        )

    # Restore PATH
    os.environ['PATH'] = oldpath


def create_tool_chain():
    """build and install a complete tool chain"."""

    now = datetime.datetime.strftime(
        datetime.datetime.now(), '%d-%b-%y %H:%M:%S'
    )
    log.info(f'Starting build at {now}')

    # Binutils and GDB
    arglist = [
        os.path.join(gp['rootdir'], 'gnu', 'binutils-gdb', 'configure'),
        '--target=' + gp['triplet'],
        '--prefix=' + gp['id'],
        '--sysconfdir=' + os.path.join(gp['id'], 'etc'),
        '--localstatedir=' + os.path.join(gp['id'], 'var'),
        '--with-sysroot=' + os.path.join(gp['id'], gp['triplet'], 'sysroot'),
        '--disable-gtk-doc',
        '--disable-gtk-doc-html',
        '--disable-doc',
        '--disable-docs',
        '--disable-documentation',
        '--with-fop=no',
        '--disable-multilib',
        '--enable-plugins',
        '--enable-poison-system-directories',
        '--disable-tls',
        '--disable-sim',
    ]

    # Optional args not set for all targets
    for opt_arg in ['arch', 'abi', 'cpu', 'mode', 'float', 'endian', 'isa_spec']:
        if gp[opt_arg]:
            if opt_arg == 'isa_spec':
                arglist.append(f'--with-isa-spec=' + gp[opt_arg])
            else:
                arglist.append(f'--with-{opt_arg}=' + gp[opt_arg])

    # Build and install it
    create_gnu_component(
        config_arglist=arglist,
        tool_name='Binutils',
        builddir=os.path.join(gp['bd'], 'binutils'),
        make_targs=['binutils', 'ld', 'gas', 'gdb'],
    )

    # GCC stage 1. We need this at present for Clang/LLVM, but only for
    # libgcc.
    targs = ['target-libgcc'] if gp['llvm'] else None
    arglist = [
        os.path.join(gp['rootdir'], 'gnu', 'gcc', 'configure'),
        '--target=' + gp['triplet'],
        '--prefix=' + gp['id'],
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

    # Optional args not set for all targets
    for opt_arg in ['arch', 'abi', 'cpu', 'mode', 'float', 'endian', 'isa_spec']:
        if gp[opt_arg]:
            if opt_arg == 'isa_spec':
                arglist.append(f'--with-isa-spec=' + gp[opt_arg])
            else:
                arglist.append(f'--with-{opt_arg}=' + gp[opt_arg])

    # Build and install it
    create_gnu_component(
        config_arglist=arglist,
        tool_name='GCC Stage 1',
        builddir=os.path.join(gp['bd'], 'gcc-stage-1'),
        make_targs=targs,
    )

    # LLVM
    if gp['llvm']:
        # Clang/LLVM
        exp_target = 'EXPERIMENTAL_' if gp['experimental'] else ''

        binutils_incdir = os.path.join(
            gp['rootdir'], 'gnu', 'binutils-gdb', 'include'
        )

        config_arglist = [
            'cmake',
            '-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_CROSSCOMPILING=True',
            '-DLLVM_ENABLE_PROJECTS=clang',
            '-DLLVM_OPTIMIZED_TABLEGEN=ON',
            '-DLLVM_ENABLE_ASSERTIONS=ON',
            '-DBUILD_SHARED_LIBS=ON',
            '-DCMAKE_INSTALL_PREFIX=' + gp['id'],
            '-DLLVM_' + exp_target + 'TARGETS_TO_BUILD=' + gp['llvm_arch'],
            '-DLLVM_BINUTILS_INCDIR=' + binutils_incdir,
            '-DLLVM_DEFAULT_TARGET_TRIPLE=' + gp['triplet'],
            '-G',
            'Ninja',
            os.path.join(gp['rootdir'], 'llvm', 'llvm-project', 'llvm'),
        ]

        create_llvm(
            conf_arglist=config_arglist,
            tool_name='Clang/LLVM',
            builddir=os.path.join(gp['bd'], 'llvm'),
        )

    # Create a C library
    create_libc()

    # GCC stage 2. Not needed for AVR LibC or LLVM
    if not ((gp['libc'] == 'avr-libc') or gp['llvm']):
        build_time_tools = os.path.join(gp['id'], gp['triplet'], 'bin')
        arglist = [
            os.path.join(gp['rootdir'], 'gnu', 'gcc', 'configure'),
            '--with-build-time-tools=' + build_time_tools,
            '--target=' + gp['triplet'],
            '--prefix=' + gp['id'],
            '--sysconfdir=' + os.path.join(gp['id'], 'etc'),
            '--localstatedir=' + os.path.join(gp['id'], 'var'),
            '--with-sysroot=' + os.path.join(gp['id'], gp['triplet'], 'sysroot'),
            '--disable-shared',
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
            '--enable-languages=c',
            '--with-newlib',
            '--disable-largefile',
            '--enable-plugins',
            '--disable-nls',
            '--enable-checking=yes',
        ]

        # Optional args not set for all targets
        for opt_arg in ['arch', 'abi', 'cpu', 'mode', 'float', 'endian', 'isa_spec']:
            if gp[opt_arg]:
                if opt_arg == 'isa_spec':
                    arglist.append(f'--with-isa-spec=' + gp[opt_arg])
                else:
                    arglist.append(f'--with-{opt_arg}=' + gp[opt_arg])

        # Build and install it
        create_gnu_component(
            config_arglist=arglist,
            tool_name='GCC Stage 2',
            builddir=os.path.join(gp['bd'], 'gcc-stage-2')
        )

    # All done
    now = datetime.datetime.strftime(
        datetime.datetime.now(), '%e-%b-%y %H:%M:%S'
    )
    log.info(f'Finishing build at {now}')


def main():
    """Main program to drive building of a tool chain.

       There is an assumed file hierarchy from the parent directory to this
       repository (known as the root directory).

       - tooling                This repo
       - gnu                    Directory for all gnu repos
         - binutils-gdb
         - gcc
       - llvm                   Directory for all LLVM repos
         - llvm-project
       - libs -                 Directory for non-tool chain specific libraries
         - avr-libc
         - newlib
       - install-<xxx>          Installation directory for tool chain <xxx>
       - build-<xxx>            Build directory for tool chain <xxx> components
         - binutils
         - gcc-stage-1
         - gcc-stage-2
         - llvm
         - avr-libc
         - newlib

       Build directories are only created as needed."""

    # Establish the root directory of the repository, since we know it is the
    # parent directory of the directory containing this file.
    gp['rootdir'] = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir)
    )

    # Parse arguments using standard technology
    args = get_args()

    # Establish logging, using "tool-chain" as the log file prefix.
    setup_logging(args.logdir, 'tool-chain')
    log_args(args)

    # Check args are OK (have to have logging and build directory set up first)
    validate_args(args)

    # Establish build directory and subdirectories
    create_builddirs(args.builddir, args.clean)

    # Log args and parameters
    log_parameters()

    # Build and install the tool chain
    create_tool_chain()


# Make sure we have new enough Python and only run if this is the main package

check_python_version(3, 6)
if __name__ == '__main__':
    sys.exit(main())
