UNIT=stress-zswap

sudo systemd-run --unit=$UNIT \
    --collect \
    -p MemoryHigh=1G \
    -p MemoryMax=1200M \
    -p MemorySwapMax=6G \
    --same-dir \
    stress-ng --vm 1 --vm-bytes 5G --vm-populate --vm-keep --timeout 600s

# To check the status of this serviee:
# sudo systemctl status $UNIT

# To stop the service:
# sudo systemctl stop $UNIT 
