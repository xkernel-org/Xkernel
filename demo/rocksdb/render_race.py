#!/usr/bin/env python3
"""Render the Xkernel RocksDB demo as an asciinema v2 cast.

Act I  — a macro sealed in the Ubuntu kernel image gets retuned to 1 live.
         Every command and output line is real, taken from recordings/
         (produced by capture_real.sh), trimmed for height, never reworded.
Act II — Vanilla vs Xkernel-tuned run the same RocksDB db_bench
         multireadrandom benchmark in parallel. Both sides replay the real,
         separately-measured paper Figure 1(b) runs shipped in
         ae/Figure1/results/nvme_{32,1}.txt, time-compressed; each side's
         counters advance at its real measured rate.

The cast is synthesized deterministically — no live recording.

Usage:
  python3 render_race.py --out xkernel-rocksdb.cast [--until SECONDS]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

W, H = 108, 30          # canvas
LEFTW = 68              # Act I left column width

# kernel box geometry (Act I, right side)
KB_COL = 71             # left border column
KB_W = 36               # total box width (borders included)
KB_IN = KB_W - 2        # inner width

# Act II pane geometry (50-col panes, 8-col gutter for the logo)
PANE = 50
LCOL, RCOL = 1, 59
BAR = 20
RACE_S = 4.0            # the 30 s benchmark plays back in this many seconds
SPEED = 1.0             # global timeline scale (Act I at natural pace)

DIM = "\x1b[90m"
AMB = "\x1b[33m"
GRN = "\x1b[32m"
BLD = "\x1b[1m"
HL = "\x1b[30;43m"      # reverse-video amber (editor-highlight)
RST = "\x1b[0m"

LOGO = [                # ASCII rendition of docs/xkernel-logo.png ("XK")
    r"XX\      /XX      /KK",
    r" XXX\  /XXX      /KK",
    r"   XXXXXXX      /KK",
    r"   XXXXXXX     /KK\KK",
    r" XXX/  \XXX   /KK  \KK",
    r"XX/      \XX /KK    \KK",
]
LOGO_W = max(len(l) for l in LOGO)

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def vlen(s: str) -> int:
    return len(ANSI.sub("", s))


def at(row: int, col: int, s: str) -> str:
    return f"\x1b[{row};{col}H{s}"


def clear_rows(rows: range, col: int = 1, width: int = KB_COL - 1) -> str:
    return "".join(at(r, col, " " * width) for r in rows)


# ---------------------------------------------------------------- kernel box
TEXTURE_A = "┈01001┈10110┈01011┈11001┈00110┈┈┈"
TEXTURE_B = "┈11010┈00101┈10011┈01101┈10100┈┈┈"


def kb_line(row: int, content: str) -> str:
    pad = " " * (KB_IN - 1 - vlen(content))
    return at(row, KB_COL, f"║ {content}{pad}║")


def kernel_box(value: int, sub: str, dot: bool | None, flash: bool = False) -> str:
    """Draw the kernel box. dot: None=absent, True/False=dot on/off row.
    flash: render the constant line in reverse-video (blink frame)."""
    val_text = f"#define BLK_MAX_REQUEST_COUNT {value}"
    if flash:
        val_line = f"{HL}{val_text}{RST}"
    elif value != 32:
        val_line = f"{AMB}{val_text}{RST}"
    else:
        val_line = val_text
    dot_line = ""
    if dot is not None:
        mark = f"{AMB}●{RST}" if dot else " "
        dot_line = f"{mark} tunable"
    s = at(1, KB_COL, "╔" + "═" * (KB_W - 2) + "╗")
    s += kb_line(2, "Ubuntu 24.04 image")
    s += kb_line(3, f"{DIM}Linux 6.8 kernel · vmlinuz{RST}")
    s += kb_line(4, f"{DIM}{TEXTURE_A}{RST}")
    s += kb_line(5, "")
    s += kb_line(6, "")
    s += kb_line(7, val_line)
    s += kb_line(8, f"{DIM}{sub}{RST}")
    s += kb_line(9, dot_line)
    s += kb_line(10, f"{DIM}{TEXTURE_B}{RST}")
    s += at(11, KB_COL, "╚" + "═" * (KB_W - 2) + "╝")
    return s


def arrow_to_box(row: int, text: str) -> str:
    """Draw text then an amber arrow reaching the box's left border."""
    start = vlen(text) + 2
    dashes = KB_COL - 1 - start - 1
    return at(row, 1, f"{text} {AMB}{'━' * dashes}▶{RST}")


