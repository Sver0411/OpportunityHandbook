#!/usr/bin/env python3
"""按 Canonical IA 重建章节文件的骨架：

  # 章节标题
  导言
  ## <canonical 分组>
  ### <canonical 条目标题>
  ...（条目内部的 ## 小节原样保留）

顺序、分组名、条目归属与显示标题全部以 meta/navigation.json 为准；
不在 Canonical IA 里的块（旧 TODO 占位、迁移残留）会被移除。

关键约定：`##` 只有在「后面紧跟 `###`」时才是分组标题，
否则它是文章内部的 H2 小节，属于当前条目，不能截断条目正文。

    python3 tools/restructure_chapters.py          # 预览
    python3 tools/restructure_chapters.py --write  # 写盘
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


def canonical_layout() -> dict[str, list[dict]]:
    """章节 location → [{'title': 分组名, 'entries': [导航节点, ...]}, ...]。"""
    nav = json.loads((ROOT / "meta" / "navigation.json").read_text(encoding="utf-8"))
    layout: dict[str, list[dict]] = {}
    for top in nav.get("items") or []:
        loc = (top.get("target") or {}).get("location")
        if not loc:
            continue
        groups: list[dict] = []
        for g in top.get("children") or []:
            kids = g.get("children") or []
            if not kids:
                # 一级栏目下的直接叶子（如 00、09、11）：合成一个「无分组」段
                groups.append({"title": "", "entries": [g]})
                continue
            groups.append({"title": g.get("title") or "", "entries": kids})
        layout[loc] = groups
    return layout


def parse_blocks(lines: list[str]):
    """切成 (kind, 起, 止)；kind ∈ {h1, group, entry}。

    `##` 只有当它后面第一个非空行是 `###` 时才算分组标题。
    """
    n = len(lines)
    marks: list[tuple[int, str]] = []
    for i, l in enumerate(lines):
        if l.startswith("# "):
            marks.append((i, "h1"))
        elif l.startswith("## "):
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and lines[j].startswith("### "):
                marks.append((i, "group"))
        elif l.startswith("### "):
            marks.append((i, "entry"))
    if not marks:
        return []
    out = []
    for k, (s, kind) in enumerate(marks):
        e = marks[k + 1][0] if k + 1 < len(marks) else n
        out.append((kind, s, e))
    return out


def trim(block: list[str]) -> list[str]:
    out = list(block)
    while out and not out[-1].strip():
        out.pop()
    return out


def retitle(block: list[str], title: str) -> list[str]:
    """把条目标题换成 Canonical 标题（正文与 id 不变，旧链接不断）。"""
    if not block or not title:
        return block
    out = list(block)
    out[0] = "### " + title + "\n"
    return out


def block_id(block: list[str]) -> str:
    m = re.search(r"^id:\s*(\S+)", "".join(block), re.M)
    return m.group(1) if m else ""


def is_question(block: list[str]) -> bool:
    return bool(re.search(r"^kind:\s*question", "".join(block), re.M))


def collect(path: Path):
    """返回 (front matter, H1, 导言, {id: 条目块}, [首页问题块])。"""
    raw = path.read_text(encoding="utf-8")
    fm = re.match(r"^---\n.*?\n---\n", raw, re.S)
    head = fm.group(0) if fm else ""
    body = raw[len(head):]
    lines = body.splitlines(keepends=True)

    blocks = parse_blocks(lines)
    h1: list[str] = []
    intro: list[str] = []
    entries: dict[str, list[str]] = {}
    questions: list[list[str]] = []

    if blocks:
        intro = trim(lines[: blocks[0][1]])
    else:
        intro = trim(lines)

    for kind, s, e in blocks:
        blk = trim(lines[s:e])
        if kind == "h1":
            h1 = blk
            intro = []
        elif kind == "entry":
            if is_question(blk):
                questions.append(blk)
            else:
                eid = block_id(blk)
                if eid:
                    entries[eid] = blk
    return head, h1, intro, entries, questions


def rebuild(path: Path, layout, pool, head, h1, intro, write: bool):
    loc = str(path.relative_to(ROOT))[:-3]
    groups = layout.get(loc)
    if groups is None:
        return 0, [f"（跳过未登记章节 {loc}）"]
    if not any(n.get("target", {}).get("type") == "entry"
               for g in groups for n in g["entries"]):
        return 0, [f"（跳过索引章节 {loc}，不重建）"]

    out: list[str] = list(h1 or [f"# {path.stem.split('-', 1)[-1]}\n"])
    if intro:
        out.append("\n")
        out.extend(intro)
    used = 0
    for g in groups:
        if g["title"]:
            out.append("\n## " + g["title"] + "\n")
        for node in g["entries"]:
            tgt = node.get("target") or {}
            if tgt.get("type") != "entry":
                continue
            eid = tgt.get("entry_id") or ""
            blk = pool.get(eid)
            if blk is None:
                out.append("\n### " + (node.get("title") or eid) + "\n\n> TODO\n")
                continue
            used += 1
            out.append("\n")
            out.extend(retitle(blk, node.get("title") or ""))
            out.append("\n")

    if write:
        path.write_text(head + "".join(out).strip("\n") + "\n", encoding="utf-8")
    return used, []


QUESTIONS_HEAD = """---
nav: false
id: meta-home-questions
title: 首页常见问题
type: doc
section: meta
order: 20
topics: [explore]
stages: [highschool, college, undergraduate, new_grad, work_1_3, career_change]
summary: 首页展示的常见问题入口，每条都链接回主线的判断文章。
last_verified: 2026-09-21
---

# 首页常见问题
"""


def write_questions(questions: list[list[str]]) -> None:
    out = [QUESTIONS_HEAD]
    for blk in questions:
        body = [re.sub(r"\]\((?![a-zA-Z]+://|#)([^)]+\.md)", r"](../book/\1", l) for l in blk]
        out.append("\n" + "".join(body).strip("\n") + "\n")
    (ROOT / "meta" / "home-questions.md").write_text("".join(out).rstrip() + "\n",
                                                     encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    layout = canonical_layout()
    files = sorted(p for p in (ROOT / "book").glob("*.md") if p.stem != "README")

    pool: dict[str, list[str]] = {}
    heads: dict[Path, tuple] = {}
    questions: list[list[str]] = []
    for path in files:
        head, h1, intro, entries, qs = collect(path)
        heads[path] = (head, h1, intro)
        pool.update(entries)
        questions.extend(qs)

    if args.write and questions:
        write_questions(questions)

    total = 0
    for path in files:
        head, h1, intro = heads[path]
        used, notes = rebuild(path, layout, pool, head, h1, intro, args.write)
        if notes:
            print(notes[0])
            continue
        total += used
        print(f"{path.name}: 归位 {used} 篇")

    placed = {n["target"]["entry_id"]
              for gs in layout.values() for g in gs for n in g["entries"]
              if (n.get("target") or {}).get("type") == "entry"}
    left = [eid for eid in pool if eid not in placed]
    print(f"合计归位 {total}；未进入 Canonical IA 的旧条目 {len(left)} 篇"
          + ("（已移除）" if args.write else "（将被移除）"))
    if left:
        print("   " + ", ".join(left[:60]))
    print(f"首页问题 {len(questions)} 条 → meta/home-questions.md")
    if not args.write:
        print("（预览模式，未写盘；加 --write 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
