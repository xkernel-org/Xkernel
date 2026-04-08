#!/bin/bash

sudo apt-get update
sudo apt-get install -y fio liburing-dev

mkdir -p iolog

python gen_iolog.py --dev sdb --op write --outfile iolog/iolog_write.txt
python gen_iolog.py --dev sdb --op read --outfile iolog/iolog_read.txt

mkdir -p results

sudo bash fio_bench.sh WRITE.fio > results/hdd_32_write.log
sudo bash fio_bench.sh READ.fio > results/hdd_32_read.log

sudo ./tune_blk_max_req.sh 128
sudo bash fio_bench.sh WRITE.fio > results/hdd_128_write.log
sudo bash fio_bench.sh READ.fio > results/hdd_128_read.log

sudo ./tune_blk_max_req.sh unload
sudo ~/Xkernel/xkernel-tool table delete --all -y
