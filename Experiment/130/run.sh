sudo systemd-run --scope \
  -p MemoryHigh=256M \
  -p MemoryMax=320M \
  ./t 4 256 128
# 参数：文件数=4，初始每文件=256MB，每轮增长=128MB
