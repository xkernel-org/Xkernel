sudo ../bin/benchmark \
  --pages 2097152 --workers 24 --migrates {4, 2, 1} \
  --src 1 --dst 0 --batch 8192 --migrate-interval 0 \
  --hot-frac 0.20 --hot-prob 0.80 --hot-rotate 1 --rotate-step full \
  --drain-per-window 0 --only-src --restat \
  --qps-sample-ms 10 --probe 2000 50 \
  --duration 30
