#!/bin/bash

# sudo apt-get install netperf -y

REMOTE_HOST="192.168.25.1"

nstat > /dev/null

echo "Running netperf tests to $REMOTE_HOST..."
for i in $(seq 1 5); do
  netperf -H "$REMOTE_HOST" -- -k THROUGHPUT | grep THROUGHPUT
done

wait

echo ""
echo "Hystart-related statistics:"
nstat | grep -i hystart
