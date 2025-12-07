The current steps probably rely specifically on Ubuntu 24.04's distribution
kernel config and GNU toolchains.

```shell
export WORK_DIR=$HOME

export KERNEL_BIN_ADDR=$WORK_DIR/linux-6.14.0-xkernel
export THIS_REPO_DIR=$WORK_DIR/Xkernel

reproducibility_issue() {
cat << EOF

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

$1

This may result in reproducibility issue and different addresses.

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

EOF
}

sudo apt update
sudo apt -yq install git fakeroot build-essential ncurses-dev xz-utils \
    libssl-dev bc flex libelf-dev bison rsync dwarves devscripts

git clone git@github.com:zhongjiechen/Xkernel.git --branch dataflow $THIS_REPO_DIR

TMPDIR=$(mktemp -d)
cd $TMPDIR
dget -u https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/linux/6.14.0-15.15/linux_6.14.0-15.15.dsc
mkdir -p $KERNEL_BIN_ADDR
rm -rf $KERNEL_BIN_ADDR
mv linux-6.14.0 $KERNEL_BIN_ADDR
cd $KERNEL_BIN_ADDR
rm -r $TMPDIR

# Build kernel
cp /boot/config-$(uname -r) .config
if ! diff .config $THIS_REPO_DIR/find-binary-addresses/config-6.8.0-71-generic >& /dev/null; then
    reproducibility_issue \
        "The base Ubuntu distro config is different from what's expected."
fi
make olddefconfig
# Disable Ubuntu-specific keys
scripts/config -d CONFIG_SYSTEM_TRUSTED_KEYS
scripts/config -d CONFIG_SYSTEM_REVOCATION_KEYS
# Give an identifiable name
scripts/config --set-str CONFIG_LOCALVERSION "-xkernel"
make olddefconfig
if ! diff .config $THIS_REPO_DIR/find-binary-addresses/config-6.14.0-xkernel >& /dev/null; then
    reproducibility_issue \
        "The Xkernel config is different from what's expected."
fi

# Some statistics
# 29:25.19 on c6320
# 28:01.91 on c6420
/usr/bin/time -v make -j$(nproc)

nm vmlinux > vmlinux.nm.txt
objdump -d vmlinux > vmlinux.disas.txt
NM1=vmlinux.nm.txt
NM2=$THIS_REPO_DIR/find-binary-addresses/xkernel.vmlinux.nm.txt
if ! diff \
          <(grep -v ' d ' $NM1 | grep -v ' r ' | grep -v ' D ' | grep -v ' R ') \
          <(grep -v ' d ' $NM2 | grep -v ' r ' | grep -v ' D ' | grep -v ' R ') \
          >& /dev/null; then
    reproducibility_issue \
        "The produced vmlinux has t/T symbols with different addresses."
fi

chmod +x ./debian/scripts/sign-module
make INSTALL_MOD_PATH=mods modules_install -j$(nproc)
```

```shell
cd $THIS_REPO_DIR
# c6420 43min25s
/usr/bin/time -v python extract_assembly_ranges.py --batch kernel-results --workers 24 |& tee find-binary-addresses/addr.all.log
```
