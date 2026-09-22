"""OpportunityHandbook 内容解析与校验（零依赖，仅用标准库）。

职责：
  * 解析 front matter 与条目 ```meta 块（一个极简 YAML 子集）
  * 扫描 book/、docs/、meta/ 下的所有正文文件
  * 校验：重复 id、缺标题、非法枚举、内部链接、last_verified
  * 产出站点使用的索引数据结构

不负责渲染 HTML，渲染在 mdrender.py 中。
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

REPO = {
    "name": "机会与成长指南",
    "slug": "OpportunityHandbook",
    "url": "https://github.com/Sver0411/OpportunityHandbook",
    "site_url": "https://sver0411.github.io/OpportunityHandbook",
    "radar_url": "https://github.com/Sver0411/OpportunityRadar",
}

STALE_DAYS = 365  # 超过 12 个月未重新核实，视为「可能需要重新核实」
SCAN_DIRS = ("book", "docs", "meta")
DOC_TYPES = ("intro", "chapter", "doc")
DOC_STATUS = ("complete", "partial", "planned")
ENTRY_STATUS = ("complete", "todo", "needs_review")

# 用户侧可见的文档状态：planned 只作为仓库内的内容路线图，不进导航、搜索与阅读序列
USER_VISIBLE_STATUS = ("complete", "partial")

# ---------------------------------------------------------------- 词表

FACETS: dict[str, dict] = {
    "stages": {
        "label": "人生阶段",
        "values": [
            ("highschool", "高中"),
            ("secondary_vocational", "中专 / 职校"),
            ("college", "专科"),
            ("undergraduate", "本科"),
            ("master", "研究生"),
            ("phd", "博士"),
            ("new_grad", "应届"),
            ("work_1_3", "工作 1–3 年"),
            ("work_3_5", "工作 3–5 年"),
            ("senior", "资深"),
            ("career_change", "转行"),
        ],
    },
    "topics": {
        "label": "方向",
        "values": [
            ("study", "升学"),
            ("job", "工作"),
            ("research", "科研"),
            ("competition", "竞赛"),
            ("project", "项目"),
            ("skill", "技能"),
            ("funding", "资助"),
            ("community", "社群"),
            ("startup", "创业"),
            ("explore", "探索"),
        ],
    },
    "outputs": {
        "label": "能换回什么",
        "values": [
            ("degree", "学历"),
            ("work_experience", "工作经历"),
            ("research_experience", "科研经历"),
            ("portfolio", "作品"),
            ("project", "项目"),
            ("income", "收入"),
            ("network", "人脉"),
            ("reputation", "声誉"),
            ("qualification", "资格"),
            ("optionality", "选择权"),
            ("paper", "论文"),
            ("recommendation", "推荐信"),
            ("award", "奖项"),
            ("public_contribution", "公开贡献"),
            ("leadership", "领导力"),
        ],
    },
    "effort": {
        "label": "投入",
        "values": [("low", "低"), ("medium", "中"), ("high", "高")],
    },
    "evidence": {
        "label": "证据类型",
        # UI 显示中文，内部 schema 仍是 official / research_backed / …（英文名见 EVIDENCE_EN）
        "values": [
            ("official", "官方规则"),
            ("research_backed", "研究支持"),
            ("industry_data", "行业数据"),
            ("experience_based", "实践经验"),
            ("uncertain", "证据不足"),
        ],
    },
}

# 中英对照：界面主显示中文，英文作为 tooltip / 兼容搜索用
EVIDENCE_EN = {
    "official": "Official",
    "research_backed": "Research-backed",
    "industry_data": "Industry-data",
    "experience_based": "Experience-based",
    "uncertain": "Uncertain",
}

# 条目状态与文档状态在界面上的说明（供页面与筛选页使用）
STATUS_NOTE = {
    "partial": "内容仍在补充",
    "planned": "尚未撰写正文",
}

VALID = {k: {v for v, _ in spec["values"]} for k, spec in FACETS.items()}
SINGLE_VALUE_FACETS = ("effort",)

# 首页问题列表：kind=question 的条目必须指向一个存在的内容条目
QUESTION_LINK_REQUIRED = True

# docs/<dir> → 「专题」下的二级分组。顺序即导航顺序。
SUBSECTIONS = [
    ("timelines", "时间线"),
    ("countries", "国家与地区"),
    ("careers", "行业与职业"),
    ("research", "科研方法"),
    ("competitions", "竞赛专题"),
    ("tools", "工具与模板"),
    ("sources", "来源与核实"),
]
SUBSECTION_LABELS = dict(SUBSECTIONS)
SUBSECTION_ORDER = {k: i for i, (k, _) in enumerate(SUBSECTIONS)}

# 章节顺序由各文件 front matter 的 section_order 决定，这里只定义一级分组名。
SECTION_LABELS = {
    "index": "目录",
    "meta": "内容规范",
    "docs": "专题",
}

# ---------------------------------------------------------------- 极简 YAML

_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")
_LIST_ITEM_RE = re.compile(r"^\s+-\s+(.*)$")


def _scalar(raw: str):
    v = raw.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_clean(x) for x in _split_inline(inner)]
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    return _clean(v)


def _split_inline(inner: str) -> list[str]:
    parts, buf, quote = [], "", None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    parts.append(buf)
    return parts


def _clean(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v.strip()


def parse_simple_yaml(text: str, issues: list[str] | None = None, where: str = "") -> dict:
    """解析标量、行内列表与缩进列表；不支持嵌套结构。

    fail-closed：无法识别的行、重复键、缩进（嵌套）结构、孤立列表项、
    引号或方括号不配对，都会记进 issues（由调用方升级为 warning/error），
    不做静默忽略——strict 模式下必须被发现。
    """
    def flag(msg: str, lineno: int) -> None:
        if issues is not None:
            prefix = f"{where}第 {lineno} 行: " if where else f"第 {lineno} 行: "
            issues.append(prefix + msg)

    data: dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if line[:1] in (" ", "\t"):
            flag(f"不支持嵌套结构（缩进行 {stripped[:40]!r}）", i + 1)
            i += 1
            continue
        if stripped.startswith("-"):
            flag(f"孤立的列表项 {stripped[:40]!r}，前面缺少键", i + 1)
            i += 1
            continue
        m = _KEY_RE.match(line)
        if not m:
            flag(f"无法识别的行 {stripped[:40]!r}", i + 1)
            i += 1
            continue
        key, raw = m.group(1), m.group(2)
        if key in data:
            flag(f"重复的键 {key!r}", i + 1)
        if raw.strip() == "":
            items, j = [], i + 1
            while j < len(lines):
                mm = _LIST_ITEM_RE.match(lines[j])
                if not mm:
                    break
                items.append(_clean(mm.group(1)))
                j += 1
            if items:
                data[key] = items
                i = j
                continue
            data[key] = ""
        else:
            if raw.count("[") != raw.count("]") or raw.count('"') % 2:
                flag(f"取值里的括号或引号不配对：{raw.strip()[:40]!r}", i + 1)
            data[key] = _scalar(raw)
        i += 1
    return data


_FM_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.S)


def split_front_matter(text: str, issues: list[str] | None = None) -> tuple[dict | None, str]:
    m = _FM_RE.match(text)
    if not m:
        return None, text
    return parse_simple_yaml(m.group(1), issues, "front matter "), text[m.end():]


# ---------------------------------------------------------------- 文本工具

_SLUG_DROP = re.compile(r"[^\w\u4e00-\u9fff\s-]", re.UNICODE)


def slugify(text: str) -> str:
    """标题 → 锚点：保留中日韩字符与字母数字，空格转连字符。"""
    s = _SLUG_DROP.sub("", text.strip())
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s.lower()


_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+?)(?:\s+\"[^\"]*\")?\)")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*(\S*)\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")


def strip_markdown(text: str) -> str:
    """把 Markdown 正文压成纯文本，用于搜索索引。"""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^\s*>\s?", "", line)
        line = _LIST_RE.sub(lambda m: m.group(3), line)
        line = re.sub(r"`([^`]*)`", r"\1", line)
        line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"\*\*([^*]*)\*\*", r"\1", line)
        line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line and set(line) - set("-|: "):
            out.append(line)
    return " ".join(out)


def first_paragraph(body: str) -> str:
    """取正文第一个「自然段」：跳过标题、列表、meta 块、引用与分隔线。"""
    for raw in strip_fenced(body).splitlines():
        s = raw.strip()
        if not s or s.startswith(("#", "-", "*", ">", "|", "`", "---")):
            continue
        text = strip_markdown(s)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        if len(text) >= 20:
            return text
    return ""


def entry_summary(meta_block: dict, body: str) -> str:
    """摘要：metadata.summary 优先；没有就用正文第一个自然段。

    正文不再被要求写成固定栏目，所以摘要也不依赖任何栏目名。
    """
    explicit = str((meta_block or {}).get("summary") or "").strip()
    if explicit:
        return re.sub(r"\s+", " ", explicit)
    return first_paragraph(body)


def first_sentence(body: str) -> str:
    """兼容旧调用：优先取「一句话」栏，取不到再退回第一个自然段。"""
    m = re.search(r"^-\s*一句话\s*[:：]\s*\n((?:\s{2,}.*\n?)+)", body, re.M)
    if not m:
        return first_paragraph(body)
    text = " ".join(x.strip() for x in m.group(1).splitlines() if x.strip())
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


# ---------------------------------------------------------------- 结构解析

def _fence_open(line: str):
    m = _FENCE_RE.match(line)
    if not m:
        return None
    return (m.group(1)[0], len(m.group(1)), (m.group(2) or "").strip())


def strip_fenced(text: str) -> str:
    """把围栏代码块的内容清空（保留行数），用于标题/链接扫描。"""
    out, fence = [], None
    for line in text.splitlines():
        if fence is None:
            f = _fence_open(line)
            if f:
                fence = f
                out.append("")
                continue
            out.append(line)
        else:
            closing = _fence_open(line)
            if closing and closing[0] == fence[0] and closing[1] >= fence[1] and not closing[2]:
                fence = None
            out.append("")
    return "\n".join(out)


def _is_group_heading(lines: list[str], i: int) -> bool:
    """判断第 i 行的 `## ` 是「章节分组标题」还是「文章小节标题」。

    约定：分组标题后面直接跟条目（或另一个分组），文章小节标题后面是正文。
    这样条目内部就可以自由使用 `##` 组织文章结构。
    """
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j >= len(lines):
        return True
    nxt = lines[j]
    return nxt.startswith("### ") or nxt.startswith("## ")


def split_entries(body: str) -> list[dict]:
    """把正文切成片段：普通文本块与条目块（### 标题 + meta 块 + 正文）。

    只有带 ```meta 块的 ### 标题才算条目；不带的 ### 视为普通小标题。
    围栏代码块内部的 ### 不会被当作标题。
    """
    lines = body.splitlines()
    segments: list[dict] = []
    buf: list[str] = []
    entry: dict | None = None
    fence = None
    group = ""  # 当前所属的 ## 分组标题，供侧栏导航使用

    def flush_entry():
        nonlocal entry
        if entry is not None:
            segments.append(entry)
            entry = None

    def flush_text():
        nonlocal buf
        if buf and any(x.strip() for x in buf):
            segments.append({"kind": "text", "lines": buf})
        buf = []

    i = 0
    while i < len(lines):
        line = lines[i]

        f = _fence_open(line)
        if f is not None:
            if fence is None:
                fence = f
            elif f[0] == fence[0] and f[1] >= fence[1] and not f[2]:
                fence = None
            (entry["lines"] if entry is not None else buf).append(line)
            i += 1
            continue

        hm = _HEADING_RE.match(line) if fence is None else None
        if hm and len(hm.group(1)) == 3:
            title = hm.group(2)
            k, meta, body_start = i + 1, None, i + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and lines[k].strip() in ("```meta", "``` meta"):
                j = k + 1
                meta_lines = []
                while j < len(lines) and not _FENCE_RE.match(lines[j]):
                    meta_lines.append(lines[j])
                    j += 1
                meta_issues: list[str] = []
                meta = parse_simple_yaml("\n".join(meta_lines), meta_issues,
                                         f"条目「{title}」的 meta 块")
                body_start = j + 1
            if meta is None:
                # 普通小标题：留在文本段里
                (entry["lines"] if entry is not None else buf).append(line)
                i += 1
                continue
            flush_entry()
            flush_text()
            entry = {"kind": "entry", "title": title, "meta": meta,
                     "meta_issues": meta_issues, "group": group, "lines": [], "line": i + 1}
            i = body_start
            continue
        if hm and len(hm.group(1)) <= 2:
            if hm.group(1) == "##" and not _is_group_heading(lines, i):
                # 条目内部的小节标题：留在条目正文里，让文章自己组织结构
                (entry["lines"] if entry is not None else buf).append(line)
                i += 1
                continue
            flush_entry()
            if len(hm.group(1)) == 1:
                group = ""
            elif len(hm.group(1)) == 2:
                group = hm.group(2)
            buf.append(line)
            i += 1
            continue
        if entry is not None:
            entry["lines"].append(line)
        else:
            buf.append(line)
        i += 1
    flush_entry()
    flush_text()
    return segments


def collect_headings(text: str) -> list[tuple[int, str]]:
    """收集标题（# 到 ####），用于目录与锚点校验；忽略代码块内的内容。"""
    found = []
    for line in strip_fenced(text).splitlines():
        hm = _HEADING_RE.match(line)
        if hm:
            found.append((len(hm.group(1)), hm.group(2)))
    return found


def walk_content_docs(root: Path) -> list[Path]:
    files: list[Path] = []
    for d in SCAN_DIRS:
        base = root / d
        if base.is_dir():
            files.extend(sorted(p for p in base.rglob("*.md")))
    return files


# ---------------------------------------------------------------- 文档模型

class Doc:
    def __init__(self, root: Path, path: Path):
        self.root = root
        self.path = path
        self.rel = path.relative_to(root).as_posix()
        self.location = self.rel[:-3]  # 去掉 .md
        self.raw = path.read_text(encoding="utf-8")
        self.front_issues: list[str] = []
        self.front, self.body = split_front_matter(self.raw, self.front_issues)
        self.front = self.front or {}
        self.segments = split_entries(self.body)
        self.entries = [s for s in self.segments if s["kind"] == "entry"]
        self.title = str(self.front.get("title") or self._fallback_title())
        self.status = str(self.front.get("status") or "complete")
        self.anchors: set[str] = set()
        for level, text in collect_headings(self.body):
            self.anchors.add(slugify(text))
        for e in self.entries:
            eid = (e["meta"] or {}).get("id")
            if eid:
                self.anchors.add(str(eid))
            self.anchors.add(slugify(e["title"]))

    def _fallback_title(self) -> str:
        for line in self.body.splitlines():
            hm = _HEADING_RE.match(line)
            if hm and len(hm.group(1)) == 1:
                return hm.group(2)
        return self.path.stem

    @property
    def route(self) -> str:
        return "#/doc/" + self.location

    def entry_route(self, entry_id: str) -> str:
        return f"{self.route}/{entry_id}"


def load_docs(root: Path) -> list[Doc]:
    return [Doc(root, p) for p in walk_content_docs(root)]


# ---------------------------------------------------------------- 校验

def _as_list(v) -> list[str]:
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return [str(x) for x in v if str(x).strip()]
    return [str(v)]


def validate(root: Path, docs: list[Doc]) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    ids: dict[str, str] = {}
    entries: list[dict] = []
    today = datetime.date.today()
    stale: list[dict] = []
    stats = {"complete": 0, "todo": 0, "questions": 0}

    def err(doc: Doc, msg: str):
        errors.append(f"{doc.rel}: {msg}")

    for doc in docs:
        f = doc.front
        # 元数据解析的 fail-closed：识别不了的写法不静默忽略
        for issue in doc.front_issues:
            warnings.append(f"{doc.rel}: {issue}")
        for e in doc.entries:
            for issue in e.get("meta_issues") or []:
                warnings.append(f"{doc.rel}: {issue}")
        if not f:
            err(doc, "缺少 front matter")
        for key in ("id", "title", "type"):
            if not f.get(key):
                err(doc, f"front matter 缺少必填字段 {key}")
        dtype = str(f.get("type") or "")
        if dtype and dtype not in DOC_TYPES:
            err(doc, f"type 取值非法：{dtype}")
        if doc.rel.startswith("book/") and dtype in ("chapter", "intro"):
            if not f.get("section"):
                err(doc, "front matter 缺少 section（一级导航分组）")
            if f.get("section_order") in (None, ""):
                err(doc, "front matter 缺少 section_order（决定导航顺序的整数）")
        if doc.status and doc.status not in DOC_STATUS:
            err(doc, f"status 取值非法：{doc.status}")
        lv = str(f.get("last_verified") or "")
        if dtype in ("chapter", "doc") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lv):
            err(doc, "front matter 的 last_verified 缺失或格式不是 YYYY-MM-DD")
        # 文档级 facet 校验：docs/ 专题页的 front matter 与条目用同一套枚举，
        # 非法取值不得静默进入索引（此前只校验条目，文档页漏掉了）
        if dtype in ("chapter", "doc", "intro"):
            for key in ("stages", "topics", "outputs", "evidence"):
                for v in _as_list(f.get(key)):
                    if v not in VALID[key]:
                        err(doc, f"front matter 的 {key} 取值非法：{v}")
            # 只有 docs/ 下的专题页（type: doc）参与筛选，因此必须写 stages；
            # 章节页（chapter/intro）的阶段由正文条目承担，不强制
            if (dtype == "doc" and f.get("nav") is not False
                    and not _as_list(f.get("stages"))):
                err(doc, "front matter 缺少 stages（筛选用的阶段维度）")

        doc_id = str(f.get("id") or "")
        if doc_id:
            if doc_id in ids:
                err(doc, f"文件 id 重复：{doc_id}（另见 {ids[doc_id]}）")
            ids[doc_id] = doc.rel

        # 章节文件名前缀与 order 一致性
        m = re.match(r"^(\d{2})-", doc.path.name)
        if m and f.get("order") is not None and str(f.get("order")) != str(int(m.group(1))):
            warnings.append(
                f"{doc.rel}: 文件名前缀 {m.group(1)} 与 front matter order={f.get('order')} 不一致"
            )

        for e in doc.entries:
            meta = e["meta"]
            if meta is None:  # 理论上不会发生：split_entries 只把带 meta 的标题当条目
                err(doc, f"条目标题「{e['title']}」缺少 ```meta 元数据块")
                continue
            eid = str(meta.get("id") or "")
            if not eid:
                err(doc, f"条目「{e['title']}」缺少 id")
                continue
            if eid in ids:
                err(doc, f"条目 id 重复：{eid}（另见 {ids[eid]}）")
            ids[eid] = doc.rel
            status = str(meta.get("status") or "")
            if status not in ENTRY_STATUS:
                err(doc, f"条目 {eid} 的 status 缺失或非法：{status!r}")
                status = status or "todo"
            title_meta = meta.get("title")
            if title_meta and str(title_meta) != e["title"]:
                err(doc, f"条目 {eid} 的 meta.title 与标题不一致")
            kind = str(meta.get("kind") or "entry")

            if kind == "question":
                stats["questions"] += 1
                link = str(meta.get("link") or "")
                if not link:
                    err(doc, f"问题条目 {eid} 缺少 link")
                entries.append({"id": eid, "kind": "question", "link": link, "title": e["title"],
                                "doc": doc.rel, "route": doc.entry_route(eid),
                                "group": e.get("group") or "",
                                "stages": _as_list(meta.get("stages")), "topics": _as_list(meta.get("topics")),
                                "status": status})
                continue

            if status == "complete":
                stats["complete"] += 1
                for key in ("stages", "topics", "outputs", "effort", "evidence", "last_verified"):
                    if not meta.get(key):
                        err(doc, f"条目 {eid} 缺少必填字段 {key}")
                for key in ("stages", "topics", "outputs", "evidence"):
                    for v in _as_list(meta.get(key)):
                        if v not in VALID[key]:
                            err(doc, f"条目 {eid} 的 {key} 取值非法：{v}")
                eff = _as_list(meta.get("effort"))
                for v in eff:
                    if v not in VALID["effort"]:
                        err(doc, f"条目 {eid} 的 effort 取值非法：{v}")
                if len(eff) != 1:
                    err(doc, f"条目 {eid} 的 effort 应为单值")
                elv = str(meta.get("last_verified") or "")
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", elv):
                    err(doc, f"条目 {eid} 的 last_verified 缺失或格式错误")
                else:
                    body_text = "\n".join(e["lines"])
                    m_body = re.search(r"最后核实\s*[:：]\s*(\d{4}-\d{2}-\d{2})", body_text)
                    if m_body and m_body.group(1) != elv:
                        err(doc, f"条目 {eid} 的正文「最后核实」({m_body.group(1)}) 与 meta ({elv}) 不一致")
                    if m_body is None:
                        # 正文不再强制固定栏目：写明「最后核实」或「来源与更新」都可以
                        pass
                    if not str(meta.get("summary") or "").strip() and not first_paragraph(
                            "\n".join(e["lines"])):
                        warnings.append(f"{doc.rel}: 条目 {eid} 没有 summary，正文也没有可用的首段，"
                                        f"搜索结果里会没有摘要")
                    try:
                        d = datetime.date.fromisoformat(elv)
                        if (today - d).days > STALE_DAYS:
                            stale.append({"id": eid, "title": e["title"], "last_verified": elv,
                                          "path": doc.rel, "route": doc.entry_route(eid)})
                    except ValueError:
                        err(doc, f"条目 {eid} 的 last_verified 不是合法日期")
                # 新写作模型下不再要求正文存在任何固定栏目；缺摘要已在上面单独告警。
            else:
                stats["todo"] += 1
            entries.append({
                "id": eid,
                "kind": "entry",
                "title": e["title"],
                "status": status,
                "doc": doc.rel,
                "path": doc.rel,
                "location": doc.location,
                "route": doc.entry_route(eid),
                "doc_title": doc.title,
                "section": _doc_section(doc),
                "group": e.get("group") or "",
                "order": doc.front.get("order"),
                "stages": _as_list(meta.get("stages")),
                "topics": _as_list(meta.get("topics")),
                "outputs": _as_list(meta.get("outputs")),
                "effort": (eff[0] if status == "complete" and eff else ""),
                "evidence": _as_list(meta.get("evidence")),
                "last_verified": str(meta.get("last_verified") or ""),
                "summary": entry_summary(e.get("meta") or {}, "\n".join(e["lines"])),
                "text": strip_markdown("\n".join(e["lines"]))[:4000],
            })

    # 内部链接（忽略代码块里的示例链接）
    known = {d.rel: d for d in docs}
    for doc in docs:
        for _, href in _LINK_RE.findall(strip_fenced(doc.raw)):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target, _, anchor = href.partition("#")
            if not target:
                continue
            resolved = (doc.path.parent / target).resolve()
            try:
                rel = resolved.relative_to(root.resolve()).as_posix()
            except ValueError:
                errors.append(f"{doc.rel}: 链接指向仓库外：{href}")
                continue
            if rel not in known:
                # 允许指向非正文文件（README / CONTRIBUTING / LICENSE 等），
                # 只要它真的在仓库里存在即可；这类文件不校验锚点。
                if resolved.is_file():
                    continue
                errors.append(f"{doc.rel}: 内部链接目标不存在：{href}")
                continue
            if anchor and anchor not in known[rel].anchors:
                errors.append(f"{doc.rel}: 内部链接锚点不存在：{href}")

    # 问题条目的 link 必须指向真实条目
    real_entry_ids = {e["id"] for e in entries if e["kind"] == "entry"}
    for q in entries:
        if q["kind"] == "question" and q.get("link") and q["link"] not in real_entry_ids:
            errors.append(f"{q['doc']}: 问题条目 {q['id']} 的 link={q['link']} 未指向任何条目")

    # README 必须包含首页问题标题（防止两处列表分叉）
    readme = root / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        for q in entries:
            if q["kind"] == "question" and q["status"] == "complete" and q["title"] not in text:
                warnings.append(f"README.md: 缺少首页问题「{q['title']}」")

    # 内容路线图必须列出所有 planned 文档（防止隐藏内容被遗忘）
    roadmap = root / "docs" / "ROADMAP.md"
    planned = [d for d in docs if d.status == "planned" and not doc_nav_hidden(d)]
    if planned and not roadmap.is_file():
        warnings.append("docs/ROADMAP.md 不存在：planned 文档需要有集中的内容路线图")
    elif planned:
        text = roadmap.read_text(encoding="utf-8")
        missing = [d.title for d in planned if d.title not in text]
        if missing:
            warnings.append(f"docs/ROADMAP.md: 未列出 {len(missing)} 个计划中的文档"
                            f"（例如 {', '.join(missing[:3])}）")

    stats["docs"] = len(docs)
    stats["planned_docs"] = len(planned)
    stats["user_docs"] = sum(1 for d in docs if doc_user_visible(d) and not doc_nav_hidden(d))
    stats["entries_total"] = len(entries)
    return errors, warnings, {"entries": entries, "ids": ids, "stale": stale, "stats": stats}


