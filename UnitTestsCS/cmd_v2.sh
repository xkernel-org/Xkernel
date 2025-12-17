sudo python check_assembly_diff.py -f block/blk-mq.c -s "BLK_MAX_REQUEST_COUNT" "64"
sudo python check_assembly_diff.py -f block/blk-mq.c -s "BLK_MAX_REQUEST_COUNT" "128"

sudo python check_assembly_diff.py -f net/ipv4/tcp_output.c -s "TCP_DELACK_MAX" "10"
sudo python check_assembly_diff.py -f net/ipv4/tcp_output.c -s "TCP_DELACK_MAX" "15"