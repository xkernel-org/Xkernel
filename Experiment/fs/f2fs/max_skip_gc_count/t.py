import os,random

# Before starting, follow the README.md of `max_vmap_retries`

p="/mnt/f2fs-test/small"; os.makedirs(p,exist_ok=True)
bs=4096
for i in range(50000):
    with open(f"{p}/f{i}", "wb", buffering=0) as f:
        f.write(b'\0'*bs)   