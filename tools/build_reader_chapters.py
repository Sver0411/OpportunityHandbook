"""Assemble existing Markdown into continuous reader chapters without editing it."""
from __future__ import annotations

import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

import build_site as B
import mdrender
import meta as M

ROOT = Path(__file__).resolve().parent.parent


class Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])


def ordered_refs(n):
    return [r for child in n["children"] for r in ordered_refs(child)] + n["refs"]


def group_intro(doc, group):
    for seg in doc.segments:
        if seg["kind"] != "text":
            continue
        lines = seg["lines"]
        for i, line in enumerate(lines):
            if line.strip() != "## " + group:
                continue
            out = []
            for raw in lines[i + 1:]:
                if re.match(r"^#{1,2}\s", raw):
                    break
                out.append(raw)
            if "\n".join(out).strip():
                return "\n".join(out).strip()
    return ""


def lead(doc):
    out = []
    for line in doc.body.splitlines():
        if line.startswith("# "):
            continue
        if re.match(r"^#{2,6}\s", line):
            break
        out.append(line)
    return "\n".join(out).strip()


def assemble(n, docs, index, routes):
    threshold = index["stale_threshold"]
    entries = {str(e["meta"]["id"]): (doc, e) for doc in docs.values() for e in doc.entries}
    chunks = []
    overview_origins = {}

    def fix_anchors(fragment, doc, prefix):
        ids = Ids(); ids.feed(fragment)
        known = set(ids.ids)
        def rewrite(match):
            name = unquote(html.unescape(match.group(1)))
            target = prefix + '--' + name
            if name in known:
                return match.group(0)
            if target in known:
                destination = '#' + target
            elif name in entries:
                source, _ = entries[name]
                destination = source.entry_route(name)
            elif name in {doc.location.rsplit('/', 1)[-1], M.slugify(doc.title)}:
                destination = doc.route
            elif name in doc.anchors:
                destination = doc.route + '/' + name
            else:
                return match.group(0)
            return 'href="' + html.escape(destination, quote=True) + '"'
        return re.sub(r'href="#([^/"\s][^"]*)"', rewrite, fragment)

    def render_md(text, doc, prefix, resolve_links=True):
        mdrender.begin_document()
        mdrender.set_context(doc.rel, routes)
        mdrender.set_id_prefix(prefix)
        fragment = B.wrap_sources(mdrender.render(text)[0])
        return fix_anchors(fragment, doc, prefix) if resolve_links else fragment

    def overview(node):
        # Reuse a real source-group introduction when one exists. If the task
        # starts with a standalone guide, relocate its existing lead paragraph.
        introductions = []
        seen_groups = set()
        included = {r['id'] for r in ordered_refs(node)}
        for ref in node["refs"]:
            if ref["id"] in entries:
                doc, entry = entries[ref["id"]]
                members = {str(e['meta']['id']) for e in doc.entries if e['group'] == entry['group']}
                # A broad old group may have been split between several new
                # tasks. Its introduction must not describe a partial subset.
                if not members.issubset(included):
                    continue
                intro = group_intro(doc, entry["group"] or ref["source_group"])
                key = (doc.location, entry["group"] or ref["source_group"])
                if intro and key not in seen_groups:
                    seen_groups.add(key)
                    introductions.append(render_md(intro, doc, "overview-" + node["id"] + '-' + str(len(introductions))))
        if introductions:
            return ''.join(introductions)
        preferred = node.get("overview", "").removeprefix("#/doc/")
        ref = next((r for r in node["refs"] if r["location"] == preferred and r["role"] == "guide" and r["id"] not in entries), None)
        if ref:
            doc = docs[ref["location"]]
            intro = lead(doc)
            if intro:
                overview_origins[ref["id"]] = intro
                return render_md(intro, doc, "overview-" + node["id"])
        summaries = [r for r in node["refs"] if r["id"] in entries] + node["refs"]
        text = node.get("summary") or next((r["summary"] for r in summaries if r["summary"]), "")
        return '<p>' + html.escape(text) + '</p>' if text else ""

    def section(ref):
        doc = docs[ref["location"]]
        mdrender.set_context(doc.rel, routes)
        if ref["id"] in entries:
            _, seg = entries[ref["id"]]
            mdrender.begin_document()
            _, fragment = B.render_entry_section(seg, threshold, M.datetime.date.today().isoformat())
            fragment = fragment.replace('class="entry"', 'class="entry reader-chapter-section" data-nav-id="' + html.escape(ref["id"]) + '"', 1)
        else:
            rendered = B.render_doc(doc, threshold, ref["id"])
            body = rendered.split('</header>', 1)[1].rsplit('</article>', 1)[0].lstrip()
            original_lead = overview_origins.get(ref["id"])
            if original_lead:
                prefix = render_md(original_lead, doc, ref["id"], False).strip()
                if not body.startswith(prefix):
                    raise ValueError('Cannot relocate original introduction: ' + ref["route"])
                body = body[len(prefix):].lstrip()
            metadata = rendered.split('</header>', 1)[0].split('<header class="doc-header">', 1)[1]
            metadata = re.sub(r'<h1>.*?</h1>', '<h3>' + html.escape(ref["title"]) + '</h3>', metadata, count=1)
            fragment = ('<section class="entry reader-chapter-section" id="' + html.escape(ref["id"])
                + '" data-nav-id="' + html.escape(ref["id"]) + '">' + metadata + body + '</section>')
        # Local source anchors retain their meaning inside the embedded article.
        return fix_anchors(fragment, doc, ref["id"])

    def body(node, nested=False):
        if nested:
            chunks.append('<section class="reader-chapter-group" id="chapter-' + html.escape(node["id"])
                + '" data-nav-id="' + html.escape(node["id"]) + '"><h2>' + html.escape(node["label"]) + '</h2>')
        intro = overview(node)
        origin = next((r["id"] for r in node["refs"] if r["id"] in overview_origins), "")
        chunks.append('<section class="reader-chapter-intro" id="overview-' + html.escape(node["id"])
                      + '" data-overview-source="' + html.escape(origin) + '">'
                      + ('' if nested else '<h2>本组概览</h2>') + intro + '</section>')
        for child in node["children"]:
            body(child, True)
        chunks.extend(section(ref) for ref in node["refs"])
        if nested:
            chunks.append('</section>')

    body(n)
    result = ('<article class="doc reader-assembled-chapter" data-chapter="' + html.escape(n["id"])
        + '"><header class="doc-header"><h1>' + html.escape(n["label"]) + '</h1></header>' + ''.join(chunks) + '</article>')
    ids = Ids(); ids.feed(result)
    if len(ids.ids) != len(set(ids.ids)):
        raise ValueError('Duplicate HTML IDs in assembled chapter ' + n["id"])
    expected = [r["id"] for r in ordered_refs(n)]
    for key in expected:
        if result.count('data-nav-id="' + key + '"') != 1:
            raise ValueError('Missing or duplicate chapter section ' + n["id"] + '/' + key)
    return result


def main():
    model = json.loads((ROOT / 'site/data/reader.json').read_text())["reader"]
    index = json.loads((ROOT / 'site/data/index.json').read_text())
    docs = {d.location: d for d in M.load_docs(ROOT)}
    routes = {d.rel: d.route for d in docs.values()}
    nodes = {}
    def visit(items):
        for n in items:
            nodes[n['id']] = n
            visit(n['children'])
    visit(model['topics'] + model['atlases'])
    out = ROOT / 'site/chapters'; out.mkdir(parents=True, exist_ok=True)
    written = set()
    for key in model['chapters']:
        target = out / (key + '.html')
        target.write_text(assemble(nodes[key], docs, index, routes), encoding='utf-8')
        written.add(target)
    for old in out.glob('*.html'):
        if old not in written:
            old.unlink()
    print('已组合', len(written), '个连续章节；Markdown 原文不变。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
