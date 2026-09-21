#!/usr/bin/env python3
"""把文章写进 Canonical IA 指定的章节文件。

用法：由各批次脚本调用

    from apply_articles import apply, nav_chapter_of
    apply({
        "judge-worth-it": {
            "summary": "……",
            "body": "……",
            "stages": "[college, undergraduate, master]",
            "topics": "[explore]",
            "outputs": "[optionality]",
            "effort": "low",
            "evidence": "[experience_based]",
        },
    })
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402

NAV = json.loads((ROOT / "meta" / "navigation.json").read_text(encoding="utf-8"))

LAST_VERIFIED = "2026-09-21"


def _walk(nodes, chapter=None, path=None):
    """产出 (entry_id -> (chapter_location, parent标题链)。"""
    path = path or []
    out = {}
    for n in nodes:
        ch = chapter
        if ch is None:
            ch = (n.get("target") or {}).get("location")
        t = n.get("target")
        if t and t.get("type") == "entry" and not n.get("children"):
            out[t["entry_id"]] = (ch, path, n["title"])
        out.update(_walk(n.get("children") or [], ch, path + [n["title"]]))
    return out


NAV_MAP = _walk(NAV["items"])


def canonical_title(entry_id: str) -> str:
    info = NAV_MAP.get(entry_id)
    return info[2] if info else entry_id


def chapter_of(entry_id: str) -> str:
    info = NAV_MAP.get(entry_id)
    if not info or not info[0]:
        raise SystemExit(f"navigation.json 里找不到 {entry_id} 的归属章节")
    return info[0]


def _meta_block(entry_id: str, art: dict, title: str) -> str:
    summary = art.get("summary", "").strip()
    stages = art.get("stages", "[college, undergraduate, master, new_grad]")
    topics = art.get("topics", "[explore]")
    outputs = art.get("outputs", "[optionality]")
    effort = art.get("effort", "medium")
    evidence = art.get("evidence", "[experience_based]")
    extra = art.get("meta_extra", [])
    lines = [
        f"id: {entry_id}",
        "status: complete",
        f"stages: {stages}",
        f"topics: {topics}",
        f"outputs: {outputs}",
        f"effort: {effort}",
        f"evidence: {evidence}",
        f"summary: {summary}",
        f"last_verified: {LAST_VERIFIED}",
    ]
    lines.extend(extra)
    return "```meta\n" + "\n".join(lines) + "\n```"


def apply(articles: dict) -> int:
    """写入/替换条目正文。返回处理的条目数。"""
    by_file: dict[str, list[tuple[str, dict]]] = {}
    for entry_id, art in articles.items():
        by_file.setdefault(chapter_of(entry_id), []).append((entry_id, art))

    touched = 0
    for location, items in by_file.items():
        path = ROOT / (location + ".md")
        if not path.is_file():
            raise SystemExit(f"章节文件不存在：{path}")
        raw = path.read_text(encoding="utf-8")
        fm_m = re.match(r"^---\n.*?\n---\n", raw, re.S)
        head = fm_m.group(0) if fm_m else ""
        rest = raw[len(head):]

        for entry_id, art in items:
            title = canonical_title(entry_id)
            block = _meta_block(entry_id, art, title)
            body = art["body"].strip()
            block_text = f"### {title}\n\n{block}\n\n{body}\n"
            pat = re.compile(r"^### " + re.escape(title) + r"(.*?)(?=^### |\Z)", re.S | re.M)
            if pat.search(rest):
                rest = pat.sub(lambda _m: block_text, rest, count=1)
            else:
                rest = rest.rstrip() + "\n\n" + block_text
            touched += 1

        path.write_text(head + rest.rstrip() + "\n", encoding="utf-8")
    return touched
