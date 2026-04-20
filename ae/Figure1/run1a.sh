#!/bin/bash

mkdir -p iolog

echo "Generating I/O logs..."

python gen_iolog.py --dev sdb --op write --outfile iolog/iolog_write.txt --bs 512
python gen_iolog.py --dev sdb --op read --outfile iolog/iolog_read.txt --bs 512

mkdir -p results

echo "Running baseline (BLK_MAX_REQUEST_COUNT = 32)..."

sudo bash fio_bench.sh WRITE.fio > results/hdd_32_write.txt
sudo bash fio_bench.sh READ.fio > results/hdd_32_read.txt

echo "Tuning BLK_MAX_REQUEST_COUNT = 128..."
sudo ./tune_blk_max_req.sh 128
echo "Running tuned (BLK_MAX_REQUEST_COUNT = 128)..."
sudo bash fio_bench.sh WRITE.fio > results/hdd_128_write.txt
sudo bash fio_bench.sh READ.fio > results/hdd_128_read.txt

echo "Unloading tunable..."
sudo ./tune_blk_max_req.sh unload
sudo ~/Xkernel/xkernel-tool table delete --all -y
sudo rm -rf ~/Xkernel/bpf/stubs/*