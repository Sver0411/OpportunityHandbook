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
import re
from pathlib import Path

REPO = {
    "name": "机会与成长指南",
    "slug": "OpportunityHandbook",
    "url": "https://github.com/Sver0411/OpportunityHandbook",
    "radar_url": "https://github.com/Sver0411/OpportunityRadar",
}

STALE_DAYS = 396  # 约 13 个月，超过视为「可能需要重新核实」
SCAN_DIRS = ("book", "docs", "meta")
DOC_TYPES = ("intro", "chapter", "doc")
DOC_STATUS = ("complete", "partial", "planned")
ENTRY_STATUS = ("complete", "todo", "needs_review")

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
        "values": [
            ("official", "Official"),
            ("research_backed", "Research-backed"),
            ("industry_data", "Industry-data"),
            ("experience_based", "Experience-based"),
            ("uncertain", "Uncertain"),
        ],
    },
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


def parse_simple_yaml(text: str) -> dict:
    """解析标量、行内列表与缩进列表；不支持嵌套结构。"""
    data: dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        m = _KEY_RE.match(line)
        if not m:
            i += 1
            continue
        key, raw = m.group(1), m.group(2)
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
            data[key] = _scalar(raw)
        i += 1
    return data


_FM_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.S)


def split_front_matter(text: str) -> tuple[dict | None, str]:
    m = _FM_RE.match(text)
    if not m:
        return None, text
    return parse_simple_yaml(m.group(1)), text[m.end():]


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


def first_sentence(body: str) -> str:
    """取条目正文里「一句话」字段的内容，作为索引摘要。"""
    m = re.search(r"^-\s*一句话\s*[:：]\s*\n((?:\s{2,}.*\n?)+)", body, re.M)
    if not m:
        return ""
    return " ".join(x.strip() for x in m.group(1).splitlines() if x.strip())


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
                meta = parse_simple_yaml("\n".join(meta_lines))
                body_start = j + 1
            if meta is None:
                # 普通小标题：留在文本段里
                (entry["lines"] if entry is not None else buf).append(line)
                i += 1
                continue
            flush_entry()
            flush_text()
            entry = {"kind": "entry", "title": title, "meta": meta,
                     "group": group, "lines": [], "line": i + 1}
            i = body_start
            continue
        if hm and len(hm.group(1)) <= 2:
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
        self.front, self.body = split_front_matter(self.raw)
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
                    m_body = re.search(r"^-\s*最后核实\s*[:：]\s*\n?\s*(\d{4}-\d{2}-\d{2})", body_text, re.M)
                    if m_body and m_body.group(1) != elv:
                        err(doc, f"条目 {eid} 的正文「最后核实」({m_body.group(1)}) 与 meta ({elv}) 不一致")
                    if not m_body:
                        warnings.append(f"{doc.rel}: 条目 {eid} 的正文缺少「最后核实」栏")
                    try:
                        d = datetime.date.fromisoformat(elv)
                        if (today - d).days > STALE_DAYS:
                            stale.append({"id": eid, "title": e["title"], "last_verified": elv,
                                          "path": doc.rel, "route": doc.entry_route(eid)})
                    except ValueError:
                        err(doc, f"条目 {eid} 的 last_verified 不是合法日期")
                if not first_sentence("\n".join(e["lines"])):
                    warnings.append(f"{doc.rel}: 条目 {eid} 的正文缺少「一句话」栏")
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
                "summary": first_sentence("\n".join(e["lines"])),
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

    stats["docs"] = len(docs)
    stats["entries_total"] = len(entries)
    return errors, warnings, {"entries": entries, "ids": ids, "stale": stale, "stats": stats}


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


def _doc_section(doc: Doc) -> str:
    """一级分组：docs/ 归入「专题」，meta/ 归入「内容规范」，book 章节读 front matter。"""
    if doc.rel.startswith("docs/"):
        return SECTION_LABELS["docs"]
    if doc.rel.startswith("meta/"):
        return SECTION_LABELS["meta"]
    return str(doc.front.get("section") or "").strip() or "其它"


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


def _entry_node(e: dict) -> dict:
    return {
        "kind": "entry",
        "label": e["title"],
        "id": e["id"],
        "href": e["route"],
        "status": e["status"],
        "count": 1 if e["status"] == "complete" else 0,
    }


