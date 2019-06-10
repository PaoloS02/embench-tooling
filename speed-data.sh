#!/bin/bash

sed -n -e '/^[[:blank:]]\+=== Execution time table ===/,/^Total[[:blank:]]\+/p' \
	< ${HOME}/gittrees/embench/build/embench-iot/testsuite/beebs.log | \
    sed -n -e '5,23p' | sed -e 's/[[:blank:]]\+/,/g' | \
    cut -d ',' -f 2
