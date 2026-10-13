#!/usr/bin/env python3
"""跨条目重复检测：同一条结论在两个不同条目里各写一遍。

与 tools/audit_duplication.py 的分工：
  - audit_duplication.py  查**条目内部**的重复段落/标题/表格；
  - 本工具查**条目之间**的重复长句（同一个意思写在两篇里，改一处忘一处）。

只报告、不修改。默认阈值 24 字，可用 --min 调整；来源行（含 http 的列表项）
与表格行不参与比对，因为官方入口本来就该在多处出现。

    python3 tools/audit_cross_duplication.py
    python3 tools/audit_cross_duplication.py --min 30 --limit 20
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAT = re.compile(r"### ([^\n]+)\n\n```meta\n([\s\S]*?)\n```\n([\s\S]*?)(?=\n### |\Z)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=24, help="参与比对的最短句长")
    ap.add_argument("--limit", type=int, default=15)
    args = ap.parse_args()

    seen: dict[str, set[str]] = collections.defaultdict(set)
    for p in sorted((ROOT / "book").rglob("*.md")):
        for m in PAT.finditer(p.read_text(encoding="utf-8")):
            eid_m = re.search(r"id:\s*(\S+)", m.group(2))
            if not eid_m:
                continue
            eid = eid_m.group(1)
            for s in re.split(r"[。\n]", m.group(3)):
                s = s.strip()
                if len(s) < args.min or s.startswith(("|", "-", "#", "`", ">")):
                    continue
                if "http" in s:          # 来源行：多处出现是正常的
                    continue
                seen[s].add(eid)

    dup = sorted(((s, ids) for s, ids in seen.items() if len(ids) > 1), key=lambda x: -len(x[1]))
    print(f"跨条目重复长句（≥{args.min} 字）：{len(dup)} 组")
    for s, ids in dup[: args.limit]:
        print(f"  [{len(ids)}] {s[:60]}… → {sorted(ids)[:5]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
