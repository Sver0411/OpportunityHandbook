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
import textwrap
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mdrender  # noqa: E402
import meta as M  # noqa: E402

LABELS = {k: {key: label for key, label in spec["values"]} for k, spec in M.FACETS.items()}


def chips(values: list[str], facet: str) -> str:
    out = []
    for v in values:
        label = LABELS.get(facet, {}).get(v, v)
        # 证据类型：界面显示中文，内部标识放 tooltip，避免让读者先面对 schema
        en = M.EVIDENCE_EN.get(v) if facet == "evidence" else None
        title = f' title="{html.escape(en)}"' if en else ""
        out.append(f'<span class="chip chip-{html.escape(facet)}"{title}>{html.escape(label)}</span>')
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


# 这些字段内容长、查阅频率低，默认折叠，避免把正文拉得很长
COLLAPSIBLE_FIELDS = ("证据与来源",)


def _split_field_blocks(lines: list[str]) -> list[tuple[str, str, list[str]]]:
    """把条目正文切成「普通文本块」与「字段块」，字段块保留自己的缩进内容。

    字段块 = `- 字段：` 行 + 其后所有缩进行（含缩进的列表与多级子项），
    遇到不缩进的新字段行或正文行即结束。
    """
    blocks: list[tuple[str, str, list[str]]] = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        m = FIELD_LABEL_RE.match(ln)
        if not m:
            blocks.append(("text", "", [ln]))
            i += 1
            continue
        name = m.group(1).strip()
        content: list[str] = []
        head = ln[m.end():].strip()
        if head:
            content.append(head)
        i += 1
        while i < n:
            nxt = lines[i]
            if not nxt.strip():
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and lines[j].startswith((" ", "\t")):
                    content.append("")
                    i = j
                    continue
                # 吃掉空行，别让它变成独立文本块，否则会把字段列表切断
                i = j
                break
            if nxt.startswith((" ", "\t")):
                content.append(nxt)
                i += 1
                continue
            break
        body = textwrap.dedent("\n".join(content)).strip("\n")
        blocks.append(("field", name, body.splitlines() if body else []))
    return blocks


def prepare_entry_body(lines: list[str]) -> str:
    """把「- 字段：」渲染成统一的字段列表：字段名与内容同一行、段间距一致；
    长字段（如「证据与来源」）折叠成可展开的一块。"""
    out: list[str] = []
    open_fields = False
    for kind, name, content in _split_field_blocks(lines):
        if kind == "text":
            if open_fields:
                out.append("</ul>")
                open_fields = False
            html_text, _ = mdrender.render("\n".join(content))
            out.append(html_text)
            continue
        if not open_fields:
            out.append('<ul class="fields">')
            open_fields = True
        inner, _ = mdrender.render("\n".join(content))
        inner = inner.strip()
        if inner.startswith("<p>") and inner.endswith("</p>") and inner.count("<p>") == 1:
            inner = inner[3:-4]
        if name in COLLAPSIBLE_FIELDS and inner:
            out.append(
                '<li class="field-collapsible">'
                f"<details><summary><strong>{html.escape(name)}</strong></summary>"
                f'<div class="detail-body">{inner}</div></details></li>'
            )
        else:
            out.append(f"<li><strong>{html.escape(name)}</strong>：{inner}</li>")
    if open_fields:
        out.append("</ul>")
    return "\n".join(out)


def render_entry_section(seg: dict, threshold: str, today_iso: str) -> tuple[str, str]:
    """渲染一个条目为 <section>，同时返回它的 id（供索引与 SEO 页复用）。"""
    meta_block = seg["meta"] or {}
    eid = str(meta_block.get("id") or M.slugify(seg["title"]))
    inner = prepare_entry_body(seg["lines"])
    html_str = (
        f'<section class="entry" id="{html.escape(eid)}">'
        f"<h3>{mdrender._inline(seg['title'])}</h3>"
        f"{entry_badges(meta_block, today_iso, threshold)}"
        f"{inner}</section>"
    )
    return eid, html_str


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
            _, html_str = render_entry_section(seg, threshold, today_iso)
            body_parts.append(html_str)
    status = doc.status
    status_note = ""
    notice = ""
    if status == "planned":
        # 这类页面不进导航与搜索，只有直接打开链接才会到这里
        status_note = f'<span class="chip chip-todo">{html.escape(M.STATUS_NOTE["planned"])}</span>'
        notice = (
            '<p class="notice">这一页还没有撰写正文。它属于'
            '<a href="#/doc/docs/ROADMAP">内容路线图</a>，因此不出现在导航与搜索结果里；'
            '你可以先回到 <a href="#/">首页问题入口</a> 或使用顶部搜索。</p>'
        )
    elif status == "partial":
        status_note = f'<span class="chip chip-todo">{html.escape(M.STATUS_NOTE["partial"])}</span>'
    header = (
        '<header class="doc-header">'
        f"<h1>{html.escape(doc.title)}</h1>"
        + (f'<p class="doc-summary">{html.escape(str(doc.front.get("summary")))}</p>'
           if doc.front.get("summary") else "")
        + notice
        + '<p class="doc-meta">'
        + status_note
        + (f'<span class="chip chip-verified">最后核实：{html.escape(str(doc.front.get("last_verified")))}</span>'
           if doc.front.get("last_verified") else "")
        + f'<a class="doc-source" href="{M.REPO["url"]}/blob/main/{doc.rel}">在 GitHub 查看原文</a>'
        + "</p></header>"
    )
    return f'<article class="doc" data-path="{html.escape(doc.rel)}">{header}' + "\n".join(body_parts) + "</article>"


