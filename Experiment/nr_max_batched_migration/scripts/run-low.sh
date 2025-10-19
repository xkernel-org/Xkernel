sudo ../bin/benchmark \
  --pages 2097152 --workers 24 --migrates 2 \
  --src 1 --dst 0 --batch 2048 --migrate-interval 50 \
  --hot-frac 0.125 --hot-prob 1 --hot-rotate 0 \
  --drain-per-window 3 --only-src \
  --qps-sample-ms 10 --probe 2000 50 \
  --duration 30