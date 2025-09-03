UNIT=zswap_min

sudo systemd-run --unit=$UNIT \
    -p MemoryHigh=1G \
    -p MemoryMax=1200M \
    -p MemorySwapMax=6G \
    --same-dir --collect --pty \
    numactl --cpunodebind=0 --membind=0 \
    time ./bin/zswap_min --total-mb 6144 --block-pages 128 --reuse-dist 16 \
               --warmup-passes 3 --burst 12 --loops 2000 
               # --warmup-passes 3 --burst 12 --loops 2000 --file ./res/dt_us/1.txt
               # --warmup-passes 3 --burst 12 --loops 2000 --file ./res/8.txt \
    
# sudo chmod 666 ./res/dt_us/1.txt
# sudo chmod 666 ./res/8.txt
# sudo chmod 666 ./res/12.txt
# sudo chmod 666 ./res/dt_us/16.txt
# sudo chmod 666 ./res/dt_us/20.txt
# sudo chmod 666 ./res/dt_us/22.txt
# sudo chmod 666 ./res/dt_us/23.txt
# sudo chmod 666 ./res/24.txt
# sudo chmod 666 ./res/32.txt
# sudo chmod 666 ./res/128.txt


# To check the status of this serviee:
# sudo systemctl status $UNIT

# To stop the service:
# sudo systemctl stop $UNIT 
