"""极简 Markdown → HTML 渲染器（零依赖）。

只实现本仓库正文实际用到的语法：
  标题、段落、有序/无序列表（含缩进与续行）、引用块、表格、分隔线、
  围栏代码块，以及行内的粗体、斜体、行内代码与链接。

内部链接会在渲染时改写为站点路由（#/doc/...），未在本仓库内解析的链接保持原样。
"""

from __future__ import annotations

import html
import re

from meta import _FENCE_RE, _HEADING_RE, _LIST_RE, slugify

CJK = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")


def _join(lines: list[str]) -> str:
    """合并软换行：中文之间不加空格，其余按空格连接。"""
    out = ""
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if not out:
            out = s
            continue
        if CJK.search(out[-1]) and CJK.search(s[0]):
            out += s
        else:
            out += " " + s
    return out


def _inline(text: str) -> str:
    t = html.escape(text, quote=False)
    t = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]*)\]\(([^)\s]+?)(?:\s+&quot;[^&]*&quot;)?\)",
               lambda m: '<a href="%s"%s>%s</a>' % (
                   html.escape(_rewrite(m.group(2)), quote=True),
                   ' class="external" target="_blank" rel="noopener noreferrer"'
                   if _rewrite(m.group(2)).startswith(("http://", "https://")) else "",
                   m.group(1)),
               t)
    return t


_CTX: dict = {"path": "", "routes": {}, "id_prefix": "", "used_ids": {}}


def begin_document() -> None:
    """开始渲染一个 HTML 文档：清空全局唯一 id 计数器。"""
    _CTX["used_ids"] = {}
    _CTX["id_prefix"] = ""


def set_id_prefix(prefix: str) -> None:
    """设置当前渲染块的 id 前缀（条目正文用条目 id，文档正文用空串）。"""
    _CTX["id_prefix"] = prefix or ""


def _unique_id(title: str) -> str:
    """生成文档内唯一的 heading id：`{entry_id}--{slug}`，重复时追加 -2、-3。"""
    base = slugify(title)
    prefix = _CTX.get("id_prefix") or ""
    full = f"{prefix}--{base}" if prefix else base
    used = _CTX["used_ids"]
    if full not in used:
        used[full] = 1
        return full
    used[full] += 1
    return f"{full}-{used[full]}"


def set_context(path: str, routes: dict[str, str]) -> None:
    """path 为当前文档相对路径，routes 为「相对 md 路径 → 站内路由」映射。"""
    _CTX["path"] = path
    _CTX["routes"] = routes


def _rewrite(href: str) -> str:
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href
    target, _, anchor = href.partition("#")
    if not target:
        return href
    import posixpath
    base = posixpath.dirname(_CTX["path"])
    rel = posixpath.normpath(posixpath.join(base, target)) if base else target
    route = _CTX["routes"].get(rel)
    if route is None:
        return href
    return route + ("/" + anchor if anchor else "")


def _table(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) >= 2 and all(set(c) <= set("-: ") for c in rows[1]):
        head, body = rows[0], rows[2:]
    else:
        head, body = rows[0], rows[1:]
    out = ['<div class="table-wrap"><table>', "<thead><tr>"]
    for c in head:
        out.append(f"<th>{_inline(c)}</th>")
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render(text: str) -> tuple[str, list[dict]]:
    """返回 (html, toc)。toc 中每项为 {level, text, id}。"""
    lines = text.splitlines()
    out: list[str] = []
    toc: list[dict] = []
    i = 0
    n = len(lines)

    def flush_paragraph(buf: list[str]):
        if buf and any(x.strip() for x in buf):
            out.append(f"<p>{_inline(_join(buf))}</p>")

    while i < n:
        line = lines[i]

        fm = _FENCE_RE.match(line)
        if fm:
            fence = fm.group(1)[0] * 3
            info = (fm.group(2) or "").strip()
            body: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith(fence):
                body.append(lines[i])
                i += 1
            i += 1
            if info == "meta":
                continue
            cls = f' class="language-{html.escape(info)}"' if info else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(body))}</code></pre>")
            continue

        hm = _HEADING_RE.match(line)
        if hm:
            level = len(hm.group(1))
            title = hm.group(2)
            hid = _unique_id(title)
            if level <= 3:
                toc.append({"level": level, "text": title, "id": hid})
            anchor = f' id="{hid}"' if level >= 2 else ""
            out.append(f"<h{min(level, 4)}{anchor}>{_inline(title)}</h{min(level, 4)}>")
            i += 1
            continue

        if line.strip() in ("---", "***", "___"):
            out.append("<hr>")
            i += 1
            continue

        if line.lstrip().startswith("|"):
            block = []
            while i < n and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(_table(block))
            continue

        if line.lstrip().startswith(">"):
            block = []
            while i < n and lines[i].lstrip().startswith(">"):
                block.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = "".join(f"<p>{_inline(x)}</p>" for x in block if x.strip())
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        if _LIST_RE.match(line):
            block = []
            while i < n and lines[i].strip():
                if _LIST_RE.match(lines[i]) or lines[i].startswith((" ", "\t")):
                    block.append(lines[i])
                    i += 1
                else:
                    break
            out.append(_list(block))
            continue

        if not line.strip():
            i += 1
            continue

        buf = []
        while i < n and lines[i].strip() and not (
            _FENCE_RE.match(lines[i]) or _HEADING_RE.match(lines[i])
            or _LIST_RE.match(lines[i]) or lines[i].lstrip().startswith(("|", ">"))
            or lines[i].strip() in ("---", "***", "___")
        ):
            buf.append(lines[i])
            i += 1
        flush_paragraph(buf)

    return "\n".join(out), toc


def _list(block: list[str]) -> str:
    """按缩进构建嵌套列表。"""
    tree: list[dict] = []
    stack: list[tuple[int, list]] = [(-1, tree)]
    last = None
    for raw in block:
        m = _LIST_RE.match(raw)
        if m:
            indent = len(m.group(1).expandtabs(4))
            marker = m.group(2)
            ordered = marker[0].isdigit()
            item = {"ordered": ordered, "text": [m.group(3)], "children": []}
            while stack and indent <= stack[-1][0]:
                stack.pop()
            if not stack:
                stack = [(-1, tree)]
            stack[-1][1].append(item)
            stack.append((indent, item["children"]))
            last = item
        elif last is not None:
            last["text"].append(raw.strip())
    return _render_list(tree)


def _render_list(items: list[dict]) -> str:
    if not items:
        return ""
    ordered = items[0]["ordered"]
    tag = "ol" if ordered else "ul"
    parts = [f"<{tag}>"]
    for it in items:
        inner = _inline(_join(it["text"]))
        parts.append(f"<li>{inner}{_render_list(it['children'])}</li>")
    parts.append(f"</{tag}>")
    return "".join(parts)
