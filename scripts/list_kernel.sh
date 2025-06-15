#! /bin/bash

echo "--------------------------"
echo "Current kernel: "
echo `uname -r`

echo "--------------------------"
echo "Installed kernels: "
for f in /boot/config-* ;do echo ${f#*-};done