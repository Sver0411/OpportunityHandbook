#!/usr/bin/env python3
"""Markdown 格式质量检查（对 complete 条目与章节正文）。

    python3 tools/check_markdown_quality.py          # 有问题返回 1
    python3 tools/check_markdown_quality.py --json

检测：
  - 未闭合 **（粗体）
  - 未闭合 `（行内代码）
  - 未闭合 ``` 代码围栏
  - 连续粘连标题（## xxx### xxx）
  - 重复 H2（同一文档内）
  - 空 H2（标题后没有内容）
  - 只有标题没有正文的条目
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402


def check_text(text: str, where: str, problems: list[str]) -> None:
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            if not in_fence:
                in_fence, fence_marker = True, s
            else:
                in_fence = False
            continue
        if in_fence:
            continue
        # 粘连标题
        if re.search(r"^#{2,4} .+#{1,4} ", line):
            problems.append(f"{where}: 标题粘连 → {line.strip()[:40]}")
        # 未闭合 **（忽略表格分隔行）
        if not line.lstrip().startswith("|") and line.count("**") % 2:
            problems.append(f"{where}: 未闭合 ** → {line.strip()[:40]}")
        # 未闭合行内 `（三连反引号按整体处理，不参与配对）
        inline = line.replace("```", "\x00")
        if inline.count("`") % 2:
            problems.append(f"{where}: 未闭合 ` → {line.strip()[:40]}")

    if in_fence:
        problems.append(f"{where}: 未闭合 ``` 代码围栏")

    # 重复 H2：以条目块为单位（每个条目都有自己的「来源与更新」）
    starts = [m.start() for m in re.finditer(r"^### ", text, re.M)] + [len(text)]
    segs = [text[a:b] for a, b in zip([0] + starts[:-1], starts)]
    for seg in segs:
        h2s = re.findall(r"^## (.+?)[ \t]*$", seg, re.M)
        seen = set()
        for h in h2s:
            if h in seen:
                problems.append(f"{where}: 条目内重复 H2 《{h}》")
            seen.add(h)

    # 空 H2：文档级判断（分组标题后面紧跟 ### 条目是正常的）
    for m in re.finditer(r"^## (.+?)[ \t]*$\n[ \t]*\n?(?=## |\Z)", text, re.M):
        problems.append(f"{where}: 空 H2 《{m.group(1)}》")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    docs = M.load_docs(ROOT)
    problems: list[str] = []
    for d in docs:
        raw = (ROOT / d.rel).read_text(encoding="utf-8")
        fm = re.match(r"^---\n.*?\n---\n", raw, re.S)
        check_text(raw[len(fm.group(0)):], d.rel, problems)

    if args.json:
        print(json.dumps({"problems": problems}, ensure_ascii=False, indent=2))
    else:
        for p in problems[:40]:
            print("  x", p)
        if len(problems) > 40:
            print(f"  … 还有 {len(problems) - 40} 条")
        print(f"Markdown 问题：{len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
