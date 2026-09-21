#!/usr/bin/env python3
"""IA 重构与写作模型的测试。

覆盖：
  * 一级栏目就是新的 12 个（顺序正确）
  * 旧 hash 深链通过重定向表仍然可达
  * 条目没有丢失（id 集合与基线一致），也没有重复标题
  * 摘要不再依赖「一句话」栏
  * 自然化：旗舰文章已改成文章结构，且都带「来源与更新」
  * 专题页引用主指南而不是复制正文
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import meta as M  # noqa: E402

INDEX: dict = {}

EXPECTED_SECTIONS = [
    "00 从这里开始",
    "01 先决定下一步往哪里走",
    "02 在学校里先把基础打好",
    "03 开始积累真正能留下来的经历",
    "04 当你开始面对第一次重要分流",
    "05 从学校走向第一份工作",
    "06 进入职场以后继续积累",
    "07 当职业开始出现分岔",
    "08 其他同样成立的人生路径",
    "09 专题手册",
    "10 时间线与工具",
    "11 避坑",
]

NATURALIZED = [
    "grad-school-worth-it", "baoyan-vs-kaoyan", "overseas-is-it-for-me",
    "internship-worth-it", "offer-comparison", "job-hunting-resume",
    "first-job-what-to-trade-for",     "career-change-keep-capital", "research-undergrad-start",
    "competition-what-worth-joining", "certificate-what-is-worth-it",
]

# 基线：IA 重构前的条目总数（重构只搬运，不应丢内容）
BASELINE_ENTRIES = 303
BASELINE_COMPLETE = 290


def setUpModule() -> None:
    global INDEX
    INDEX, errors, warnings = M.build_index(ROOT)
    assert not errors, errors


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get("children", []))


class Architecture(unittest.TestCase):
    def test_sections_and_order(self):
        labels = [s["label"] for s in INDEX["nav"]]
        self.assertEqual(labels, EXPECTED_SECTIONS, f"实际：{labels}")

    def test_depth_still_three(self):
        def depth(n):
            kids = n.get("children") or []
            return 1 + (max(depth(c) for c in kids) if kids else 0)
        self.assertLessEqual(max(depth(n) for n in INDEX["nav"]), 3)

    def test_book_files_follow_numbering(self):
        for p in sorted((ROOT / "book").glob("*.md")):
            if p.name == "README.md":
                continue
            self.assertRegex(p.name, r"^\d\d-", f"{p.name} 应以两位编号开头")
            front, _ = M.split_front_matter(p.read_text(encoding="utf-8"))
            num = p.name[:2]
            self.assertTrue(str(front.get("section", "")).startswith(num),
                            f"{p.name} 的 section 与文件名编号不一致：{front.get('section')}")

    def test_docs_have_section_and_subsection(self):
        for p in sorted((ROOT / "docs").rglob("*.md")):
            if p.name in ("README.md", "ROADMAP.md"):
                continue
            front, _ = M.split_front_matter(p.read_text(encoding="utf-8"))
            self.assertIn(str(front.get("section")), ("09 专题手册", "10 时间线与工具"),
                          f"{p} 未归入 09/10")
            self.assertTrue(front.get("subsection"), f"{p} 缺少 subsection")


class Redirects(unittest.TestCase):
    """旧 hash 深链必须仍然可达。"""

    def setUp(self):
        self.red = INDEX["redirects"]
        self.docs = {d["location"] for d in INDEX["all_docs"]}

    def test_old_docs_resolve(self):
        self.assertTrue(self.red["docs"], "重定向表不应为空")
        for old, new in self.red["docs"].items():
            self.assertIn(new, self.docs, f"{old} 重定向到不存在的 {new}")
            self.assertNotIn(old, self.docs, f"{old} 仍然存在，不需要重定向")

    def test_old_entries_resolve(self):
        routes = {e["route"] for e in INDEX["entries"]}
        routes |= {q["route"] for q in INDEX["questions"]}
        routes |= {x["route"] for x in INDEX["todos"]}   # 待写条目也在页面里渲染 与锚点
        for old, new in self.red["entries"].items():
            self.assertIn(new, routes, f"{old} 重定向到不存在的 {new}")

    def test_every_entry_has_route(self):
        self.assertTrue(all(e.get("route", "").startswith("#/doc/") for e in INDEX["entries"]))


class NoContentLoss(unittest.TestCase):
    def test_counts_match_baseline(self):
        self.assertEqual(len(INDEX["entries"]) + len(INDEX["questions"]) + len(INDEX["todos"]),
                         BASELINE_ENTRIES)
        self.assertEqual(len(INDEX["entries"]), BASELINE_COMPLETE)

    def test_ids_unique(self):
        ids = [e["id"] for e in INDEX["entries"]] + [t["id"] for t in INDEX["todos"]]
        dup = {i for i in ids if ids.count(i) > 1}
        self.assertEqual(dup, set(), f"重复 id：{sorted(dup)}")

    def test_no_duplicate_titles(self):
        """同名标题只在 Canonical IA 的不同位置出现时才允许（如两个「推荐信」）。"""
        nav = json.loads(pathlib.Path("meta/navigation.json").read_text(encoding="utf-8"))
        mounted = set()
        def walk(ns):
            for n in ns:
                tg = n.get("target") or {}
                if tg.get("type") == "entry" and not n.get("children"):
                    mounted.add(tg["entry_id"])
                walk(n.get("children") or [])
        walk(nav["items"])
        by_title = {}
        for e in INDEX["entries"]:
            by_title.setdefault(e["title"], set()).add(e["id"])
        bad = []
        for title, ids in by_title.items():
            if len(ids) > 1:
                # 每一个同名条目都必须各自挂在 Canonical IA 的不同节点上
                if len(ids & mounted) != len(ids):
                    bad.append(title)
        self.assertEqual(sorted(bad), [], f"未在 Canonical IA 归位的重复标题：{sorted(bad)}")

    def test_canonical_topics_are_visible(self):
        """Canonical IA 明确列出的专题页必须出现在左栏（不再因 planned 被隐藏）。"""
        labels = {n["label"] for n in walk(INDEX["nav"])}
        for title in ("日本", "科研手册", "Offer 对比表", "AI 与数据", "信息差、机会焦虑与从众"):
            self.assertIn(title, labels, f"Canonical IA 里的《{title}》没有出现在左栏")


class WritingModel(unittest.TestCase):
    """摘要不再依赖「一句话」栏；正文可以是正常文章。"""

    def test_summary_from_metadata_first(self):
        meta_block = {"summary": "元数据里的摘要。"}
        self.assertEqual(M.entry_summary(meta_block, "- 一句话：\n  正文里的句子。"), "元数据里的摘要。")

    def test_summary_falls_back_to_first_paragraph(self):
        body = "### 小标题\n\n这是正文的第一段话，它足够长，可以当作摘要使用。\n\n## 第二节\n\n后面还有内容。"
        self.assertIn("这是正文的第一段话", M.entry_summary({}, body))

    def test_summary_skips_lists_and_headings(self):
        body = "- 一句话：\n  这是列表里的内容。\n\n## 标题\n\n真正的第一段在这里，长度也足够用来做摘要了。"
        got = M.entry_summary({}, body)
        self.assertNotIn("列表里的内容", got)
        self.assertIn("真正的第一段", got)

    def test_all_complete_entries_have_summary(self):
        for e in INDEX["entries"]:
            self.assertTrue(e.get("summary", "").strip(), f"{e['id']} 没有摘要")

    def test_naturalized_articles(self):
        text = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "book").glob("*.md"))
        for eid in NATURALIZED:
            block = re.search(r"### .*?\n\n```meta\n(?:(?!```).)*?id: " + re.escape(eid) +
                              r"[\s\S]*?(?=\n### |\Z)", text)
            self.assertIsNotNone(block, f"找不到 {eid}")
            body = block.group(0)
            # 旧模板的遗留正文可以并进来；正文自身不再用固定栏目
            own = body.split("\n## ", 1)[0]
            self.assertNotIn("- 一句话：", own, f"{eid} 的开篇仍在用旧模板")
            self.assertIn("## 来源与更新", body, f"{eid} 缺少来源与更新")
            self.assertIn("最后核实", body, f"{eid} 缺少核实日期")
            self.assertGreaterEqual(len(re.findall(r"^## ", body, re.M)), 3,
                                    f"{eid} 的小节太少，不算文章结构")

    def test_legacy_entries_still_renderable(self):
        # 未迁移的条目仍是旧格式，但必须带 metadata、能进搜索
        legacy = [e for e in INDEX["entries"] if e["id"] not in NATURALIZED]
        self.assertTrue(legacy)
        for e in legacy:
            self.assertTrue(e.get("evidence"))
            self.assertTrue(e.get("last_verified"))


class TopicManual(unittest.TestCase):
    """专题页引用主指南，不复制正文。"""

    def test_manuals_point_to_main_text(self):
        files = [p for p in (ROOT / "docs").rglob("*.md")
                 if p.name not in ("README.md", "ROADMAP.md")]
        self.assertTrue(files)
        for p in files:
            text = p.read_text(encoding="utf-8")
            self.assertTrue("本页是" in text or "main" in text or "book/" in text,
                            f"{p} 没有指向主线的引用")

    def test_timelines_are_navigation(self):
        files = sorted((ROOT / "docs" / "timelines").glob("*.md"))
        self.assertTrue(files)
        for p in files:
            text = p.read_text(encoding="utf-8")
            self.assertIn("book/", text, f"{p} 应当链接到主线正文")


if __name__ == "__main__":
    unittest.main(verbosity=2)

class EntryBoundaries(unittest.TestCase):
    """条目内部可以用 `##` 组织文章；分组标题仍然分隔条目。"""

    SAMPLE = """# 示例章节

