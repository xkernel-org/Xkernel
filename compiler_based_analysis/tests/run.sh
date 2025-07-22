#!/bin/bash

set -e

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $THIS_DIR

bear -- clang -c test.c

echo
echo ">> integer literal"
echo

../tool/constant_analysis --mode=int-literal -p . ./test.c

echo
echo ">> macro constant"
echo

../tool/constant_analysis --mode=macro-const -p . ./test.c
