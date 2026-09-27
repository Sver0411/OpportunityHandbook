#!/usr/bin/env python3
"""一次性清理：删除条目正文中「## 来源与更新」之后的残留内容。

背景：早期 apply_articles 的条目块在第一个 `## ` 处即截断，导致重写后的
新正文后面残留整段旧正文（新旧两版叠加）。该 bug 已在 apply_articles 中修复，
本脚本用于清理历史遗留。

规则：以 `### ` 为条目边界；保留到第一个「## 来源与更新」小节结束为止，
其后的内容（重复的旧小节）一律删除。**不触碰任何分组标题**（`## ` 且不含 ### 子项）。

    python3 tools/migrations/trim_entry_tails.py --dry-run
    python3 tools/migrations/trim_entry_tails.py --write
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    for path in sorted((ROOT / "book").glob("*.md")):
        if path.stem == "README":
            continue
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        starts = [i for i, l in enumerate(lines) if l.startswith("### ")]
        spans = [(s, starts[k + 1] if k + 1 < len(starts) else len(lines))
                 for k, s in enumerate(starts)]
        changed = False
        for s, e in reversed(spans):
            blk = lines[s:e]
            idx = next((j for j, l in enumerate(blk) if l.strip() == "## 来源与更新"), None)
            if idx is None:
                continue
            end = len(blk)
            for j in range(idx + 1, len(blk)):
                if re.match(r"^## ", blk[j]):
                    end = j
                    break
            tail = blk[end:]
            # 分组标题（## 且其后第一个非空行是 ###）必须保留：
            # 它属于章节结构，不是条目的正文残留。
            keep = []
            for k, l in enumerate(tail):
                if re.match(r"^## ", l):
                    nxt = k + 1
                    while nxt < len(tail) and not tail[nxt].strip():
                        nxt += 1
                    if nxt >= len(tail) or tail[nxt].startswith("### "):
                        keep.append(l.rstrip())
            junk = [l for l in tail if l.strip() and not re.match(r"^## ", l)]
            if junk:
                new_blk = blk[:end]
                while new_blk and not new_blk[-1].strip():
                    new_blk.pop()
                new_blk.append("\n")
                for gh in keep:
                    new_blk.append("\n" + gh + "\n")
                lines[s:e] = new_blk
                changed = True
                total += 1
        if changed and args.write:
            path.write_text("".join(lines), encoding="utf-8")

    print(f"需清理条目：{total}" + ("（已写盘）" if args.write else "（dry-run）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
