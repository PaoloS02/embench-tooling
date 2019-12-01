#!/usr/bin/env python3

# Common python procedures for use across tooling.

# Copyright (C) 2019 Embecosm Limited
#
# Contributor: Jeremy Bennett <jeremy.bennett@embecosm.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tooling common procedures.
"""

import logging
import math
import os
import re
import sys
import time


# What we export

__all__ = [
    'check_python_version',
    'log',
    'gp',
    'setup_logging',
    'log_args',
    'arglist_to_str',
]

# Handle for the logger
log = logging.getLogger()

# All the global parameters
gp = dict()


# Make sure we have new enough python
def check_python_version(major, minor):
    """Check the python version is at least {major}.{minor}."""
    if ((sys.version_info[0] < major)
        or ((sys.version_info[0] == major) and (sys.version_info[1] < minor))):
        log.error(f'ERROR: Requires Python {major}.{minor} or later')
        sys.exit(1)


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


def arglist_to_str(arglist):
    """Make arglist into a string"""

    for arg in arglist:
        if arg == arglist[0]:
            str = arg
        else:
            str = str + ' ' + arg

    return str
