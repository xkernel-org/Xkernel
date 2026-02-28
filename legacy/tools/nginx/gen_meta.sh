#!/bin/bash

# 创建目录
mkdir -p /var/www/html/bench
cd /var/www/html/bench
sudo rm -rf ./*

echo "Generating 100 files with Heavy-Tailed distribution..."
echo "Source: /dev/urandom (To prevent compression cheating)"

for i in {1..100}; do
    # 生成 1-100 的随机数来决定文件属于哪一类
    rand=$(($RANDOM % 100 + 1))
    
    if [ $rand -le 20 ]; then
        # [20% 概率] Class A: 100KB - 1MB
        # CDF: 0-20% < 1MB
        size_kb=$(( ($RANDOM % 900) + 100 ))
        size_mb=$(echo "scale=3; $size_kb / 1024" | bc)
        size_bytes=$(( $size_kb * 1024 ))
        class="Class A (100KB-1MB)"
        use_bytes=true

    elif [ $rand -le 40 ]; then
        # [20% 概率] Class B: 1MB - 5MB
        # CDF: 20-40% < 5MB
        size=$(( ($RANDOM % 4) + 1 ))
        size_mb=$size
        size_bytes=0
        class="Class B (1MB-5MB)"
        use_bytes=false

    elif [ $rand -le 60 ]; then
        # [20% 概率] Class C: 5MB - 8MB
        # CDF: 40-60% < 8MB
        size=$(( ($RANDOM % 3) + 5 ))
        size_mb=$size
        size_bytes=0
        class="Class C (5MB-8MB)"
        use_bytes=false

    elif [ $rand -le 80 ]; then
        # [20% 概率] Class D: 8MB - 10MB
        # CDF: 60-80% < 10MB
        size=$(( ($RANDOM % 2) + 8 ))
        size_mb=$size
        size_bytes=0
        class="Class D (8MB-10MB)"
        use_bytes=false

    elif [ $rand -le 90 ]; then
        # [10% 概率] Class E: 10MB - 30MB
        # CDF: 80-90% < 30MB
        size=$(( ($RANDOM % 20) + 10 ))
        size_mb=$size
        size_bytes=0
        class="Class E (10MB-30MB)"
        use_bytes=false

    else
        # [10% 概率] Class F: 30MB - 100MB
        # CDF: 90-100% < 100MB
        size=$(( ($RANDOM % 70) + 30 ))
        size_mb=$size
        size_bytes=0
        class="Class F (30MB-100MB)"
        use_bytes=false
    fi

    if [ "$use_bytes" = true ]; then
        echo "[File $i/100] Generating ${size_kb}KB ($class)..."
        # 使用字节为单位生成文件
        dd if=/dev/urandom of=file_$i.bin bs=1 count=$size_bytes status=none
    else
        echo "[File $i/100] Generating ${size}MB ($class)..."
        # 使用 /dev/urandom 防止 NGINX gzip 压缩作弊
        # 如果嫌慢，可以改用 if=/dev/zero，但要确保 NGINX 关闭了 gzip
        dd if=/dev/urandom of=file_$i.bin bs=1M count=$size status=none
    fi
done

echo "Done. Workset generation complete."
ls -lhS # 按大小排序显示