# ---------------------------------------------------------------- Act II bits
def pane_box(lines: list[str]) -> list[str]:
    out = ["╭" + "─" * (PANE - 2) + "╮"]
    for line in lines:
        pad = " " * (PANE - 4 - vlen(line))
        out.append(f"│ {line}{pad} │")
    out.append("╰" + "─" * (PANE - 2) + "╯")
    return out


def bar(fraction: float, color: str) -> str:
    eighths = " ▏▎▍▌▋▊▉"
    cells = min(fraction, 1.0) * BAR
    full = int(cells)
    body = "█" * full
    if full < BAR:
        body += eighths[int((cells - full) * 8)].strip() or ""
    fill = color + body + RST
    return fill + DIM + "░" * (BAR - vlen(body)) + RST


def center(row: int, s: str) -> str:
    return at(row, (W - vlen(s)) // 2 + 1, s)


# ---------------------------------------------------------------- timeline
def build_events(r: dict) -> list[tuple[float, str]]:
    base, tuned, wl = r["baseline"], r["tuned"], r["workload"]

    ev: list[tuple[float, str]] = []

    # ===== Scene 1 — the macro sealed in the Ubuntu image (0–3.4 s) =====
    ev.append((0.0, "\x1b[?25l\x1b[2J" + kernel_box(32, "(fixed at compile time)", None)))
    ev.append((0.9, at(2, 1, f"{DIM}── tunables/blk_max_request_count.toml ────────────{RST}")))
    toml = [
        '  kernel_dir = "~/linux-6.8.0"',
        '  name = "BLK_MAX_REQUEST_COUNT"',
        "  [source]",
        '  file = "block/blk-mq.c"',
    ]
    ev.append((1.3, "".join(at(3 + i, 1, line) for i, line in enumerate(toml))))
    ev.append((2.0, arrow_to_box(7, f'  {AMB}original = "BLK_MAX_REQUEST_COUNT"{RST}')))

    # ===== Scene 2 — runtime, build, tunable (3.4–9.0 s) =====
    ev.append((3.4, at(13, 1, f"{DIM}${RST} {AMB}sudo insmod kernel/kfuncs/xk-kfuncs.ko{RST}")))
    ev.append((4.1, at(14, 1, f"{GRN}✓{RST} Xkernel runtime loaded")))
    ev.append((4.9, at(16, 1, f"{DIM}${RST} {AMB}./xkernel-tool build tunables/blk_max_request_count.toml{RST}")))
    build_out = [  # real lines from recordings/build.txt, trimmed
        "[1/1] BLK_MAX_REQUEST_COUNT (ConstID=1)",
        "✓ Linear relationship found: IV = -V + 4294967296",
        "Generated: bpf/stubs/xtune_stub_1.bpf.c",
        "Added Scope Table entry: ConstID=1, V=32, CS=[1]",
    ]
    for i, line in enumerate(build_out):
        ev.append((5.5 + 0.4 * i, at(17 + i, 1, f"  {line}")))
    ev.append((7.3, at(22, 1, f"{AMB}●{RST} BLK_MAX_REQUEST_COUNT is now tunable")
                  + kernel_box(32, "(fixed at compile time)", True)))
    ev.append((7.7, kernel_box(32, "(fixed at compile time)", False)))
    ev.append((8.1, kernel_box(32, "(fixed at compile time)", True)))

    # ===== Scene 3a — the X-tune program (9.0–12.3 s) =====
    ev.append((9.0, clear_rows(range(2, 23))
                  + at(2, 1, f"{DIM}${RST} vi bpf/stubs/xtune_stub_1.bpf.c")))
    prog = [  # real program from recordings/stub.c, trimmed
        (4, f'  X_TUNE_0(blk_add_rq_to_plug, "+0x118") {{'),
        (5, "      if (!x_transition_done(x_ctx)) return 0;"),
        (7, f"      {HL}u64 val = 1;{RST}  {AMB}◄── the new value{RST}"),
        (8, "      x_set(x_ctx, val);"),
        (9, "      return 0;"),
        (10, "  }"),
    ]
    ev.append((9.5, "".join(at(row, 1, line) for row, line in prog)))

    # ===== Scene 3b — load by ConstID, the constant flips (12.3–16.3 s) =====
    ev.append((12.3, clear_rows(range(2, 12))
                   + at(2, 1, f"{DIM}${RST} {AMB}sudo ./xkernel-tool load 0 1{RST}")))
    load_out = [  # real lines from recordings/load.txt, trimmed
        "Compiling BPF files...",
        "  Compiled: xtune_stub_1.bpf.c",
        "Loaded and attached: xtune_stub_1.bpf.o",
        "▶ kprobe/blk_add_rq_to_plug+0x118  (mode: Immediate)",
    ]
    for i, line in enumerate(load_out):
        ev.append((12.8 + 0.3 * i, at(3 + i, 1, f"  {line}")))
    flip_sub = "(was 32 — retuned live)"
    ev.append((14.3, arrow_to_box(7, f"{GRN}✓{RST} retuned live — no recompile, no reboot")
                   + kernel_box(1, flip_sub, True, flash=True)))
    ev.append((14.7, kernel_box(1, flip_sub, True)))
    ev.append((15.1, kernel_box(1, flip_sub, True, flash=True)))
    ev.append((15.5, kernel_box(1, flip_sub, True)))

    # ===== Scene 4 — banner, then the benchmark race (16.3 s → …) =====
    ev.append((16.3, at(13, 1, f"{DIM}{'━' * W}{RST}")
                   + center(14, f"{BLD}{AMB}▶   L E T ' S   R U N   I T !{RST}")
                   + at(15, 1, f"{DIM}{'━' * W}{RST}")))

    t0 = 17.8
    scaffold = "\x1b[2J"
    lbox = pane_box(["RocksDB db_bench · Vanilla",
                     "BLK_MAX_REQUEST_COUNT = 32"])
    rbox = pane_box([f"RocksDB db_bench · {AMB}Xkernel tuned{RST}",
                     f"BLK_MAX_REQUEST_COUNT = {AMB}1{RST}"])
    for i, (l, rr) in enumerate(zip(lbox, rbox)):
        scaffold += at(1 + i, LCOL, l) + at(1 + i, RCOL, rr)
    cmd = [  # the real invocation (taskset/duration flags omitted per review)
        f"{DIM}${RST} db_bench --benchmarks=multireadrandom \\",
        f"    --use_existing_db=true --num={wl['num_keys']} \\",
        f"    --batch_size={wl['batch_size']} --multiread_batched=true \\",
        "    --use_direct_reads=true --async_io=true",
    ]
    cfg = [
        f"  {DIM}dataset{RST}  {wl['key_size']} B keys · 2 KiB values · NVMe SSD",
        f"  {DIM}engine{RST}   io_uring MultiGet · Direct I/O",
    ]
    for col in (LCOL, RCOL):
        for i, line in enumerate(cmd):
            scaffold += at(6 + i, col, line)
        for i, line in enumerate(cfg):
            scaffold += at(11 + i, col, line)
    # XK logo watermark, centered in the right panel while the benchmark runs
    logo_col = RCOL + (PANE - LOGO_W) // 2
    for i, line in enumerate(LOGO):
        scaffold += at(18 + i, logo_col, f"{AMB}{line}{RST}")
    ev.append((t0, scaffold))

    scale = tuned["ops_total"]          # bar scale: tuned side fills 100%
    duration = wl["duration_s"]
    compress = duration / RACE_S

    def progress(col: int, ops: int, elapsed: float, rate: int, mbs: float, color: str) -> str:
        line1 = f"reading  {bar(ops / scale, color)} {ops:>9,d} ops"
        line2 = f"{DIM}         t = {elapsed:4.1f} s · {rate:,} ops/sec · {mbs} MB/s{RST}"
        return at(14, col, line1) + at(15, col, line2)

    race0 = t0 + 0.6
    ticks = int(RACE_S * 10)
    for k in range(ticks + 1):
        elapsed = (k / 10) * compress
        b_ops = min(int(elapsed * base["ops_per_sec"]), base["ops_total"])
        t_ops = min(int(elapsed * tuned["ops_per_sec"]), tuned["ops_total"])
        if k == ticks:
            b_ops, t_ops = base["ops_total"], tuned["ops_total"]
        ev.append((race0 + k / 10,
                   progress(LCOL, b_ops, elapsed, base["ops_per_sec"], base["mb_per_sec"], "")
                   + progress(RCOL, t_ops, elapsed, tuned["ops_per_sec"], tuned["mb_per_sec"], AMB)))
    t_done = race0 + RACE_S

    # both sides finish together (fixed 30 s) — tuned did 1.18x the work
    sp = r["speedup"]
    done = clear_rows(range(18, 24), logo_col, LOGO_W)  # watermark makes way
    done += at(17, LCOL, f"{GRN}✓{RST} done — {base['ops_total']:,} ops in {duration} s")
    done += at(17, RCOL, f"{GRN}✓{RST} done — {AMB}{tuned['ops_total']:,}{RST} ops in {duration} s")
    for col, side, c in ((LCOL, base, ""), (RCOL, tuned, AMB)):
        rs = RST if c else ""
        done += at(19, col, f"  {DIM}ops/sec{RST}   {c}{side['ops_per_sec']:,}{rs}")
        done += at(20, col, f"  {DIM}P50 lat{RST}   {c}{side['p50_us']:.0f} µs{rs}")
        done += at(21, col, f"  {DIM}P75 lat{RST}   {c}{side['p75_us']:.0f} µs{rs}")
    ev.append((t_done + 0.15, done))

    # ===== summary hold — XK logo anchors the closing frame =====
    t_sum = t_done + 0.9
    line1 = f"{BLD}Xkernel{RST} · runtime kernel tuning — no recompile, no reboot"
    line2 = (f"throughput {base['ops_per_sec'] / 1000:.1f}K → {AMB}{tuned['ops_per_sec'] / 1000:.1f}K ops/s ({sp['throughput']:.1f}×){RST}"
             f" · P50 lat {base['p50_us']:.0f} → {AMB}{tuned['p50_us']:.0f} µs ({sp['p50']:.2f}× lower){RST}")
    block = at(23, 1, DIM + "─" * W + RST)
    for i, line in enumerate(LOGO):
        block += at(24 + i, 4, f"{AMB}{line}{RST}")
    block += at(26, 30, line1) + at(28, 30, line2)
    ev.append((t_sum, block))
    ev.append((t_sum + 0.5, at(H, 1, "")))
    return ev


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "xkernel-rocksdb.cast")
    ap.add_argument("--until", type=float, default=None,
                    help="truncate the timeline (for still-frame previews)")
    args = ap.parse_args()

    results = json.loads((Path(__file__).parent / "results.json").read_text())
    events = sorted(build_events(results), key=lambda e: e[0])
    if args.until is not None:
        events = [(t, s) for t, s in events if t <= args.until]

    header = {"version": 2, "width": W, "height": H,
              "env": {"TERM": "xterm-256color", "SHELL": "/bin/bash"}}
    with args.out.open("w") as f:
        f.write(json.dumps(header) + "\n")
        for t, s in events:
            f.write(json.dumps([round(t * SPEED, 2), "o", s]) + "\n")
    print(f"wrote {args.out} ({len(events)} events, {events[-1][0] * SPEED:.1f}s timeline)")


if __name__ == "__main__":
    main()
