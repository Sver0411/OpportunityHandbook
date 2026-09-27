#!/usr/bin/env python3
"""扫描 book/ 里两类不稳妥表达：
  1. 无可靠来源的精确时间/比例区间（如「3–6 个月」「1.5–3 年」）
  2. 过度绝对化表达（大多数导师都会……、一般公司都……、基本都会……）

只报告，供人工确认后改写。
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

NUM = re.compile(r"\d+(?:\.\d+)?\s*(?:–|—|-|~|到)\s*\d+(?:\.\d+)?\s*(?:个月|年|周|天|小时|%|％)?")
ABS = re.compile(
    r"(大多数|多数导师|多数公司|一般公司|一般导师|基本都会|一定要|肯定会|几乎没有例外|通常一定|只要…就|通常一定|基本归零)")


def scan(kind: str) -> list:
    out = []
    pat = NUM if kind == "num" else ABS
    for p in sorted((ROOT / "book").glob("*.md")):
        lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
        starts = [i for i, l in enumerate(lines) if l.startswith("### ")]
        spans = [(s, starts[k + 1] if k + 1 < len(starts) else len(lines)) for k, s in enumerate(starts)]
        for s, e in spans:
            blk = "".join(lines[s:e])
            m = re.search(r"^id:\s*(\S+)", blk, re.M)
            eid = m.group(1) if m else "?"
            for mm in pat.finditer(blk):
                seg = mm.group(0).strip()
                if kind == "num" and not any(u in seg for u in ("个月", "年", "周", "天", "小时", "%", "％")):
                    continue
                out.append((p.name, eid, seg))
    return out


def main() -> int:
    nums = scan("num")
    absx = scan("abs")
    print(f"数字区间表述：{len(nums)} 处（时间/比例）")
    for n in nums[:20]:
        print(f"   {n[0]} | {n[1]} | {n[2]}")
    print(f"\n绝对化表述：{len(absx)} 处")
    for a in absx[:20]:
        print(f"   {a[0]} | {a[1]} | {a[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
