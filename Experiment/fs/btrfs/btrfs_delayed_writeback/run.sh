# Follow the setup and triggering instructions in the `btrfs_max_bio_sectors` README.md

git clone https://github.com/josefbacik/fs_mark.git
cd fs_mark && make

# when removing files, kernel path will be triggered too
# -n means the number of files you create, it can be greater 
./fs_mark -d /mnt/btrfs/fm -D 32 -s 1024 -n 20000 -t 32 -S 4


