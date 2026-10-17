#!/usr/bin/env python3
"""生成 downloads/ 下的 PDF / DOCX / XLSX，并写出 manifest.json。

设计约束：
- 全部从结构化内容生成，重复执行结果一致（可 diff、可复查）；
- PDF 用 reportlab 内置中文字体（STSong-Light），不依赖系统字体；
- 每个文件都在生成后立刻做一次「能否打开、有无内容」的自检；
- manifest 是站点下载卡片与下载中心的唯一数据源。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (BaseDocTemplate, Frame, Flowable, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "downloads"
TODAY = "2026-10-18"

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
FONT = "STSong-Light"
INK = colors.HexColor("#1f1f1f")
MUTED = colors.HexColor("#5f5f5f")
FAINT = colors.HexColor("#8a8a8a")
RULE = colors.HexColor("#d9d6cf")
BLUE = colors.HexColor("#2f5d8a")
AMBER = colors.HexColor("#9a6a20")
RED = colors.HexColor("#a33b36")


# ------------------------------------------------------------------ PDF
class CheckItem(Flowable):
    """一条可勾选的事项：左侧方框 + 右侧文字（可带一行说明）。"""

    def __init__(self, text: str, note: str = "", width: float = 470):
        super().__init__()
        self.p = Paragraph(text, ST["item"])
        self.n = Paragraph(note, ST["note"]) if note else None
        self.width = width

    def wrap(self, aw, ah):
        self.width = aw
        h = self.p.wrap(aw - 20, ah)[1]
        if self.n:
            h += 3 + self.n.wrap(aw - 20, ah)[1]
        self.height = h + 5
        return aw, self.height

    def draw(self):
        c = self.canv
        box = 8.2
        top = self.height - 12
        c.setStrokeColor(colors.HexColor("#7a7a7a"))
        c.setLineWidth(0.7)
        c.rect(1, top, box, box, stroke=1, fill=0)
        self.p.drawOn(c, 20, self.height - self.p.height - 4)
        if self.n:
            self.n.drawOn(c, 20, self.height - self.p.height - 4 - self.n.height - 2)


ST = {
    "kicker": ParagraphStyle("k", fontName=FONT, fontSize=8.5, leading=12, textColor=FAINT),
    "title": ParagraphStyle("t", fontName=FONT, fontSize=21, leading=30, textColor=INK, spaceAfter=6),
    "lead": ParagraphStyle("l", fontName=FONT, fontSize=10.5, leading=18, textColor=MUTED),
    "meta": ParagraphStyle("m", fontName=FONT, fontSize=9, leading=15, textColor=MUTED),
    "h2": ParagraphStyle("h2", fontName=FONT, fontSize=12.5, leading=19, textColor=BLUE,
                         spaceBefore=10, spaceAfter=4),
    "item": ParagraphStyle("i", fontName=FONT, fontSize=10.5, leading=17, textColor=INK),
    "note": ParagraphStyle("n", fontName=FONT, fontSize=8.8, leading=14, textColor=MUTED),
    "box": ParagraphStyle("b", fontName=FONT, fontSize=9, leading=16, textColor=MUTED),
}


class NumberedCanvas(pdfcanvas.Canvas):
    """两遍绘制，得到「第 X 页 / 共 Y 页」。"""

    def __init__(self, *a, **kw):
        self._title = kw.pop("doc_title", "")
        super().__init__(*a, **kw)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for st in self._pages:
            self.__dict__.update(st)
            self._footer(total)
            super().showPage()
        super().save()

    def _footer(self, total):
        w, _ = A4
        self.setStrokeColor(RULE)
        self.setLineWidth(0.5)
        self.line(20 * mm, 18 * mm, w - 20 * mm, 18 * mm)
        self.setFont(FONT, 8)
        self.setFillColor(FAINT)
        self.drawString(20 * mm, 13 * mm, f"机会手册 ｜ {self._title}")
        self.drawRightString(w - 20 * mm, 13 * mm, f"第 {self._pageNumber} 页 / 共 {total} 页")


def build_pdf(spec: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(path), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=24 * mm,
        title=spec["title"], author="机会手册", subject=spec["desc"],
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame])])

    story: list = []
    story.append(Paragraph(spec["kicker"], ST["kicker"]))
    story.append(Paragraph(spec["title"], ST["title"]))
    story.append(Paragraph(spec["lead"], ST["lead"]))
    story.append(Spacer(1, 8))

    meta = [["用途", spec["usage"]], ["适用", spec["audience"]],
            ["配套文章", spec["source"]], ["最近核实", spec["verified"]]]
    t = Table(meta, colWidths=[22 * mm, doc.width - 22 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("TEXTCOLOR", (0, 0), (0, -1), FAINT),
        ("TEXTCOLOR", (1, 0), (1, -1), MUTED),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#e8e5de")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    for sec in spec["sections"]:
        block: list = [Paragraph(sec["h"], ST["h2"])]
        for it in sec["items"]:
            if isinstance(it, tuple):
                block.append(CheckItem(it[0], it[1]))
            else:
                block.append(CheckItem(it))
        # 标题与首条不拆开，其余条目顺排，避免整段被推到下一页留下大片空白
        story.append(KeepTogether(block[:2]))
        story.extend(block[2:])

    if spec.get("tail"):
        story.append(Spacer(1, 10))
        box = Table([[Paragraph(spec["tail"], ST["box"])]], colWidths=[doc.width])
        box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9d6cf")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f5f1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(box)

    doc.build(story, canvasmaker=lambda *a, **kw: NumberedCanvas(*a, doc_title=spec["title"], **kw))


# ------------------------------------------------------------------ DOCX
def _cn_font(run, size=10.5, bold=False, color=None):
    run.font.name = "宋体"
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def _shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def _docx_footer(section, text):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    _cn_font(r, 8, color="8a8a8a")
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    p._p.append(fld)



def _set_table_widths(table, widths):
    """固定列宽：python-docx 只设 cell.width 会被 autofit 覆盖，必须同时写 tblGrid。"""
    limit = 16.4
    total = sum(widths)
    if total > limit:                     # 等比缩到正文宽度内，避免超出页边距
        widths = [w * limit / total for w in widths]
    table.autofit = False
    table.allow_autofit = False
    tbl = table._tbl
    tblPr = tbl.tblPr
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:w"), str(int(sum(widths) * 567)))
    tblW.set(qn("w:type"), "dxa")
    tblPr.append(tblW)
    grid = tbl.tblGrid
    for i, w in enumerate(widths):
        if i < len(grid.gridCol_lst):
            grid.gridCol_lst[i].set(qn("w:w"), str(int(w * 567)))
    for row in table.rows:
        for i, w in enumerate(widths):
            if i < len(row.cells):
                row.cells[i].width = Cm(w)

def build_docx(spec: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "宋体"
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    for s in doc.sections:
        s.top_margin = Cm(2.0)
        s.bottom_margin = Cm(2.0)
        s.left_margin = Cm(2.2)
        s.right_margin = Cm(2.2)
        _docx_footer(s, f"机会手册 · {spec['title']} · 第 ")

    p = doc.add_paragraph()
    _cn_font(p.add_run(spec["kicker"]), 8.5, color="8a8a8a")
    p = doc.add_paragraph()
    _cn_font(p.add_run(spec["title"]), 18, bold=True)
    p = doc.add_paragraph()
    _cn_font(p.add_run(spec["lead"]), 10, color="5f5f5f")

    info = doc.add_table(rows=0, cols=2)
    info.alignment = WD_TABLE_ALIGNMENT.LEFT
    for k, v in (("用途", spec["usage"]), ("适用", spec["audience"]),
                 ("配套文章", spec["source"]), ("最近核实", spec["verified"])):
        row = info.add_row().cells
        row[0].width = Cm(2.6)
        row[1].width = Cm(13.4)
        _cn_font(row[0].paragraphs[0].add_run(k), 8.5, color="8a8a8a")
        _cn_font(row[1].paragraphs[0].add_run(v), 8.5, color="5f5f5f")
        _shade(row[0], "F6F5F1")
    _set_table_widths(info, [2.6, 13.4])
    doc.add_paragraph()

    for sec in spec["sections"]:
        h = doc.add_paragraph()
        _cn_font(h.add_run(sec["h"]), 12, bold=True, color="2f5d8a")
        if sec.get("intro"):
            ip = doc.add_paragraph()
            _cn_font(ip.add_run(sec["intro"]), 9, color="5f5f5f")

        if sec.get("cols"):
            rows = sec.get("rows", 8)
            table = doc.add_table(rows=1, cols=len(sec["cols"]))
            table.style = "Table Grid"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, (name, width) in enumerate(zip(sec["cols"], sec["widths"])):
                cell = table.rows[0].cells[i]
                cell.width = Cm(width)
                _cn_font(cell.paragraphs[0].add_run(name), 9, bold=True)
                _shade(cell, "EDF1F6")
            for _ in range(rows):
                table.add_row()
            _set_table_widths(table, sec["widths"])
            doc.add_paragraph()
        else:
            for _ in range(sec.get("lines", 4)):
                line = doc.add_paragraph()
                _cn_font(line.add_run(" "), 10.5)
                line.paragraph_format.space_after = Pt(12)
                pPr = line._p.get_or_add_pPr()
                bdr = OxmlElement("w:pBdr")
                bottom = OxmlElement("w:bottom")
                bottom.set(qn("w:val"), "single")
                bottom.set(qn("w:sz"), "4")
                bottom.set(qn("w:color"), "D9D6CF")
                bdr.append(bottom)
                pPr.append(bdr)
            doc.add_paragraph()

    if spec.get("tail"):
        p = doc.add_paragraph()
        _cn_font(p.add_run(spec["tail"]), 8.5, color="8a8a8a")

    doc.save(str(path))


# ------------------------------------------------------------------ XLSX
HEAD_FILL = PatternFill("solid", fgColor="EDF1F6")
THIN = Side(style="thin", color="D9D6CF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def build_xlsx(spec: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    guide = wb.active
    guide.title = "使用说明"
    guide.column_dimensions["A"].width = 16
    guide.column_dimensions["B"].width = 88
    guide["A1"] = spec["title"]
    guide["A1"].font = Font(name="宋体", size=15, bold=True)
    guide["A2"] = spec["lead"]
    guide["A2"].font = Font(name="宋体", size=10, color="5F5F5A")
    guide["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    guide.row_dimensions[2].height = 46
    rows = [("用途", spec["usage"]), ("适用", spec["audience"]),
            ("配套文章", spec["source"]), ("最近核实", spec["verified"])]
    rows += [(k, v) for k, v in spec.get("howto", [])]
    r = 4
    for k, v in rows:
        guide.cell(r, 1, k).font = Font(name="宋体", size=9, color="8A8A82")
        c = guide.cell(r, 2, v)
        c.font = Font(name="宋体", size=9, color="3A3A36")
        c.alignment = Alignment(wrap_text=True, vertical="top")
        guide.row_dimensions[r].height = 30
        r += 1
    if spec.get("tail"):
        c = guide.cell(r + 1, 2, spec["tail"])
        c.font = Font(name="宋体", size=9, color="8A8A82")
        c.alignment = Alignment(wrap_text=True, vertical="top")
        guide.row_dimensions[r + 1].height = 44

    for sheet in spec["sheets"]:
        ws = wb.create_sheet(sheet["name"])
        ws.freeze_panes = "A2"
        cols = sheet["cols"]
        for i, (name, width) in enumerate(cols, start=1):
            c = ws.cell(1, i, name)
            c.font = Font(name="宋体", size=9, bold=True)
            c.fill = HEAD_FILL
            c.border = BORDER
            c.alignment = Alignment(wrap_text=True, vertical="center")
            ws.column_dimensions[get_column_letter(i)].width = width
        ws.row_dimensions[1].height = 30
        ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{2 + sheet.get('rows', 20)}"
        for r_i, row in enumerate(sheet.get("sample", []), start=2):
            for c_i, val in enumerate(row, start=1):
                cell = ws.cell(r_i, c_i, val)
                cell.font = Font(name="宋体", size=9, color="6B6B66" if r_i == 2 else "1F1F1F")
                cell.border = BORDER
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        last = 2 + sheet.get("rows", 20)
        for r_i in range(2, last):
            for c_i in range(1, len(cols) + 1):
                cell = ws.cell(r_i, c_i)
                cell.border = BORDER
                cell.font = Font(name="宋体", size=9)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[r_i].height = 24
        for ref, value in sheet.get("cells", {}).items():
            ws[ref] = value
            ws[ref].font = Font(name="宋体", size=9, bold=True)
            ws[ref].border = BORDER
        for col, formula in sheet.get("formulas", {}).items():
            for r_i in range(2, last):
                ws[f"{col}{r_i}"] = formula.replace("{row}", str(r_i))
        for col, fmt in sheet.get("numfmt", {}).items():
            for r_i in range(2, last):
                ws[f"{col}{r_i}"].number_format = fmt
        for v in sheet.get("validations", []):
            dv = DataValidation(type="list", formula1='"' + ",".join(v["options"]) + '"',
                                allow_blank=True, showDropDown=False)
            ws.add_data_validation(dv)
            dv.add(f"{v['col']}2:{v['col']}{last}")
        for rng in sheet.get("score_ranges", []):
            dv = DataValidation(type="whole", operator="between", formula1="1", formula2="5",
                                allow_blank=True, showErrorMessage=True,
                                error="请填 1–5 的整数", errorTitle="评分范围")
            ws.add_data_validation(dv)
            dv.add(rng)
        if sheet.get("total_row"):
            tr = last
            ws.cell(tr, 1, "合计").font = Font(name="宋体", size=9, bold=True)
            for col in sheet["total_row"]:
                ws[f"{col}{tr}"] = f"=SUM({col}2:{col}{last - 1})"
                ws[f"{col}{tr}"].font = Font(name="宋体", size=9, bold=True)
                ws[f"{col}{tr}"].border = BORDER
        ws.print_title_rows = "1:1"
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True

    wb.save(str(path))


# ------------------------------------------------------------------ 校验
def verify(path: Path) -> tuple[bool, str]:
    suffix = path.suffix.lower()
    size = path.stat().st_size
    if size < 2000:
        return False, f"文件过小（{size} B）"
    try:
        if suffix == ".pdf":
            raw = path.read_bytes()
            if not raw.startswith(b"%PDF-"):
                return False, "不是有效 PDF"
            pages = len(re.findall(rb"/Type\s*/Page[^s]", raw))
            text_len = len(re.findall(rb"stream", raw))
            if pages < 1 or text_len == 0:
                return False, "无页面或无内容流"
            return True, f"{pages} 页"
        if suffix == ".docx":
            d = Document(str(path))
            paras = len([p for p in d.paragraphs if p.text.strip()])
            cells = sum(len(t.rows) for t in d.tables)
            if paras < 3 and cells < 3:
                return False, "正文与表格为空"
            return True, f"{paras} 段 / {len(d.tables)} 表 / {cells} 行"
        if suffix == ".xlsx":
            from openpyxl import load_workbook
            wb = load_workbook(str(path))
            sheets = wb.sheetnames
            cells = sum(ws.max_row * ws.max_column for ws in wb.worksheets)
            if len(sheets) < 2 or cells < 20:
                return False, "工作表或内容不足"
            return True, f"{len(sheets)} 表 / {cells} 单元格"
    except Exception as e:  # noqa: BLE001
        return False, f"打开失败：{e}"
    return False, "未知格式"


def main() -> int:
    from downloads_spec import SPECS

    OUT.mkdir(parents=True, exist_ok=True)
    items, failures, reports = [], [], []
    for spec in SPECS:
        rel = spec["path"]
        path = ROOT / rel
        if spec["format"] == "pdf":
            build_pdf(spec, path)
        elif spec["format"] == "docx":
            build_docx(spec, path)
        elif spec["format"] == "xlsx":
            build_xlsx(spec, path)
        ok, info = verify(path)
        reports.append((rel, path.stat().st_size, info, ok))
        if not ok:
            failures.append((rel, info))
            continue
        items.append({
            "id": spec["id"], "title": spec["title"], "format": spec["format"],
            "path": rel, "desc": spec["desc"], "scene": spec["scene"],
            "article": spec["article"], "audience": spec["audience"],
            "note": info, "updated": TODAY,
        })

    manifest = {"generated": TODAY, "items": items}
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for rel, size, info, ok in reports:
        print(f"{'ok ' if ok else 'FAIL'} {rel:52s} {size/1024:6.1f} KB  {info}")
    print(f"\n{len(items)}/{len(SPECS)} 个文件通过自检")
    if failures:
        print("失败：", failures)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
