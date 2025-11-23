- Download `liburing` and compile:

```bash
$ git clone https://github.com/axboe/liburing.git
$ cd liburing
$ ./configure
$ make -j
$ cd examples
$ make proxy
```

- In terminal 1:

```bash
$ cd examples
$ ./proxy -m0 -c1 -s1 -x1 -V -b64
```

- In terminal 2:

```bash
$ dd if=/dev/zero bs=1K count=1024 2>/dev/null | nc -N 127.0.0.1 4444

# or:
# while true; do
#   dd if=/dev/zero bs=1K count=1024 2>/dev/null | nc -N 127.0.0.1 4444
# done
```
