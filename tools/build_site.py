#!/usr/bin/env python3
"""把 book/、docs/、meta/ 下的 Markdown 渲染为静态 HTML 片段，输出到 site/content/。

Markdown 始终是唯一正文来源；本脚本只产出构建产物（.gitignore 已忽略）。
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mdrender  # noqa: E402
import meta as M  # noqa: E402

LABELS = {k: {key: label for key, label in spec["values"]} for k, spec in M.FACETS.items()}


def chips(values: list[str], facet: str) -> str:
    out = []
    for v in values:
        label = LABELS.get(facet, {}).get(v, v)
        out.append(f'<span class="chip chip-{html.escape(facet)}">{html.escape(label)}</span>')
    return "".join(out)


def entry_badges(meta_block: dict, today_iso: str, threshold: str) -> str:
    status = str(meta_block.get("status") or "todo")
    parts: list[str] = []
    if status == "todo":
        parts.append('<span class="chip chip-todo">待补充</span>')
    elif status == "needs_review":
        parts.append('<span class="chip chip-todo">待复核</span>')
    if meta_block.get("effort"):
        eff = meta_block["effort"]
        eff = eff[0] if isinstance(eff, list) else eff
        parts.append(f'<span class="chip chip-effort">投入 {html.escape(LABELS["effort"].get(str(eff), str(eff)))}</span>')
    parts.append(chips(M._as_list(meta_block.get("topics")), "topics"))
    parts.append(chips(M._as_list(meta_block.get("stages")), "stages"))
    parts.append(chips(M._as_list(meta_block.get("outputs")), "outputs"))
    parts.append(chips(M._as_list(meta_block.get("evidence")), "evidence"))
    lv = str(meta_block.get("last_verified") or "")
    if lv:
        stale = lv < threshold
        cls = "chip chip-stale" if stale else "chip chip-verified"
        note = "可能需要重新核实" if stale else "最后核实"
        parts.append(f'<span class="{cls}">{note}：{html.escape(lv)}</span>')
    return '<p class="entry-badges">' + "".join(p for p in parts if p) + "</p>"


FIELD_LABEL_RE = re.compile(r"^-\s*([^：:\n]{2,14})\s*[:：]\s*")
H1_RE = re.compile(r"^#\s+(.*?)\s*#*\s*$")


def _join_content(parts: list[str]) -> str:
    """字段内容的软换行合并：任一侧是中日韩字符时不加空格。"""
    out = ""
    for raw in parts:
        p = raw.strip()
        if not p:
            continue
        if not out:
            out = p
            continue
        if mdrender.CJK.search(out[-1]) or mdrender.CJK.search(p[0]):
            out += p
        else:
            out += " " + p
    return out


def prepare_entry_body(lines: list[str]) -> str:
    """把「- 字段：」的字段名加粗、把跨行的字段内容并成一段，
    再把相邻的字段列表合并成一个 <ul class="fields">。"""
    out: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = FIELD_LABEL_RE.match(ln)
        if not m:
            out.append(ln)
            i += 1
            continue
        content = [ln[m.end():]]
        i += 1
        while i < len(lines) and lines[i].strip() and lines[i][:1] in (" ", "\t") \
                and not mdrender._LIST_RE.match(lines[i]):
            content.append(lines[i])
            i += 1
        out.append(f"- **{m.group(1)}**：{_join_content(content)}")

    html_text, _ = mdrender.render("\n".join(out))
    if html_text.startswith("<ul>"):
        html_text = html_text.replace("</ul>\n<ul>", "")
        html_text = html_text.replace("<ul>", '<ul class="fields">', 1)
    return html_text


def render_doc(doc: M.Doc, threshold: str) -> str:
    today_iso = M.datetime.date.today().isoformat()
    body_parts: list[str] = []
    dropped_h1 = False
    for seg in doc.segments:
        if seg["kind"] == "text":
            lines = list(seg["lines"])
            if not dropped_h1:
                for k, ln in enumerate(lines):
                    if not ln.strip():
                        continue
                    if H1_RE.match(ln):
                        lines[k] = ""
                        dropped_h1 = True
                    break
            html_text, _ = mdrender.render("\n".join(lines))
            body_parts.append(html_text)
        else:
            meta_block = seg["meta"] or {}
            eid = str(meta_block.get("id") or M.slugify(seg["title"]))
            inner = prepare_entry_body(seg["lines"])
            body_parts.append(
                f'<section class="entry" id="{html.escape(eid)}">'
                f"<h3>{mdrender._inline(seg['title'])}</h3>"
                f"{entry_badges(meta_block, today_iso, threshold)}"
                f"{inner}</section>"
            )
    status = doc.status
    status_note = ""
    if status == "planned":
        status_note = '<span class="chip chip-todo">结构占位</span>'
    elif status == "partial":
        status_note = '<span class="chip chip-todo">部分完成</span>'
    header = (
        '<header class="doc-header">'
        f"<h1>{html.escape(doc.title)}</h1>"
        + (f'<p class="doc-summary">{html.escape(str(doc.front.get("summary")))}</p>'
           if doc.front.get("summary") else "")
        + '<p class="doc-meta">'
        + status_note
        + (f'<span class="chip chip-verified">最后核实：{html.escape(str(doc.front.get("last_verified")))}</span>'
           if doc.front.get("last_verified") else "")
        + f'<a class="doc-source" href="{M.REPO["url"]}/blob/main/{doc.rel}">在 GitHub 查看原文</a>'
        + "</p></header>"
    )
    return f'<article class="doc" data-path="{html.escape(doc.rel)}">{header}' + "\n".join(body_parts) + "</article>"


def main() -> int:
    ap = argparse.ArgumentParser(description="渲染静态站点内容")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_root = root / "site" / "content"
    docs = M.load_docs(root)
    index, errors, warnings = M.build_index(root)
    if errors:
        print(f"内容校验失败（{len(errors)} 条错误），先修复再构建站点", file=sys.stderr)
        for e in errors:
            print(f"  x {e}", file=sys.stderr)
        return 1

    routes = {doc.rel: doc.route for doc in docs}
    threshold = index["stale_threshold"]
    count = 0
    for doc in docs:
        mdrender.set_context(doc.rel, routes)
        target = out_root / (doc.location + ".html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_doc(doc, threshold), encoding="utf-8")
        count += 1

    data_dir = root / "site" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not args.quiet:
        print(f"已渲染 {count} 个页面到 site/content/，索引写入 site/data/index.json")
        if warnings:
            print(f"（{len(warnings)} 条警告，详见 build_index.py --report）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
