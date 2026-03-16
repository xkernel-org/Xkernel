> [!NOTE]
>
> This README assumes analysis is run as part of Xkernel, namely, Linux kernel
> source code has been downloaded and built with GCC following the instructions
> in project root [README](../README.md).
>
> To only run this analysis individually, follow the instructions in
> https://github.com/xkernel-org/linux-analysis.

```shell
# FIXME change to GitHub link once publicized
# 3 min on c6420
wget 'https://mir.cs.illinois.edu/~wentaoz5/ss-public/scripts/setup.sh' -O- | bash
```

As prompted, log out the current shell and log back in again.

Build Linux kernel again for whole-program analysis with
[wllvm](https://github.com/travitch/whole-program-llvm).

```shell
# 9 min on c6420
export DEV_MODE=1 # FIXME remove this eventually
/usr/bin/time -v bash $WORKDIR/linux-analysis/scripts/build-with-wllvm.sh
```

Run individual SS analysis:

```shell
bash $WORKDIR/linux-analysis/scripts/ss-analysis.sh \
    $WORKDIR/linux-analysis/dataset/AIO_PLUG_THRESHOLD/1.input.txt
```
