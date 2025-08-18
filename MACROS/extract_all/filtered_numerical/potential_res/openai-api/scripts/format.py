#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import argparse
from pathlib import Path
import re

# 认定的子系统前缀（可自行增删）
SUBSYS = {
    "mm","block","fs","net","ipc","lib","init","kernel","drivers","sound",
    "crypto","security","virt","arch","tools","scripts","firmware",
    "Documentation","include"
}

# 解释字段以“1…”开头的宽松判断：1 / 1. / 1、 / 1． / 1␠
EXPLAIN_START = re.compile(r'^\s*1(?:[\.．、\s]|$)')

def process(input_csv: Path, output_txt: Path, encoding: str = "utf-8-sig"):
    # 用 csv.reader 处理“引号里的换行”
    with input_csv.open("r", encoding=encoding, newline="") as fin, \
         output_txt.open("w", encoding="utf-8", newline="") as fout:

        reader = csv.reader(fin)
        writer = csv.writer(fout, lineterminator="\n")

        for row in reader:
            if not row:
                writer.writerow(row)
                continue

            first = (row[0] or "").strip()
            # 解释字段：取最后一列（你的表头也是 Explanation 在最后）
            explain = row[-1] if len(row) >= 1 else ""

            if (first in SUBSYS) and isinstance(explain, str) and EXPLAIN_START.match(explain):
                # 第一行：把最后一列清空，保持其他列不变（包括可能存在的“倒数第二列”空字段）
                row1 = row[:-1] + [""]
                writer.writerow(row1)
                # 第二行：只写解释这一列；csv.writer 会自动加引号
                writer.writerow([explain])
            else:
                # 其他行原样（按 CSV 规则）输出
                writer.writerow(row)

def main():
    ap = argparse.ArgumentParser(description="将 Explanation 字段换到下一行输出")
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("output.txt"))
    ap.add_argument("--encoding", default="utf-8-sig",
                    help="输入文件编码（默认 utf-8-sig；若是 GBK 可用 gb18030）")
    args = ap.parse_args()
    process(args.input_csv, args.output, args.encoding)

if __name__ == "__main__":
    main()
