#!/usr/bin/env python3
import argparse, os, re, subprocess, sys, shutil

SYMS_PATHS = ["/proc/kallmodsyms", "/proc/kallsyms"]  # kallmodsyms 更可靠
LINE_RE = re.compile(r"^([0-9a-fA-F]{1,16})\s+([A-Za-z])\s+(\S+?)(?:\s+\[([^\]]+)\])?$")

def read_kallsyms():
    """从 kallsyms 或 kallmodsyms 读取所有符号。"""
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
    """检查 kptr_restrict 是否隐藏了地址。"""
    # 若全部地址是 0，通常是 kptr_restrict 在隐藏地址
    return any(addr != 0 for addr,_,_,_ in rows)

def is_text_sym(row):
    """检查是否为代码符号 (t/T)。"""
    return row[1] in ("t","T")

def skip_weird(name):
    """跳过特殊前缀的符号。"""
    # __pfx_* / __cfi_* 常见“前缀/校验”符号；也可按需添加 .cold 处理
    return name.startswith("__pfx_") or name.startswith("__cfi_")

def find_symbol(rows, name, module=None):
    """
    (已修正) 查找符号，返回地址最小的匹配项。
    不再依赖文件顺序。
    """
    candidates = [r for r in rows if r[2]==name and is_text_sym(r) and not skip_weird(r[2])]
    if not candidates:
        return None
    
    if module:
        mod_cands = [r for r in candidates if r[3]==module]
        if mod_cands:
            # 返回同一模块中，地址最小的符号
            return min(mod_cands, key=lambda r: r[0]) 

    # 降级：返回所有候选中地址最小的
    return min(candidates, key=lambda r: r[0])

def next_text_in_same_module(rows, start_addr, module):
    """
    (已修正) 查找下一个符号。
    全局搜索地址 > start_addr 且同模块的符号，并返回地址最小的那个。
    """
    candidates = []
    for (addr, typ, name, mod) in rows:
        # 寻找：1. 同一模块 2. 是代码符号 3. 非特殊符号 4. 地址 > 起始地址
        if (mod == module and 
            is_text_sym((addr, typ, name, mod)) and 
            not skip_weird(name) and 
            addr > start_addr):
            candidates.append((addr, typ, name, mod))
    
    # 返回这些候选中，地址最小的那个
    if candidates:
        return min(candidates, key=lambda r: r[0])
    
    return None # 没找到

def objdump_range(start, stop):
    """调用 objdump 反汇编 /proc/kcore 中的地址范围。"""
    if shutil.which("objdump") is None:
        sys.exit("error: objdump not found in PATH")
    # 注意：/proc/kcore 需要 root；--start/--stop 接收“运行时虚拟地址”
    cmd = ["sudo","objdump","-d",f"--start-address={start}",f"--stop-address={stop}","/proc/kcore"]
    env = dict(os.environ); env["LANG"]="C"
    out = subprocess.check_output(cmd, env=env).decode("utf-8","ignore")
    return out

def calc_offset(start_address, disas):
    """为反汇编输出添加 (+0x...) 偏移量。"""
    out_lines = []
    for ln in disas.splitlines():
        s = ln.strip().strip(":")
        if not s or s.startswith("/proc/kcore") or s.startswith("Disassembly"):
            continue
        # 形如：ffffffffb239dd29:   48 81 fe 10 27 00 00     cmp ...
        addr_match = re.match(r"^([0-9a-fA-F]+)", s)
        if not addr_match:
            continue
            
        addr = addr_match.group(1)
        try:
            a = int(addr, 16)
        except ValueError:
            continue
        
        # 只显示在范围内的地址
        if a >= start_address:
            off = a - start_address
            out_lines.append(f"(+0x{off:x}){ln}")
    return "\n".join(out_lines)

def main():
    ap = argparse.ArgumentParser(description="Disassemble a kernel function via /proc/kcore")
    ap.add_argument("--func", type=str, required=True, help="symbol name (e.g., xfs_iwalk_threaded)")
    ap.add_argument("--module", type=str, help="module name (e.g., xfs)")
    ap.add_argument("--fallback-bytes", type=lambda x:int(x,0), default=0x2000,
                     help="fallback stop size when next symbol not found (default 0x2000)")
    args = ap.parse_args()

    rows, path = read_kallsyms()
    if not visible_addrs(rows):
        print("ERROR: all addresses are 0. Run as root and set `sysctl kernel.kptr_restrict=0`.", file=sys.stderr)
        print("       Also check `kernel.perf_event_paranoid` if needed.", file=sys.stderr)
        sys.exit(1)

    # (变更) find_symbol 不再返回 idx
    sym = find_symbol(rows, args.func, args.module)
    if not sym:
        sys.exit(f"error: symbol `{args.func}`{' in module ' + args.module if args.module else ''} not found in {path}")

    start_addr,_,name,mod = sym
    
    # (变更) 调用新函数，传入 start_addr 和 mod
    nxt = next_text_in_same_module(rows, start_addr, mod)
    
    source = "unknown"
    if nxt:
        stop_addr = nxt[0]
        source = "next text sym in same module"
    else:
        stop_addr = start_addr + args.fallback_bytes
        source = "fallback"

    print(f"Symbol  : {name}  [{mod or 'vmlinux'}]")
    print(f"Start   : 0x{start_addr:x}")
    print(f"Stop    : 0x{stop_addr:x}  (source: {source})")
    print(f"Syms    : {path}")

    # (新增) 安全检查，防止 objdump 崩溃
    if stop_addr <= start_addr:
        print(f"WARNING: Stop address (0x{stop_addr:x}) is not after start address (0x{start_addr:x}).", file=sys.stderr)
        print(f"         Using fallback size (0x{args.fallback_bytes:x}) instead.", file=sys.stderr)
        stop_addr = start_addr + args.fallback_bytes
        print(f"New Stop: 0x{stop_addr:x}  (source: forced fallback)")

    try:
        dis = objdump_range(start_addr, stop_addr)
        print("\n--- Disassembly ---")
        print(calc_offset(start_addr, dis))
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: objdump failed with exit code {e.returncode}", file=sys.stderr)
        print(f"Command: {' '.join(e.cmd)}", file=sys.stderr)
        print("Output:", file=sys.stderr)
        print(e.output.decode('utf-8', 'ignore'), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()