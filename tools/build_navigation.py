#!/usr/bin/env python3
"""从 Canonical IA 生成 meta/navigation.json（导航唯一事实源）。

    python3 tools/build_navigation.py
    python3 tools/build_navigation.py --report    # 打印节点统计与待补目标
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402
from ia_canonical import TREE  # noqa: E402

# 一级栏目 → 章节落地页
CHAPTER_TARGET = {
    "00 从这里开始": "book/00-从这里开始",
    "01 先决定下一步往哪里走": "book/01-先决定下一步往哪里走",
    "02 在学校里先把基础打好": "book/02-在学校里先把基础打好",
    "03 开始积累真正能留下来的经历": "book/03-开始积累真正能留下来的经历",
    "04 当你开始面对第一次重要分流": "book/04-当你开始面对第一次重要分流",
    "05 从学校走向第一份工作": "book/05-从学校走向第一份工作",
    "06 进入职场以后继续积累": "book/06-进入职场以后继续积累",
    "07 当职业开始出现分岔": "book/07-当职业开始出现分岔",
    "08 其他同样成立的人生路径": "book/08-其他同样成立的人生路径",
    "09 专题手册": "book/09-专题手册",
    "10 时间线与工具": "book/10-时间线与工具",
    "11 避坑": "book/11-避坑",
}


def parse_target(token: str) -> dict | None:
    """@e:<id> / @d:<location> / @n:<id> → 目标对象（@n 表示正文待写）。"""
    if not token:
        return None
    kind, _, val = token.partition(":")
    val = val.strip()
    if not val:
        return None
    if kind == "@e":
        return {"type": "entry", "entry_id": val}
    if kind == "@d":
        loc, _, anchor = val.partition("#")
        return {"type": "doc", "location": loc.strip(), "anchor": anchor.strip()}
    if kind == "@n":
        return {"type": "entry", "entry_id": val}
    raise SystemExit(f"无法识别的目标标记：{token}")


def build() -> dict:
    root_nodes: list[dict] = []
    stack: list[dict] = []

    for raw in TREE.strip().splitlines():
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        title, _, marker = line.rpartition(" @")
        title = title.strip() if " @" in line else line
        target = parse_target(("@" + marker).strip()) if " @" in line else None
        node: dict = {"title": title}
        if target:
            node["target"] = target
        level = indent // 2
        while len(stack) > level:
            stack.pop()
        if level == 0:
            # 一级栏目：绑定章节落地页
            if title in CHAPTER_TARGET:
                node["target"] = {"type": "doc", "location": CHAPTER_TARGET[title], "anchor": ""}
            root_nodes.append(node)
            stack = [node]
        else:
            parent = stack[-1]
            children = parent.setdefault("children", [])
            index = len(children) + 1
            if not target:
                # 二级分组：绑定章节页里的分组锚点
                loc = (parent.get("target") or {}).get("location")
                if loc:
                    node["target"] = {"type": "doc", "location": loc, "anchor": M.slugify(title)}
            children.append(node)
            stack.append(node)

    # 为每个节点补上稳定的 nav_id（位置型，便于引用与测试）
    def assign(nodes: list[dict], prefix: str) -> None:
        for i, n in enumerate(nodes, start=1):
            nav_id = f"{prefix}{i:02d}" if prefix else f"{i - 1:02d}"
            n["nav_id"] = nav_id
            assign(n.get("children") or [], nav_id + "-")

    assign(root_nodes, "")
    return {"version": 1, "items": root_nodes}


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 navigation.json")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    data = build()
    out = ROOT / "meta" / "navigation.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.report:
        docs = {d.location: d for d in M.load_docs(ROOT)}
        entries = {}
        for d in docs.values():
            for e in d.entries:
                entries[e["meta"].get("id")] = e

        total = leaves = 0
        missing: list[str] = []
        def walk(ns):
            nonlocal total, leaves
            for n in ns:
                total += 1
                t = n.get("target")
                if t and (n.get("children") is None):
                    leaves += 1
                    if t["type"] == "entry" and t["entry_id"] not in entries:
                        missing.append(f"entry:{t['entry_id']}")
                    if t["type"] == "doc" and t["location"] not in docs:
                        missing.append(f"doc:{t['location']}")
                walk(n.get("children") or [])
        walk(data["items"])
        print(f"Canonical IA 节点：{total}（叶子 {leaves}）")
        print(f"待补目标：{len(missing)}")
        for m in missing[:20]:
            print("  ", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
