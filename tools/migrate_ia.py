#!/usr/bin/env python3
"""IA 重构：把 book/ 从「按主题分类」重组为「按人生推进顺序」的 12 个一级栏目。

做法：
  * 声明式目标结构（下面 PLAN），条目按 id 归属到新文件与新分组；
  * 条目正文原样搬移，只改它所在的文件与分组（不改内容）；
  * 记录重定向：旧文档 location → 新文档 location，旧条目 route → 新条目 route；
  * 重写仓库里的内部链接（旧文件名 → 新文件名，锚点保留）；
  * 删除被搬空的旧文件。

    python3 tools/migrate_ia.py --dry-run
    python3 tools/migrate_ia.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from refactor_book import parse as parse_doc  # noqa: E402
from meta import slugify  # noqa: E402

# ---------------------------------------------------------------- 目标结构
# (新文件名, front matter, [(分组标题, [条目 id 或 新建 stub 的 (id, 标题, 说明)]), ...])

def stub(eid: str, title: str, note: str) -> tuple:
    return ("stub", eid, title, note)


PLAN: list[tuple[str, dict, list]] = [
    ("00-从这里开始.md", dict(
        id="chapter-00-start", title="从这里开始", section="00 从这里开始", section_order=0, order=0,
        summary="这本指南怎么用、判断一个选择值不值得的四步框架，以及最常被搜到的几个问题。",
    ), [
        ("这本指南怎么用", [
            stub("guide-how-to-use", "这本指南怎么用", "说明三种读法：按主线读、按阶段进入、按专题查。"),
            stub("guide-no-single-path", "人生并不是只有一条标准路线", "说明为什么本书不按年龄和年份组织，以及非标准路线的合法性。"),
        ]),
        ("先做哪一步", ["start-first-step", "start-when-no-direction"]),
        ("怎么判断一个选择值不值得", [
            "judge-compare-two-opportunities", "judge-decline-good-opportunity",
            "judge-short-vs-long-term", "judge-opportunity-cost", "judge-cognitive-biases",
        ]),
        ("三个关键概念", [
            "judge-verifiable-outcomes",
            stub("judge-long-term-accumulation", "什么东西值得长期积累", "可跨场景复用的能力、可验证的成果、关系与声誉——以及为什么时间是它们的乘数。"),
            stub("judge-optionality", "什么叫未来选择权", "用「保留多少条路」评估一个决定，而不是只算当下的收益。"),
        ]),
        ("常见问题", [
            "q-grad-school", "q-baoyan-kaoyan", "q-competitions", "q-undergrad-research",
            "q-first-job", "q-promotion", "q-career-change", "q-certificates",
            "q-unknown-direction", "q-pay-to-win", "q-github-project", "q-offer",
            "q-compare-opportunities",
        ]),
    ]),

    ("01-先决定下一步往哪里走.md", dict(
        id="chapter-01-first-choice", title="先决定下一步往哪里走", section="01 先决定下一步往哪里走",
        section_order=10, order=1,
        summary="第一次面对教育与人生路线分流时，先认清有哪几条路，再谈怎么选。",
    ), [
        ("认识你面前的几条主要路线", [
            "paths-continue-study-default", "paths-direct-work", "paths-vocational-and-trades",
            "paths-overseas", "paths-military", "paths-volunteering", "paths-gap-year",
            "paths-freelance", "paths-startup",
        ]),
        ("选学校与选专业", [
            stub("choose-school-vs-major", "学校和专业哪个更重要", "先看目标行业怎么筛人，再决定把分数投给学校还是专业。"),
            stub("choose-city", "城市要不要纳入选择", "行业密度、实习机会与生活成本会长期影响你的选择面。"),
            stub("choose-major-mismatch", "如果第一次选择不理想怎么办", "转专业、辅修与双学位的可行性与代价。"),
        ]),
        ("专科与职业教育", [
            "study-zhuanshengben",
            stub("vocational-outcomes", "专科毕业后的主要出口", "就业、专升本、职业本科与技能路线的现实差别。"),
            stub("apprenticeship", "学徒制与技能路线", "把技能当成职业资本来积累的方式。"),
        ]),
        ("家庭经济与教育成本", [
            "funding-student-types", "funding-scholarship-system", "funding-student-loan",
            stub("education-cost-budget", "为教育投入多少钱才合理", "把学费、生活费与机会成本一起算，而不是只算学费。"),
        ]),
        ("给自己保留退路", [
            "paths-switching-between-paths", "paths-work-then-study", "paths-part-time-study",
        ]),
    ]),

    ("02-在学校里先把基础打好.md", dict(
        id="chapter-02-foundations", title="在学校里先把基础打好", section="02 在学校里先把基础打好",
        section_order=20, order=2,
        summary="在校期间最该积累的东西：学业、通用能力、专业技能、语言与证书。",
    ), [
        ("学业", [
            stub("gpa-matters", "GPA 与排名到底重要吗", "什么时候它是硬门槛，什么时候它只是众多信号之一。"),
            stub("failing-courses", "挂科会带来什么影响", "对保研、留学与求职的实际影响范围。"),
            stub("coursework-depth", "专业课应该学到什么程度", "以能不能用来自我检验，而不是以分数。"),
        ]),
        ("认识真实世界", [
            stub("understand-industry", "怎么了解一个行业", "用招聘信息和从业者访谈替代行业报告的印象。"),
            stub("read-jd", "招聘 JD 应该怎么看", "把 JD 当成需求清单，反推自己缺什么。"),
            "explore-why-no-direction", "explore-low-cost-experiments", "explore-experiment-length",
            "explore-what-to-try", "explore-six-questions-after-each-try", "explore-when-to-continue",
            "explore-when-to-quit", "explore-assessments", "explore-failure-modes",
        ]),
        ("通用能力", [
            "skill-general",
            stub("skill-information-retrieval", "信息检索", "从官方来源找到答案，而不是从二手转述里找感觉。"),
            stub("skill-writing", "写作", "把一件事写清楚，是几乎所有岗位都用得上的能力。"),
            stub("skill-data", "数据能力", "用数据支持判断，而不是用数据装饰结论。"),
            stub("skill-ai-tools", "AI 与数字工具", "把它当效率工具使用，同时知道它的边界与核验方式。"),
        ]),
        ("专业技能", ["skill-what-to-learn", "skill-learning-vs-building", "skill-professional"]),
        ("语言", ["skill-english", "skill-language-tests", "skill-second-language"]),
        ("证书", [
            "certificate-what-is-worth-it", "skill-occupational-certificates",
            "skill-industry-certification", "skill-online-courses", "skill-bootcamp",
        ]),
    ]),

    ("03-开始积累真正能留下来的经历.md", dict(
        id="chapter-03-experience", title="开始积累真正能留下来的经历", section="03 开始积累真正能留下来的经历",
        section_order=30, order=3,
        summary="把时间换成以后仍然存在的成果：项目、竞赛、科研初体验、开源、社群与实习准备。",
    ), [
        ("项目与作品", [
            "project-what-is-real", "project-tutorial", "project-personal", "project-team",
            "project-what-counts-as-experience", "project-portfolio",
            "project-demo", "project-enterprise", "project-social",
            "project-data-test-metrics", "project-users-feedback",
        ]),
        ("竞赛", [
            "competition-what-worth-joining", "competition-award-vs-process",
            "competition-pay-to-win-recognition", "competition-mathematical-modeling",
            "competition-programming-contest", "competition-ai-data", "competition-business-case",
            "competition-startup-pitch", "competition-design", "competition-writing-speaking",
            "competition-hackathon", "competition-game-jam", "competition-vocational-skills",
            "competition-international",
        ]),
        ("科研初体验", [
            "research-what-is-research", "research-who-suits", "research-undergrad-start",
            "research-find-supervisor", "research-choosing-a-lab",
        ]),
        ("开源与公共贡献", [
            "opensource-first-contribution", "project-issue-pr", "project-code-review",
            "project-documentation", "project-maintainer", "project-sig-working-group",
        ]),
        ("社群与活动", [
            "community-student-chapter", "community-sig-working-group",
            "community-professional-association", "community-student-chapter-org",
            "community-meetup",
        ]),
        ("实习准备", ["internship-worth-it", "internship-types", "internship-how-to-find", "internship-remote"]),
    ]),

    ("04-当你开始面对第一次重要分流.md", dict(
        id="chapter-04-first-fork", title="当你开始面对第一次重要分流", section="04 当你开始面对第一次重要分流",
        section_order=40, order=4,
        summary="升学、留学、科研与实习之间怎么选：先定主线，再准备材料，最后谈成本与资助。",
    ), [
        ("先决定主线", [
            stub("choose-main-track", "升学还是工作", "先看目标岗位的学历门槛，再看自己缺的是学历还是经历。"),
            stub("home-or-abroad", "国内还是海外", "把成本、身份与毕业后去向放在一起比较。"),
            stub("research-or-industry", "科研还是产业", "用一次真实研究经历来判断，而不是用想象。"),
            stub("parallel-tracks", "怎么设置主线和备选", "主线的准备强度与备选的时间占比怎么分配。"),
        ]),
        ("国内升学", [
            "grad-school-worth-it", "study-baoyan", "study-kaoyan", "baoyan-vs-kaoyan",
            "study-academic-vs-professional", "study-cross-major", "study-second-round-interview",
            "study-transfer-adjustment", "study-retake-exam", "study-full-time-vs-part-time",
            "study-phd-worth-it", "research-phd-worth-it", "study-phd-application",
        ]),
        ("海外升学", [
            "overseas-is-it-for-me", "overseas-taught-vs-research-master", "overseas-phd-application",
            "overseas-exchange", "overseas-visiting-student", "overseas-summer-school",
            "overseas-research-internship", "overseas-language-test-timing",
            "overseas-admission-tests", "overseas-recommendation-letters", "overseas-sop-ps",
            "overseas-research-proposal", "overseas-contacting-professors",
            "overseas-funding", "overseas-total-cost", "overseas-visa",
            "overseas-degree-recognition",
        ]),
        ("深入科研", [
            "research-master", "research-literature-reading", "research-literature-review",
            "research-reproduction", "research-question", "research-experiment-design",
            "research-quantitative", "research-qualitative", "research-summer-program",
            "research-writing-and-submission", "research-authorship", "research-venues",
            "research-preprint", "research-ethics", "research-predatory",
        ]),
        ("实习进一步升级", [
            "internship-off-cycle", "internship-return-offer", "internship-research-intern",
            "internship-overseas", "internship-to-first-job",
        ]),
        ("资助", [
            "funding-fellowship-grant", "funding-stipend", "funding-travel-and-conference-grant",
            "funding-fee-waiver", "funding-research-grant", "funding-corporate-program",
            "funding-full-funding", "funding-free-opportunities", "funding-open-source",
        ]),
    ]),

    ("05-从学校走向第一份工作.md", dict(
        id="chapter-05-first-job", title="从学校走向第一份工作", section="05 从学校走向第一份工作",
        section_order=50, order=5,
        summary="校招怎么运作、简历与面试怎么准备、Offer 怎么比较与签约。",
    ), [
        ("校招是怎么运作的", ["campus-recruiting-timeline", "job-hunting-early-batch"]),
        ("找岗位", ["job-hunting-referral", "job-hunting-online-application", "job-hunting-experienced-hire"]),
        ("简历与作品", ["job-hunting-resume", "job-hunting-portfolio"]),
        ("笔试与面试", [
            "job-hunting-written-test", "job-hunting-interview", "job-hunting-hr-interview",
            "job-hunting-background-check",
        ]),
        ("Offer", [
            "offer-comparison", "job-hunting-salary-negotiation", "job-hunting-tripartite-agreement",
        ]),
        ("第一份工作", [
            "first-job-what-to-trade-for", "first-job-big-vs-small", "first-job-company-types",
            "first-job-pay-vs-growth", "first-job-city", "first-job-role-vs-industry",
        ]),
        ("如果没有顺利进入下一站", [
            "job-hunting-long-search",
            stub("lower-requirements", "要不要降低岗位要求", "分清楚降的是岗位门槛还是自己的底线。"),
            stub("blank-period", "空窗期怎么处理", "把空窗期变成有产出、能解释的一段时间。"),
        ]),
    ]),

    ("06-进入职场以后继续积累.md", dict(
        id="chapter-06-early-career", title="进入职场以后继续积累", section="06 进入职场以后继续积累",
        section_order=60, order=6,
        summary="从学会一份工作到独立负责：职场前几年的积累方式、行业关系与第一次重新选择。",
    ), [
        ("刚进入职场", [
            stub("probation-period", "怎么度过试用期", "先确认「做对」的标准，再谈做得更好。"),
            stub("learn-the-job", "怎么真正学会一份工作", "从模仿流程到理解为什么这么做。"),
            stub("understand-business", "怎么理解业务", "知道你的输出被谁使用、怎么被衡量。"),
            stub("work-with-manager", "怎么和直属领导合作", "把沟通节奏、预期与反馈方式先对齐。"),
            stub("find-workplace-mentor", "怎么找职场 Mentor", "从一次具体请教开始，而不是直接要一个导师。"),
            "promotion-first-years", "career-3-to-5-years",
        ]),
        ("从执行到独立负责", [
            stub("career-ownership", "Ownership 意味着什么", "对结果负责，而不是对任务负责。"),
            stub("career-visible-results", "怎么证明自己的成果", "把工作记录成可以被复述、被核对的形式。"),
            stub("career-bigger-projects", "怎么承担更大的项目", "用已有交付建立可靠性，再要更大的范围。"),
        ]),
        ("工作后继续学习", [
            stub("learn-after-work", "工作后还要不要继续学技能", "以「能不能用在手上」为标准筛选要学的东西。"),
            stub("certificate-after-work", "工作后考证", "只考目标岗位真正在用的那几本。"),
            stub("language-after-work", "工作后学语言", "把语言放进真实使用场景，而不是重新开始背单词。"),
            stub("side-project-after-work", "工作后做个人项目", "用业余项目验证方向，而不是消耗休息时间。"),
        ]),
        ("建立行业关系", [
            "community-mentorship", "community-networking", "community-reviewer-and-speaker",
            "community-industry-influence", "community-ambassador", "community-organizer",
            "community-reviewer", "community-speaker-cfp", "community-conference-volunteer",
        ]),
        ("第一次重新选择", [
            stub("first-job-hop", "什么时候适合第一次跳槽", "把跳槽要换回的东西写清楚，再开始看机会。"),
            "career-internal-transfer", "career-study-after-work", "career-work-overseas",
        ]),
    ]),

    ("07-当职业开始出现分岔.md", dict(
        id="chapter-07-career-fork", title="当职业开始出现分岔", section="07 当职业开始出现分岔",
        section_order=70, order=7,
        summary="已有职业资本之后怎么重新配置：晋升、专家与管理路线、跳槽、转行，以及再次进入教育体系。",
    ), [
        ("晋升", [
            "career-promotion-package", "career-influence",
            stub("career-not-promoted", "长期不晋升怎么办", "先判断差距在能力、机会还是评价体系。"),
        ]),
        ("专家路线", [
            "career-senior-ic-track",
            stub("career-staff-principal", "Staff / Principal 等角色", "资深专业序列的职责变化与常见要求。"),
        ]),
        ("管理路线", ["career-management-track"]),
        ("跳槽", [
            "career-job-hopping",
            stub("career-hop-pay", "平薪跳槽与涨薪跳槽", "什么时候值得为平台或经验接受平薪。"),
            stub("career-change-city", "换城市", "把生活成本、家庭因素与机会密度一起算。"),
        ]),
        ("转行", [
            "career-change-keep-capital", "career-transferable-capital", "career-bridge-opportunity",
            "career-pay-cut-transition",
        ]),
        ("再次进入教育体系", [
            stub("mba-mpa", "MBA / MPA 等职业学位", "职业学位解决的是网络与转型，不是知识缺口。"),
            stub("second-master", "第二硕士", "什么时候值得再读一个硕士，什么时候只是延迟决策。"),
        ]),
    ]),

    ("08-其他同样成立的人生路径.md", dict(
        id="chapter-08-other-paths", title="其他同样成立的人生路径", section="08 其他同样成立的人生路径",
        section_order=80, order=8,
        summary="自由职业、副业与创业：从验证需求到拿到第一批用户，以及路径之间的转换。",
    ), [
        ("自由职业", ["startup-freelance", "startup-freelance-orders", "startup-consulting"]),
        ("副业", ["startup-side-project", "startup-content-creation", "startup-indie-hacker", "startup-small-business"]),
        ("创业", [
            "startup-validate-before-quit", "startup-quit-to-start", "startup-company-registration",
            "startup-sole-proprietorship", "startup-accelerator", "startup-competition",
            "startup-funding",
        ]),
        ("路径之间怎么切换", [
            "side-project-to-main-business",
            stub("career-break-return", "职业中断后重新进入职场", "把中断期讲成一段有产出的经历。"),
            stub("second-career", "第二职业", "在主业之外建立第二条职业线的方式与边界。"),
        ]),
    ]),

    ("11-避坑.md", dict(
        id="chapter-11-pitfalls", title="避坑", section="11 避坑",
        section_order=110, order=11,
        summary="按领域整理常见低价值投入：升学与留学、求职与实习、科研、竞赛、证书、项目履历、创业与信息差。",
    ), [
        ("升学与留学", ["trap-guaranteed-admission", "trap-brand-name-only"]),
        ("求职与实习", ["trap-fake-internships-and-paid-research", "trap-expensive-job-coaching"]),
        ("科研", ["trap-buying-papers", "trap-predatory-journals"]),
        ("竞赛", ["trap-paid-competitions"]),
        ("证书与培训", ["trap-certificate-hoarding"]),
        ("项目与履历", ["trap-collecting-courses-and-half-projects", "trap-chasing-hype"]),
        ("信息差、机会焦虑与从众", ["trap-information-asymmetry", "trap-opportunity-anxiety"]),
    ]),
]

# docs/ 下的专题重新归入 09 / 10 两个一级栏目
DOCS_SECTION = {
    "docs/research": ("09 专题手册", "科研手册"),
    "docs/competitions": ("09 专题手册", "竞赛手册"),
    "docs/countries": ("09 专题手册", "国家与地区"),
    "docs/careers": ("09 专题手册", "行业与职业"),
    "docs/sources": ("09 专题手册", "来源与核实"),
    "docs/timelines": ("10 时间线与工具", "路径时间线"),
    "docs/tools": ("10 时间线与工具", "工具与模板"),
}
DOCS_SECTION_ORDER = {"09 专题手册": 90, "10 时间线与工具": 100}
SUBSECTION_ORDER = {
    "科研手册": 1, "竞赛手册": 2, "国家与地区": 3, "行业与职业": 4, "来源与核实": 5,
    "路径时间线": 1, "工具与模板": 2,
}


# 章节散文（含没有 meta 的 ### 小标题）需要跟着内容一起搬
PROSE_CARRY = {
    "00-从这里开始.md": ["02-怎么判断一个机会值不值得.md"],
}


def load_entries() -> tuple[dict[str, dict], dict[str, str]]:
    """把 book/ 下所有条目按 id 收集起来（保留原文），并收集各文件的散文。"""
    entries: dict[str, dict] = {}
    prose_of: dict[str, str] = {}
    for p in sorted((ROOT / "book").glob("*.md")):
        front, prose, items = parse_doc(p)
        blocks = []
        for e in items:
            if not e["id"]:
                # 没有 meta 的 ### 小标题：属于章节散文
                blocks.append(f"### {e['title']}\n\n{e['body_text']}")
                continue
            entries[e["id"]] = {"title": e["title"], "meta_text": e["meta_text"],
                                "body_text": e["body_text"], "src": p.name}
        text = "\n\n".join(x for x in ([prose.strip()] + blocks) if x)
        prose_of[p.name] = text
    return entries, prose_of


def render_entry(title: str, meta_text: str, body: str) -> str:
    return f"### {title}\n\n```meta\n{meta_text}\n```\n\n{body}\n"


def render_stub(eid: str, title: str, note: str) -> str:
    return (f"### {title}\n\n```meta\nid: {eid}\nstatus: todo\n```\n\n"
            f"> TODO：{note}\n")


def front_matter(meta: dict) -> str:
    keys = ["id", "title", "type", "section", "section_order", "order", "status",
            "topics", "stages", "summary", "last_verified"]
    lines = []
    for k in keys:
        if k in meta:
            lines.append(f"{k}: {meta[k]}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def intro_for(chapter_meta: dict) -> str:
    return f"# {chapter_meta['title']}\n\n{chapter_meta['summary']}\n"




def link_rewriter(id_home: dict[str, str], doc_map: dict[str, str]):
    """返回一个函数：把旧章节文件名（带或不带锚点）改写成新的归属文件。"""
    def fix(text: str) -> str:
        def repl(m):
            prefix, fname, anchor = m.group(1), m.group(2), m.group(3) or ""
            base = fname[:-3]
            if anchor:
                target = id_home.get(anchor)
                # 锚点是条目 id：跟着条目走；不是条目 id 就跟着文档走
                new_base = (target[:-3] if target else doc_map.get("book/" + base, "")[5:])
                if not new_base:
                    return m.group(0)
                return f"{prefix}{new_base}.md#{anchor}"
            new_loc = doc_map.get("book/" + base)
            if not new_loc:
                return m.group(0)
            return f"{prefix}{new_loc[5:]}.md"
        return re.sub(r"(\]\()(\d\d-[^)#]+\.md)(?:#([^)]*))?", repl, text)
    return fix

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    entries, prose_of = load_entries()
    used: set[str] = set()
    id_home: dict[str, str] = {}          # entry id -> 新文件名
    doc_redirect: dict[str, str] = {}     # 旧 location -> 新 location
    entry_redirect: dict[str, str] = {}   # 旧条目 route -> 新条目 route
    missing: list[str] = []

    planned_files: list[tuple[Path, str]] = []

    for fname, meta, groups in PLAN:
        meta = dict(meta)
        meta.setdefault("type", "chapter")
        meta.setdefault("status", "complete")
        meta.setdefault("topics", "[explore]")
        meta.setdefault("stages", "[highschool, secondary_school, college, undergraduate, master, new_grad, work_1_3, work_3_5, career_change]"
                        if False else "[college, undergraduate, master, new_grad, work_1_3, work_3_5, career_change]")
        meta.setdefault("last_verified", "2026-09-21")
        body = [front_matter(meta).rstrip(), "", intro_for(meta).rstrip(), ""]
        for src in PROSE_CARRY.get(fname, []):
            carried = prose_of.get(src, "").strip()
            if carried:
                body += [carried, ""]
        for label, items in groups:
            body.append(f"## {label}\n")
            for it in items:
                if isinstance(it, tuple) and it and it[0] == "stub":
                    body.append(render_stub(it[1], it[2], it[3]))
                    continue
                e = entries.get(it)
                if not e:
                    missing.append(it)
                    continue
                used.add(it)
                id_home[it] = fname
                body.append(render_entry(e["title"], e["meta_text"], e["body_text"]))
        text = "\n".join(body).rstrip() + "\n"
        planned_files.append((ROOT / "book" / fname, text))

    if missing:
        print("!! 目标结构里出现了找不到的条目 id：", missing[:10], file=sys.stderr)
        return 1

    leftover = sorted(set(entries) - used)
    if leftover:
        print(f"!! 有 {len(leftover)} 条条目没有进入新结构：{leftover[:10]}", file=sys.stderr)
        return 1

    # 旧的章节文件名 → 新文件名（按条目归属决定）
    old_docs = {e["src"] for e in entries.values()}
    for old in sorted(old_docs):
        ids = [i for i, e in entries.items() if e["src"] == old]
        homes = {}
        for i in ids:
            homes[id_home[i]] = homes.get(id_home[i], 0) + 1
        primary = max(homes.items(), key=lambda x: x[1])[0] if homes else old
        old_loc = "book/" + old[:-3]
        new_loc = "book/" + primary[:-3]
        if old_loc != new_loc:
            doc_redirect[old_loc] = new_loc
        for i in ids:
            old_route = f"#/doc/{old_loc}/{i}"
            new_route = f"#/doc/book/{id_home[i][:-3]}/{i}"
            if old_route != new_route:
                entry_redirect[old_route] = new_route

    print(f"新结构：{len(planned_files)} 个章节文件；条目 {len(used)} 条全部归位")
    print("重定向：文档 %d 条，条目 %d 条" % (len(doc_redirect), len(entry_redirect)))

    if args.dry_run:
        for path, text in planned_files:
            print(f"  [dry] {path.name}: {len(text.splitlines())} 行")
        return 0

    # 删除被搬空的旧章节文件（保留 00 与新文件同名的情况）
    new_names = {p.name for p, _ in planned_files}
    removed = []
    for p in sorted((ROOT / "book").glob("*.md")):
        if p.name == "README.md" or p.name in new_names:
            continue
        if re.match(r"^\d\d-", p.name):
            p.unlink()
            removed.append(p.name)

    fix_links = link_rewriter(id_home, doc_redirect)
    for path, text in planned_files:
        path.write_text(fix_links(text), encoding="utf-8")

    # 仓库里其它 md 文件（README、专题、规范）里的章节引用一并改写
    touched = []
    for p in sorted(ROOT.rglob("*.md")):
        if p.parts[-2] == ".workbuddy" or ".workbuddy" in p.parts:
            continue
        if p.parent == ROOT / "book" and p.name in new_names:
            continue
        raw = p.read_text(encoding="utf-8")
        fixed = fix_links(raw)
        if fixed != raw:
            p.write_text(fixed, encoding="utf-8")
            touched.append(str(p.relative_to(ROOT)))
    print("改写链接的文件：", len(touched), touched[:8])

    (ROOT / "meta" / "ia-redirects.json").write_text(json.dumps({
        "_comment": "IA 重构（2026-09）的旧→新重定向：保证旧 hash 深链不失效。",
        "docs": doc_redirect,
        "entries": entry_redirect,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("删除旧文件：", removed)
    print("写入 meta/ia-redirects.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
