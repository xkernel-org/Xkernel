#!/usr/bin/env bash
# Install and prepare the Linux 6.14.8 source tree used by Figure 10/11.
#
# Most AE experiments use Linux 6.8 and do not need this script. Figure 10 and
# Figure 11 use Linux 6.14.8-061408-generic; their README files provide the
# preferred artifact-evaluation steps, including installing the matching Ubuntu
# mainline kernel packages. This helper prepares the matching upstream source
# tree for Xkernel code generation; it does not build or install a full kernel.

set -euo pipefail

KERNEL_VERSION="6.14.8"
LOCALVERSION="-061408-generic"
if [[ -n "${SUDO_USER:-}" ]]; then
    TARGET_HOME="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
else
    TARGET_HOME="$HOME"
fi

KERNELDIR="${KERNELDIR:-$TARGET_HOME/linux-${KERNEL_VERSION}${LOCALVERSION}}"
TARBALL="linux-${KERNEL_VERSION}.tar.xz"
URL="https://cdn.kernel.org/pub/linux/kernel/v6.x/${TARBALL}"

sudo apt-get update
sudo apt-get install -y \
    build-essential bc bison dwarves elfutils flex libdw-dev libelf-dev libssl-dev \
    ncurses-dev rsync xz-utils

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

cd "$TMPDIR"
wget "$URL"
tar -xf "$TARBALL"

rm -rf "$KERNELDIR"
mv "linux-${KERNEL_VERSION}" "$KERNELDIR"
cd "$KERNELDIR"

cp "/boot/config-$(uname -r)" .config
scripts/config -d CONFIG_SYSTEM_TRUSTED_KEYS
scripts/config -d CONFIG_SYSTEM_REVOCATION_KEYS
scripts/config --set-str CONFIG_LOCALVERSION "$LOCALVERSION"
make olddefconfig
make prepare scripts

# Optional quick sanity check for the Figure 10/11 target files.
make -j"$(nproc)" mm/shrinker.o mm/migrate.o

if [[ -n "${SUDO_USER:-}" ]]; then
    sudo chown -R "$SUDO_USER:$SUDO_USER" "$KERNELDIR"
fi

echo "Linux source tree installed at: $KERNELDIR"
echo "Use: export KERNEL_DIR=$KERNELDIR"
