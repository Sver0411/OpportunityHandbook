#!/usr/bin/env python3
"""生成 assets/diagrams/ 下的流程图与信息图（SVG，可重复执行）。

只做纯静态 SVG：不依赖外部字体、不引用图片、文字全部是 <text>，
放大后仍清晰，屏幕阅读器与搜索引擎都能读到步骤文字。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "diagrams"

INK = "#1f1f1f"
MUTED = "#5f5f5f"
FAINT = "#8a8a8a"
LINE = "#d9d6cf"
BLUE_F, BLUE_S = "#eef3f8", "#2f5d8a"
AMBER_F, AMBER_S = "#fbf3e4", "#9a6a20"
RED_F, RED_S = "#fbeceb", "#a33b36"
GREEN_F, GREEN_S = "#edf4ee", "#3d6b45"
GRAY_F = "#f6f5f1"

FONT = "PingFang SC, Noto Sans CJK SC, Source Han Sans SC, Microsoft YaHei, sans-serif"


def cjk_len(s: str) -> float:
    """估算文字宽度：中文按 1em，西文按 0.55em。"""
    w = 0.0
    for ch in s:
        w += 1.0 if re.match(r"[\u3000-\u9fff\uff00-\uffef]", ch) else 0.55
    return w


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


class Canvas:
    def __init__(self, w: int, h: int, title: str):
        self.w, self.h = w, h
        self.parts: list[str] = []
        self.parts.append(f'<title>{esc(title)}</title>')

    def text(self, x, y, s, size=17, fill=INK, weight=400, anchor="start", maxw=None):
        if maxw is not None:
            need = cjk_len(s) * size
            assert need <= maxw + 1, f"文字超出容器: {s!r} 需 {need:.0f}px > {maxw}px"
        self.parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')

    def rect(self, x, y, w, h, fill="#ffffff", stroke=LINE, rx=10, sw=1.2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def line(self, x1, y1, x2, y2, stroke=LINE, sw=1.2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def arrow(self, x1, y1, x2, y2, stroke="#9c9c9c", sw=1.4):
        self.parts.append(
            f'<path d="M{x1:.0f} {y1:.0f} L{x2:.0f} {y2:.0f}" fill="none" '
            f'stroke="{stroke}" stroke-width="{sw}" marker-end="url(#a)"/>')

    def badge(self, x, y, n, fill=BLUE_S):
        self.parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="{fill}"/>')
        self.parts.append(
            f'<text x="{x:.0f}" y="{y + 4:.0f}" font-size="13" fill="#ffffff" '
            f'font-weight="500" text-anchor="middle">{n}</text>')

    def save(self, name: str):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" font-family="{FONT}">')
        defs = ('<defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" '
                'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
                '<path d="M2 1L8 5L2 9" fill="none" stroke="#9c9c9c" stroke-width="1.4" '
                'stroke-linecap="round" stroke-linejoin="round"/></marker></defs>')
        svg = "\n".join([head, defs] + self.parts + ["</svg>"])
        (OUT / name).write_text(svg + "\n", encoding="utf-8")


def header(c: Canvas, kicker: str, title: str, lead: str = ""):
    c.text(40, 52, kicker, 13, FAINT)
    c.text(40, 92, title, 27, INK, 500)
    if lead:
        c.text(40, 122, lead, 15, MUTED)


def footer(c: Canvas, y: int, note: str):
    """页脚统一加「示意图」标记：这些图是自绘的，不是官方页面截图。"""
    c.line(40, y, c.w - 40, y, LINE, 1)
    c.text(40, y + 28, "示意图 ｜ " + note, 13, FAINT, maxw=c.w - 80)


# ---------------------------------------------------------------- 1 新生报到
def new_student():
    c = Canvas(760, 570, "大学新生报到时间线")
    header(c, "场景 1 · 新生入学", "报到前、报到当天与第一个月",
           "四段时间，各自要做的事不同；先做完左边，再进下一段。")
    stages = [
        ("报到前 2 周", "核对通知书与须知\n办助学贷款回执\n户口迁移看个人\n证件照片装文件袋",
         "绿色通道与回执\n报到当天带去"),
        ("报到当天", "核验录取信息\n缴费或走绿色通道\n领钥匙与校园卡\n预约入学体检",
         "钱不够走绿色通道\n别因缴费卡住报到"),
        ("第一周", "看培养方案与选课\n班会与导师见面\n开通图书馆数据库\n社团讲座先看再选",
         "选课开放时间\n以本院通知为准"),
        ("第一个月", "跟上作业与测验\n记一个月账复盘\n有困难尽早申请\n决定社团去留",
         "资助申请通常看\n困难认定结果"),
    ]
    y = 156
    for i, (name, body, note) in enumerate(stages):
        x = 40 + i * 180
        c.rect(x, y, 164, 250, GRAY_F if i % 2 == 0 else "#ffffff")
        c.badge(x + 22, y + 26, i + 1)
        c.text(x + 42, y + 31, name, 16, INK, 500)
        for j, ln in enumerate(body.split("\n")):
            c.text(x + 14, y + 64 + j * 25, ln, 14, MUTED, maxw=140)
        c.rect(x, y + 178, 164, 58, AMBER_F, AMBER_S, rx=8, sw=0.8)
        for j, ln in enumerate(note.split("\n")):
            c.text(x + 12, y + 200 + j * 19, ln, 12.5, AMBER_S, maxw=142)
        if i < 3:
            c.arrow(x + 166, y + 28, x + 178, y + 28, "#c9c5bd")
    c.rect(40, 424, 680, 66, BLUE_F, BLUE_S, rx=8, sw=0.8)
    c.text(56, 448, "顺序不能反：先完成报到与注册，才有学籍；没有学籍，后面的选课、考试、资助都办不了。",
           14, BLUE_S, maxw=650)
    c.text(56, 472, "具体时间、地点、缴费方式以录取通知书和学校迎新通知为准，各校差别很大。",
           14, BLUE_S, maxw=650)
    footer(c, 512, "图中不给日期：报到时间每年、每校都不同。以通知书与迎新系统为准。")
    c.save("new-student-timeline.svg")


# ---------------------------------------------------------------- 2 资助类型
def funding():
    c = Canvas(760, 486, "五类资助的区别")
    header(c, "场景 2 · 奖助学金", "先分清是哪一类，再准备材料",
           "同样叫「资助」，有的要还、有的不用还、有的要用劳动换。")
    cols = [
        ("国家助学贷款", "要还", "入学前在户籍地\n或入学后校园地", "看回执与合同", BLUE_F, BLUE_S),
        ("奖学金", "不用还", "按成绩与综测\n学院组织评定", "看学院通知", GREEN_F, GREEN_S),
        ("助学金", "不用还", "先做困难认定\n再申请", "先认定后申请", GREEN_F, GREEN_S),
        ("勤工助学", "劳动换报酬", "校内岗位\n按月或按小时", "看学工部门", AMBER_F, AMBER_S),
        ("临时困难补助", "不用还", "突发变故\n临时困难", "先找辅导员", AMBER_F, AMBER_S),
    ]
    y = 156
    for i, (name, kind, how, where, f, s) in enumerate(cols):
        x = 40 + i * 138
        c.rect(x, y, 128, 206, f, s, rx=10, sw=0.9)
        c.text(x + 64, y + 30, name, 15, s, 500, "middle", maxw=118)
        c.rect(x + 14, y + 44, 100, 26, "#ffffff", s, rx=6, sw=0.8)
        c.text(x + 64, y + 62, kind, 13, s, 400, "middle")
        for j, ln in enumerate(how.split("\n")):
            c.text(x + 14, y + 100 + j * 22, ln, 13, MUTED, maxw=104)
        c.text(x + 14, y + 176, where, 12.5, s, maxw=104)
    c.rect(40, 386, 680, 44, GRAY_F, LINE, rx=8, sw=0.8)
    c.text(56, 413, "额度、比例、名额、申请时间每年每校都不同：一律以本校学生资助管理部门当年通知为准。",
           13.5, MUTED, maxw=650)
    footer(c, 444, "判断顺序：先问「这笔钱要不要还」，再问「谁评定」，最后才看金额。")
    c.save("funding-types.svg")


# ---------------------------------------------------------------- 3 毕设流程
def thesis():
    c = Canvas(760, 546, "本科毕业论文流程")
    header(c, "场景 3 · 毕业论文", "从选题到归档的八个环节",
           "每个环节都有一次「过或不过」的判断，不是走完就算。")
    steps = ["选题", "开题", "中期检查", "初稿", "查重", "送审", "答辩", "终稿归档"]
    for i, name in enumerate(steps):
        col, row = i % 4, i // 4
        x = 40 + col * 172
        y = 160 + row * 140
        c.rect(x, y, 140, 62, "#ffffff", BLUE_S, rx=8, sw=0.9)
        c.badge(x + 20, y + 31, i + 1)
        c.text(x + 40, y + 36, name, 16, INK, 500)
        if col < 3:
            c.arrow(x + 142, y + 31, x + 168, y + 31)
    # 第一行末尾折回第二行开头
    c.parts.append('<path d="M626 222 L626 266 Q626 272 620 272 L116 272 '
                   'Q110 272 110 278 L110 296" fill="none" stroke="#9c9c9c" '
                   'stroke-width="1.4" marker-end="url(#a)"/>')
    notes = [
        (212, 244, ["开题不过要重来", "换题成本最高"]),
        (40, 384, ["查重率上限", "以学校规定为准"]),
        (212, 384, ["外审不通过", "可能延期半年"]),
        (556, 384, ["归档晚了", "影响离校手续"]),
    ]
    for x, y, lines in notes:
        for j, ln in enumerate(lines):
            c.text(x, y + j * 18, ln, 12, RED_S, maxw=150)
    c.rect(40, 428, 680, 52, AMBER_F, AMBER_S, rx=8, sw=0.8)
    c.text(56, 451, "本图只排顺序，不写日期：开题、中期、送审、答辩的时间点由学院当年通知决定。",
           13.5, AMBER_S, maxw=650)
    c.text(56, 471, "提前问清三件事：查重系统是哪个、送审是校内还是校外、答辩后多久交终稿。",
           13.5, AMBER_S, maxw=650)
    footer(c, 496, "卡点集中在开题与送审：这两步不过，后面所有安排都要顺延。")
    c.save("thesis-flow.svg")


# ---------------------------------------------------------------- 4 找实习
def internship_flow():
    c = Canvas(760, 490, "第一次找实习的流程")
    header(c, "场景 4 · 实习", "从找岗位到入职，中间有一道核验",
           "多数人跳过核验直接投递，问题都出在这道关口。")
    steps = [("筛岗位", "看职责是否具体"), ("核验", "主体·地点·收费"),
             ("投递", "一岗一版简历"), ("面试", "问清带教与内容"),
             ("Offer", "确认时间与报酬"), ("签协议", "看清性质与条款"),
             ("入职", "材料与报到")]
    for i, (name, sub) in enumerate(steps):
        col, row = i % 4, i // 4
        x = 40 + col * 172
        y = 160 + row * 110
        fill, stroke = (AMBER_F, AMBER_S) if name == "核验" else ("#ffffff", BLUE_S)
        c.rect(x, y, 140, 66, fill, stroke, rx=8, sw=1.0 if name == "核验" else 0.9)
        c.text(x + 14, y + 28, name, 16, INK, 500)
        c.text(x + 14, y + 50, sub, 12.5, MUTED, maxw=116)
        if col < 3:
            c.arrow(x + 142, y + 33, x + 168, y + 33)
        elif i == 3:
            c.arrow(x + 70, y + 68, x + 70, y + 108)
    c.rect(424, 270, 276, 62, "#ffffff", AMBER_S, rx=8, sw=0.9, dash="5 4")
    c.text(438, 292, "核验三问", 13.5, AMBER_S, 500)
    c.text(438, 313, "主体真实吗 · 职责具体吗 · 要收费吗", 12.5, MUTED, maxw=250)
    c.rect(40, 386, 680, 34, GRAY_F, LINE, rx=8, sw=0.8)
    c.text(56, 408, "任何环节先收费（押金、培训费、服装费、内推费）都是风险信号，先停下来核实。",
           13.5, MUTED, maxw=650)
    footer(c, 442, "实习不等于劳动关系；报酬、工时、保险以协议约定与适用法律为准。")
    c.save("internship-flow.svg")


# ---------------------------------------------------------------- 5 实习三段
def internship_phases():
    c = Canvas(760, 526, "实习前、中、后的关键事项")
    header(c, "场景 5 · 实习权益", "三个阶段各自要留下什么",
           "实习的权益靠协议与记录，不靠口头承诺。")
    phases = [
        ("实习前", BLUE_F, BLUE_S, [
            "协议性质：实习还是劳务",
            "岗位职责与工作地点",
            "报酬标准与发放时间",
            "工作时间与加班安排",
            "保险、安全与培训",
            "保密与成果归属",
        ]),
        ("实习中", GREEN_F, GREEN_S, [
            "每周留一份周报或记录",
            "任务范围变化要书面确认",
            "加班、调休留痕",
            "遇到问题先记录再沟通",
            "定期向带教要反馈",
        ]),
        ("结束后", AMBER_F, AMBER_S, [
            "实习证明与评价",
            "成果与作品归档",
            "转正或推荐沟通",
            "复盘：留下什么、缺什么",
        ]),
    ]
    for i, (name, f, s, items) in enumerate(phases):
        x = 40 + i * 232
        c.rect(x, 152, 216, 286, f, s, rx=10, sw=0.9)
        c.text(x + 18, 182, name, 17, s, 500)
        c.line(x + 18, 194, x + 198, 194, s, 0.8)
        for j, it in enumerate(items):
            c.badge(x + 30, 218 + j * 32, j + 1, s)
            c.text(x + 48, 223 + j * 32, it, 13, MUTED, maxw=158)
    c.rect(40, 452, 680, 30, GRAY_F, LINE, rx=8, sw=0.8)
    c.text(56, 472, "实习关系是否构成劳动关系，要看主体资格、管理程度与报酬方式，不能一概而论。",
           13, MUTED, maxw=650)
    footer(c, 486, "协议条款与争议处理，以签署的协议文本和现行法律为准。")
    c.save("internship-phases.svg")


# ---------------------------------------------------------------- 6 毕业去向
def graduation():
    c = Canvas(760, 570, "毕业去向与档案户口")
    header(c, "场景 6 · 毕业离校", "先定去向，再定档案和户口",
           "去向不同，档案、户口、报到手续的走法完全不同。")
    c.rect(40, 150, 680, 44, GRAY_F, LINE, rx=8, sw=0.8)
    c.text(56, 178, "毕业前 6 个月：你的下一站定了吗？", 15, INK, 500)
    routes = [
        ("已签约就业", "三方或劳动合同\n档案转单位或人才\n户口看城市政策", BLUE_F, BLUE_S),
        ("国内升学", "录取通知书调档函\n档案转录取学校\n户口可迁可留", GREEN_F, GREEN_S),
        ("出国（境）", "录取与签证材料\n档案回原籍或留校\n户口按当地政策", GREEN_F, GREEN_S),
        ("考公考编", "政审与档案核查\n按录用通知报到\n注意服务期约定", AMBER_F, AMBER_S),
        ("还没定", "先确认档案去哪\n问清应届生期限\n档案别自己拿着", RED_F, RED_S),
    ]
    for i, (name, body, f, s) in enumerate(routes):
        x = 40 + i * 138
        y = 214
        c.rect(x, y, 128, 176, f, s, rx=9, sw=0.9)
        c.text(x + 64, y + 28, name, 14.5, s, 500, "middle", maxw=118)
        for j, ln in enumerate(body.split("\n")):
            c.text(x + 12, y + 58 + j * 34, ln, 12, MUTED, maxw=106)
    c.line(380, 194, 380, 214, LINE, 1)
    c.rect(40, 410, 680, 76, "#ffffff", LINE, rx=8, sw=0.9)
    c.text(56, 434, "离校前必须确认的三件事", 13.5, INK, 500)
    c.text(56, 456, "① 档案寄到哪、单号是多少　② 户口迁不迁、迁到哪　③ 毕业证与学位证的领取方式",
           13, MUTED, maxw=650)
    c.text(56, 476, "三件都办了再离校，比事后补办省事得多。", 13, MUTED, maxw=650)
    footer(c, 512, "各校就业部门与省市人社部门的流程不同，具体以本校离校通知与当地政策为准。")
    c.save("graduation-paths.svg")


# ---------------------------------------------------------------- 7 学籍申诉
def appeal():
    c = Canvas(760, 546, "学籍异常的处理流程")
    header(c, "场景 7 · 学籍与申诉", "从发现异常到书面答复",
           "先查规定，再动笔；口头沟通要留痕。")
    steps = [
        ("发现异常", "成绩缺失、学籍状态\n不符、处分通知"),
        ("查规定", "学生手册、学籍管理\n办法、学院细则"),
        ("收集证据", "系统截图、邮件、\n通知、时间线"),
        ("书面申请", "事实、依据、请求\n三项写清"),
        ("等书面答复", "记下受理日期与\n答复期限"),
        ("复核或申诉", "按校内渠道逐级\n走，注意时限"),
    ]
    for i, (name, sub) in enumerate(steps):
        col, row = i % 3, i // 3
        x = 40 + col * 232
        y = 158 + row * 132
        c.rect(x, y, 200, 76, "#ffffff", BLUE_S, rx=9, sw=0.9)
        c.badge(x + 22, y + 24, i + 1)
        c.text(x + 44, y + 29, name, 15.5, INK, 500)
        for j, ln in enumerate(sub.split("\n")):
            c.text(x + 20, y + 52 + j * 18, ln, 12.5, MUTED, maxw=168)
        if col < 2:
            c.arrow(x + 202, y + 38, x + 228, y + 38)
        elif i == 2:
            c.arrow(x + 100, y + 78, x + 100, y + 126)
    c.rect(40, 424, 680, 58, RED_F, RED_S, rx=8, sw=0.8)
    c.text(56, 447, "三个最容易吃亏的地方：错过申请期限、只有口头沟通没有书面记录、" +
           "材料交了没要回执。", 13.5, RED_S, maxw=650)
    c.text(56, 469, "申诉渠道、期限与受理部门由学校规定，不全国统一；先在学校官网找到现行办法。",
           13.5, RED_S, maxw=650)
    footer(c, 502, "本图是处理顺序示意，不构成法律意见；涉及处分与退学，建议同时咨询学校法律援助。")
    c.save("status-appeal.svg")


# ---------------------------------------------------------------- 8 兼职风险
def scam():
    c = Canvas(760, 546, "兼职与招聘风险识别")
    header(c, "场景 8 · 防骗", "五种高频套路与对应动作",
           "共同点：先让你付出（钱、账号、时间），再谈回报。")
    rows = [
        ("异常收费", "押金、服装费、体检费、内推费", "不交；要合同与收费依据", RED_S),
        ("刷单返利", "先小单返现，再诱导大额垫付", "立刻停；保存聊天与转账记录", RED_S),
        ("虚假兼职", "高薪、无门槛、只留私人联系方式", "查企业主体；不私下转账", AMBER_S),
        ("培训贷", "先培训后上岗，让你签贷款", "不签金融合同；问清退款条款", AMBER_S),
        ("出借账户", "借你的卡、微信、收款码走账", "不借；这可能涉刑", RED_S),
    ]
    y = 156
    c.text(40, y, "类型", 12.5, FAINT)
    c.text(160, y, "典型话术 / 信号", 12.5, FAINT)
    c.text(470, y, "立刻做什么", 12.5, FAINT)
    c.line(40, y + 10, 720, y + 10, LINE, 1)
    for i, (name, signal, act, color) in enumerate(rows):
        yy = y + 22 + i * 54
        c.rect(40, yy, 680, 46, "#ffffff" if i % 2 == 0 else GRAY_F, LINE, rx=6, sw=0.7)
        c.text(52, yy + 28, name, 14, color, 500)
        c.text(160, yy + 28, signal, 13, MUTED, maxw=300)
        c.text(470, yy + 28, act, 13, INK, maxw=232)
    c.rect(40, 444, 680, 44, RED_F, RED_S, rx=8, sw=0.8)
    c.text(56, 471, "已经转出去：先联系银行或支付平台止付，再报警，同时告知辅导员与家长；不要为了面子拖时间。",
           13, RED_S, maxw=650)
    footer(c, 504, "不承诺能追回资金；处理渠道以公安机关与金融机构的实际流程为准。")
    c.save("part-time-risk.svg")


# ---------------------------------------------------------------- 9 四年规划
def four_years():
    c = Canvas(760, 574, "大学四年的四条线")
    header(c, "场景 9 · 四年规划", "四条线并行，但不必都满",
           "目标是升学就看前两条，目标是就业就看后两条，另一条保持及格。")
    years = ["大一", "大二", "大三", "大四"]
    lanes = [
        ("课程与 GPA", ["适应节奏别挂科", "稳住绩点补短板", "核心课与方向课", "补学分、清欠课"]),
        ("科研与竞赛", ["先看，进实验室", "跟一个项目做到底", "出成果或参赛", "写进简历与材料"]),
        ("实习与实践", ["社团志愿校内岗", "第一段实习", "对口实习争转正", "毕业实习或补短板"]),
        ("升学与就业", ["了解出口，别急", "试水夏令营招聘会", "定方向并投递", "拿结果、做选择"]),
    ]
    x0, y0 = 40, 152
    c.text(x0 + 76, y0 - 8, "", 12)
    for j, yr in enumerate(years):
        c.text(x0 + 156 + j * 132 + 60, y0 - 6, yr, 13, FAINT, 400, "middle")
    for i, (lane, cells) in enumerate(lanes):
        yy = y0 + 8 + i * 84
        c.text(x0, yy + 34, lane, 14, INK, 500, maxw=140)
        for j, cell in enumerate(cells):
            x = x0 + 156 + j * 132
            c.rect(x, yy, 122, 68, GRAY_F if j % 2 == 0 else "#ffffff", LINE, rx=7, sw=0.8)
            # 单元格内自动折行
            line, buf = "", []
            for ch in cell:
                if cjk_len(line + ch) * 12 > 100:
                    buf.append(line); line = ch
                else:
                    line += ch
            buf.append(line)
            for k, ln in enumerate(buf[:2]):
                c.text(x + 11, yy + 26 + k * 18, ln, 12, MUTED, maxw=102)
    c.rect(40, 486, 680, 26, BLUE_F, BLUE_S, rx=7, sw=0.8)
    c.text(56, 504, "每条线只写一件事：同时推进四件事，通常四件都做不完。", 13, BLUE_S, maxw=650)
    footer(c, 528, "时间点因专业与学校而异；这张图用来分配精力，不用来当截止日期表。")
    c.save("four-year-plan.svg")


# ---------------------------------------------------------------- 10 求职入职
def job_flow():
    c = Canvas(760, 490, "从筛岗到入职")
    header(c, "场景 10 · 求职", "六个环节，两个容易翻车的地方",
           "筛岗决定上限，签约决定下限。")
    steps = [
        ("筛岗位", "职责、门槛、地点"),
        ("投递", "一岗一版，留记录"),
        ("笔试面试", "问清团队与考核"),
        ("Offer 比较", "不只比月薪"),
        ("签约", "试用期、违约、地点"),
        ("入职材料", "证件、体检、档案"),
    ]
    for i, (name, sub) in enumerate(steps):
        col, row = i % 3, i // 3
        x = 40 + col * 232
        y = 158 + row * 118
        c.rect(x, y, 200, 70, "#ffffff", BLUE_S, rx=9, sw=0.9)
        c.text(x + 16, y + 30, name, 16, INK, 500)
        c.text(x + 16, y + 54, sub, 12.5, MUTED, maxw=168)
        if col < 2:
            c.arrow(x + 202, y + 35, x + 228, y + 35)
        elif i == 2:
            c.arrow(x + 100, y + 72, x + 100, y + 112)
    c.rect(40, 396, 332, 44, AMBER_F, AMBER_S, rx=8, sw=0.8)
    c.text(56, 423, "比较项：内容、薪酬结构、地点、成长、合同", 12.5, AMBER_S, maxw=300)
    c.rect(388, 396, 332, 44, RED_F, RED_S, rx=8, sw=0.8)
    c.text(404, 423, "签约前确认：试用期、违约金、工作地点", 12.5, RED_S, maxw=300)
    footer(c, 452, "薪酬结构要拆开看：固定、绩效、补贴、年终奖的算法完全不同。")
    c.save("job-to-onboard.svg")


# ---------------------------------------------------------------- 11 资助核验
def funding_lookup():
    c = Canvas(760, 470, "怎么找到学校的资助部门与正式政策")
    header(c, "场景 2 · 奖助学金", "从学校官网走到具体科室",
           "先找到「谁发通知」，再找「通知原文」；不要在搜索结果的转载页上做决定。")
    steps = [
        ("学校官网", "首页找「机构设置」\n或「职能部门」"),
        ("学生工作部（处）", "多数学校资助业务\n挂在这里"),
        ("学生资助管理中心", "科室页通常有\n办公地点与电话"),
        ("通知与文件", "看原文，不看摘要"),
    ]
    for i, (name, sub) in enumerate(steps):
        x = 40 + i * 172
        c.rect(x, 158, 148, 100, "#ffffff" if i % 2 == 0 else GRAY_F, BLUE_S, rx=9, sw=0.9)
        c.badge(x + 20, 180, i + 1)
        c.text(x + 14, 214, name, 14, INK, 500, maxw=122)
        for j, ln in enumerate(sub.split("\n")):
            c.text(x + 14, 236 + j * 18, ln, 11.5, MUTED, maxw=122)
        if i < 3:
            c.arrow(x + 150, 208, x + 168, 208)
    c.rect(40, 276, 680, 98, AMBER_F, AMBER_S, rx=9, sw=0.8)
    c.text(56, 300, "判断一份通知是否可信，看三件事", 13.5, AMBER_S, 500)
    checks = ["① 发布单位是学校或学院，不是个人或机构转载",
              "② 有发布日期与适用学年，不是往年的旧文件",
              "③ 写清适用对象、材料与截止时间，不是只有一句「可以申请」"]
    for j, ln in enumerate(checks):
        c.text(56, 324 + j * 20, ln, 12.5, MUTED, maxw=650)
    c.rect(40, 386, 680, 34, GRAY_F, LINE, rx=8, sw=0.8)
    c.text(56, 408, "国家级政策可到全国学生资助管理中心核对；校级细则一律以本校文件为准。",
           13, MUTED, maxw=650)
    footer(c, 442, "学校机构名称各不相同（学生处 / 学工部 / 研工部），找不到就问辅导员要科室名。")
    c.save("funding-lookup.svg")


# ---------------------------------------------------------------- 12 毕业时间线
def graduation_timeline():
    c = Canvas(760, 430, "毕业前到离校后的时间线")
    header(c, "场景 6 · 毕业离校", "五个节点的硬事项",
           "线上是节点，节点上下分开写：上面是有截止日的，下面是能提前做的。")
    c.line(60, 212, 700, 212, "#cfcbc3", 2)
    nodes = [
        ("前 6 个月", ["论文中期", "学位申请材料", "去向登记"], 70),
        ("前 3 个月", ["成绩单多开几份", "问清档案流程", "就业协议或录取"], 230),
        ("前 1 个月", ["答辩与查重", "毕业资格公示", "离校手续单"], 390),
        ("毕业当月", ["领证", "档案转递", "户口迁移"], 550),
        ("离校后 1 个月", ["入职或入学", "社保起缴", "确认档案到达"], 700),
    ]
    for i, (name, items, x) in enumerate(nodes):
        c.parts.append(f'<circle cx="{x}" cy="212" r="6" fill="{BLUE_S}"/>')
        if i % 2 == 0:
            c.text(x + 10, 200, name, 13.5, INK, 500, maxw=150)
            for j, it in enumerate(items):
                c.text(x, 180 - j * 18, it, 11.5, MUTED, maxw=150)
            c.line(x, 202, x, 208, "#cfcbc3", 1)
        elif i == 4:
            c.text(x - 6, 236, name, 13.5, INK, 500, "end", maxw=150)
            for j, it in enumerate(items):
                c.text(x, 258 + j * 18, it, 11.5, MUTED, "end", maxw=150)
            c.line(x, 216, x, 222, "#cfcbc3", 1)
        else:
            c.text(x + 10, 236, name, 13.5, INK, 500, maxw=150)
            for j, it in enumerate(items):
                c.text(x, 258 + j * 18, it, 11.5, MUTED, maxw=150)
            c.line(x, 216, x, 222, "#cfcbc3", 1)
    c.rect(40, 330, 680, 34, AMBER_F, AMBER_S, rx=8, sw=0.8)
    c.text(56, 352, "档案与户口必须在离校前确认去向；具体日期以本校就业部门与学院通知为准。",
           13, AMBER_S, maxw=650)
    footer(c, 382, "本图只给先后顺序，不写具体日期：各校答辩、公示与派遣时间不同。")
    c.save("graduation-timeline.svg")


# ---------------------------------------------------------------- 13 诈骗处置
def scam_response():
    c = Canvas(760, 400, "遭遇诈骗后的处理步骤")
    header(c, "场景 8 · 防骗", "已经转出去了，按这个顺序做",
           "先止损，再留证，最后才是追。顺序反了，证据会丢。")
    steps = [
        ("1 立刻停止", "不再转账、不再充值\n不再按对方指令操作"),
        ("2 保存证据", "聊天记录、转账凭证\n对方账号与电话"),
        ("3 联系机构", "银行或支付平台\n申请止付、冻结"),
        ("4 报警", "110 或 96110\n带上证据与时间线"),
        ("5 告知学校", "辅导员、保卫处\n同步家长"),
        ("6 复盘", "复盘怎么被骗\n避免二次受骗"),
    ]
    for i, (name, sub) in enumerate(steps):
        col, row = i % 3, i // 3
        x = 40 + col * 232
        y = 156 + row * 108
        fill, stroke = (RED_F, RED_S) if i < 3 else ("#ffffff", BLUE_S)
        c.rect(x, y, 200, 82, fill, stroke, rx=9, sw=0.9)
        c.text(x + 14, y + 26, name, 15, INK, 500)
        for j, ln in enumerate(sub.split("\n")):
            c.text(x + 14, y + 48 + j * 17, ln, 12, MUTED, maxw=172)
        if col < 2:
            c.arrow(x + 202, y + 40, x + 228, y + 40)
        elif i == 2:
            c.arrow(x + 100, y + 84, x + 100, y + 102)
    c.rect(40, 366, 680, 30, RED_F, RED_S, rx=8, sw=0.8)
    c.text(56, 386, "不承诺能追回资金；越早止付，可能性越高。不要相信「付费追款」的二次诈骗。",
           12.5, RED_S, maxw=650)
    footer(c, 410, "处理渠道以公安机关与金融机构的实际流程为准；学校可协助出具情况说明。")
    c.save("scam-response.svg")


# ---------------------------------------------------------------- 14 机会关系
def opportunity_relations():
    c = Canvas(760, 546, "科研、竞赛、实习与升学就业的关系")
    header(c, "场景 9 · 四年规划", "四条线之间怎么互相供料",
           "课程是底座，中间两条线产出材料，出口那条线用材料。")
    c.rect(280, 150, 200, 52, "#ffffff", BLUE_S, rx=9, sw=0.9)
    c.text(380, 182, "升学 or 就业", 15, INK, 500, "middle")
    c.rect(280, 232, 200, 52, "#ffffff", AMBER_S, rx=9, sw=0.9)
    c.text(380, 264, "简历 / 陈述 / 推荐信", 13, AMBER_S, 500, "middle")
    c.rect(80, 316, 200, 72, BLUE_F, BLUE_S, rx=9, sw=0.9)
    c.text(96, 344, "科研与竞赛", 15, INK, 500)
    c.text(96, 368, "问题、方法、成果", 12, MUTED, maxw=170)
    c.rect(480, 316, 200, 72, GREEN_F, GREEN_S, rx=9, sw=0.9)
    c.text(496, 344, "实习与实践", 15, INK, 500)
    c.text(496, 368, "经历、作品、评价", 12, MUTED, maxw=170)
    c.rect(280, 420, 200, 48, GRAY_F, LINE, rx=8, sw=0.8)
    c.text(380, 449, "课程与 GPA（底座）", 13.5, INK, 500, "middle")
    c.arrow(380, 232, 380, 204)
    c.arrow(210, 316, 300, 286)
    c.arrow(550, 316, 460, 286)
    c.line(180, 402, 580, 402, "#b9b5ad", 1.4)
    c.line(180, 388, 180, 402, "#b9b5ad", 1.4)
    c.line(580, 388, 580, 402, "#b9b5ad", 1.4)
    c.line(380, 420, 380, 402, "#b9b5ad", 1.4)
    c.text(196, 300, "产出可写的项目", 11.5, MUTED)
    c.text(470, 300, "产出可讲的经历", 11.5, MUTED)
    footer(c, 500, "两条中间线不必都满：升学看科研与竞赛，就业看实习与作品，另一条保持及格。")
    c.save("opportunity-relations.svg")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in (new_student, funding, thesis, internship_flow, internship_phases,
               graduation, appeal, scam, four_years, job_flow,
               funding_lookup, graduation_timeline, scam_response, opportunity_relations):
        fn()
    files = sorted(OUT.glob("*.svg"))
    for f in files:
        print(f"{f.name:34s} {f.stat().st_size/1024:6.1f} KB")
    print(f"共 {len(files)} 张")


if __name__ == "__main__":
    main()