def _load_redirects(root: Path) -> dict:
    path = root / "meta" / "ia-redirects.json"
    if not path.is_file():
        return {"docs": {}, "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"docs": {}, "entries": {}}
    return {"docs": data.get("docs") or {}, "entries": data.get("entries") or {}}


def stale_threshold() -> str:
    return (datetime.date.today() - datetime.timedelta(days=STALE_DAYS)).isoformat()


# ---------------------------------------------------------------- 导航树

def _int(v, default: int = 0) -> int:
    try:
        return int(str(v))
    except (TypeError, ValueError):
        return default


def doc_nav_hidden(doc: Doc) -> bool:
    v = doc.front.get("nav")
    if v is None or v == "":
        return False
    return str(v).strip().lower() in ("false", "no", "0", "off")


def doc_user_visible(doc: Doc) -> bool:
    """planned 文档只在仓库里作内容路线图，不进用户侧导航、搜索与阅读序列。"""
    return doc.status in USER_VISIBLE_STATUS


def _doc_section(doc: Doc) -> str:
    """一级分组：一律优先读 front matter 的 section（IA 重构后 book 与 docs 都显式声明）。"""
    explicit = str(doc.front.get("section") or "").strip()
    if explicit:
        return explicit
    if doc.rel.startswith("docs/"):
        return SECTION_LABELS["docs"]
    if doc.rel.startswith("meta/"):
        return SECTION_LABELS["meta"]
    return "其它"


def _doc_subsection(doc: Doc) -> tuple[str, int]:
    explicit = str(doc.front.get("subsection") or "").strip()
    if explicit:
        return explicit, _int(doc.front.get("sub_order"), 500)
    head = doc.rel.split("/")[1] if "/" in doc.rel else ""
    if head in SUBSECTION_LABELS:
        return SUBSECTION_LABELS[head], SUBSECTION_ORDER[head]
    return "", 500


def _doc_section_order(doc: Doc) -> int:
    explicit = doc.front.get("section_order")
    if explicit not in (None, ""):
        return _int(explicit, 500)
    if doc.rel.startswith("docs/"):
        return 90
    if doc.rel.startswith("meta/"):
        return 95
    return 500


def _group_route(doc: Doc, label: str) -> str:
    """分组节点的入口：章节文档 + 该 ## 标题的锚点（与渲染时的 id 规则一致）。"""
    if not label:
        return doc.route
    return f"{doc.route}/{slugify(label)}"


def _group_nodes(doc: Doc, items: list[dict]) -> list[dict]:
    """文档内的 ## 分组节点。条目本身不进左栏，由正文与页内目录承担。"""
    groups: list[dict] = []
    index: dict[str, dict] = {}
    for e in items:
        label = e.get("group") or ""
        if label not in index:
            index[label] = {"kind": "group", "label": label,
                            "href": _group_route(doc, label), "status": doc.status,
                            "count": 0, "children": []}
            groups.append(index[label])
        index[label]["count"] += 1
    if len(groups) == 1 and not groups[0]["label"]:
        return []                       # 文档里没有 ## 分组：文档节点本身就是入口
    for g in groups:
        if not g["label"]:
            g["label"] = "本章条目"
    return groups


def _doc_node(doc: Doc, items: list[dict], with_groups: bool) -> dict:
    node = {"kind": "doc", "label": doc.title, "href": doc.route,
            "status": doc.status, "count": len(items), "children": []}
    if with_groups:
        groups = _group_nodes(doc, items)
        if groups:
            node["children"] = groups
    return node


def _count(node: dict) -> int:
    return node.get("count", 0) + sum(_count(c) for c in node.get("children", []))


def _first_doc_href(children: list[dict]) -> str:
    """取子树里第一个「文档级」链接（跳过条目级链接），用作分组标题的入口。"""
    for c in children or []:
        if c.get("kind") == "entry":
            continue
        if c.get("href"):
            return c["href"]
        h = _first_doc_href(c.get("children", []))
        if h:
            return h
    return ""


def _entry_href(entry_id: str, entry_doc: dict[str, str]) -> str:
    loc = entry_doc.get(entry_id)
    if not loc:
        return ""
    return "#/doc/" + loc + "/" + entry_id


def _target_href(target: dict, entry_doc: dict[str, str], docs_by_loc: set[str]) -> str:
    if not target:
        return ""
    t = target.get("type")
    if t == "entry":
        return _entry_href(target.get("entry_id") or "", entry_doc)
    if t == "doc":
        loc = target.get("location") or ""
        if loc not in docs_by_loc:
            return ""
        anchor = (target.get("anchor") or "").strip()
        return "#/doc/" + loc + ("/" + anchor if anchor else "")
    return ""


def build_nav_from_ia(docs: list[Doc], entries: list[dict]) -> tuple[list[dict], list[str]]:
    """用户侧导航树：完全由 meta/navigation.json 决定（Canonical IA）。

    不再从正文的 section / subsection / ## 标题推导层级；Markdown 只负责正文。
    返回 (nav, 未解析的节点路径列表)。
    """
    path_nav = Path(__file__).resolve().parent.parent / "meta" / "navigation.json"
    if not path_nav.is_file():
        return build_nav(docs, entries), []

    spec = json.loads(path_nav.read_text(encoding="utf-8"))
    entry_doc: dict[str, str] = {}
    entry_status: dict[str, str] = {}
    for e in entries:
        eid = str(e.get("id") or "")
        if eid:
            entry_doc.setdefault(eid, e.get("location") or "")
            entry_status[eid] = e.get("status") or ""
    def _norm_loc(loc: str) -> str:
        return loc[:-3] if str(loc).endswith(".md") else str(loc)

    docs_by_loc = {_norm_loc(d.rel) for d in docs}

    unresolved: list[str] = []

    def convert(nodes: list[dict], depth: int, trail: list[str]) -> list[dict]:
        out: list[dict] = []
        for n in nodes:
            title = n.get("title") or ""
            # 左栏显示名可与章节标题不同（nav_label）：不改变 title / nav_id / target
            label = n.get("nav_label") or title
            kids = n.get("children") or []
            target = n.get("target") or {}
            here = trail + [title]
            children = convert(kids, depth + 1, here) if kids else []
            kind = "section" if depth == 0 else ("entry" if not kids and target.get("type") == "entry"
                                                 else ("doc" if not kids else "group"))
            href = _target_href(target, entry_doc, docs_by_loc)
            # 只有「明确写了 target 却解析不到」或「叶子节点没有落脚点」才算问题；
            # 纯分组节点没有 target 是正常的，它的链接沿用第一个子节点。
            if (target and not href) or (not href and not kids):
                unresolved.append(" > ".join(here))
            href = href or first_href(children)
            node = {
                "kind": kind,
                "label": label,
                "title": title,
                "nav_id": n.get("nav_id") or "",
                "href": href,
                "children": children,
            }
            leaves = _leaf_count(node)
            if leaves:
                node["count"] = leaves
            out.append(node)
        return out

    def first_href(children: list[dict]) -> str:
        for c in children:
            if c.get("href"):
                return c["href"]
            h = first_href(c.get("children") or [])
            if h:
                return h
        return ""

    def _leaf_count(node: dict) -> int:
        kids = node.get("children") or []
        if not kids:
            return 1 if node.get("href") else 0
        return sum(_leaf_count(k) for k in kids)

    nav = convert(spec.get("items") or [], 0, [])
    return nav, unresolved


def build_nav(docs: list[Doc], entries: list[dict]) -> list[dict]:
    """旧版：从正文结构推导导航。navigation.json 存在时不再使用，仅作兜底。"""
    """用户侧导航树：一级「领域」→ 二级「问题组 / 专题分组」→ 三级「文档」。

    只收录 complete / partial 的文档；planned 不进导航。条目不再展开到左栏
    （条目的检索、筛选与深链由 index.json 的 entries 承担）。
    """
    by_doc: dict[str, list[dict]] = {}
    for e in entries:
        if e["kind"] != "question" and e["status"] == "complete":
            by_doc.setdefault(e["doc"], []).append(e)

    sections: dict[str, dict] = {}
    order: list[str] = []
    for doc in docs:
        if doc_nav_hidden(doc) or not doc_user_visible(doc):
            continue
        if str(doc.front.get("type") or "") not in ("intro", "chapter", "doc"):
            continue
        label = _doc_section(doc)
        sec = sections.get(label)
        if sec is None:
            sec = sections[label] = {"kind": "section", "label": label,
                                     "order": _doc_section_order(doc), "subs": {}, "docs": []}
            order.append(label)
        sec["order"] = min(sec["order"], _doc_section_order(doc))
        sub_label, sub_order = _doc_subsection(doc)
        bucket = sec["subs"].get(sub_label)
        if bucket is None:
            bucket = sec["subs"][sub_label] = {"kind": "subsection", "label": sub_label,
                                               "order": sub_order, "docs": []}
        bucket["docs"].append(doc)

    nav: list[dict] = []
    # 一级栏目按 section_order 排列（book 与 docs 混排时不能依赖文件路径顺序）
    for label in sorted(order, key=lambda l: (sections[l]["order"], l)):
        sec = sections[label]
        groups = sorted(sec["subs"].values(), key=lambda g: (g["order"], g["label"]))
        children: list[dict] = []

        if len(groups) == 1 and not groups[0]["label"]:
            # 章节型分组：一级是领域，二级是 ## 问题组
            docs_sorted = sorted(groups[0]["docs"], key=lambda d: (_int(d.front.get("order")), d.title))
            children = _section_children(docs_sorted, by_doc, with_groups=True)
        else:
            # 专题型分组：一级是领域，二级是专题分类，三级是具体文档
            for g in groups:
                docs_sorted = sorted(g["docs"], key=lambda d: (_int(d.front.get("order")), d.title))
                sub_children = _section_children(docs_sorted, by_doc, with_groups=False)
                if not sub_children:
                    continue
                sub = {"kind": "subsection", "label": g["label"],
                       "href": _first_doc_href(sub_children), "children": sub_children}
                sub["count"] = _count(sub)
                children.append(sub)

        if not children:
            continue                     # 该领域下暂时没有可读内容，整块隐藏

        node = {"kind": "section", "label": sec["label"], "children": children}
        node["href"] = _first_doc_href(children)
        node["count"] = _count(node)
        nav.append(node)
    return nav


def _section_children(docs_sorted: list[Doc], by_doc: dict, with_groups: bool) -> list[dict]:
    """一个分组内部：with_groups 时展开文档的 ## 分组，否则只给文档节点。"""
    if len(docs_sorted) == 1 and with_groups:
        doc = docs_sorted[0]
        items = by_doc.get(doc.rel, [])
        groups = _group_nodes(doc, items)
        return groups or [_doc_node(doc, items, with_groups=False)]

    return [_doc_node(d, by_doc.get(d.rel, []), with_groups) for d in docs_sorted]


def build_index(root: Path) -> tuple[dict, list[str], list[str]]:
    docs = load_docs(root)
    errors, warnings, extra = validate(root, docs)
    entries = extra["entries"]
    real_entries = [e for e in entries if e["kind"] == "entry" and e["status"] == "complete"]
    questions = [e for e in entries if e["kind"] == "question" and e["status"] == "complete"]

    nav, nav_unresolved = build_nav_from_ia(docs, entries)
    for p in nav_unresolved:
        warnings.append(f"navigation.json：节点无法解析到正文：{p}")

    index = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "repo": REPO,
        "stale_threshold": stale_threshold(),
        "stale_days": STALE_DAYS,
        "facets": {k: {"label": v["label"],
                       "values": [{"key": vv, "label": ll,
                                   **({"en": EVIDENCE_EN[vv]} if k == "evidence" and vv in EVIDENCE_EN else {})}
                                  for vv, ll in v["values"]],
                       "multi": k not in SINGLE_VALUE_FACETS}
                   for k, v in FACETS.items()},
        "status_note": STATUS_NOTE,
        "nav": nav,
        # IA 重构留下的旧地址 → 新地址（保证旧 hash 深链不失效）
        "redirects": _load_redirects(root),
        # docs：用户侧文档（无 planned），供阅读序列使用
        "docs": [
            {"location": d.location, "title": d.title, "route": d.route,
             "status": d.status, "summary": str(d.front.get("summary") or ""),
             "last_verified": str(d.front.get("last_verified") or "")}
            for d in docs if not doc_nav_hidden(d) and doc_user_visible(d)
        ],
        # all_docs：含 planned，仅供路由解析与元数据查询（保证旧深链不失效）
        "all_docs": [
            {"location": d.location, "title": d.title, "route": d.route,
             "status": d.status, "last_verified": str(d.front.get("last_verified") or "")}
            for d in docs if not doc_nav_hidden(d)
        ],
        # roadmap：planned 文档的清单（只在内容路线图页面呈现）
        "roadmap": [
            {"location": d.location, "title": d.title, "route": d.route,
             "section": _doc_section(d), "group": _doc_subsection(d)[0]}
            for d in docs if d.status == "planned" and not doc_nav_hidden(d)
        ],        "entries": [
            {k: v for k, v in e.items() if k != "kind" or True}
            for e in sorted(real_entries, key=lambda e: (str(e.get("order") or 0), e["doc"], e["title"]))
        ],
        "questions": [
            {"id": q["id"], "title": q["title"], "link": q["link"], "route": q["route"],
             "topics": q["topics"], "stages": q["stages"]}
            for q in questions
        ],
        "todos": [
            {"id": e["id"], "title": e["title"], "doc": e["doc"], "doc_title": e["doc_title"], "route": e["route"]}
            for e in entries if e["kind"] == "entry" and e["status"] != "complete"
        ],
        "stats": extra["stats"] | {"stale": len(extra["stale"])},
        "stale": extra["stale"],
    }
    return index, errors, warnings
