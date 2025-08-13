#!/bin/bash

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

BASE_SYMBOL_ADDRESS1=$(bash $THIS_DIR/get__update_sd_lb_stats.constprop.0__addr.sh)
BASE_SYMBOL_ADDRESS2=$(bash $THIS_DIR/get__sched_balance_rq__addr.sh)

ADDR1=$(printf "%x" $((0x$BASE_SYMBOL_ADDRESS1+0x840)))
ADDR2=$(printf "%x" $((0x$BASE_SYMBOL_ADDRESS1+0xa09)))
ADDR3=$(printf "%x" $((0x$BASE_SYMBOL_ADDRESS2+0x3f9)))

bash $THIS_DIR/../../../scripts/runtime-disas.sh update_sd_lb_stats.constprop.0 |\
    grep -A1 -e  $ADDR1 -e $ADDR2
bash $THIS_DIR/../../../scripts/runtime-disas.sh sched_balance_rq |\
    grep -e  $ADDR3
