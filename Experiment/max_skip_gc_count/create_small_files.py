import os,random

p="/mnt/f2/small"; os.makedirs(p,exist_ok=True)
bs=4096
for i in range(50000):
    with open(f"{p}/f{i}", "wb", buffering=0) as f:
        f.write(b'\0'*bs)    # 先写 4K