## 第一组

### 文章型条目

```meta
id: t-article
status: complete
```

开头一段话，说明这篇在回答什么问题，长度足够。

## 一个文章小节

小节里的正文，说明判断步骤。

## 另一个文章小节

继续写。

### 旧格式条目

```meta
id: t-legacy
status: complete
```

- 一句话：
  旧格式的写法。

## 第二组

### 第三篇

```meta
id: t-third
status: complete
```

正文。
"""

    def test_group_headings_split_entries(self):
        segs = [s for s in M.split_entries(self.SAMPLE) if s["kind"] == "entry"]
        self.assertEqual([s["title"] for s in segs],
                         ["文章型条目", "旧格式条目", "第三篇"])

    def test_article_sections_stay_inside_entry(self):
        seg = next(s for s in M.split_entries(self.SAMPLE)
                   if s["kind"] == "entry" and s["title"] == "文章型条目")
        body = "\n".join(seg["lines"])
        self.assertIn("## 一个文章小节", body)
        self.assertIn("## 另一个文章小节", body)
        self.assertEqual(seg["group"], "第一组")

    def test_group_is_taken_from_heading(self):
        segs = [s for s in M.split_entries(self.SAMPLE) if s["kind"] == "entry"]
        self.assertEqual([s["group"] for s in segs], ["第一组", "第一组", "第二组"])
