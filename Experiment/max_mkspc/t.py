import os, sys, errno
p="/mnt/ubifs"; os.chdir(p)
BATCH=128
fds=[]
try:
    for i in range(1, 5000):
        f = open(f"s{i}", "wb", buffering=0)
        f.write(os.urandom(8192))
        f.flush()
        fds.append(f)
        if len(fds) >= BATCH:
            # 批量 fsync，减少单次最坏时延
            for g in fds:
                try: os.fsync(g.fileno())
                except OSError as e:
                    if e.errno in (errno.ENOSPC, errno.EIO): raise
            for g in fds: g.close()
            fds.clear()
except KeyboardInterrupt:
    pass
finally:
    for g in fds:
        try: os.fsync(g.fileno())
        except OSError: pass
        g.close()
