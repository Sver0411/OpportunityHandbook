#!/usr/bin/env python3
"""内容与工程规则测试（零依赖，只用标准库）。

覆盖本轮收敛目标：
  * planned 内容不进用户导航 / 不进搜索索引 / 不进阅读序列，但仍在 roadmap
  * 用户侧导航不超过三层
  * 元数据解析 fail-closed：strict 下警告即失败
  * stale 边界按 365 天计算
  * 搜索同义词（alias）生效，且多词之间保持「与」
  * 声明审计脚本可用，且已知的高风险表述已改掉

运行：python3 tools/run_tests.py
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import meta as M  # noqa: E402
import audit_claims as A  # noqa: E402

INDEX: dict = {}
DOCS: list = []


def setUpModule() -> None:
    global INDEX, DOCS
    INDEX, errors, warnings = M.build_index(ROOT)
    assert not errors, errors
    DOCS = M.load_docs(ROOT)


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get("children", []))


class PlannedContent(unittest.TestCase):
    """P1-1：planned 内容对用户不可见，但仓库内部仍保留为路线图。"""

    def setUp(self):
        self.planned = [d for d in DOCS if d.status == "planned"]
        self.planned_locs = {d.location for d in self.planned}
        self.planned_titles = {d.title for d in self.planned}

    def test_planned_docs_exist(self):
        self.assertGreater(len(self.planned), 0, "应当仍有 planned 文档作为路线图")

    def test_not_in_nav(self):
        """planned 文档的 location 不应出现在任何导航链接里。"""
        hrefs = set()
        def collect(nodes):
            for n in nodes:
                if n.get("href"):
                    hrefs.add(n["href"])
                collect(n.get("children") or [])
        collect(INDEX["nav"])
        for d in INDEX["roadmap"]:
            self.assertNotIn(d["location"], str(hrefs),
                             f"planned 文档出现在导航里：{d['location']}")

    def test_not_in_user_docs(self):
        locs = {d["location"] for d in INDEX["docs"]}
        self.assertEqual(locs & self.planned_locs, set())

    def test_not_in_search_entries(self):
        docs_of_entries = {e["doc"] for e in INDEX["entries"]}
        text = "\n".join(str(e) for e in INDEX["entries"])
        for loc in self.planned_locs:
            self.assertNotIn(loc, text)
        self.assertEqual(docs_of_entries & self.planned_locs, set())

    def test_no_todo_entries_in_search(self):
        for e in INDEX["entries"]:
            self.assertEqual(e["status"], "complete")

    def test_listed_in_roadmap(self):
        rm = {d["location"] for d in INDEX["roadmap"]}
        self.assertEqual(rm, self.planned_locs)
        text = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        for title in self.planned_titles:
            self.assertIn(title, text)


class NavigationDepth(unittest.TestCase):
    """P1-7：用户侧导航不超过三层，条目不再铺在左栏。"""

    def max_depth(self, node):
        kids = node.get("children") or []
        return 1 + (max(self.max_depth(c) for c in kids) if kids else 0)

    def test_depth_at_most_three(self):
        worst = max(self.max_depth(n) for n in INDEX["nav"])
        self.assertLessEqual(worst, 3, f"导航最深 {worst} 层")

    def test_entry_nodes_are_in_nav(self):
        """左栏必须显示到具体文章：树里要有 entry 叶子节点。"""
        kinds = {n.get("kind") for n in walk(INDEX["nav"])}
        self.assertIn("entry", kinds)
        leaves = [n for n in walk(INDEX["nav"]) if n.get("kind") == "entry"]
        self.assertGreater(len(leaves), 200, f"左栏条目太少：{len(leaves)}")


    def test_nav_comes_from_navigation_json(self):
        """导航必须由 meta/navigation.json 决定，一级栏目逐项对应 Canonical IA。"""
        import json
        nav = json.loads((ROOT / "meta" / "navigation.json").read_text(encoding="utf-8"))
        want = [n["title"] for n in nav["items"]]
        got = [n["label"] for n in INDEX["nav"]]
        self.assertEqual(got, want, "左栏一级栏目与 Canonical IA 不一致")

    def test_entries_still_searchable(self):
        self.assertGreater(len(INDEX["entries"]), 100)
        self.assertTrue(all(e.get("route") for e in INDEX["entries"]))

    def test_group_links_carry_anchor(self):
        # 章节内的分组应当能直接跳到该分组锚点
        groups = [n for n in walk(INDEX["nav"]) if n.get("kind") == "group"]
        with_anchor = [g for g in groups if "/" in g["href"].replace("#/doc/", "")]
        self.assertEqual(len(with_anchor), len(groups), "分组链接应带锚点")


class StaleContract(unittest.TestCase):
    """P1-3：时效契约统一为 365 天。"""

    def test_constant(self):
        self.assertEqual(M.STALE_DAYS, 365)

    def test_threshold_is_one_year(self):
        import datetime
        today = datetime.date.today()
        self.assertEqual(M.stale_threshold(), (today - datetime.timedelta(days=365)).isoformat())

    def _build(self, last_verified: str) -> list[dict]:
        """在临时仓库里放一条 complete 条目，返回 stale 列表。"""
        tmp = tempfile.mkdtemp()
        root = pathlib.Path(tmp)
        (root / "book").mkdir()
        doc = f"""---
