#!/bin/bash
#
# Script to measure the static frequency of instructions in RISC-V binaries.
#
# Copyright (C) 2019 Embecosm Limited
#
# Contributor: Jeremy Bennett <jeremy.bennett@embecosm.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Get arg

progdir="$(dirname $0)"
topdir="$(cd ${progdir}/..; pwd)"
srcdir=${topdir}/embench-iot/src

cd ${srcdir}

for d in *
do
    if [ -d ${d} ]
    then
	data=$(sloccount ${d} | grep '^ansic:' | \
		   sed -e 's/ \+/,/g' -e 's/ansic:,//' -e 's/(//' -e 's/%)//')
	lines=$(echo ${data} | cut -d ',' -f 1)
	pc=$(echo ${data} | cut -d ',' -f 2)
	if [ "${pc}" = "100.00" ]
	then
	    printf "%-14s,%4d\n" "${d}" "${lines}"
	fi
    fi
done
