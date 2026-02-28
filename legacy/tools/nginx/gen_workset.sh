#!/bin/bash

# 目录设置
TARGET_DIR="/var/www/html/bench"
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"
sudo rm -rf ./*

echo "=================================================="
echo "   NGINX Workload Generator (Extreme Tails)       "
echo "=================================================="
echo "WARNING: This workload contains extreme outliers."
echo "Even 'Small' types will generate ~100MB files."
echo "--------------------------------------------------"
echo "1) Profile Photo (Mainly <20KB, Tail -> 100MB)"
echo "2) Photo         (Mainly <200KB, Tail -> 100MB)"
echo "3) HD Photo      (Mainly <1MB, Tail -> 100MB)"
echo "4) Video         (Mainly <10MB, Tail -> 500MB)"
echo "5) HD Video      (Mainly <50MB, Tail -> 500MB)"
echo "=================================================="
read -p "Enter choice [1-5]: " choice

if [[ ! "$choice" =~ ^[1-5]$ ]]; then
    echo "Invalid choice. Exiting."
    exit 1
fi

FILE_COUNT=100
echo "Generating $FILE_COUNT files..."

get_rand_kb() {
    shuf -i $1-$2 -n 1
}

for i in $(seq 1 $FILE_COUNT); do
    p=$((RANDOM % 100 + 1))
    
    case $choice in
        1) 
            # === Profile Photo ===
            TYPE_NAME="Profile Photo"
            if   [ $p -le 30 ]; then val=$(get_rand_kb 6 15); size_kb=$(echo "scale=1; $val/10" | bc)
            elif [ $p -le 80 ]; then val=$(get_rand_kb 15 50); size_kb=$(echo "scale=1; $val/10" | bc)
            elif [ $p -le 95 ]; then val=$(get_rand_kb 50 200); size_kb=$(echo "scale=1; $val/10" | bc)
            elif [ $p -le 98 ]; then size_kb=$(get_rand_kb 200 5000) # 5MB intermediate
            else                     size_kb=$(get_rand_kb 10000 100000) # EXTREME TAIL: 10MB-100MB
            fi
            ;;
            
        2) 
            # === Photo ===
            TYPE_NAME="Photo"
            if   [ $p -le 20 ]; then size_kb=$(get_rand_kb 2 15)
            elif [ $p -le 60 ]; then size_kb=$(get_rand_kb 15 60)
            elif [ $p -le 90 ]; then size_kb=$(get_rand_kb 60 200)
            elif [ $p -le 98 ]; then size_kb=$(get_rand_kb 200 5000)
            else                     size_kb=$(get_rand_kb 10000 100000) # EXTREME TAIL: 10MB-100MB
            fi
            ;;
            
        3) 
            # === HD Photo ===
            TYPE_NAME="HD Photo"
            if   [ $p -le 20 ]; then size_kb=$(get_rand_kb 10 50)
            elif [ $p -le 70 ]; then size_kb=$(get_rand_kb 50 200)
            elif [ $p -le 90 ]; then size_kb=$(get_rand_kb 200 1500)
            elif [ $p -le 98 ]; then size_kb=$(get_rand_kb 1500 8000)
            else                     size_kb=$(get_rand_kb 10000 100000) # EXTREME TAIL: 10MB-100MB
            fi
            ;;
            
        4) 
            # === Video ===
            # Tail adjusted to match HD Video (up to 500MB)
            TYPE_NAME="Video"
            if   [ $p -le 20 ]; then size_kb=$(get_rand_kb 20 200)
            elif [ $p -le 60 ]; then size_kb=$(get_rand_kb 200 1200)
            elif [ $p -le 90 ]; then size_kb=$(get_rand_kb 1200 8000)
            elif [ $p -le 98 ]; then size_kb=$(get_rand_kb 8000 50000)
            else                     size_kb=$(get_rand_kb 50000 500000) # MATCHED HD VIDEO: 50MB-500MB
            fi
            ;;
            
        5) 
            # === HD Video ===
            TYPE_NAME="HD Video"
            if   [ $p -le 5 ];  then size_kb=$(get_rand_kb 100 500)
            elif [ $p -le 20 ]; then size_kb=$(get_rand_kb 500 2000)
            elif [ $p -le 50 ]; then size_kb=$(get_rand_kb 2000 6000)
            elif [ $p -le 80 ]; then size_kb=$(get_rand_kb 6000 12000)
            elif [ $p -le 95 ]; then size_kb=$(get_rand_kb 12000 80000)
            elif [ $p -le 98 ]; then size_kb=$(get_rand_kb 80000 200000)
            else                     size_kb=$(get_rand_kb 200000 500000) # 200MB - 500MB
            fi
            ;;
    esac

    # 计算与写入
    size_bytes=$(echo "$size_kb * 1024" | bc | cut -d'.' -f1)
    
    if [ $(echo "$size_kb < 1024" | bc) -eq 1 ]; then
        bs_arg="1K"
        dd if=/dev/urandom of="file_${i}.bin" bs=1 count=$size_bytes status=none
        display="$size_kb KB"
    else
        bs_arg="1M"
        count_arg=$(echo "$size_kb / 1024" | bc)
        if [ "$count_arg" -eq 0 ]; then count_arg=1; fi
        dd if=/dev/urandom of="file_${i}.bin" bs=$bs_arg count=$count_arg status=none
        display="$count_arg MB"
    fi

    # 简单高亮显示大文件
    if [ $(echo "$size_kb > 50000" | bc) -eq 1 ]; then
        echo -ne "[File $i/$FILE_COUNT] $TYPE_NAME | Size: \033[1;31m$display\033[0m (Heavy Tail!) ... \n"
    else
        echo -ne "[File $i/$FILE_COUNT] $TYPE_NAME | Size: $display ... \r"
    fi
done

echo -e "\n\nGeneration Complete."
echo "--- Largest 5 Files (Checking heavy tails) ---"
ls -lhS file_*.bin | head -n 5