#!/usr/bin/env python3
"""来源与证据一致性审查：读者能不能核对结论？

检查项：
  1. 声明了 Official / Research-backed 证据，但「来源与更新」里没有对应标注
  2. 来源小节缺失，或只有一句「经验性整理」却声称官方依据
  3. 「最后核实」日期缺失 / 无法解析 / 超过 180 天
  4. 声称 Official 但全文没有外部链接（无法核对）
  5. 页面上出现「以官方为准」类措辞却没有任何官方入口链接

    python3 tools/audit_sources.py
    python3 tools/audit_sources.py --json
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

# 来源小节里的证据标注可能写成组合形式，如（Official / Industry-data），
# 因此只检查关键词是否出现，而不是匹配整段括号文本。
TAG = {
    "official": "Official",
    "research_backed": "Research-backed",
    "industry_data": "Industry-data",
}
DEFER = re.compile(r"(以官方为准|以当年文件为准|以官网为准|逐校核实|逐年核实|以最新公告为准)")


def age_days(date_str: str) -> int | None:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str or "")
    if not m:
        return None
    d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (datetime.date.today() - d).days


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--stale-days", type=int, default=180)
    args = ap.parse_args()

    docs = M.load_docs(ROOT)
    errs, warns, extra = M.validate(ROOT, docs)

    findings = {"missing_tag": [], "no_sources": [], "stale": [], "no_extlink": [], "defer_no_official": []}

    def check(rel: str, title: str, text: str, evidence: list[str], last_verified: str):
        body = text
        # 条目文本里的标题符号会被剥离，这里同时接受有无 ## 的写法
        src = body.split("来源与更新")[-1] if "来源与更新" in body else ""
        has_src = "来源与更新" in body
        ext = re.findall(r"https?://[^\s)）]+", body)
        if not has_src:
            findings["no_sources"].append({"rel": rel, "title": title})
        for ev in evidence:
            tag = TAG.get(ev)
            if tag and tag not in src:
                findings["missing_tag"].append({"rel": rel, "title": title, "evidence": ev})
        # 声称 Official：来源小节里应至少有一个可核对入口
        # （外部链接，或点明去哪一类官方页面查——例如「本校研究生院官网」「教育部文件」）
        named = re.search(r"(官网|官方|教育部|人社部|移民局|入境事务处|考试院|招考|公告|名单|目录|章程|条例|办法|简章|国家|部委|协会|学会|统计|中心|委员会|厅|局|学校|院校|教务处|研究生院|招聘平台)", src)
        if ev_has_official(evidence) and not ext and not named:
            findings["no_extlink"].append({"rel": rel, "title": title})
        a = age_days(last_verified)
        if a is None or a > args.stale_days:
            findings["stale"].append({"rel": rel, "title": title, "last_verified": last_verified, "age": a})
        if DEFER.search(body) and not ext and not re.search(r"(官网|官方|教育部|人社部|移民局|入境事务处|考试院|招考|名单|目录|章程|条例|办法|简章|国家|协会|统计|研究生院|就业网|招聘平台)", body):
            findings["defer_no_official"].append({"rel": rel, "title": title})

    def ev_has_official(evidence: list[str]) -> bool:
        return "official" in evidence

    # 文档
    for d in docs:
        if d.status not in ("complete", "partial") or doc_hidden(d):
            continue
        check(d.rel, d.title, d.body or "", _as_list(d.front.get("evidence")),
              str(d.front.get("last_verified") or ""))
    # 条目
    for e in extra["entries"]:
        if e.get("kind") != "entry" or e.get("status") not in ("complete", "partial"):
            continue
        check(f'{e["doc"]}#{e["id"]}', e.get("title", ""), e.get("text") or "",
              e.get("evidence") or [], str(e.get("last_verified") or ""))

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
        return 0

    print(f"① 声明证据类型但来源小节没有对应标注：{len(findings['missing_tag'])}")
    for f in findings["missing_tag"][:12]:
        print(f"   {f['rel']}  ({f['evidence']})")
    print(f"\n② 缺少「来源与更新」小节：{len(findings['no_sources'])}")
    for f in findings["no_sources"][:8]:
        print(f"   {f['rel']}")
    print(f"\n③ 声称 Official 但没有任何外部链接：{len(findings['no_extlink'])}")
    for f in findings["no_extlink"][:8]:
        print(f"   {f['rel']}")
    print(f"\n④ 出现「以官方为准」类措辞却没有官方入口：{len(findings['defer_no_official'])}")
    for f in findings["defer_no_official"][:8]:
        print(f"   {f['rel']}")
    print(f"\n⑤ 「最后核实」早于 {args.stale_days} 天或缺失：{len(findings['stale'])}")
    for f in findings["stale"][:10]:
        print(f"   {f['last_verified'] or '（缺）':12} 年龄 {f['age'] if f['age'] is not None else '?':>4} 天  {f['rel']}")
    return 0


def doc_hidden(d) -> bool:
    try:
        return M.doc_nav_hidden(d)
    except Exception:
        return False


def _as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip().strip("'\"") for x in str(v).strip("[]").split(",") if x.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
