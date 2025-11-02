fio --name=plug_storm --filename=/users/yltang/sdb/aio.dat \
    --size=8G --rw=randread --bs=4k \
    --ioengine=libaio --direct=1 \
    --iodepth=3 \
    --iodepth_batch_submit=3 \
    --iodepth_batch_complete_min=1 --iodepth_batch_complete=1 \
    --time_based=1 --runtime=20