def _doc_children(doc: Doc, items: list[dict], use_groups: bool) -> list[dict]:
    """items 为本文档的条目（不含问题条目）。use_groups 决定是否保留 ## 分组层。"""
    if not use_groups:
        return [_entry_node(e) for e in items]
    groups: list[dict] = []
    index: dict[str, dict] = {}
    for e in items:
        label = e.get("group") or ""
        if label not in index:
            index[label] = {"kind": "group", "label": label, "href": doc.route, "children": []}
            groups.append(index[label])
        index[label]["children"].append(_entry_node(e))
    # 只有一个匿名分组（文档里没有 ## 分组）时拍平，避免多余一层
    if len(groups) == 1 and not groups[0]["label"].strip():
        return groups[0]["children"]
    return groups


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


def build_nav(docs: list[Doc], entries: list[dict]) -> list[dict]:
    """构建「一级分组 → （二级分组）→ 文档 → ## 分组 → 条目」的导航树。"""
    by_doc: dict[str, list[dict]] = {}
    for e in entries:
        if e["kind"] != "question":  # 首页问答只在首页正文里呈现
            by_doc.setdefault(e["doc"], []).append(e)

    sections: dict[str, dict] = {}
    order: list[str] = []
    for doc in docs:
        if doc_nav_hidden(doc):
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
    for label in order:
        sec = sections[label]
        groups = sorted(sec["subs"].values(), key=lambda g: (g["order"], g["label"], ))
        multi_doc = sum(len(g["docs"]) for g in groups) > 1 or len(groups) > 1
        sec_href = ""

        if len(groups) == 1 and not groups[0]["label"]:
            # 普通章节：直接展开文档
            docs_sorted = sorted(groups[0]["docs"], key=lambda d: (_int(d.front.get("order")), d.title))
            children = _section_children(sec["label"], docs_sorted, by_doc, multi_doc)
            same = next((d for d in docs_sorted if d.title == sec["label"]), None)
            sec_href = same.route if same else _first_doc_href(children)
        else:
            children = []
            for g in groups:
                docs_sorted = sorted(g["docs"], key=lambda d: (_int(d.front.get("order")), d.title))
                sub = {"kind": "subsection", "label": g["label"],
                       "children": _section_children(g["label"], docs_sorted, by_doc, True)}
                sub["href"] = _first_doc_href(sub["children"])
                sub["count"] = _count(sub)
                children.append(sub)

        node = {"kind": "section", "label": sec["label"], "children": children}
        node["href"] = sec_href or _first_doc_href(children)
        node["count"] = _count(node)
        nav.append(node)
    return nav


def _section_children(label: str, docs_sorted: list[Doc], by_doc: dict, multi_doc: bool) -> list[dict]:
    """一个分组内部：单文档时展开其 ## 分组，多文档时每篇文档一个节点。"""
    if len(docs_sorted) == 1:
        doc = docs_sorted[0]
        return _doc_children(doc, by_doc.get(doc.rel, []), use_groups=True)

    out: list[dict] = []
    for doc in docs_sorted:
        items = by_doc.get(doc.rel, [])
        if doc.title == label:
            # 文档名与分组名相同（例如「从这里开始」）：拍平，不再多一层
            out.extend(_doc_children(doc, items, use_groups=False))
            continue
        node = {"kind": "doc", "label": doc.title, "href": doc.route,
                "children": _doc_children(doc, items, use_groups=False)}
        node["count"] = _count(node)
        out.append(node)
    return out


def build_index(root: Path) -> tuple[dict, list[str], list[str]]:
    docs = load_docs(root)
    errors, warnings, extra = validate(root, docs)
    entries = extra["entries"]
    real_entries = [e for e in entries if e["kind"] == "entry" and e["status"] == "complete"]
    questions = [e for e in entries if e["kind"] == "question" and e["status"] == "complete"]

    nav = build_nav(docs, entries)

    index = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "repo": REPO,
        "stale_threshold": stale_threshold(),
        "stale_days": STALE_DAYS,
        "facets": {k: {"label": v["label"],
                       "values": [{"key": vv, "label": ll} for vv, ll in v["values"]],
                       "multi": k not in SINGLE_VALUE_FACETS}
                   for k, v in FACETS.items()},
        "nav": nav,
        "docs": [
            {"location": d.location, "title": d.title, "route": d.route,
             "status": d.status, "summary": str(d.front.get("summary") or ""),
             "last_verified": str(d.front.get("last_verified") or "")}
            for d in docs if not doc_nav_hidden(d)
        ],
        "entries": [
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
