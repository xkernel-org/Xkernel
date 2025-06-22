# The following steps show how to upgrade cloudlab machines from 24.04 to 25.04

# Fix emulab bug on linux 6.11
sudo sed -i 's/static int ipod_wq_proc(struct ctl_table \*table, int write,/static int ipod_wq_proc(const struct ctl_table \*table, int write,/' /var/lib/dkms/emulab-ipod-dkms/3.4.0/source/ipod.c

# Upgrade to 24.10 from 24.04
sudo sed -i 's/^Prompt=lts$/Prompt=normal/' /etc/update-manager/release-upgrades && sudo sed -i 's/noble/oracular/g' /etc/apt/sources.list.d/ubuntu.sources && sudo apt update && sudo apt dist-upgrade -y

sudo reboot

# Upgrade to 25.04 from 24.10
sudo sed -i 's/oracular/plucky/g' /etc/apt/sources.list.d/ubuntu.sources && sudo apt update && sudo apt dist-upgrade -y

sudo reboot