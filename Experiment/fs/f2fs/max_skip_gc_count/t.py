import os,random

# Follow the setup and triggering instructions in the `max_vmap_entries` README.md

p="/mnt/f2fs-test/small"; os.makedirs(p,exist_ok=True)
bs=4096
for i in range(50000):
    with open(f"{p}/f{i}", "wb", buffering=0) as f:
        f.write(b'\0'*bs)   