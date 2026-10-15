#!/usr/bin/env python3
"""给内容较多的章节加一行阅读提示（幂等）。

合并成「一章一个文件」之后，最长的章约 140 分钟，读者需要先知道这件事，
才知道该通读还是跳读。提示写在章首导读的引用块里。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = "这一章内容较多"


def read_minutes(text: str) -> float:
    body = re.sub(r"```meta\n.*?\n```", "", text, flags=re.S)
    body = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)
    body = re.sub(r"[#>*|`\-]", "", body)
    return len(re.sub(r"\s", "", body)) / 400


def main() -> int:
    changed = []
    for path in sorted((ROOT / "book").glob("[0-9][0-9]-*.md")):
        text = path.read_text(encoding="utf-8")
        if MARK in text:
            continue
        minutes = read_minutes(text)
        if minutes < 60:
            continue
        lines = text.split("\n")
        head = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
        if head is None:
            continue
        j = head + 1
        while j < len(lines) and (not lines[j].strip() or lines[j].startswith(">")):
            j += 1
        k = j - 1
        while k > head and not lines[k].strip():
            k -= 1
        if k <= head or not lines[k].startswith(">"):
            continue
        hint = (f"> 这一章内容较多（约 {round(minutes / 5) * 5} 分钟）。"
                "只想解决某个具体问题时，用下面的分组表跳到关心的那一组；想通读，就顺着往下读。")
        lines.insert(k + 1, hint)
        path.write_text("\n".join(lines), encoding="utf-8")
        changed.append((path.name, round(minutes)))
    for name, m in changed:
        print(f"  加提示：{name}（约 {m} 分钟）")
    print(f"共 {len(changed)} 章")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
