#!/bin/bash
CPU=${1:-3}
sudo cyclictest -t 1 -a $CPU -p 99 -d 1000 -l 10000