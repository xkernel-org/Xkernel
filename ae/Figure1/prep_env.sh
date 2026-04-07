#!/bin/bash

sudo apt-get update
sudo apt-get install -y fio liburing-dev

python gen_iolog.py --dev sdb --op write --outfile iolog_write.txt
