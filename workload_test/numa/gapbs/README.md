Setup

```shell
cd /tmp/
git clone https://github.com/sbeamer/gapbs.git
cd gapbs
make -j10
sudo cp pr bfs /usr/bin/
cd /tmp/
rm -rf gapbs

# Example run
# CloudLab c6420: 22min peak 297GB
/usr/bin/time -v pr -u 30 -n 10 |& tee log.txt
```
