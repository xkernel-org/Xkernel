# 1) 编译
gcc -O2 -Wall t.c -luring -o t

# 2) 准备目录与样本文件（一次性）
mkdir -p ./iowqA
for i in $(seq 0 4095); do : > ./iowqA/f$(printf "%06d" $i); done
sync

# 3) 跑之前可选清缓存（让 openat 更容易阻塞元数据路径）
echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null

# 4) 运行（参数：目录 文件数 队列深度 秒数）
./t ./iowqA 4096 512 20