PAGE_SHELL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="机会与成长指南">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="{depth}styles.css">
</head>
<body>
<main class="permalink-main">
<p class="permalink-back"><a href="{depth}">← 回到《机会与成长指南》</a>　
<a href="{spa}">在完整手册中打开这一条</a></p>
{body}
<p class="permalink-foot">这一页是静态入口，内容与手册正文一致（Markdown 为唯一正文来源）。
完整手册支持全文搜索，以及按人生阶段、方向、能换回什么、投入与证据类型的叠加筛选。</p>
</main>
</body>
</html>
"""


def _description(text: str, limit: int = 120) -> str:
    s = M.strip_markdown(text or "").replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit] + ("…" if len(s) > limit else "")


def build_permalinks(root: Path, docs: list[M.Doc], index: dict, threshold: str) -> tuple[int, list[str]]:
    """为每个条目与可读文档生成静态页，供搜索引擎与直接分享使用。

    旧的 hash 深链（#/doc/...）不受影响；这里只是多一份可被抓取的入口。
    """
    site = str(index["repo"].get("site_url") or "").rstrip("/")
    out_root = root / "site" / "pages"
    today_iso = M.datetime.date.today().isoformat()
    indexable: list[str] = []
    count = 0
    written: set[Path] = set()

    def write(rel_parts: list[str], html_text: str) -> None:
        target = out_root.joinpath(*rel_parts) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html_text, encoding="utf-8")
        written.add(target)

    def url_for(rel_parts: list[str]) -> str:
        quoted = "/".join(urllib.parse.quote(p) for p in rel_parts)
        return f"{site}/pages/{quoted}/"

    for doc in docs:
        if doc_nav_visible(doc):
            parts = ["doc"] + doc.location.split("/")
            body = render_doc(doc, threshold)
            write(parts, PAGE_SHELL.format(
                title=f"{doc.title}｜机会与成长指南",
                desc=_description(str(doc.front.get("summary") or doc.title)),
                url=url_for(parts), og_type="article", depth="../../",
                spa=f"../../#/doc/{doc.location}", body=body))
            indexable.append(url_for(parts))
            count += 1

        for seg in doc.segments:
            if seg["kind"] != "entry":
                continue
            meta_block = seg["meta"] or {}
            if str(meta_block.get("status") or "") != "complete":
                continue
            if str(meta_block.get("kind") or "") == "question":
                continue          # 首页问题条目只是入口，不单独生成页面（避免重复内容）
            eid, body = render_entry_section(seg, threshold, today_iso)
            parts = [eid]
            write(parts, PAGE_SHELL.format(
                title=f"{seg['title']}｜机会与成长指南",
                desc=_description(M.first_sentence("\n".join(seg["lines"])) or seg["title"]),
                url=url_for(parts), og_type="article", depth="../../",
                spa=f"../../#/doc/{doc.location}/{eid}", body=body))
            indexable.append(url_for(parts))
            count += 1

    # sitemap 与 robots
    site_root = root / "site"
    home = site + "/"
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f"  <url><loc>{html.escape(home)}</loc></url>"]
    for u in indexable:
        lines.append(f"  <url><loc>{html.escape(u)}</loc></url>")
    lines.append("</urlset>")
    (site_root / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (site_root / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: " + home + "sitemap.xml\n", encoding="utf-8")

    # 清掉上一轮生成、这一轮不再产出的页面，避免陈旧内容被一起部署
    removed = 0
    if out_root.is_dir():
        for page in sorted(out_root.rglob("index.html")):
            if page in written:
                continue
            page.unlink()
            removed += 1
            parent = page.parent
            if parent != out_root and not any(parent.iterdir()):
                parent.rmdir()
    return count, [home] + indexable, removed


def doc_nav_visible(doc: M.Doc) -> bool:
    return not M.doc_nav_hidden(doc) and M.doc_user_visible(doc)


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

    pages, _, removed = build_permalinks(root, docs, index, threshold)
    if not args.quiet:
        extra = f"，清理 {removed} 个陈旧页面" if removed else ""
        print(f"已生成 {pages} 个静态入口页（pages/）+ sitemap.xml + robots.txt{extra}")

    if not args.quiet:
        print(f"已渲染 {count} 个页面到 site/content/，索引写入 site/data/index.json")
        if warnings:
            print(f"（{len(warnings)} 条警告，详见 build_index.py --report）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
