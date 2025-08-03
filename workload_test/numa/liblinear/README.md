Wentao: this benchmark comes from https://github.com/ece-fast-lab/ASPLOS-2025-M5
as well but it is not perfect for our purpose, as (1) it seems to have multiple
stages and the preparation takes a few minutes doing thing I don't know before
multiple threads are spawned (2) the finish time with the same configuration
can be quite nondeterministic. So this is not actively used and we may or may
not revisit it later.

Setup

```shell
cd /tmp
wget https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/multicore-liblinear/liblinear-multicore-2.49.zip -O liblinear-multicore-2.49.zip
unzip liblinear-multicore-2.49.zip -d.
cd liblinear-multicore-2.49
make -j10
sudo cp train /usr/bin
cd /tmp
rm -r liblinear-multicore-2.49.zip liblinear-multicore-2.49
wget https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/kdd12.xz -O kdd12.xz
xz -d kdd12.xz
sudo mv kdd12 /opt/
```

```shell
/usr/bin/time -v train -s 6 -m 20 /opt/kdd12
```
