Setup

```shell
sudo apt install -yq gfortran

cd /tmp/
wget https://www.nas.nasa.gov/assets/npb/NPB3.4.3.tar.gz -O NPB3.4.3.tar.gz
tar zxvf NPB3.4.3.tar.gz
cd NPB3.4.3/NPB3.4-OMP
cp config/make.def.template config/make.def
# make BT CLASS=E -j$(nproc)
make CG CLASS=E -j1
# make FT CLASS=E -j$(nproc)
# make MG CLASS=E -j$(nproc)

sudo cp bin/cg.E.x /usr/bin
cd /tmp/
rm -rf NPB3.4.3 NPB3.4.3.tar.gz

# Example run
# CloudLab c6420: 2h13min peak 154GB
export OMP_NUM_THREADS=$(nproc)
/usr/bin/time -v cg.E.x |& tee log.txt
```
