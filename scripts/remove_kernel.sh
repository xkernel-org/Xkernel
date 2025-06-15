#! /bin/bash

if [ $# -eq 1 ];
then
	kernel_version=$1
	echo 'Start removing linux kernel:'${kernel_version}
	rm /boot/{config-,initrd.img-,System.map-,vmlinuz-}${kernel_version}
	rm -rf /lib/modules/${kernel_version}
	sudo update-grub
else
	echo "Use list_kernel.sh to list the installed kernels and specify the kernel version.
	e.g. sudo ./remove_kernel.sh 6.8.0"
fi