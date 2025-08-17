# Override the variable in Makefile
export KERNELDIR=$HOME/linux-6.14.0-export-symbol

# Download Ubuntu Linux source
# Instead of "linux-source" package which seems a "moving target", lock the
# version via launchpad.
sudo apt-get update && sudo apt install git fakeroot build-essential ncurses-dev xz-utils libssl-dev bc flex libelf-dev bison rsync dwarves devscripts -y
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
chmod +x ./debian/scripts/sign-module
sudo make modules_install -j$(nproc)
sudo make install