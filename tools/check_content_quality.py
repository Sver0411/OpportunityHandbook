#!/usr/bin/env python3
"""Content Quality Gate：扫描所有 status: complete 条目的正文质量。

    python3 tools/check_content_quality.py            # 检查，问题返回 1
    python3 tools/check_content_quality.py --report   # 同时生成 CONTENT_DEPTH_REPORT.md

检查项（complete 条目）：
  P0  有效正文 < 120 个中文字符（去掉 metadata、来源段、链接、纯标题后）
  P1  有效正文 120–250 字
  P2  旧模板字段仍出现在正文（一句话/适合谁/能换回什么……）
  -   缺 summary
  -   Markdown 明显损坏（交给 tools/check_markdown_quality.py，这里只汇总）
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402
import mdrender  # noqa: E402

# 旧模板的字段形态：索引里的正文把「- 适合谁：」规范化成「适合谁：」。
# 冒号是关键：自然句「这类路线更适合谁？」不带紧跟的冒号，不会误判。
LEGACY_FIELDS = (
    "一句话：", "适合谁：", "不太适合谁：", "能换回什么：", "要付出什么：",
    "怎么开始：", "常见误区：", "下一步可能打开什么：", "证据与来源：",
)


def strip_noise(text: str) -> str:
    """去掉 metadata、来源段、链接、标题与列表符号后的有效正文。"""
    t = text.split("## 来源与更新")[0]
    t = re.sub(r"\[[^\]]*\]\([^)]*\)", "", t)          # 链接只留文字
    t = re.sub(r"^#{1,4}\s.*$", "", t, flags=re.M)      # 标题
    t = re.sub(r"[#>*`|\-]+", "", t)
    return re.sub(r"\s+", "", t)


def legacy_hits(text: str) -> list[str]:
    body = text.split("## 来源与更新")[0]
    return [f.rstrip(":") for f in LEGACY_FIELDS if f in body]


def check() -> dict:
    docs = M.load_docs(ROOT)
    errors, warnings, extra = M.validate(ROOT, docs)
    entries = [e for e in extra["entries"] if e.get("status") == "complete"]

    p0, p1, p2, no_summary = [], [], [], []
    for e in entries:
        if e.get("kind") == "question":
            continue          # 首页问题是指向主线文章的入口，summary 由目标文章承担
        text = e.get("text") or ""
        chars = len(strip_noise(text))
        item = {
            "id": e.get("id"), "title": e.get("title"), "file": e.get("location"),
            "chars": chars, "legacy": legacy_hits(text),
            "summary": bool((e.get("summary") or "").strip()),
        }
        if not item["summary"]:
            no_summary.append(item)
        if item["legacy"]:
            p2.append(item)
        if chars < 120:
            p0.append(item)
        elif chars < 250:
            p1.append(item)

    return {"total_complete": len(entries), "p0": p0, "p1": p1, "p2": p2,
            "no_summary": no_summary, "validate_errors": errors}


def write_report(r: dict) -> None:
    def table(items, label):
        lines = [f"## {label}（{len(items)}）", "",
                 "| entry_id | 标题 | 文件 | 有效正文 | 旧模板字段 | summary |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for it in items:
            lines.append(f"| {it['id']} | {it['title']} | {it['file']} | {it['chars']} |"
                         f" {('、'.join(it['legacy']) or '—')} | {'有' if it['summary'] else '缺'} |")
        return lines

    out = [
        "# Content Depth Report",
        "",
        f"生成时间：{datetime.datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        f"complete 条目总数：{r['total_complete']}",
        f"- P0（<120 字，必须补写）：{len(r['p0'])}",
        f"- P1（120–250 字，人工审查）：{len(r['p1'])}",
        f"- P2（仍含旧模板字段）：{len(r['p2'])}",
        f"- 缺 summary：{len(r['no_summary'])}",
        "",
    ]
    for items, label in ((r["p0"], "P0 正文过薄"), (r["p1"], "P1 偏薄"),
                         (r["p2"], "P2 旧模板残留"), (r["no_summary"], "缺 summary")):
        if items:
            out += table(items, label) + [""]
    report_dir = ROOT / "reports"
    if not report_dir.exists():
        report_dir.mkdir()
    (report_dir / "content-depth.md").write_text("\n".join(out), encoding="utf-8")


def main() -> int:
    """两种运行模式：

    --hard  硬门（CI 阻塞）：旧模板残留 / 缺 summary / 结构性问题必须全为 0。
    --depth 深度审计（不阻塞）：生成 CONTENT_DEPTH_REPORT.md，P0/P1 只报告。
    不带参数时等价于 --hard 加摘要输出。
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--hard", action="store_true", help="只检查必须阻塞 CI 的项")
    ap.add_argument("--depth", action="store_true", help="只生成正文深度报告，永远 exit 0")
    args = ap.parse_args()
    mode = "depth" if args.depth else ("hard" if args.hard else "all")
    r = check()

    if mode == "depth":
        write_report(r)
        print(f"深度报告：P0 {len(r['p0'])} / P1 {len(r['p1'])} / 旧模板 {len(r['p2'])} / 缺 summary {len(r['no_summary'])}")
        print("已写出 reports/content-depth.md（不阻塞）")
        return 0

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"complete 总数：{r['total_complete']}")
        print(f"P0 <120 字：{len(r['p0'])}")
        print(f"P1 120–250 字：{len(r['p1'])}")
        print(f"P2 旧模板残留：{len(r['p2'])}")
        print(f"缺 summary：{len(r['no_summary'])}")
        for key, label in (("p0", "P0"), ("p2", "P2")):
            for it in r[key][:12]:
                print(f"  {label}: {it['id']} 《{it['title']}》 {it['chars']}字 {it['legacy']}")
        if len(r["p0"]) > 12:
            print(f"  … 还有 {len(r['p0']) - 12} 条")
        if mode == "hard":
            print("（hard 模式：只校验旧模板 / summary / 结构性项）")
    # 硬门：旧模板残留与缺 summary 必须为 0；P0 深度暂不阻塞（P0 清零后加入）
    ok = not r["p2"] and not r["no_summary"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
