#!/usr/bin/env python3
"""语义错链检查：链接能打开，但指错主题（锚文本主题 ≠ 目标标题主题）。

    python3 tools/check_semantic_links.py

输出可疑链接清单，供人工确认后修正。
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import meta as M  # noqa: E402

TOPICS = {
    "国家与地区": ["国家", "地区", "签证", "留学国家", "移民"],
    "科研": ["科研", "研究", "导师", "文献", "论文", "实验", "暑研"],
    "竞赛": ["比赛", "竞赛", "奖项"],
    "项目": ["项目", "作品", "开源", "Demo", "Issue"],
    "工具模板": ["表", "模板", "工具", "检查表", "邮件模板", "清单", "对比表"],
    "时间线": ["时间线"],
    "职业行业": ["职业", "行业", "岗位", "职位", "晋升", "跳槽"],
    "升学": ["升学", "保研", "考研", "推免", "复试", "调剂", "留学申请"],
    "证书资格": ["证书", "资格", "认证"],
    "资助": ["资助", "奖学金", "Funding", "贷款", "学费", "Fee Waiver"],
    "简历": ["简历"],
    "面试": ["面试", "面试官", "行为面", "Case"],
    "社群协会": ["社群", "协会", "Meetup", "社团", "组织", "网络"],
    "能力技能": ["能力", "技能", "写作", "英语", "语言", "数据能力", "协作", "表达", "GPA"],
    "自由职业创业": ["自由职业", "创业", "副业", "独立开发", "客户", "融资", "孵化", "加速"],
}


def topics(text: str) -> set:
    return {t for t, words in TOPICS.items() if any(w in text for w in words)}


def main() -> int:
    docs = M.load_docs(ROOT)
    entry_title = {}
    doc_title = {d.location: d.title for d in docs}
    for d in docs:
        for seg in d.segments:
            if seg["kind"] != "entry":
                continue
            meta = seg["meta"] or {}
            eid = str(meta.get("id") or "")
            if eid:
                entry_title[(d.location, eid)] = seg["title"]

    suspicious = []
    checked = 0
    for p in sorted((ROOT / "book").glob("*.md")):
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"\[([^\]]{2,40})\]\(([^)\s]+\.md)(?:#([^)\s]+))?\)", text):
            label, target, anchor = m.group(1), m.group(2), m.group(3)
            rel = (p.parent / target).resolve().relative_to(ROOT).with_suffix("")
            loc = rel.as_posix()
            tt = entry_title.get((loc, anchor), "") if anchor else doc_title.get(loc, "")
            if not tt:
                continue
            checked += 1
            ta, tb = topics(label), topics(tt)
            if ta and tb and not (ta & tb):
                suspicious.append((p.name, label, loc + ("#" + anchor if anchor else ""), tt))

    print(f"检查链接 {checked} 条，其中语义不一致 {len(suspicious)} 条：")
    for s in suspicious:
        print(f"  {s[0]}：锚文本「{s[1]}」→ 目标 {s[2]}（目标标题：{s[3]}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
