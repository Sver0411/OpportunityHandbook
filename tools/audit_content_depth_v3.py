#!/usr/bin/env python3
"""内容深度审计 v3（保守、中性分类，只用于发现问题）。

与 v2 的区别：**不再自动宣布某篇文章「已经充分」**。默认立场是「建议人工审查」，
只有在若干独立条件同时满足时才会归入「基本完整」，且长度较长的一律标为
「长文但仍需人工抽查」。判定维度：

  · 有效正文长度（去掉 metadata、来源段、链接、代码块、纯标题）
  · 小节数量与段落数量
  · 是否以列表为主（缺少解释性段落）
  · 是否有动作步骤 / 判断条件 / 代价与退出
  · 是否有来源小节
  · 是否只有定义（开头是「X 是……」且没有展开）
  · 是否与同章其他条目结构高度相似（模板化）

    python3 tools/audit_content_depth_v3.py            # 摘要 + 写 reports/content-depth-v3.md
    python3 tools/audit_content_depth_v3.py --json
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402

ACTION_HINTS = ("步骤", "第一步", "怎么做", "做法", "流程", "清单", "模板", "示例", "例：",
                "操作", "打开", "记录", "填写", "检查", "执行", "写法")
JUDGE_HINTS = ("判断", "条件", "什么情况", "取决于", "边界", "不适合", "代价", "成本",
               "风险", "注意", "限制", "止损", "退出", "什么时候")
DEFINITION_OPEN = re.compile(r"^[^\n]{0,40}(是|指|指的是)[^。]{0,60}。")
GENERIC_H2 = {"简介", "它是什么", "为什么重要", "怎么开始", "常见误区", "常见错误",
              "适合谁", "不适合谁", "总结", "小结", "风险", "结论"}


def strip_noise(text: str) -> str:
    t = re.sub(r"```meta.*?```", "", text, flags=re.S)
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"^#+.*$", "", t, flags=re.M)
    t = re.sub(r"[|>*`\-\s]", "", t)
    return t


def analyze(seg_lines: list[str]) -> dict:
    text = "\n".join(seg_lines)
    body = re.sub(r"```meta.*?```", "", text, flags=re.S)
    chars = len(strip_noise(body))
    h2 = re.findall(r"^## +(.+?)\s*$", body, re.M)
    paragraphs = [p for p in re.split(r"\n\s*\n", body) if p.strip() and not p.strip().startswith(("#", "-", "*", "|", "```"))]
    bullets = len(re.findall(r"^\s*[-*]\s", body, re.M))
    has_action = any(h in body for h in ACTION_HINTS)
    has_judge = any(h in body for h in JUDGE_HINTS)
    has_source = "来源与更新" in body or "（Official）" in body or "Experience-based" in body
    generic = [h for h in h2 if h.strip() in GENERIC_H2]
    return {"chars": chars, "h2": len(h2), "h2_list": h2, "paras": len(paragraphs),
            "bullets": bullets, "action": has_action, "judge": has_judge,
            "source": has_source, "generic_h2": generic,
            "definition_open": bool(DEFINITION_OPEN.match(body.strip())),
            "list_heavy": bullets >= 8 and len(paragraphs) <= 2}


def verdict(a: dict) -> str:
    """中性分类，默认偏保守。"""
    if a["chars"] < 400:
        return "明显需要深化"
    if a["h2"] <= 2 and a["paras"] <= 3:
        return "明显需要深化"
    if a["definition_open"] and a["chars"] < 800 and not a["action"]:
        return "明显需要深化"
    if a["list_heavy"] and not a["judge"]:
        return "明显需要深化"
    if (a["chars"] < 900 and a["h2"] <= 3) or not a["action"] or not a["judge"] or not a["source"]:
        return "建议人工审查"
    if a["chars"] >= 1800:
        return "长文但仍需人工抽查"
    if len(a["generic_h2"]) >= 2:
        return "建议人工审查"
    return "基本完整"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    docs = M.load_docs(ROOT)
    rows: list[dict] = []
    for d in docs:
        for seg in d.segments:
            if seg["kind"] != "entry":
                continue
            meta = seg["meta"] or {}
            if str(meta.get("status")) != "complete":
                continue
            # kind: question 的条目是「问题入口」（标题 + 链接），按设计不承载正文
            if str(meta.get("kind") or "entry") == "question":
                continue
            a = analyze(seg["lines"])
            a.update({"rel": d.rel, "title": seg["title"], "id": str(meta.get("id") or ""),
                      "verdict": verdict(a)})
            rows.append(a)

    counts = collections.Counter(r["verdict"] for r in rows)

    # 模板化：同章内 H2 组合出现次数
    combos = collections.Counter()
    h2_counter = collections.Counter()
    for r in rows:
        h2_counter.update(r["h2_list"])
        combos[" → ".join(r["h2_list"][:4])] += 1

    order = ["明显需要深化", "建议人工审查", "长文但仍需人工抽查", "基本完整"]
    todo = [r for r in rows if r["verdict"] in ("明显需要深化", "建议人工审查")]
    todo.sort(key=lambda r: r["chars"])

    if args.json:
        print(json.dumps({"counts": dict(counts), "total": len(rows), "todo": todo,
                          "top_h2": h2_counter.most_common(15),
                          "top_combos": combos.most_common(8)}, ensure_ascii=False, indent=2))
        return 0

    lines = ["# 内容深度审计 v3（保守版）", "",
             f"生成时间：{datetime.datetime.now().astimezone().isoformat(timespec='seconds')}",
             "",
             "本工具**不裁定文章是否合格**：它只把可能有问题的地方列出来供人工阅读。"
             "默认立场偏保守——只有同时满足「长度、小节数、动作步骤、判断条件、来源」"
             "才会标为「基本完整」，长文一律标为「需人工抽查」。", "",
             f"检查对象：{len(rows)} 个 complete 条目（book/ 主线）", "",
             "| 分类 | 数量 |", "| --- | --- |"]
    for k in order:
        lines.append(f"| {k} | {counts.get(k, 0)} |")
    lines += ["", "## 建议优先阅读的条目（按有效长度升序）", ""]
    if todo:
        lines += ["| 有效字数 | 小节 | 段落 | 列表行 | 动作 | 判断 | 来源 | 分类 | 条目 |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in todo:
            lines.append(f"| {r['chars']} | {r['h2']} | {r['paras']} | {r['bullets']} | "
                         f"{'有' if r['action'] else '—'} | {'有' if r['judge'] else '—'} | "
                         f"{'有' if r['source'] else '—'} | {r['verdict']} | "
                         f"{r['rel']} · {r['title']} |")
    else:
        lines.append("没有需要优先处理的条目。")

    lines += ["", "## 结构重复情况（模板化检查）", "",
              "出现次数最多的 H2（同一标题在多篇里重复出现）：", ""]
    for h, c in h2_counter.most_common(12):
        lines.append(f"- {h}（{c} 次）")
    lines += ["", "出现次数最多的前四个 H2 组合：", ""]
    for combo, c in combos.most_common(6):
        if c > 2:
            lines.append(f"- {c} 次：{combo}")
    lines += ["", "## 分类口径", "",
              "- **明显需要深化**：不足 400 字、或小节与段落都很少、或只有定义、或几乎只有列表；",
              "- **建议人工审查**：长度或结构勉强合格，但缺少动作步骤/判断条件/来源之一；",
              "- **长文但仍需人工抽查**：1800 字以上，脚本不做判断，必须人工读；",
              "- **基本完整**：各项条件都满足，仍建议按章节抽查。", "",
              "审计只是发现问题的工具，**不能作为「内容已经合格」的证明**。", ""]

    out = ROOT / "reports" / "content-depth-v3.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("内容深度审计 v3（保守版）：")
    for k in order:
        print(f"  {k}：{counts.get(k, 0)}")
    print(f"需优先阅读：{len(todo)} 个条目；报告：reports/content-depth-v3.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
