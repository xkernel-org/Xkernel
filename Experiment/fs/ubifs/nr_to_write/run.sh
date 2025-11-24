# Follow the setup and triggering instructions in the `hard_lebs` README.md

sudo dd if=/dev/zero of=/mnt/ubi/fill bs=1M \
    count=85 conv=fsync status=progress