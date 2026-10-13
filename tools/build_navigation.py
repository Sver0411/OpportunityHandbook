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
    "03 做项目、打比赛、进实验室": "book/03-做项目、打比赛、进实验室",
    "04 升学、就业还是出国": "book/04-升学、就业还是出国",
    "05 从学校走向第一份工作": "book/05-从学校走向第一份工作",
    "06 从新人到能独立负责": "book/06-从新人到能独立负责",
    "07 晋升、跳槽还是转行": "book/07-晋升、跳槽还是转行",
    "08 自由职业、副业与创业": "book/08-自由职业、副业与创业",
    "09 专题手册": "book/09-专题手册",
    "10 路径时间线": "book/10-路径时间线",
    "11 工具与模板": "book/11-工具与模板",
    "12 完整案例": "book/12-完整案例",
    "13 操作手册": "book/13-操作手册",
    "14 避坑": "book/14-避坑",
    "15 内容地图": "book/15-内容地图",
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


def _entry_locations() -> dict[str, str]:
    """条目 id → 它所在的文档 location（章节拆分后条目会换文档）。"""
    import meta as M  # noqa: PLC0415

    out: dict[str, str] = {}
    for doc in M.load_docs(ROOT):
        for e in doc.entries:
            meta = e.get("meta") or {}
            eid = str(meta.get("id") or "")
            if eid:
                out[eid] = doc.location
    return out


def _first_entry_location(node: dict, locs: dict[str, str]) -> str:
    """节点下第一个条目所在文档。"""
    for child in node.get("children") or []:
        tg = child.get("target") or {}
        if tg.get("type") == "entry" and tg.get("entry_id") in locs:
            return locs[tg["entry_id"]]
        deep = _first_entry_location(child, locs)
        if deep:
            return deep
    return ""


def group_target(node: dict, parent: dict, locs: dict[str, str]) -> dict:
    """分组节点的落点。

    如果这一组的内容仍在父章节页里（未拆分），沿用「章节页 + 分组锚点」；
    如果已经拆到独立分册，就直接指向那个分册（分组标题在那里是页面标题）。
    """
    parent_loc = (parent.get("target") or {}).get("location") or ""
    own_loc = _first_entry_location(node, locs)
    if own_loc and own_loc != parent_loc:
        return {"type": "doc", "location": own_loc, "anchor": ""}
    if parent_loc:
        return {"type": "doc", "location": parent_loc, "anchor": M.slugify(node["title"])}
    return {}


def build() -> dict:
    locs = _entry_locations()
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
                # 二级分组：落点要等整棵树建完才知道（要看它的后代条目住在哪），
                # 先做标记，最后统一解析。
                node["_group"] = True
            children.append(node)
            stack.append(node)

    # 二级分组的落点：等后代条目都挂上以后再解析
    def resolve_groups(nodes: list[dict], parent: dict | None) -> None:
        for n in nodes:
            if n.pop("_group", False):
                n["target"] = group_target(n, parent or {}, locs)
            resolve_groups(n.get("children") or [], n)

    resolve_groups(root_nodes, None)

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
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8", newline="\n")

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
