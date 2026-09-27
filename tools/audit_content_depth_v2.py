#!/usr/bin/env python3
"""内容深度审计 v2（report-only）。

不再用单一字数阈值判定，而是同时看「有效长度 / 小节数 / 是否有行动步骤 /
是否有判断条件 / 是否有来源 / 是否只是列表或索引」，把页面分成：

    充分 / 可能偏薄 / 明显偏薄 / 索引型 / 占位 / 需人工检查

    python3 tools/audit_content_depth_v2.py            # 打印摘要并写出 reports/content-depth-v2.md
    python3 tools/audit_content_depth_v2.py --json
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402

INDEX_DIRS = ("docs/manuals/",)          # 索引型页面（手册的"继续深入"表格是刻意设计）
ACTION_HINTS = ("步骤", "做法", "流程", "清单", "模板", "示例", "例：", "怎么做", "操作",
                "第一步", "1.", "①", "检查", "执行")
JUDGE_HINTS = ("判断", "条件", "什么情况", "取决于", "边界", "不适合", "代价", "成本", "风险",
               "误区", "注意", "限制")


def strip_noise(text: str) -> str:
    t = re.sub(r"```meta.*?```", "", text, flags=re.S)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"^#+.*$", "", t, flags=re.M)
    t = re.sub(r"[|>*`\-\s]", "", t)
    return t


def classify(text: str, h2: int, rel: str, status: str, is_entry: bool) -> dict:
    chars = len(strip_noise(text))
    bullets = len(re.findall(r"^\s*[-*]\s", text, re.M))
    has_action = any(h in text for h in ACTION_HINTS)
    has_judge = any(h in text for h in JUDGE_HINTS)
    has_source = ("来源与更新" in text) or ("（Official）" in text) or ("Experience-based" in text)
    is_index = rel.startswith(INDEX_DIRS) and chars < 3000

    if status in ("planned", "todo"):
        kind = "占位"
    elif is_index and not has_action:
        kind = "索引型"
    elif chars < 250:
        kind = "明显偏薄"
    elif chars < 550 and h2 <= 3:
        kind = "可能偏薄"
    elif not has_action and not has_judge and chars < 1200:
        kind = "需人工检查"
    else:
        kind = "充分"

    return {"chars": chars, "h2": h2, "bullets": bullets, "action": has_action,
            "judge": has_judge, "source": has_source, "kind": kind,
            "rel": rel, "status": status, "is_entry": is_entry}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    docs = M.load_docs(ROOT)
    rows: list[dict] = []
    for d in docs:
        raw = (ROOT / d.rel).read_text(encoding="utf-8")
        body = raw.split("---", 2)[2] if raw.startswith("---") else raw
        if d.front.get("nav") is False:
            continue
        for seg in d.segments:
            if seg["kind"] != "entry":
                continue
            meta = seg["meta"] or {}
            text = "\n".join(seg["lines"])
            h2 = len(re.findall(r"^## ", text, re.M))
            rows.append(dict(classify(text, h2, d.rel, str(meta.get("status") or ""), True),
                             title=seg["title"], id=str(meta.get("id") or "")))
        # 文档级正文（专​​题页、工具页、时间线等）
        if str(d.front.get("type") or "") == "doc":
            text_only = re.sub(r"```meta.*?```", "", body, flags=re.S)
            h2 = len(re.findall(r"^## ", body, re.M))
            rows.append(dict(classify(text_only, h2, d.rel, d.status, False),
                             title=d.title, id=str(d.front.get("id") or "")))

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1

    order = ["明显偏薄", "可能偏薄", "需人工检查", "索引型", "占位", "充分"]
    thin = [r for r in rows if r["kind"] in ("明显偏薄", "可能偏薄", "需人工检查", "占位")]
    thin.sort(key=lambda r: r["chars"])

    if args.json:
        print(json.dumps({"counts": counts, "total": len(rows), "thin": thin},
                         ensure_ascii=False, indent=2))
        return 0

    lines = ["# 内容深度审计 v2", "",
             f"生成时间：{datetime.datetime.now().astimezone().isoformat(timespec='seconds')}",
             "",
             "判定不只看字数，同时看小节数、是否有行动步骤、是否有判断条件、是否有来源，"
             "并单独识别索引型页面与占位页面。本报告只报告，不阻塞构建。", "",
             f"检查对象：{len(rows)} 个页面（条目 + 专题页）", "",
             "| 分类 | 数量 |", "| --- | --- |"]
    for k in order:
        lines.append(f"| {k} | {counts.get(k, 0)} |")
    lines += ["", "## 需要处理的页面（按有效长度升序）", ""]
    if thin:
        lines += ["| 有效字数 | 小节 | 行动步骤 | 判断条件 | 来源 | 分类 | 页面 |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in thin[:80]:
            lines.append(
                f"| {r['chars']} | {r['h2']} | {'有' if r['action'] else '—'} | "
                f"{'有' if r['judge'] else '—'} | {'有' if r['source'] else '—'} | "
                f"{r['kind']} | {r['rel']} · {r['title']} |")
    else:
        lines.append("没有需要处理的页面。")
    lines += ["", "## 分类口径", "",
              "- **充分**：有内容深度，含行动步骤或判断条件，且有来源标注；",
              "- **可能偏薄**：有效长度偏短且小节很少；",
              "- **明显偏薄**：有效正文不足 250 字；",
              "- **索引型**：手册等以「继续深入」表格为主的页面（刻意设计，不计为偏薄）；",
              "- **占位**：`status: planned / todo`；",
              "- **需人工检查**：长度尚可但既无行动步骤也无判断条件，需要人读一遍判断。", "",
              "来源：仓库内文件的正文与 metadata，统计方式为脚本计算。 （Experience-based）", ""]

    out = ROOT / "reports" / "content-depth-v2.md"
    out.write_text("\n".join(lines), encoding="utf-8")

    print("内容深度审计 v2：")
    for k in order:
        print(f"  {k}：{counts.get(k, 0)}")
    print(f"报告已写出：reports/content-depth-v2.md（需处理 {len(thin)} 个页面）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
