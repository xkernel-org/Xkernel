#!/bin/bash

op_delay=5
thread=10

# 小规模固定值
r_values=(100 1000 10000 50000)

# 大规模：100K 到 3M，步长 100K
for (( r=100000; r<=3000000; r+=100000 )); do
    r_values+=($r)
done

# 执行测试
for r in "${r_values[@]}"; do
    output_file="xk_${op_delay}_${r}.txt"
    echo "Running: ../bench -d ${op_delay} -j ${thread} -r $r -n $((r*5))"
    ../bench -d "${op_delay}" -j "${thread}" -r "$r" -n $((r*5)) > "$output_file" 2>&1
    echo "Output saved to $output_file"
done

echo "All done!"