#!/bin/bash

set -ex

export LLVM_COMPILER=clang

KERNEL_DIR=${KERNEL_DIR:-../linux-wllvm-defconfig}

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

# SOURCE_FILE=net/sunrpc/cache.c
# DEFINITION_SOURCE_FILE=net/sunrpc/cache.c
# SED_PATTERN='s|\#define	DFR_MAX	300|#define	DFR_MAX	299|'

### 2. GSSD_MIN_TIMEOUT

# SOURCE_FILE=net/sunrpc/auth_gss/auth_gss.c
# DEFINITION_SOURCE_FILE=net/sunrpc/auth_gss/auth_gss.c
# SED_PATTERN='s|\#define GSSD_MIN_TIMEOUT (60 \* 60)|#define GSSD_MIN_TIMEOUT (60 \* 30)|'

### 3. SMC_TX_WORK_DELAY

# SOURCE_FILE=net/smc/smc_tx.c
# DEFINITION_SOURCE_FILE=net/smc/smc_tx.c
# SED_PATTERN='s|\#define SMC_TX_WORK_DELAY	0|#define SMC_TX_WORK_DELAY	7|'

### 4. SMC_LGR_NUM_INCR

# SOURCE_FILE=net/smc/smc_core.c
# DEFINITION_SOURCE_FILE=net/smc/smc_core.c
# SED_PATTERN='s|\#define SMC_LGR_NUM_INCR		256|#define SMC_LGR_NUM_INCR		253|'

### 5. RDS_IB_RECYCLE_BATCH_COUNT

# SOURCE_FILE=net/rds/ib_recv.c
# DEFINITION_SOURCE_FILE=net/rds/ib.h
# SED_PATTERN='s|\#define RDS_IB_RECYCLE_BATCH_COUNT	32|#define RDS_IB_RECYCLE_BATCH_COUNT	31|'

### 6. QUEUE_THRESHOLD

# SOURCE_FILE=net/sched/sch_pie.c
# DEFINITION_SOURCE_FILE=include/net/pie.h
# SED_PATTERN='s|\#define QUEUE_THRESHOLD	16384|#define QUEUE_THRESHOLD	16381|'

### 7. PIE_SCALE

# SOURCE_FILE=net/sched/sch_pie.c
# DEFINITION_SOURCE_FILE=include/net/pie.h
# SED_PATTERN='s|\#define PIE_SCALE	8|#define PIE_SCALE	7|'

### 8. BUSY_POLL_BUDGET (invoked in two files)

# SOURCE_FILE=io_uring/napi.c
# DEFINITION_SOURCE_FILE=include/net/busy_poll.h
# SED_PATTERN='s|\#define BUSY_POLL_BUDGET 8|\#define BUSY_POLL_BUDGET 7|'

# SOURCE_FILE=fs/eventpoll.c
# DEFINITION_SOURCE_FILE=include/net/busy_poll.h
# SED_PATTERN='s|\#define BUSY_POLL_BUDGET 8|\#define BUSY_POLL_BUDGET 7|'

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

diff -s --color=always \
    <(grep -v '^![0-9]' $LL_FILE         | grep -v '^    #dbg_value') \
    <(grep -v '^![0-9]' $LL_FILE.mutated | grep -v '^    #dbg_value') \
    || true

echo $KERNEL_DIR/$LL_FILE
