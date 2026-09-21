#!/usr/bin/env python3
"""构建搜索索引并校验正文。

用法：
    python3 tools/build_index.py              # 校验 + 写出 site/data/index.json
    python3 tools/build_index.py --report      # 额外打印各章条目统计
    python3 tools/build_index.py --report-stale # 列出超过 12 个月未核实的条目
    python3 tools/build_index.py --strict      # 把警告也当作失败（CI 用）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import meta as M  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="构建 OpportunityHandbook 索引并校验内容")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--out", default=None, help="索引输出路径，默认 <root>/site/data/index.json")
    ap.add_argument("--report", action="store_true", help="打印各章条目统计")
    ap.add_argument("--report-stale", action="store_true", help="列出需要重新核实的条目")
    ap.add_argument("--strict", action="store_true", help="警告也视为失败")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out) if args.out else root / "site" / "data" / "index.json"

    index, errors, warnings = M.build_index(root)

    def say(*a):
        if not args.quiet:
            print(*a)

    if args.report:
        say("章节统计")
        for item in index.get("docs", []):
            extra = f" / 问题入口 {item['questions']}" if item.get("questions") else ""
            say(f"  {item['title']}: 完成 {item['complete']} / 待写 {item['todo']}{extra}")

    if args.report_stale:
        say(f"\n需要重新核实（最后核实早于 {index['stale_threshold']}）")
        if not index["stale"]:
            say("  无")
        for s in index["stale"]:
            say(f"  {s['last_verified']}  {s['title']}  ({s['path']})")

    if warnings:
        say(f"\n警告 {len(warnings)} 条")
        for w in warnings:
            say(f"  ! {w}")
    if errors:
        say(f"\n错误 {len(errors)} 条")
        for e in errors:
            say(f"  x {e}")

    stats = index["stats"]
    say(f"\n文件 {stats['docs']} 个 · 条目 {stats['entries_total']} 条"
        f"（完成 {stats['complete']} / 待写 {stats['todo']}）"
        f" · 首页问题 {stats['questions']} 条 · 待重新核实 {stats['stale']} 条")

    if errors:
        return 1
    if args.strict and warnings:
        say("--strict：存在警告，判定失败")
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say(f"索引已写出：{out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
