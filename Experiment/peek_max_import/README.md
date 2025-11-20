git clone https://github.com/axboe/liburing.git
cd liburing
./configure
make -j


cd examples
make proxy


# in terminal 1:
cd examples

./proxy -m0 -c1 -s1 -x1 -V -b64


# in terminal 2:
dd if=/dev/zero bs=1K count=1024 2>/dev/null | nc -N 127.0.0.1 4444

or:
while true; do
  dd if=/dev/zero bs=1K count=1024 2>/dev/null | nc -N 127.0.0.1 4444
done
