#!/usr/bin/env python3
"""把 book/ 章节按「分组 + 条目」重排，并用给定正文替换标为 todo 的条目。

用法：从另一个脚本里 import refactor 并调用 apply(path, groups, fills)。

- groups：[(分组标题, [条目 id, ...]), ...]，顺序即侧栏顺序。
- fills：{条目 id: (元数据 dict, 正文字符串)}。未提供的条目保持原样（todo）。
- 未出现在 groups 里的条目，统一放到末尾的「待写条目」分组下。
"""

from __future__ import annotations

import re
from pathlib import Path

ENTRY_RE = re.compile(r"^###\s+(.*?)\s*$")
META_RE = re.compile(r"^```meta\s*\n(.*?)\n```\s*$", re.S | re.M)


def parse(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit(f"{path} 缺少 front matter")
    front = m.group(1)
    body = text[m.end():]

    lines = body.splitlines()
    prose: list[str] = []
    entries: list[dict] = []
    cur = None
    for ln in lines:
        em = ENTRY_RE.match(ln)
        if em:
            if cur:
                entries.append(cur)
            cur = {"title": em.group(1), "lines": []}
            continue
        (cur["lines"] if cur else prose).append(ln)
    if cur:
        entries.append(cur)

    for e in entries:
        blob = "\n".join(e["lines"])
        mm = META_RE.search(blob)
        e["meta_text"] = mm.group(1) if mm else ""
        e["body_text"] = (blob[:mm.start()] + blob[mm.end():]).strip("\n") if mm else blob.strip("\n")
        e["id"] = ""
        for ln in e["meta_text"].splitlines():
            if ln.startswith("id:"):
                e["id"] = ln.split(":", 1)[1].strip()
        e["status"] = "todo"
        for ln in e["meta_text"].splitlines():
            if ln.startswith("status:"):
                e["status"] = ln.split(":", 1)[1].strip()
    return front, "\n".join(prose).strip("\n"), entries


def render_entry(e: dict) -> str:
    return f"### {e['title']}\n\n```meta\n{e['meta_text']}\n```\n\n{e['body_text']}\n"


def apply(path: Path, groups: list[tuple[str, list[str]]], fills: dict):
    front, prose, entries = parse(path)
    by_id = {e["id"]: e for e in entries}

    missing = [i for _, ids in groups for i in ids if i and i not in by_id]
    if missing:
        raise SystemExit(f"{path.name}: groups 里出现了不存在的 id：{missing}")

    used: set[str] = set()
    out = [f"---\n{front}\n---", "", prose, ""]

    for label, ids in groups:
        out.append(f"## {label}\n")
        for i in ids:
            e = by_id[i]
            used.add(i)
            if i in fills:
                meta, body = fills[i]
                meta_text = "\n".join(f"{k}: {v}" for k, v in meta.items())
                out.append(f"### {e['title']}\n\n```meta\n{meta_text}\n```\n\n{body.strip()}\n")
            else:
                out.append(render_entry(e))

    rest = [e for e in entries if e["id"] not in used]
    if rest:
        out.append("## 待写条目\n")
        for e in rest:
            out.append(render_entry(e))

    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    filled = sum(1 for i in fills if i in by_id)
    print(f"{path.name}: 分组 {len(groups)} 个，本次补全 {filled} 条，仍待写 {len(rest)} 条")
