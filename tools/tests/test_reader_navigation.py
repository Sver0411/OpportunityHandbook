"""Reader tasks must retain all published destinations and their identities."""
import unittest
import meta as M
import reader_navigation as R
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ReaderNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index, errors, _ = M.build_index(ROOT)
        assert not errors, errors
        cls.model = R.build(cls.index)
        cls.nodes = {n["id"]: n for n in R.walk([cls.model["map"]] + cls.model["topics"] + cls.model["atlases"] + [cls.model["references"]])}

    def test_no_published_leaf_is_lost_or_mounted_twice(self):
        source = {n["href"] for n in R.walk(self.index["nav"]) if not n.get("children")}
        refs = [ref["route"] for n in self.nodes.values() for ref in n["refs"]]
        self.assertEqual(set(refs), source)
        self.assertEqual(len(refs), len(set(refs)))
        self.assertEqual(set(self.model["owners"]), source)

    def test_every_completed_article_has_a_primary_task(self):
        for entry in self.index["entries"]:
            self.assertIn(entry["route"], self.model["owners"], entry["id"])

    def test_task_bundles_join_steps_tools_and_cases(self):
        mentor = self.nodes["supervisor"]
        ids = {ref["id"] for ref in mentor["refs"]}
        self.assertTrue({"research-find-supervisor", "doc-tool-advisor-shortlist", "tool-contacting-supervisor-email",
                         "depth-case-联系导师", "depth-playbook-第一次联系导师"}.issubset(ids))
        self.assertTrue({"understand", "guide", "tool", "steps", "case"}.issubset({r["role"] for r in mentor["refs"]}))

    def test_cross_stage_articles_follow_the_task(self):
        expected = {"work-grad-school-after-work": "continuing", "career-break-return": "change",
                    "second-career": "change", "research-literature-reading": "literature",
                    "research-writing-and-submission": "publishing", "freelance-stability": "business"}
        by_id = {e["id"]: e for e in self.index["entries"]}
        for entry, task in expected.items():
            self.assertEqual(self.model["owners"][by_id[entry]["route"]], task)

    def test_country_materials_have_one_entrance_and_distinct_labels(self):
        places = self.nodes["places"]["children"]
        self.assertEqual(len({n["label"] for n in places}), len(places))
        japan = next(n for n in places if n["label"] == "日本")
        self.assertEqual(len(japan["refs"]), 2)
        self.assertEqual(len({r["title"] for r in japan["refs"]}), 2)

    def test_topic_depth_is_independent_of_the_book_tree(self):
        graduate = self.nodes["graduate"]
        self.assertIn("kaoyan", {n["id"] for n in graduate["children"]})
        self.assertTrue(self.nodes["kaoyan"]["refs"])
        self.assertEqual(len(self.model["topics"]), 11)

    def test_single_catalogue_uses_existing_secondary_overviews(self):
        self.assertEqual(len(self.model["navigation"]), 15)
        self.assertEqual(self.model["navigation"][0]["label"], "内容地图")
        self.assertEqual([n["label"] for n in self.model["navigation"][1:12]], [n["label"] for n in self.model["topics"]])
        source_docs = {d["location"] for d in self.index["all_docs"]}
        for n in self.nodes.values():
            if n.get("overview"):
                self.assertIn(n["overview"].removeprefix("#/doc/"), source_docs)

    def test_every_first_level_group_has_an_authored_introduction(self):
        for n in self.model["topics"] + self.model["atlases"] + [self.model["resources"]]:
            self.assertGreaterEqual(n["intro_html"].count("<h2 "), 3, n["id"])
            self.assertGreater(len(n["intro_html"]), 600, n["id"])
            self.assertIn("<p>", n["intro_html"])

    def test_public_sector_is_a_primary_chapter_with_exam_stages(self):
        public = self.nodes["public-sector"]
        self.assertIn(public, self.model["topics"])
        self.assertEqual({n["id"] for n in public["children"]},
                         {"civil-choices", "civil-apply", "civil-written", "civil-interview", "civil-programs"})
        self.assertTrue(all(n["refs"] for n in public["children"]))

    def test_map_outline_follows_current_chapters_and_is_not_in_reference_library(self):
        roots = self.model["navigation"]
        self.assertEqual([n["label"] for n in roots[0]["children"]], [n["label"] for n in roots[1:]])
        self.assertEqual(self.model["owners"]["#/doc/book/18-内容地图"], "content-map")
        self.assertNotIn("map-all-content", {r["id"] for r in self.model["references"]["refs"]})

    def test_reading_sequence_tracks_continuous_chapters_and_independent_library(self):
        pages = self.model["reading_order"]
        self.assertEqual(pages[0]["id"], "content-map")
        self.assertEqual(pages[1]["id"], "choices")
        self.assertEqual(len({p["route"] for p in pages}), len(pages))
        self.assertFalse(any(p["id"].startswith("map-section-") for p in pages))
        mentor = next(i for i, p in enumerate(pages) if p["id"] == "supervisor")
        self.assertEqual(pages[mentor + 1]["id"], "literature")
        self.assertTrue(any(p["route"] == "#/chapter/graduate" for p in pages))
        self.assertFalse(any(p["id"] == "research-find-supervisor" for p in pages))
        self.assertTrue(any(p["id"].startswith("library-tool--") for p in pages))

    def test_guides_embed_directions_in_authored_paragraphs(self):
        for n in self.model["topics"] + self.model["atlases"] + [self.model["resources"]]:
            for child in n["children"]:
                self.assertIn('#/guide/' + child["id"], n["intro_html"], n["id"] + '/' + child["id"])
        for n in self.model["libraries"]:
            self.assertGreaterEqual(n["intro_html"].count('<h2 '), 3)
            self.assertIn('<p>', n["intro_html"])
            self.assertIn('#/doc/', n["intro_html"])

    def test_authored_guide_links_resolve_to_published_destinations(self):
        import re
        from html import unescape
        from urllib.parse import unquote
        pages = self.model["topics"] + self.model["atlases"] + [self.model["resources"]] + self.model["libraries"] + self.model["atlases"][1]["children"]
        destinations = {d["route"] for d in self.index["all_docs"]} | {e["route"] for e in self.index["entries"]}
        guides = set(self.nodes) | {n["id"] for n in self.model["libraries"]} | {"reference-library"}
        for page in pages:
            for raw in re.findall(r'href="([^"]+)"', page["intro_html"]):
                route = unquote(unescape(raw)).split("?", 1)[0]
                if route.startswith("#/guide/"):
                    self.assertIn(route.removeprefix("#/guide/"), guides, page["id"])
                elif route.startswith("#/doc/"):
                    self.assertTrue(route in destinations, page["id"] + ': ' + route)

    def test_unreviewed_source_groups_cannot_disappear(self):
        import copy
        index = copy.deepcopy(self.index)
        index["nav"].append({"title": "99 未归类", "label": "新内容", "href": "#/doc/new", "children": []})
        with self.assertRaisesRegex(ValueError, "assign"):
            R.build(index)

    def test_reading_order_is_not_mutated(self):
        import copy
        old = copy.deepcopy(self.index["nav"])
        R.build(self.index)
        self.assertEqual(self.index["nav"], old)


if __name__ == "__main__":
    unittest.main()
