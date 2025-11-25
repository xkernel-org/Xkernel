UNIT=zswap_min

sudo systemd-run --unit=$UNIT \
    -p MemoryHigh=1G \
    -p MemoryMax=1200M \
    -p MemorySwapMax=6G \
    --same-dir --collect --pty \
    numactl --cpunodebind=0 --membind=0 \
    time ./bin/zswap_min --total-mb 4096 --block-pages 128 --reuse-dist 16 \
               --warmup-passes 3 --burst 12 --loops 2000 --file ./res/16.txt

sudo chown yltang:xkernel-PG0 ./res/16.txt

# To check the status of this serviee:
# sudo systemctl status $UNIT

# To stop the service:
# sudo systemctl stop $UNIT 
