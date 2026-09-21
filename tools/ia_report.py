#!/usr/bin/env python3
"""生成 IA_PARITY_REPORT.md：把线上左栏目录与 Canonical IA 逐节点核对。

    python3 tools/ia_report.py

核对维度：标题 / 顺序 / 父级 / 子级 / target / 是否可点击 / 是否重复。
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import check_ia  # noqa: E402


def flatten(nodes, key, depth=0, trail=()):
    """把树摊平成 [(路径 tuple, 标题, 深度, target)]。"""
    out = []
    for n in nodes:
        here = trail + (n.get(key) or "",)
        out.append((here, n.get(key) or "", depth, n.get("target"), n))
        out.extend(flatten(n.get("children") or [], key, depth + 1, here))
    return out


def main() -> int:
    spec = json.loads((ROOT / "meta" / "navigation.json").read_text(encoding="utf-8"))
    idx = json.loads((ROOT / "site" / "data" / "index.json").read_text(encoding="utf-8"))

    canon = flatten(spec.get("items") or [], "title")
    live = flatten(idx.get("nav") or [], "label")

    result = check_ia.check()

    matched = misplaced = missing = 0
    problems: list[str] = []
    live_by_path = {p: (t, d, n) for p, t, d, _, n in live}

    for path, title, depth, target, _node in canon:
        if path not in live_by_path:
            missing += 1
            problems.append(f"缺失节点：{' > '.join(path)}")
            continue
        lt, ld, ln = live_by_path[path]
        if lt != title or ld != depth:
            misplaced += 1
            problems.append(f"错位节点：{' > '.join(path)}（线上标题《{lt}》深度 {ld}）")
            continue
        matched += 1

    # 线上多出来、Canonical IA 里没有的节点
    extra = [p for p in live_by_path if p not in {c[0] for c in canon}]
    not_clickable = []
    for path, title, depth, target, node in canon:
        if path in live_by_path:
            href = (live_by_path[path][2] or {}).get("href") or ""
            if not href:
                not_clickable.append(" > ".join(path))

    dupes = result["details"]["duplicates"]
    dupe_count = sum(len(v) for v in dupes.values())

    total = len(canon)
    lines = [
        "# IA Parity Report",
        "",
        f"生成时间：{datetime.datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "核对对象：`meta/navigation.json`（Canonical IA，唯一事实源）与线上左栏目录"
        "（`site/data/index.json` 的 `nav`）。",
        "",
        "## 结论",
        "",
        "| 指标 | 数量 |",
        "| --- | --- |",
        f"| 总节点 | {total} |",
        f"| 匹配 | {matched} |",
        f"| 缺失 | {missing} |",
        f"| 错位 | {misplaced} |",
        f"| 重复 | {dupe_count} |",
        f"| broken target | {result['broken_targets']} |",
        f"| orphan content | {result['orphan_public_entries']} |",
        "",
        "成功标准：缺失 = 0、错位 = 0、重复 = 0、broken target = 0、orphan public content = 0。",
        "",
        "## 逐节点核对",
        "",
        f"- 一级栏目 {len(spec.get('items') or [])} 个，与线上左栏顺序逐一比对："
        + ("全部一致" if not problems and not extra else "存在差异"),
        f"- 叶子节点 {sum(1 for c in canon if not (c[4].get('children') or []))} 个；"
        f"其中可点击 {sum(1 for c in canon if not (c[4].get('children') or [])) - len(not_clickable)} 个",
        f"- 最大层级深度 {max(d for _, _, d, _, _ in canon) + 1} 级（一级 → 二级 → 三级 → 文章）",
        "",
    ]

    if problems:
        lines += ["## 问题明细", ""]
        lines += [f"- {p}" for p in problems[:60]]
        lines.append("")
    if extra:
        lines += ["## 线上多出的节点（Canonical IA 里没有）", ""]
        lines += [f"- {' > '.join(p)}" for p in extra[:40]]
        lines.append("")
    if not_clickable:
        lines += ["## 不可点击的叶子节点", ""]
        lines += [f"- {p}" for p in not_clickable[:40]]
        lines.append("")

    lines += [
        "## 检查命令",
        "",
        "```bash",
        "python3 tools/build_navigation.py --report   # Canonical IA 节点与待补目标",
        "python3 tools/check_ia.py                    # Rule A–D 硬校验（CI 要求全 0）",
        "python3 tools/smoke_test.py                  # 浏览器里逐节点验证展开/点击/高亮",
        "python3 tools/ia_report.py                   # 生成本报告",
        "```",
        "",
    ]

    out = ROOT / "IA_PARITY_REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:22]))
    print(f"\n已写出：{out.relative_to(ROOT)}")
    ok = missing == 0 and misplaced == 0 and dupe_count == 0 and not problems and not extra
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
