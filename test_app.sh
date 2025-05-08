#!/bin/bash
set -e

echo "[*] Creating a 10MB file for loopback device..."
dd if=/dev/zero of=./backing.img bs=1M count=10 status=none

echo "[*] Setting up loop device..."
LOOP_DEV=$(sudo losetup --show -f ./backing.img)

echo "[*] Creating a device-mapper linear device (dmsetup)..."
echo "0 20480 linear $LOOP_DEV 0" | sudo dmsetup create mydmtest

echo "[+] Device-mapper device created: /dev/mapper/mydmtest"
ls -l /dev/mapper/mydmtest

# Pause to allow inspection
read -p "[*] Press Enter to clean up..."

echo "[*] Cleaning up..."
sudo dmsetup remove mydmtest
sudo losetup -d "$LOOP_DEV"
rm -f ./backing.img

echo "[+] Done. Device and backing file cleaned up."