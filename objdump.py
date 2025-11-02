#!/usr/bin/env python3
import argparse, os, re, subprocess, sys, shutil

SYMS_PATHS = ["/proc/kallmodsyms", "/proc/kallsyms"]  # kallmodsyms 更可靠
LINE_RE = re.compile(r"^([0-9a-fA-F]{1,16})\s+([A-Za-z])\s+(\S+?)(?:\s+\[([^\]]+)\])?$")

def read_kallsyms():
    path = next((p for p in SYMS_PATHS if os.path.exists(p)), SYMS_PATHS[-1])
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            m = LINE_RE.match(ln.strip())
            if not m: 
                continue
            addr_hex, typ, name, mod = m.groups()
            try:
                addr = int(addr_hex, 16)
            except ValueError:
                addr = 0
            rows.append((addr, typ, name, mod))  # (addr, type, name, module)
    return rows, path

def visible_addrs(rows):
    # 若全部地址是 0，通常是 kptr_restrict 在隐藏地址
    return any(addr != 0 for addr,_,_,_ in rows)

def is_text_sym(row):
    return row[1] in ("t","T")

def skip_weird(name):
    # __pfx_* / __cfi_* 常见“前缀/校验”符号；也可按需添加 .cold 处理
    return name.startswith("__pfx_") or name.startswith("__cfi_")

def find_symbol(rows, name, module=None):
    # 多个同名：优先匹配同一模块；其次任意模块的 text 符号
    candidates = [r for r in rows if r[2]==name and is_text_sym(r) and not skip_weird(r[2])]
    if module:
        mod_cands = [r for r in candidates if r[3]==module]
        if mod_cands:
            return mod_cands[0], rows.index(mod_cands[0])
    return (candidates[0], rows.index(candidates[0])) if candidates else (None, -1)

def next_text_in_same_module(rows, start_idx):
    _,_,_,mod = rows[start_idx]
    for j in range(start_idx+1, len(rows)):
        addr,typ,name,mj = rows[j]
        if mj != mod:
            # 不同模块的符号，跳过
            continue
        if is_text_sym(rows[j]) and not skip_weird(name) and addr != 0:
            return rows[j]
    return None

def objdump_range(start, stop):
    if shutil.which("objdump") is None:
        sys.exit("error: objdump not found in PATH")
    # 注意：/proc/kcore 需要 root；--start/--stop 接收“运行时虚拟地址”
    cmd = ["sudo","objdump","-d",f"--start-address={start}",f"--stop-address={stop}","/proc/kcore"]
    env = dict(os.environ); env["LANG"]="C"
    out = subprocess.check_output(cmd, env=env).decode("utf-8","ignore")
    return out

def calc_offset(start_address, disas):
    out_lines = []
    for ln in disas.splitlines():
        s = ln.strip().strip(":")
        if not s or s.startswith("/proc/kcore") or s.startswith("Disassembly"):
            continue
        # 形如：ffffffffb239dd29:  48 81 fe 10 27 00 00    cmp ...
        addr = s.split(":",1)[0].split()[0]
        try:
            a = int(addr, 16)
        except ValueError:
            continue
        off = a - start_address
        out_lines.append(f"(+0x{off:x}){ln}")
    return "\n".join(out_lines)

def main():
    ap = argparse.ArgumentParser(description="Disassemble a kernel function via /proc/kcore")
    ap.add_argument("--func", type=str, default="blk_mq_delay_run_hw_queue", help="symbol name")
    ap.add_argument("--module", type=str, help="module name (e.g., xfs)")
    ap.add_argument("--fallback-bytes", type=lambda x:int(x,0), default=0x2000,
                    help="fallback stop size when next symbol not found (default 0x2000)")
    args = ap.parse_args()

    rows, path = read_kallsyms()
    if not visible_addrs(rows):
        print("ERROR: all addresses are 0. Run as root and set `sysctl kernel.kptr_restrict=0`.", file=sys.stderr)
        print("       Also check `kernel.perf_event_paranoid` if needed.", file=sys.stderr)
        sys.exit(1)

    sym, idx = find_symbol(rows, args.func, args.module)
    if not sym:
        sys.exit(f"error: symbol `{args.func}` not found in {path}")

    start_addr,_,name,mod = sym
    nxt = next_text_in_same_module(rows, idx)
    if nxt:
        stop_addr = nxt[0]
    else:
        stop_addr = start_addr + args.fallback_bytes

    print(f"Symbol  : {name}  [{mod or 'vmlinux'}]")
    print(f"Start   : 0x{start_addr:x}")
    print(f"Stop    : 0x{stop_addr:x}  (source: {'next text sym in same module' if nxt else 'fallback'})")
    print(f"Syms    : {path}")

    dis = objdump_range(start_addr, stop_addr)
    print(calc_offset(start_addr, dis))

if __name__ == "__main__":
    main()