#!/bin/bash

set -ex

export LLVM_COMPILER=clang

KERNEL_DIR=${KERNEL_DIR:-../linux-wllvm-defconfig}
THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [[ ! -d $KERNEL_DIR ]]; then
    echo "KERNEL_DIR not set or does not exist"
    exit 1
fi

if ! command -v opt >/dev/null 2>&1; then
    export PATH=/usr/lib/llvm-20/bin:$PATH
    if ! command -v opt >/dev/null 2>&1; then
        echo "opt not found"
        exit 1
    fi
fi

### 1. DFR_MAX

SOURCE_FILE=net/sunrpc/cache.c
DEFINITION_SOURCE_FILE=net/sunrpc/cache.c
SED_PATTERN='s|\#define	DFR_MAX	300|#define	DFR_MAX	299|'

source .all-cases-locate-ir.sh

OBJ_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).o
BC_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).bc
LL_FILE=$(dirname $SOURCE_FILE)/$(basename $SOURCE_FILE .c).ll

cd $KERNEL_DIR

rm -f $OBJ_FILE
make CC=wllvm AR=llvm-ar HOSTCC=clang $OBJ_FILE
extract-bc $OBJ_FILE -o $BC_FILE
llvm-dis $BC_FILE -o $LL_FILE
mv $LL_FILE{,.origin}
mv $BC_FILE{,.origin}
mv $OBJ_FILE{,.origin}

cp $DEFINITION_SOURCE_FILE{,.origin}
sed -i "$SED_PATTERN" $DEFINITION_SOURCE_FILE

rm -f $OBJ_FILE
make CC=wllvm AR=llvm-ar HOSTCC=clang $OBJ_FILE
extract-bc $OBJ_FILE -o $BC_FILE
llvm-dis $BC_FILE -o $LL_FILE
mv $LL_FILE{,.mutated}

mv $DEFINITION_SOURCE_FILE{.origin,}
mv $BC_FILE{.origin,}
mv $LL_FILE{.origin,}
mv $OBJ_FILE{.origin,}

set +e # Allow diff to legitimately fail

diff -s --color=always \
    <(grep -v '^![0-9]' $LL_FILE         | grep -v '^    #dbg_value') \
    <(grep -v '^![0-9]' $LL_FILE.mutated | grep -v '^    #dbg_value')

diff -s `#--color=always` \
    <(grep -v '^![0-9]' $LL_FILE         | grep -v '^    #dbg_value') \
    <(grep -v '^![0-9]' $LL_FILE.mutated | grep -v '^    #dbg_value') \
    > $LL_FILE.diff

set -e

python $THIS_DIR/parse_ir_diff.py $LL_FILE.diff $KERNEL_DIR/$LL_FILE

echo $KERNEL_DIR/$LL_FILE
