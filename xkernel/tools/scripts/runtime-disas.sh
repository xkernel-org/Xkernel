#!/bin/bash

# Usage: bash ./runtime-disas.sh select_task_rq_fair | less

set -e

# sudo is not configured in Wentao's KVM/QEMU setup
if sudo true >& /dev/null; then
    SUDO=sudo
else
    SUDO=""
fi

truncate -s 0 /tmp/disas.txt

FUNC_NAME=${1:-"select_task_rq_fair"}

TEXT_OFFSET=$(     $SUDO readelf -W --segments /proc/kcore |\
                         grep '^  LOAD' |\
                         awk '{ print $2; }' |\
                         head -1 | tail -1 )
TEXT_VA_START=$(   $SUDO readelf -W --segments /proc/kcore |\
                         grep '^  LOAD' |\
                         awk '{ print $3; }' |\
                         head -1 | tail -1 )
TEXT_VA=0x$(       $SUDO grep " $FUNC_NAME\$" /proc/kallsyms |\
                         awk '{ print $1; }' )
TEXT_VA2=0x$(      $SUDO grep " $FUNC_NAME\$" -A1 /proc/kallsyms |\
                         tail -1 |\
                         awk '{ print $1; }' )

# $SUDO dd if=/proc/kcore of=/tmp/insns.bin bs=1 \
# skip=$((TEXT_VA-TEXT_VA_START+TEXT_OFFSET)) \
# count=$((TEXT_VA2-TEXT_VA)) status=none

# objdump -b binary -m i386:x86-64 -D /tmp/insns.bin --adjust-vma=$TEXT_VA > /tmp/disas.txt

$SUDO objdump -D --start-address=$TEXT_VA --stop-address=$TEXT_VA2 /proc/kcore > /tmp/disas.txt

cat /tmp/disas.txt
rm -f /tmp/insn.bin
