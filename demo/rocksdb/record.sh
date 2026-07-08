#!/usr/bin/env bash
# Regenerate the DiskANN race GIF from results.json.
# The cast is synthesized deterministically by render_race.py (no live
# recording needed); agg turns it into a GIF.

set -euo pipefail
cd "$(dirname "$0")"

AGG="${AGG:-$HOME/.cargo/bin/agg}"
command -v "$AGG" >/dev/null || AGG=agg

python3 render_race.py --out xkernel-rocksdb.cast

"$AGG" \
  --font-size 16 \
  --fps-cap 15 \
  --last-frame-duration 3 \
  --line-height 1.25 \
  --font-family "DejaVu Sans Mono,Ubuntu Mono,Liberation Mono,Noto Sans Mono" \
  --theme 16181d,e2e5ea,272b33,e05f65,6bc46d,f5a623,539bf5,b083f0,39c5cf,c8ccd4,9aa1ad,e6767c,7fd28a,f7b955,6fb0f7,c49bf5,5cd4de,eceff3 \
  xkernel-rocksdb.cast xkernel-rocksdb.gif

ls -lh xkernel-rocksdb.gif
