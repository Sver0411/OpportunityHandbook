"""Continuous chapters preserve every source body and keep library copies separate."""
import html
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

import build_reader_chapters as C
import build_site as B
import meta as M
import mdrender
import reader_navigation as R

ROOT = Path(__file__).resolve().parents[2]


def plain(source):
    class Text(HTMLParser):
        def __init__(self):
            super().__init__(); self.text = []
        def handle_data(self, value):
            self.text.append(value)
    parser = Text(); parser.feed(source)
    return re.sub(r'\s+', ' ', ''.join(parser.text)).strip()


class Sections(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack = []; self.sections = {}; self.overviews = {}
    def handle_starttag(self, tag, attrs):
        if tag == 'section':
            self.stack.append([dict(attrs), []])
    def handle_data(self, value):
        for _, parts in self.stack:
            parts.append(value)
    def handle_endtag(self, tag):
        if tag == 'section':
            attrs, parts = self.stack.pop()
            text = re.sub(r'\s+', ' ', ''.join(parts)).strip()
            if 'reader-chapter-section' in attrs.get('class', ''):
                self.sections[attrs['data-nav-id']] = text
            if attrs.get('data-overview-source'):
                self.overviews[attrs['data-overview-source']] = text


class ContinuousChapters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index, errors, _ = M.build_index(ROOT)
        assert not errors, errors
        cls.model = R.build(cls.index)
        cls.docs = {d.location: d for d in M.load_docs(ROOT)}
        cls.routes = {d.rel: d.route for d in cls.docs.values()}
        cls.nodes = {n['id']: n for n in R.walk(cls.model['topics'] + cls.model['atlases'])}
        cls.entries = {e['meta']['id']: e for d in cls.docs.values() for e in d.entries}

    def test_all_chapters_include_every_menu_body_once_in_menu_order(self):
        nav = {n['nav_id']: n for n in R.walk(self.model['navigation'])}
        for key, chapter in self.model['chapters'].items():
            generated = C.assemble(self.nodes[key], self.docs, self.index, self.routes)
            parsed = Sections(); parsed.feed(generated)
            wanted = [r['id'] for r in C.ordered_refs(self.nodes[key])]
            self.assertEqual(list(parsed.sections), wanted, key)
            self.assertEqual(chapter['sections'], wanted, key)
            menu = [n['nav_id'] for n in R.walk(nav[key]['children']) if not n['children']]
            self.assertEqual(menu, wanted, key)
            ids = C.Ids(); ids.feed(generated)
            self.assertEqual(len(ids.ids), len(set(ids.ids)), key)

    def test_assembled_entry_and_document_text_is_unchanged(self):
        for key in self.model['chapters']:
            n = self.nodes[key]
            generated = C.assemble(n, self.docs, self.index, self.routes)
            parsed = Sections(); parsed.feed(generated)
            for ref in C.ordered_refs(n):
                doc = self.docs[ref['location']]
                mdrender.set_context(doc.rel, self.routes)
                if ref['id'] in self.entries:
                    mdrender.begin_document()
                    _, original = B.render_entry_section(self.entries[ref['id']], self.index['stale_threshold'], M.datetime.date.today().isoformat())
                else:
                    rendered = B.render_doc(doc, self.index['stale_threshold'], ref['id'])
                    metadata, body = rendered.split('</header>', 1)
                    metadata = metadata.split('<header class="doc-header">', 1)[1]
                    metadata = re.sub(r'<h1>.*?</h1>', '<h3>' + html.escape(ref['title']) + '</h3>', metadata, count=1)
                    body = body.rsplit('</article>', 1)[0].lstrip()
                    if ref['id'] in parsed.overviews:
                        mdrender.begin_document(); mdrender.set_context(doc.rel, self.routes)
                        prefix = B.wrap_sources(mdrender.render(C.lead(doc))[0]).strip()
                        self.assertTrue(parsed.overviews[ref['id']].endswith(plain(prefix)), ref['route'])
                        self.assertTrue(body.startswith(prefix), ref['route'])
                        body = body[len(prefix):].lstrip()
                    original = metadata + body
                self.assertEqual(parsed.sections[ref['id']], plain(original), key + '/' + ref['id'])

    def test_library_copy_stays_independent_and_has_distinct_navigation_identity(self):
        nav = list(R.walk(self.model['navigation']))
        ids = [n['nav_id'] for n in nav]
        self.assertEqual(len(ids), len(set(ids)))
        for library in self.model['libraries']:
            parent = next(n for n in nav if n['nav_id'] == library['id'])
            self.assertEqual(parent['href'], '#/guide/' + library['id'])
            for ref in library['refs']:
                leaf = next(n for n in parent['children'] if n['nav_id'] == library['id'] + '--' + ref['id'])
                self.assertEqual(leaf['href'], ref['route'] + '?from=' + library['id'])
                self.assertFalse(leaf['reading_anchor'])
                target = self.model['chapter_for'].get(ref['route'])
                if target:
                    core = next(n for n in nav if n['nav_id'] == ref['id'])
                    self.assertEqual(unquote(core['href']), '#/chapter/' + target['chapter'] + '?section=' + ref['id'])

    def test_matching_source_group_introductions_are_preserved(self):
        for key in self.model['chapters']:
            n = self.nodes[key]
            text = plain(C.assemble(n, self.docs, self.index, self.routes))
            included = {r['id'] for r in C.ordered_refs(n)}
            for ref in C.ordered_refs(n):
                if ref['id'] not in self.entries:
                    continue
                doc = self.docs[ref['location']]
                group = self.entries[ref['id']]['group'] or ref['source_group']
                members = {str(e['meta']['id']) for e in doc.entries if e['group'] == self.entries[ref['id']]['group']}
                if not members.issubset(included):
                    continue
                intro = C.group_intro(doc, group)
                if intro:
                    mdrender.begin_document(); mdrender.set_context(doc.rel, self.routes)
                    self.assertIn(plain(mdrender.render(intro)[0]), text, key + '/' + group)

    def test_broad_original_intro_is_not_misapplied_to_partial_task(self):
        generated = C.assemble(self.nodes['explore'], self.docs, self.index, self.routes)
        self.assertNotIn('创业前该验证什么', generated.split('</section>', 1)[0])


class GroupIntroParsing(unittest.TestCase):
    def test_declared_group_intro_is_not_swallowed_by_previous_entry(self):
        body = '''# 学习
## 本章分组
| 分组 | 说明 |
| --- | --- |
| [学业](#学业) | 学业 |
| [通用能力](#通用能力) | 通用能力 |
## 学业
这里是已有的学业概览。
### 成绩
```meta
id: example-grades
```
原有正文。
## 来源与更新
仍是这篇文章的小节。
## 通用能力
这里是已有的通用能力概览。
### 写作
```meta
id: example-writing
```
另一篇正文。
'''
        segments = M.split_entries(body)
        entries = [s for s in segments if s['kind'] == 'entry']
        self.assertEqual([e['group'] for e in entries], ['学业', '通用能力'])
        self.assertIn('## 来源与更新', entries[0]['lines'])
        self.assertNotIn('## 通用能力', entries[0]['lines'])
        intros = '\n'.join('\n'.join(s['lines']) for s in segments if s['kind'] == 'text')
        self.assertIn('这里是已有的通用能力概览。', intros)


if __name__ == '__main__':
    unittest.main()
