```shell
# Override the variable in Makefile
export KERNELDIR=$HOME/linux-6.14.0-export-symbol

# Download Ubuntu Linux source
# Instead of "linux-source" package which seems a "moving target", lock the
# version via launchpad.
sudo apt install git fakeroot build-essential ncurses-dev xz-utils libssl-dev bc flex libelf-dev bison rsync dwarves devscripts -y
TMPDIR=$(mktemp -d)
cd $TMPDIR
dget -u https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/linux/6.14.0-15.15/linux_6.14.0-15.15.dsc
mkdir -p $KERNELDIR
rm -rf $KERNELDIR
mv linux-6.14.0 $KERNELDIR
cd $KERNELDIR
rm -r $TMPDIR

# Patch kernel
patch -p1 << 'EOF'
diff --git a/arch/x86/kernel/alternative.c b/arch/x86/kernel/alternative.c
index c71b575..cf2236e 100644
--- a/arch/x86/kernel/alternative.c
+++ b/arch/x86/kernel/alternative.c
@@ -2016,6 +2016,7 @@ void *text_poke(void *addr, const void *opcode, size_t len)

 	return __text_poke(text_poke_memcpy, addr, opcode, len);
 }
+EXPORT_SYMBOL_GPL(text_poke);

 /**
  * text_poke_kgdb - Update instructions on a live kernel by kgdb
EOF

# Build kernel
cp /boot/config-$(uname -r) .config
make olddefconfig
# Disable Ubuntu-specific keys
scripts/config -d CONFIG_SYSTEM_TRUSTED_KEYS
scripts/config -d CONFIG_SYSTEM_REVOCATION_KEYS
# Give an identifiable name
scripts/config --set-str CONFIG_LOCALVERSION "-export-text-poke"
make olddefconfig
# Some statistics
# 29:25.19 on c6320
# 28:01.91 on c6420
/usr/bin/time -v make -j$(nproc)
```

> [!CAUTION]
> Proceed with caution.
> Back up your data.
> In the worst case where the system is broken, it may (or may not) help to
> connect to CloudLab console and navigate grub.

```shell
# FIXME: modules and initrd are massively larger than the distro for reasons
# I don't yet know
chmod +x ./debian/scripts/sign-module
sudo make modules_install -j$(nproc)
sudo make install
```

```shell
# Override the variable in Makefile
export KERNELDIR=$HOME/linux-6.14.0-export-symbol
cd <Xkernel>/kernel_module/
make RAW_TEXT_POKE=m
```

```shell
sudo reboot
```

Example of `ttwu_do_activate`

```shell
uname -r
# Expect: 6.14.0-export-text-poke

cd <Xkernel>
bash scripts/runtime-disas.sh ttwu_do_activate | less
# ...
# ffffffffb7e521d3:       48 0f 49 c2             cmovns %rdx,%rax
# ffffffffb7e521d7:       48 c1 f8 03             sar    $0x3,%rax <-- get this address
# ffffffffb7e521db:       48 01 f0                add    %rsi,%rax
# ...
TARGET_ADDR=ffffffffb7e521d7
NEW_INSN="0x48,0xc1,0xf8,0x02"
sudo insmod kernel_module/raw_text_poke.ko target_addr=0x$TARGET_ADDR new_insn=$NEW_INSN

sudo dmesg | tail
# Expect something like:
# [  502.546089] Patching 4 bytes at ffffffffb7e521d7
bash scripts/runtime-disas.sh ttwu_do_activate | grep -C2 ^$TARGET_ADDR:
# ffffffffb7e521cf:       48 8d 42 07             lea    0x7(%rdx),%rax
# ffffffffb7e521d3:       48 0f 49 c2             cmovns %rdx,%rax
# ffffffffb7e521d7:       48 c1 f8 02             sar    $0x2,%rax <-- Check if it gets effective
# ffffffffb7e521db:       48 01 f0                add    %rsi,%rax <-- Also ensure nothing is corrupted afterwards
# ffffffffb7e521de:       48 39 c1                cmp    %rax,%rcx

sudo rmmod raw_text_poke
sudo dmesg | tail
# Expect something like:
# [  729.144214] Restoring 4 bytes at ffffffffb7e521d7

bash scripts/runtime-disas.sh ttwu_do_activate | grep -C2 ^$TARGET_ADDR:
# ffffffffb7e521cf:       48 8d 42 07             lea    0x7(%rdx),%rax
# ffffffffb7e521d3:       48 0f 49 c2             cmovns %rdx,%rax
# ffffffffb7e521d7:       48 c1 f8 03             sar    $0x3,%rax <-- it should get back
# ffffffffb7e521db:       48 01 f0                add    %rsi,%rax
# ffffffffb7e521de:       48 39 c1                cmp    %rax,%rcx
```
