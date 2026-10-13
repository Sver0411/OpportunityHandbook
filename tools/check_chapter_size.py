#!/usr/bin/env python3
"""防止正文文件重新长成「几千行的大章节」。

    python3 tools/check_chapter_size.py            # 检查（超限返回 1）
    python3 tools/check_chapter_size.py --limit 800

背景：章节按分组拆成多个分册之后，单文件改动成本才降下来。如果没有门禁，
下一个内容批次很容易又把它们堆回一个文件里。规则很简单：正文文件超过
LIMIT 行就必须拆（用 tools/split_chapter.py），否则发布被阻止。

阈值给了一点余量：目前最大的分册约 780 行，因此 900 行意味着「再明显长一截
就该拆了」，不会因为正常增写而频繁触发。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LIMIT = 900


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=LIMIT)
    args = ap.parse_args()

    over: list[tuple[int, Path]] = []
    for p in sorted((ROOT / "book").rglob("*.md")):
        n = len(p.read_text(encoding="utf-8").splitlines())
        if n > args.limit:
            over.append((n, p.relative_to(ROOT)))

    biggest = max(
        ((len(p.read_text(encoding="utf-8").splitlines()), p.relative_to(ROOT))
         for p in (ROOT / "book").rglob("*.md")),
        default=(0, None),
    )
    print(f"正文文件行数上限：{args.limit}；当前最长：{biggest[0]} 行（{biggest[1]}）")

    if over:
        for n, p in sorted(over, reverse=True):
            print(f"  x {p}: {n} 行")
        print("→ 超过上限：请用 tools/split_chapter.py 按分组拆分")
        return 1
    print("→ 没有超长文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
