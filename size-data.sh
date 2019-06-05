#!/bin/bash

sed -n -e '/^[[:blank:]]\+=== Size table ===/,/^Total[[:blank:]]\+/p' \
	< ${HOME}/gittrees/embench/build/embench-beebs/testsuite/beebs.log | \
    sed -n -e '5,23p' | sed -e 's/[[:blank:]]\+/,/g' | \
    cut -d ',' -f 2
