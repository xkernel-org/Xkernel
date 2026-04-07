#!/bin/bash

sudo apt-get update
sudo apt-get install -y fio liburing-dev

python gen_iolog.py --dev nvme1n1 --op write --outfile iolog_write.txt
