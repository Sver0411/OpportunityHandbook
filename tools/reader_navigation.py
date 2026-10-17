"""Reader navigation: explicit topic/task ownership, independent of book order.

The canonical book navigation and published article IDs remain intact. Every
published leaf is assigned once; task bundles and resource indexes reuse links.
Unknown source groups fail the build so new material cannot silently disappear.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import quote

import mdrender
from meta import slugify


def node(key, label, summary="", children=()):
    return {"id": key, "label": label, "summary": summary,
            "children": list(children), "refs": []}


def catalog():
    return [
        node("choices", "选择与方向", "看见不同路线，算清投入与代价，用小行动验证方向。", [
            node("start-here", "先花 30 秒：从哪一种情况进入", "按你现在最头疼的事分流，一行就是一条最短路径。"),
            node("explore", "不知道方向时怎么开始", "了解行业、访问从业者，设计一次低成本体验。"),
            node("routes", "认识不同路线", "读书、工作、公共服务与其他生活安排。"),
            node("decide", "比较机会与代价", "先核实门槛，再比较成本、产出与未来选择权。"),
            node("fallback", "主线、备选与退出", "决定投入多少，以及什么时候调整或停止。"),
            node("resources", "资源约束与起步", "信息、时间、经济与关系的差距，分别怎么处理。"),
        ]),
        node("education", "升学与继续教育", "从学校与专业选择，到读研、留学和工作后进修。", [
            node("school", "学校、专业与城市"), node("vocational", "中职、专科与职业教育"),
            node("graduate", "国内读研", "读研是否值得，以及保研、考研的准备。", [
                node("kaoyan", "考研：择校、备考与录取")]),
            node("overseas-study", "海外升学与申请"), node("postgraduate", "读研期间与博士去向"),
            node("continuing", "工作后继续教育"), node("funding", "教育成本与资助"),
        ]),
        node("learning", "学习与技能", "学业、通用能力、语言考试、证书与数字工具。", [
            node("academic", "学业与学习安排"), node("skills", "学一项新技能"),
            node("general", "检索、写作与协作"), node("language", "英语与语言考试"),
            node("certificates", "证书与资格"), node("digital", "AI 与数字生活"),
        ]),
        node("research", "科研与学术", "从第一次接触科研，到研究问题、实验、论文与评审。", [
            node("research-first", "找到第一次科研机会"),
            node("supervisor", "导师与实验室", "把筛选、联系步骤、邮件模板和完整案例放在一起。"),
            node("literature", "文献与研究问题"), node("experiments", "实验、数据与复现"),
            node("publishing", "写作、投稿与评审"),
        ]),
        node("practice", "项目、竞赛与开源", "做出作品、参加竞赛，或完成一次真实的公共贡献。", [
            node("projects", "做出一个项目"), node("competitions", "参加一场竞赛"),
            node("opensource", "完成开源贡献"), node("community", "社群活动与公共贡献"),
        ]),
        node("jobs", "实习与求职", "从了解岗位、准备投递，到面试、比较 Offer 与入职。", [
            node("roles", "看懂岗位与要求"), node("internships", "找实习与选择实习"),
            node("applications", "校招、投递与简历"), node("interviews", "笔试与面试"),
            node("offers", "Offer、谈薪与入职核实"),
            node("job-setbacks", "没有顺利进入下一站"),
        ]),
        node("public-sector", "考公、考编与公共服务", "先核实报考条件与岗位，再安排笔试、面试及后续环节。", [
            node("civil-choices", "认识公务员、选调与事业单位"),
            node("civil-apply", "报考条件、选岗与报名"),
            node("civil-written", "行测、申论与笔试准备"),
            node("civil-interview", "面试、体检与考察"),
            node("civil-programs", "事业单位与基层项目"),
        ]),
        node("career", "职场成长与职业转换", "站稳脚跟、积累成果，判断晋升、跳槽和重新开始。", [
            node("onboarding", "入职与站稳脚跟"), node("ownership", "从执行到独立负责"),
            node("promotion", "晋升、专家与管理路线"), node("growth", "工作后的持续积累"),
            node("network", "职业关系与行业影响"), node("switching", "留下、转岗或跳槽"),
            node("change", "转行与重新进入职场"), node("overseas-work", "海外工作"),
        ]),
        node("independent", "自由职业、副业与创业", "验证需求、获得客户，算清报价、交付与经营成本。", [
            node("independent-start", "选择独立工作方式"), node("customers", "需求、用户与第一位客户"),
            node("delivery", "报价、交付与合作"), node("business", "现金流、规模与转主业"),
        ]),
        node("life", "生活与保障", "钱、健康、家庭与权益，是长期选择的现实条件。", [
            node("money", "日常财务与大额投入"), node("insurance", "社保、税与保险"),
            node("rights", "工作权益与纠纷"), node("wellbeing", "身体、心理与精力"),
            node("care", "家庭支持与照护"),
        ]),
    ]


# Chapter number + source group -> task. These are editorial decisions, not
# keyword guesses. New or renamed canonical groups require explicit review.
GROUP_TASKS = {
    "00": "decide",
    "01": {"认识你面前的几条主要路线": "routes", "给自己保留退路": "fallback",
           "选学校与选专业": "school", "专科与职业教育": "vocational",
           "中职与专科阶段的探索与作品": "projects", "家庭经济与教育成本": "funding",
           "家庭沟通与支持": "care", "不走常规的几条路": "routes",
           "没有资源时怎么起步": "resources", "专科生的上升通道": "vocational"},
    "02": {"学业": "academic", "开始认识真实世界": "explore", "通用能力": "general",
           "专业技能": "skills", "英语与其他语言 · 判断层": "language", "证书": "certificates",
           "校内资源与规则": "academic"},
    "03": {"项目与作品": "projects", "竞赛": "competitions", "科研初体验": "research-first",
           "开源与公共贡献": "opensource", "社群与活动": "community", "实习准备": "internships"},
    "04": {"先决定主线": "decide", "国内升学": "graduate", "海外升学": "overseas-study",
           "深入科研": "experiments", "读研期间怎么用这两年": "postgraduate",
           "读博与博士毕业": "postgraduate", "实习进一步升级": "internships", "资助": "funding"},
    "05": {"四六级怎么准备": "language", "四六级分数的用途与校内规定": "language",
           "留学语言考试怎么准备": "language", "专升本怎么准备": "vocational",
           "考研择校与信息透明度": "kaoyan", "考研科目复习与专业课": "kaoyan",
           "考研报名、初试与复试": "kaoyan", "考研调剂与二战": "kaoyan",
           "考公与考编怎么准备": "civil-apply", "笔试：行测与申论": "civil-written",
           "面试与后续环节": "civil-interview", "事业单位与基层项目": "civil-programs"},
    "06": {"校招是怎么运作的": "applications", "找岗位": "roles", "简历与作品": "applications",
           "笔试与面试": "interviews", "Offer": "offers", "入职前的核实": "offers",
           "第一份工作": "offers", "毕业前后的衔接": "offers",
           "如果没有顺利进入下一站": "job-setbacks", "失败之后": "job-setbacks"},
    "07": {"刚进入职场": "onboarding", "从执行到独立负责": "ownership",
           "工作后的学习与外部投入": "growth", "建立行业关系": "network",
           "海外工作": "overseas-work", "第一次重新选择": "switching"},
    "08": {"晋升": "promotion", "专家路线": "promotion", "管理路线": "promotion",
           "资深阶段：技能与收入": "growth", "跳槽": "switching", "转行": "change",
           "转行期的钱与关系": "change", "照护与职业节奏": "care",
           "再次进入教育体系": "continuing", "职业中段与年龄": "change"},
    "09": {"自由职业": "delivery", "副业": "independent-start", "创业": "customers"},
    "10": {"升学与申请": "overseas-study", "科研": "experiments", "竞赛": "competitions",
           "项目与作品": "projects", "开源": "opensource", "学习与数字生活": "skills",
           "求职": "applications", "职业成长": "ownership", "人脉与社群": "network",
           "证书与语言考试": "certificates", "创业与自由职业": "customers",
           "权益与制度": "rights", "参考与来源": "references"},
    "15": {"升学与留学": "graduate", "求职与实习": "applications",
           "科研、竞赛与证书": "competitions", "项目、创业与副业": "projects",
           "信息差与话术": "explore", "钱、健康与法律": "rights"},
    "16": {"拿到钱的第一年": "money", "社保、公积金与税": "insurance", "保险与风险": "insurance",
           "家庭与共同财务": "care"},
    "17": "wellbeing",
    "18": "content-map",
}

# Exact titles for resources whose old parent groups mix unrelated tasks.
RESOURCE_TASKS = {
    "高中毕业后的选择": "school", "高中到大学": "school", "中职升学": "vocational",
    "专升本": "vocational", "本科四年": "academic", "保研": "graduate", "考研": "kaoyan",
    "考公": "civil-apply", "留学申请": "overseas-study", "留学语言考试": "language",
    "四六级": "language", "博士申请": "postgraduate", "科研入门": "research-first",
    "实习准备": "internships", "校招": "applications", "入职第一年": "onboarding",
    "转行": "change", "海外工作与签证": "overseas-work", "离职与纠纷维权": "rights",
    "机会价值判断表": "decide", "Offer 对比表": "offers", "探索复盘模板": "explore",
    "职业资本盘点表": "growth", "转行 Bridge Plan": "change", "导师筛选表": "supervisor",
    "联系导师邮件模板": "supervisor", "留学选校表": "overseas-study", "考研择校对比表": "kaoyan",
    "上升通道对比表": "vocational", "四六级备考排期表": "language", "留学语言考试排期表": "language",
    "Research Question Canvas": "literature", "Baseline 与消融设计表": "experiments",
    "实验记录模板": "experiments", "论文精读表（Paper Reading Sheet）": "literature",
    "文献地图（Literature Map）": "literature", "岗位筛选表": "roles", "求职追踪表": "applications",
    "JD 拆解表": "roles", "面试复盘表": "interviews", "求职漏斗诊断表": "job-setbacks",
    "项目设计 Canvas": "projects", "项目测试计划模板": "projects", "Benchmark 记录表": "projects",
    "技能 Gap 矩阵": "skills", "Failure Log": "skills", "README 检查表": "projects",
    "项目发布检查表": "projects", "PR 检查表": "opensource", "客户沟通与需求确认表": "delivery",
    "自由职业报价单模板": "delivery", "日常账本与月度预算": "money", "转行现金流表": "change",
    "体检项目对照表": "wellbeing", "精力预算表": "wellbeing", "纠纷证据清单": "rights",
    "时间线检查表": "decide", "读博规划表": "postgraduate", "职校作品清单": "projects",
    "Case：第一次做真正的项目": "projects", "Case：本科生第一次进实验室": "research-first",
    "Case：从教程项目到工程作品（三种项目）": "projects", "Case：联系导师的完整过程": "supervisor",
    "Case：第一次开源贡献": "opensource", "Case：留学选校从几十个到一份名单": "overseas-study",
    "Case：把一次竞赛变成作品集与简历素材": "competitions", "Case：第一次找技术实习": "internships",
    "Case：两个 Offer 怎么选": "offers", "Case：第一次面试失败之后": "interviews",
    "Case：第一次转行": "change", "Case：第一次自由职业客户": "customers",
    "Case：第一次被欠薪": "rights", "Case：第一次自己买保险": "insurance",
    "Case：第一次去看心理科": "wellbeing", "Playbook：第一次做项目": "projects",
    "Playbook：第一次开源贡献": "opensource", "Playbook：第一次参加 Hackathon": "competitions",
    "Playbook：把一项新技术学到“能用”": "skills", "Playbook：第一次做实验与记录": "experiments",
    "Playbook：第一次写论文": "publishing", "Playbook：第一次联系导师": "supervisor",
    "Playbook：第一次找实习": "internships", "Playbook：第一次技术面试": "interviews",
    "Playbook：第一次谈薪": "offers", "Playbook：第一次做信息访谈": "explore",
    "Playbook：第一次准备考公笔试": "civil-written", "Playbook：第一次准备考研": "kaoyan",
    "Playbook：第一次考四六级": "language", "Playbook：第一次准备专升本": "vocational",
    "Playbook：第一次判断一个证书值不值得考": "certificates",
    "Playbook：第一次申请奖学金或研究资助": "funding", "Playbook：第一次接单": "delivery",
    "Playbook：第一次核对合同与社保": "rights", "Playbook：第一次处理劳动争议": "rights",
}

OVERRIDES = {
    "paths-public-sector": "civil-choices",
    "start-when-no-direction": "explore", "guide-how-to-use": "decide",
    "judge-starting-line": "resources", "judge-failure-worth-it": "fallback",
    "digital-online-identity": "digital", "digital-device-and-files": "digital", "skill-ai-tools": "digital",
    "research-ra": "research-first", "research-summer-program": "research-first",
    "overseas-research-internship": "research-first", "internship-research-intern": "research-first",
    "career-break-return": "change", "second-career": "change", "direction-again": "explore",
    "work-study-again": "continuing", "work-postgrad": "continuing",
    "research-choosing-a-lab": "supervisor", "research-literature-reading": "literature",
    "research-writing-and-submission": "publishing", "research-recommendation-letter": "publishing",
    "work-grad-school-after-work": "continuing", "work-overseas-job": "overseas-work",
    "work-parttime-study-cost": "continuing", "startup-freelance": "independent-start",
    "freelance-clients": "customers", "freelance-stability": "business",
    "freelance-client-concentration": "business", "startup-business-model": "business",
    "startup-incubator": "business", "startup-accelerator": "business", "startup-funding": "business",
    "side-project-to-main-business": "business", "depth-career-入职前三个月": "onboarding",
    "depth-career-学会一份工作": "onboarding", "depth-career-晋升材料": "promotion",
    "depth-career-IC与管理路线": "promotion", "depth-career-在职跳槽": "switching",
    "depth-ent-定价与报价": "delivery", "depth-ent-现金流与合同": "business",
    "depth-ent-从自由职业到工作室": "business", "manual-startup": "independent-start",
    "manual-research": "research-first",
}

# A document's stable location is clearer than a label for these cross-cutting guides.
DOC_TASKS = {
    "docs/research/联系导师与套磁": "supervisor",
    "docs/research/文献阅读与综述": "literature", "docs/research/论文写作与投稿": "publishing",
    "docs/research-deep/研究问题的提出": "literature", "docs/research-deep/论文精读方法": "literature",
    "docs/research-deep/同行评审与回复": "publishing",
    "docs/funding/全额资助与资金包": "funding", "docs/learning/用AI学习与工作": "digital",
}

ROLE_LABELS = {"understand": "判断与入门", "guide": "深入方法", "steps": "行动步骤",
               "timeline": "时间线", "tool": "工具与模板", "case": "完整案例", "risk": "风险与核实"}

OVERVIEW_DOCS = {
    "supervisor": "docs/research/联系导师与套磁", "literature": "docs/research/文献阅读与综述",
    "experiments": "docs/research/实验设计与数据", "publishing": "docs/research/论文写作与投稿",
}


def walk(nodes):
    for item in nodes:
        yield item
        yield from walk(item.get("children", []))


def build(index, root=None):
    topics = catalog()
    # 「先花 30 秒」不是分组，而是全站的分流入口：点一次直接落到 00 章首屏的分流表。
    # 它必须是「选择与方向」里的第一项——读者不必再展开子分组找标题。
    # overview 与 document 都指向 00 章：document 用于跳转，overview 让前端认得出
    # 「这一页属于 start-here」，否则会用「第一个以该文档开头的条目」猜主人（会猜错）。
    start_here = topics[0]["children"][0]
    start_here["document"] = "#/doc/book/00-从这里开始"
    start_here["overview"] = "#/doc/book/00-从这里开始"
    content_map = node("content-map", "内容地图", "从当前问题出发，找到合适的章节与下一步。")
    content_map["document"] = "#/doc/book/18-内容地图"
    atlases = [node("places", "国家与地区", "同一地区的制度说明与申请操作，在一个入口查找。"),
               node("careers", "行业与岗位", "分别按行业环境和具体工作职责查找。", [
                   node("industries", "按行业了解"), node("occupations", "按岗位了解")])]
    references = node("references", "术语与官方入口", "核对概念、查找原始来源和办理入口。")
    # 资料库按「角色」反查：时间线 / 工具 / 案例 / 步骤 / 风险。
    # 先建好并注册进 by_id，assign 时同步投放——同一篇文章既可按任务读，
    # 也可按类型查（「我想把所有表格找出来」）。缺了这一步，这一栏就是空的。
    resources = []
    for role in ["timeline", "tool", "case", "steps", "risk"]:
        resources.append({"id": "library-" + role, "label": ROLE_LABELS[role],
                          "role": role, "children": [], "refs": []})
    by_id = {n["id"]: n for n in walk([content_map] + topics + atlases + [references] + resources)}
    records = {e["route"]: e for e in index["entries"] + index["docs"]}
    owners = {}
    source_routes = set()

    def assign(leaf, chapter, group):
        route = leaf.get("href")
        if not route:
            raise ValueError("Reader navigation: missing route: " + leaf["label"])
        source_routes.add(route)
        record = records.get(route, {})
        title = leaf["label"]
        destination = None
        if chapter == "10" and group.startswith("国家与地区"):
            destination = "place-" + hashlib.sha1(title.encode()).hexdigest()[:10]
            if destination not in by_id:
                child = node(destination, title)
                by_id[destination] = child
                by_id["places"]["children"].append(child)
        elif chapter == "10" and group.startswith("行业与职业"):
            destination = "atlas-" + hashlib.sha1(route.encode()).hexdigest()[:10]
            child = node(destination, title)
            by_id[destination] = child
            by_id["industries" if "行业概览" in group else "occupations"]["children"].append(child)
        elif chapter in {"11", "12", "13", "14"}:
            destination = RESOURCE_TASKS.get(title.replace("「", "“").replace("」", "”")) or RESOURCE_TASKS.get(record.get("title", ""))
        elif chapter == "15":
            # 按条目 id 归属：同一组里的坑指向的任务不同（科研→发表、理财→钱、体检→健康）。
            destination = {"trap-guaranteed-admission": "overseas-study",
                           "trap-fake-internships-and-paid-research": "internships",
                           "trap-predatory-journals": "publishing",
                           "trap-paid-competitions": "competitions",
                           "trap-certificate-hoarding": "certificates",
                           "trap-collecting-courses-and-half-projects": "projects",
                           "trap-startup-side-gig": "business",
                           "trap-ai-shortcut": "digital",
                           "trap-information-asymmetry": "decide",
                           "trap-survivor-advice": "resources",
                           "trap-money-course": "money",
                           "trap-checkup-upsell": "wellbeing",
                           "trap-paid-legal-service": "rights"}.get(record.get("id")) \
                or (GROUP_TASKS["15"].get(group) if isinstance(GROUP_TASKS["15"], dict) else None)
        else:
            mapping = GROUP_TASKS.get(chapter)
            destination = mapping if isinstance(mapping, str) else (mapping or {}).get(group)
        destination = OVERRIDES.get(record.get("id"), DOC_TASKS.get(record.get("location"), destination))
        # Entry-specific ownership for the research lifecycle.
        if record.get("id") in {"research-find-supervisor", "research-choose-lab", "study-choose-supervisor"}:
            destination = "supervisor"
        if record.get("id") in {"research-literature", "research-question"}:
            destination = "literature"
        if record.get("id") in {"research-paper", "research-conference", "research-recommendation"}:
            destination = "publishing"
        if destination not in by_id:
            raise ValueError(f"Reader navigation: assign {chapter}/{group}/{title} to a task")
        if route in owners:
            if owners[route] != destination:
                raise ValueError("Reader navigation: conflicting ownership: " + route)
            return
        owners[route] = destination
        role = {"10": "guide", "11": "timeline", "12": "tool", "13": "case", "14": "steps", "15": "risk"}.get(chapter, "understand")
        summary = record.get("summary") or ""
        display_title = record.get("title") or title
        if chapter == "10" and group.startswith("国家与地区"):
            display_title += " · " + ("制度与概念" if "制度与概念" in group else "申请与操作")
        ref = {"title": display_title, "route": route,
               "id": record.get("id") or route, "role": role,
               "summary": summary, "source_group": group,
               "location": record.get("location") or ""}
        by_id[destination]["refs"].append(ref)
        # 同一篇按角色进资料库：读法不同，入口也就不同。
        library = by_id.get("library-" + role)
        if library is not None:
            library["refs"].append(ref)

    for section in index["nav"]:
        chapter = section["title"][:2]
        def visit(item, group=""):
            children = item.get("children", [])
            if not children:
                assign(item, chapter, group)
            else:
                for child in children:
                    visit(child, group or child["title"])
        visit(section)

    featured = ["explore", "supervisor", "internships", "kaoyan", "offers", "change"]
    for n in walk([content_map] + topics + atlases + [references] + resources):
        n["route"] = "#/guide/" + n["id"]
        n["count"] = len(n["refs"]) + sum(child.get("count", 0) for child in n["children"])
        if n["refs"]:
            preferred = OVERVIEW_DOCS.get(n["id"])
            first = next((ref for ref in n["refs"] if ref["location"] == preferred), n["refs"][0])
            # Existing book group pages already contain their overview and body.
            n["overview"] = "#/doc/" + first["location"] if first["role"] == "understand" and first["location"] else first["route"]
    def count(n):
        n["count"] = len(n["refs"]) + sum(count(c) for c in n["children"])
        return n["count"]
    for n in topics + atlases:
        count(n)
    resource_hub = node("reference-library", "资料与工具", "按用途查找时间线、工具、案例与官方来源。", resources + [references])
    resource_hub["route"] = "#/guide/reference-library"
    count(resource_hub)

    # Reading mode is explicit. Main task chapters and individual countries
    # assemble their existing bodies; resource and career catalogues keep
    # independent articles. A source article can therefore have both views.
    chapters = {}
    chapter_for = {}
    group_targets = {}
    def register_chapter(n, chapter_root):
        n["chapter_root"] = chapter_root
        n["chapter_anchor"] = "chapter-" + n["id"] if n["id"] != chapter_root else ""
        for child in n["children"]:
            register_chapter(child, chapter_root)
        for ref in n["refs"]:
            chapter_for[ref["route"]] = {"chapter": chapter_root, "section": ref["id"]}
            if ref["role"] == "understand" and ref["source_group"]:
                key = "#/doc/" + ref["location"] + "/" + slugify(ref["source_group"])
                group_targets.setdefault(key, set()).add(chapter_root)
    for root_node in topics + [atlases[0]]:
        for n in root_node["children"]:
            if n.get("document"):
                continue  # The 30-second routing page remains a portal.
            register_chapter(n, n["id"])
            def ordered_refs(item):
                return [ref for child in item["children"] for ref in ordered_refs(child)] + item["refs"]
            ordered = ordered_refs(n)
            chapters[n["id"]] = {"id": n["id"], "title": n["label"],
                "sections": [r["id"] for r in ordered],
                "sources": sorted({r["location"] for r in ordered})}

    def to_nav(n, standalone=False):
        standalone = standalone or n["id"] == "reference-library"
        children = [to_nav(child, standalone) for child in n["children"]]
        children += [{"kind": "entry" if ref["role"] == "understand" else "doc", "label": ref["title"],
                      "title": ref["title"],
                      "href": ("#/chapter/" + n["chapter_root"] + "?section=" + quote(ref["id"]) if n.get("chapter_root")
                               else ref["route"] + ("?from=" + n["id"] if standalone else "")),
                      "nav_id": n["id"] + "--" + ref["id"] if standalone else ref["id"],
                      "reading_anchor": bool(n.get("chapter_root")), "children": []}
                     for ref in n["refs"]]
        href = n.get("overview", n.get("route", "#/guide/" + n["id"]))
        if n.get("chapter_root"):
            href = "#/chapter/" + n["chapter_root"]
            if n["chapter_anchor"]:
                href += "?section=" + quote(n["chapter_anchor"])
        elif n.get("role"):
            href = "#/guide/" + n["id"]
        elif n.get("overview"):
            href += "?from=" + n["id"]
        return {"kind": "group" if children else "doc", "label": n["label"], "title": n["label"],
                "nav_id": n["id"], "href": href, "children": children,
                "reading_anchor": bool(n.get("chapter_anchor")),
                "count": n.get("count", 0)}

    navigation = [to_nav(n) for n in topics + atlases + [resource_hub]]
    for nav_root in navigation:
        nav_root["kind"] = "section"
        nav_root["href"] = "#/guide/" + nav_root["nav_id"]
    # These are authored chapter introductions, not generated link directories.
    # Keep their Markdown outside book/docs so existing article identities and
    # source coverage stay stable while the new catalogue gains its own guides.
    guide_root = Path(root) if root is not None else Path(__file__).resolve().parent.parent
    for group in topics + atlases + [resource_hub] + resources + atlases[1]["children"]:
        source = guide_root / "reader" / "overviews" / (group["id"] + ".md")
        if not source.is_file():
            raise ValueError("Reader navigation: missing chapter introduction: " + str(source))
        text = source.read_text(encoding="utf-8")
        if text.count("\n## ") < 3 or len(text) < 600:
            raise ValueError("Reader navigation: chapter introduction needs a complete article: " + str(source))
        mdrender.begin_document()
        mdrender.set_context(str(source.relative_to(guide_root)), {})
        group["intro_html"], _ = mdrender.render(text)
    map_source = (guide_root / "book" / "18-内容地图.md").read_text(encoding="utf-8").split("---", 2)[-1]
    mdrender.begin_document()
    _, map_heads = mdrender.render(map_source)
    map_nav = {"kind": "section", "label": content_map["label"], "title": content_map["label"],
               "nav_id": content_map["id"], "href": content_map["document"], "children": [
                   {"kind": "anchor", "label": h["text"], "title": h["text"],
                    "nav_id": "map-section-" + h["id"], "anchor": h["id"],
                    "href": content_map["document"] + "?section=" + quote(h["id"]), "children": []}
                   for h in map_heads if h["level"] == 2 and h["text"] != "来源与更新"]}
    navigation.insert(0, map_nav)
    # Page turns follow the displayed catalogue, including chapter introductions
    # and individual entries. Repeated overview/body routes appear only once.
    reading_order, seen = [], set()
    def order_pages(items, parent_href=""):
        for n in items:
            key = n["href"]
            repeats_parent = not n["children"] and key.split("?", 1)[0] == parent_href.split("?", 1)[0]
            if n["kind"] != "anchor" and not n.get("reading_anchor") and not repeats_parent and key not in seen:
                seen.add(key)
                reading_order.append({"id": n["nav_id"], "title": n["label"], "route": key})
            order_pages(n["children"], key)
    order_pages(navigation)
    return {"version": 3, "map": content_map, "topics": topics, "atlases": atlases, "references": references, "resources": resource_hub,
            "navigation": navigation,
            "chapters": chapters, "chapter_for": chapter_for,
            "chapter_aliases": {key: "#/chapter/" + next(iter(targets)) for key, targets in group_targets.items() if len(targets) == 1},
            "reading_order": reading_order,
            "libraries": resources, "roles": ROLE_LABELS, "featured": featured,
            "owners": owners, "coverage": {"source_routes": len(source_routes), "assigned_routes": len(owners)}}
