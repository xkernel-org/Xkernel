Setup

```
sudo apt -yq install libopenmpi-dev

cd /tmp/
git clone git@github.com:whentojump/graph500.git
cd graph500/src
make -j2
sudo cp graph500_reference_bfs graph500_reference_bfs_sssp /usr/bin/
```

Example run

```shell
/usr/bin/time -v mpirun -n 32 graph500_reference_bfs 26 |& tee log.txt
```
