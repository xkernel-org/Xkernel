#!/bin/bash

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

BASE_SYMBOL_ADDRESS=$(bash $THIS_DIR/get__task_numa_fault__addr.sh)

ADDR1=$(printf "%x" $((0x$BASE_SYMBOL_ADDRESS+0x843)))
ADDR2=$(printf "%x" $((0x$BASE_SYMBOL_ADDRESS+0x84c)))
ADDR3=$(printf "%x" $((0x$BASE_SYMBOL_ADDRESS+0x9cf)))
ADDR4=$(printf "%x" $((0x$BASE_SYMBOL_ADDRESS+0x9d8)))
ADDR5=$(printf "%x" $((0x$BASE_SYMBOL_ADDRESS+0xb40)))

bash $THIS_DIR/../../../scripts/runtime-disas.sh task_numa_fault |\
    grep -e  $ADDR1 -e $ADDR2 -e $ADDR3 -e $ADDR4 -e $ADDR5