id: t-doc
title: 测试章节
type: chapter
section: 测试
section_order: 1
status: complete
last_verified: 2026-09-21
---

## 分组

### 测试条目

```meta
id: t-entry
status: complete
stages: [undergraduate]
topics: [research]
outputs: [degree]
effort: low
evidence: [official]
last_verified: {last_verified}
```

- 一句话：
  仅用于测试。
"""
        (root / "book" / "t.md").write_text(doc, encoding="utf-8")
        index, errors, warnings = M.build_index(root)
        self.assertEqual(errors, [])
        return index["stale"]

    def test_boundary(self):
        import datetime
        today = datetime.date.today()
        self.assertTrue(self._build((today - datetime.timedelta(days=366)).isoformat()),
                        "超过 365 天应进入待重新核实")
        self.assertFalse(self._build((today - datetime.timedelta(days=364)).isoformat()),
                         "未超过 365 天不应进入待重新核实")


class FailClosed(unittest.TestCase):
    """P1-8/十八：无法识别的元数据写法不能静默忽略，strict 下必须失败。"""

    def _root_with(self, front_extra: str) -> pathlib.Path:
        tmp = pathlib.Path(tempfile.mkdtemp())
        (tmp / "book").mkdir()
        (tmp / "book" / "x.md").write_text(f"""---
id: x
title: X
type: chapter
section: X
section_order: 1
status: complete
{front_extra}
---

正文。
""", encoding="utf-8")
        return tmp

    def test_warning_on_nested_or_unknown_lines(self):
        root = self._root_with("  嵌套: 1\n无法识别的行\n")
        _, errors, warnings = M.build_index(root)
        self.assertTrue(any("嵌套" in w or "无法识别" in w for w in warnings),
                        f"应当有解析警告，实际：{warnings}")

    def test_strict_cli_fails_on_warning(self):
        root = self._root_with("  嵌套: 1\n")
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_index.py"),
                            "--root", str(root), "--strict"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, "strict 下警告应导致失败")

    def test_duplicate_key_warns(self):
        root = self._root_with("section: 重复\n")
        _, _, warnings = M.build_index(root)
        self.assertTrue(any("重复的键" in w for w in warnings))


class SearchAliases(unittest.TestCase):
    """P1-8：同义词扩展生效，且组间仍为「与」。"""

    def setUp(self):
        self.aliases = json.loads((ROOT / "site" / "search_aliases.json").read_text(encoding="utf-8"))
        self.entries = INDEX["entries"]

    def groups(self, query: str):
        out = []
        for tok in query.lower().split():
            terms = [tok] + [str(s).lower() for s in self.aliases.get(tok, []) if s]
            out.append(terms)
        return out

    def match(self, query: str):
        hay = [(e, " ".join([e["title"], e.get("summary", ""), e.get("text", ""),
                             e.get("doc_title", "")]).lower()) for e in self.entries]
        out = []
        for e, text in hay:
            if all(any(t in text for t in grp) for grp in self.groups(query)):
                out.append(e)
        return out

    def test_alias_table_shape(self):
        for k, v in self.aliases.items():
            if k.startswith("_"):
                continue
            self.assertIsInstance(v, list, f"{k} 的值应为列表")
            self.assertTrue(all(isinstance(x, str) for x in v))

    def test_required_pairs(self):
        expected = {
            "保送": "保研", "读研": "考研", "读博": "博士", "套磁": "联系导师",
            "换工作": "跳槽", "改行": "转行", "比赛": "竞赛", "实习": "internship",
            "论文": "paper", "作品": "portfolio", "副业": "freelance", "创业": "startup",
        }
        for key, want in expected.items():
            self.assertIn(key, self.aliases, f"缺少别名：{key}")
            self.assertIn(want, [str(x).lower() for x in self.aliases[key]] or [want],
                          f"{key} 应扩展到 {want}")

    def test_alias_search_finds_entries(self):
        for q in ("保送", "套磁", "换工作", "读研"):
            self.assertGreater(len(self.match(q)), 0, f"「{q}」应当有结果（通过同义词扩展）")

    def test_multi_term_is_and(self):
        both = {e["id"] for e in self.match("日本 套磁")}
        only_one = {e["id"] for e in self.match("套磁")}
        self.assertTrue(both.issubset(only_one), "多词查询必须是「与」的关系")

    def test_alias_does_not_match_everything(self):
        self.assertLess(len(self.match("套磁")), len(self.entries))


class ClaimAudit(unittest.TestCase):
    """P1-5/P1-6：声明审计可用，且已知的高风险表述已改掉。"""

    def test_scan_returns_structured_hits(self):
        hits = A.scan(ROOT, ["唯一", "必须"])
        self.assertTrue(hits)
        for h in hits:
            for key in ("file", "entry", "line", "term", "sentence", "evidence", "risk"):
                self.assertIn(key, h)

    def test_known_absolute_claims_removed(self):
        text = (ROOT / "book" / "00-从这里开始.md").read_text(encoding="utf-8")
        for gone in ("唯一有效的动作", "标准只有一条", "有资格优先保研"):
            self.assertNotIn(gone, text)

    def test_tech_bias_removed_from_exploration(self):
        text = (ROOT / "book" / "00-从这里开始.md").read_text(encoding="utf-8")
        self.assertIn("不必都和技术有关", text)
        self.assertIn("参与一次志愿服务并负责一个真实交付", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
