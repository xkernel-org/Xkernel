#!/bin/bash

while true; do
    timeout 1 ./wakeup_task 42 100
    timeout 1 ./wakeup_task 42 200
    timeout 1 ./wakeup_task 42 400
    timeout 1 ./wakeup_task 42 800
    timeout 1 ./wakeup_task 42 1600
done
