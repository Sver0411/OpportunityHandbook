<div align="center">

**简体中文** · [English](README.en.md)

# 机会手册 · OpportunityHandbook

**不是替你规划一条标准人生，而是让你看清：世界上到底有哪些路。**

一份从升学、科研、求职，到晋升、转行、出国与重新开始的现实选择手册。

<p><a href="https://sver0411.github.io/OpportunityHandbook/">在线阅读</a>&nbsp;·&nbsp;<a href="book/17-内容地图.md">内容地图</a>&nbsp;·&nbsp;<a href="https://sver0411.github.io/OpportunityHandbook/#/browse">按条件筛选</a>&nbsp;·&nbsp;<a href="#你可以直接从这些问题开始">从问题开始</a>&nbsp;·&nbsp;<a href="#opportunityhandbook--opportunityradar">搭配 OpportunityRadar</a></p>

<p>
  <a href="https://github.com/Sver0411/OpportunityHandbook/actions/workflows/ci.yml"><img alt="内容校验" src="https://img.shields.io/github/actions/workflow/status/Sver0411/OpportunityHandbook/ci.yml?branch=main&amp;style=flat-square&amp;label=%E5%86%85%E5%AE%B9%E6%A0%A1%E9%AA%8C"></a>&nbsp;&nbsp;
  <a href="https://github.com/Sver0411/OpportunityHandbook/actions/workflows/pages.yml"><img alt="在线阅读" src="https://img.shields.io/github/actions/workflow/status/Sver0411/OpportunityHandbook/pages.yml?branch=main&amp;style=flat-square&amp;label=%E5%9C%A8%E7%BA%BF%E9%98%85%E8%AF%BB"></a>&nbsp;&nbsp;
  <a href="LICENSE-CONTENT"><img alt="正文许可：CC BY 4.0" src="https://img.shields.io/badge/%E6%AD%A3%E6%96%87-CC_BY_4.0-5B7F67?style=flat-square"></a>&nbsp;&nbsp;
  <a href="LICENSE"><img alt="代码许可：MIT" src="https://img.shields.io/badge/%E4%BB%A3%E7%A0%81-MIT-202620?style=flat-square"></a>
</p>

</div>

### 导出 PDF

右上角「导出 PDF」有四种范围：**这一篇 / 这一页 / 整个章节 / 整本手册**。
选中后在浏览器的打印对话框里选「另存为 PDF」即可；想带页码，勾选对话框里的「页眉和页脚」。

整本导出会自动生成**封面**（书名、章节与页面数、导出日期、授权）与**目录**（章节 → 页面），
页面顺序与左栏一致，每页右下角有页码。排版用页面自身的 CSS，所以 PDF 里文字可选、可检索，
站外链接会补出完整地址，表格与代码不跨页。

命令行批量导出（同样会带上封面与「第 N 页 / 共 M 页」，且**整本是一个 PDF**）：

```bash
python3 tools/export_pdf.py --list          # 看有哪些章节
python3 tools/export_pdf.py --book           # 整本一个 PDF → dist/pdf/机会手册-全书-YYYY-MM-DD.pdf
python3 tools/export_pdf.py --chapter 15     # 只导出第 15 章
python3 tools/export_pdf.py --all            # 一章一个 PDF（主线 + 横切章）
python3 tools/export_pdf.py --book --out ~/Desktop
```

输出默认在 `dist/pdf/`（不进仓库）。需要本机有 Chrome / Chromium；页码与封面由
`tools/pdf_driver.py` 通过 DevTools 协议的 printToPDF 控制（不引入任何第三方库）。

### 一次完整的搭配方式

假设你突然想：“我是不是应该试试科研？”

1. 先在机会手册里弄清科研平时在做什么、它与项目和实习有什么区别、第一次尝试应该留下什么，以及怎样判断一个实验室；
2. 把模糊愿望变成一个更真实的目标，例如：“我想用每周 8 小时，低成本验证自己是否喜欢机器人方向的研究，并留下可展示的成果”；
3. 再把这个目标交给机会雷达，让它寻找目前仍开放的实验室项目、暑研、研究实习或相关开源项目，并核实资格与时间；
4. 当手上出现多个候选，再用机会手册的机会价值判断表、导师筛选表或时间线做最后比较。

这比一开始就搜索“有什么科研推荐”更有效，因为你已经知道自己究竟要验证什么。

## 你可以直接从这些问题开始

你不需要从第一页读到最后一页。遇到什么问题，就从什么地方进入。

### 我还在学校

- [我到底要不要读研？](book/04-升学、就业还是出国/02-国内升学.md#grad-school-worth-it)
- [保研和考研应该怎么选？](book/04-升学、就业还是出国/02-国内升学.md#baoyan-vs-kaoyan)
- [学校和专业哪个更重要？](book/01-先决定下一步往哪里走/02-选学校与选专业.md#choose-school-vs-major)
- [什么比赛值得参加？](book/03-做项目、打比赛、进实验室/02-竞赛.md#competition-what-worth-joining)
- [这个比赛是不是交了钱就能拿奖？](book/03-做项目、打比赛、进实验室/02-竞赛.md#competition-what-worth-joining)
- [本科生怎么开始科研？](book/03-做项目、打比赛、进实验室/03-科研初体验.md#research-undergrad-start)
- [我的 GitHub 项目算项目经历吗？](book/03-做项目、打比赛、进实验室/01-项目与作品.md#project-what-is-real)
- [什么证书值得考？](book/02-在学校里先把基础打好/06-证书.md#certificate-what-is-worth-it)
- [专业不喜欢，要不要转？](book/01-先决定下一步往哪里走/02-选学校与选专业.md#choose-major-mismatch)
- [实习应该什么时候开始找？](docs/playbooks/第一次找实习.md)
- [中职毕业，能不能继续升学？](book/01-先决定下一步往哪里走/03-专科与职业教育.md#vocational-exam-path)
- [中职和专科阶段有哪些资助？](book/01-先决定下一步往哪里走/03-专科与职业教育.md#vocational-subsidy)
- [怎么联系导师 / 要不要套磁？](docs/playbooks/第一次联系导师.md)
- [家里预算有限，还能留学吗？](book/04-升学、就业还是出国/03-海外升学.md#overseas-funding)
- [怎么和父母沟通升学与职业选择？](book/01-先决定下一步往哪里走/07-家庭沟通与支持.md#family-talk)

### 我快毕业了

- [第一份工作应该怎么看？](book/05-从学校走向第一份工作/06-第一份工作.md#first-job-what-to-trade-for)
- [两个 Offer 应该怎么比较？](book/05-从学校走向第一份工作/05-Offer.md#offer-comparison)
- [大公司还是小公司？](book/05-从学校走向第一份工作/06-第一份工作.md#first-job-big-vs-small)
- [工资还是成长？](book/05-从学校走向第一份工作/06-第一份工作.md#first-job-pay-vs-growth)
- [一直找不到工作怎么办？](book/05-从学校走向第一份工作/07-如果没有顺利进入下一站.md#job-hunting-long-search)
- [投了很多简历都没回音，问题在哪？](docs/job-search/求职漏斗诊断.md)
- [博士毕业以后有哪些出口？](book/04-升学、就业还是出国/07-读博与博士毕业.md#phd-career-paths)
- [要不要考公 / 进体制？](book/01-先决定下一步往哪里走/01-认识你面前的几条主要路线.md#paths-public-sector)

### 我已经工作了

- [工作几年以后应该怎么升职？](book/06-从新人到能独立负责/02-从执行到独立负责.md#work-record-achievements)
- [什么时候适合第一次跳槽？](book/06-从新人到能独立负责/05-第一次重新选择.md#career-job-hopping)
- [技术路线还是管理路线？](book/07-晋升、跳槽还是转行/03-管理路线.md#mgmt-ic-or-manager)
- [转行前应该先判断什么？](book/07-晋升、跳槽还是转行/05-转行.md#switch-before-decide)
- [转行要不要从零开始？](book/07-晋升、跳槽还是转行/05-转行.md#career-change-keep-capital)
- [工作以后还值得读硕士吗？](book/07-晋升、跳槽还是转行/06-再次进入教育体系.md#edu-master-after-work)
- [40 岁以后还能换方向吗？](book/07-晋升、跳槽还是转行/08-职业中段与年龄.md#career-after-40)
- [技能过时了怎么办？](book/07-晋升、跳槽还是转行/07-资深阶段：技能与收入.md#career-skill-decay)


- [第一个月的工资怎么分配？](book/15-钱与生活基本盘/01-拿到钱的第一年.md#money-first-salary-split)
- [社保和公积金到底有什么用？](book/15-钱与生活基本盘/02-社保公积金与税.md#money-social-insurance)
- [状态持续不好，什么时候该找专业帮助？](book/16-身体与心理的可持续性/02-心理与求助.md#health-mental-support)
- [被欠薪或被违法辞退怎么办？](docs/rights/被欠薪与劳动仲裁.md)
- [家里需要我出钱，应该怎么安排？](book/01-先决定下一步往哪里走/07-家庭沟通与支持.md#care-family-budget)

### 我不知道自己想做什么

- [不知道自己想做什么怎么办？](book/02-在学校里先把基础打好/02-开始认识真实世界.md#explore-low-cost-experiments)
- [怎么比较两个完全不同的机会？](book/00-从这里开始.md#judge-compare-two-opportunities)
- [什么东西值得长期积累？](book/00-从这里开始.md#judge-long-term-accumulation)
- [什么叫未来选择权？](book/00-从这里开始.md#judge-optionality)

## 一份手册，五种入口

| 入口 | 适合什么时候用 | 从哪里开始 |
| --- | --- | --- |
| **导出 PDF** | 想离线读、发给别人或存档 | 网页右上角「导出 PDF」（这一篇 / 这一页 / 整个章节）；整本批量导出见下方命令行 |
| **内容地图** | 还不知道该从哪一篇开始 | [`book/17-内容地图.md`](book/17-内容地图.md) |
| **主线正文** | 想理解一条路径从哪里开始、后来会遇到什么 | [`book/`](book) |
| **时间线** | 已经知道目标，但不知道什么时候准备什么 | [`docs/timelines/`](docs/timelines) |
| **实用工具** | 手上已经有具体选择，需要比较、记录或复盘 | [`docs/tools/`](docs/tools) |
| **专题手册** | 想集中了解国家、行业、科研、竞赛、开源、证书或资助 | [`docs/`](docs) |
| **钱与生活** | 拿到第一笔收入之后：分配、社保公积金与税、保险与风险 | [`book/15-钱与生活基本盘.md`](book/15-钱与生活基本盘.md) |
| **身体与心理** | 长期投入的前提：节奏、什么时候找专业人士、就医与医保 | [`book/16-身体与心理的可持续性.md`](book/16-身体与心理的可持续性.md) |

在线阅读页还可以按人生阶段、方向、预期成果、投入大小和证据类型筛选。你可以查“本科阶段 + 想留下作品 + 低投入”，也可以查“工作三到五年 + 准备转行 + 能接受短期降薪”。

## 为什么没有直接让 AI 给答案

AI 很擅长生成一个完整、顺滑、听起来合理的回答。路径类问题真正困难的部分却是：

- 这是全国规则，还是某个学校、地区或公司的做法？
- 这是官方事实、研究结论、行业数据，还是个人经验？
- 这个规则现在还有效吗？
- 这句话对哪些人成立，又在哪些情况下不成立？

因此，本书为不同内容保留证据边界：

| 标记 | 含义 |
| --- | --- |
| **官方来源** | 政策、法规、学校、考试机构或组织的正式说明 |
| **研究支持** | 有研究证据，但仍需要注意适用范围 |
| **行业数据** | 有统计或行业材料，需要保留时间和口径 |
| **实践经验** | 可以参考，但不应被写成普遍结论 |
| **证据不足** | 暂无可靠来源，或现实中仍存在争议 |

容易变化的内容带有最后核实日期。超过合理时效后，在线页面会提醒读者重新确认。

## 这里不会做什么

- **不替你决定。** 这里提供条件、代价和判断方法，不会用“你就应该”结束讨论。
- **不制造虚假的精确。** 没有依据时，不编造录取率、成功率、未来薪资或回报倍数。
- **不推荐付费机会。** 项目没有返佣，也不会把培训机构的营销内容当作事实依据。
- **不追逐短期风口。** 重点是变化较慢的判断方法，而不是每隔几个月更换一次“最有前途的方向”。
- **不替代专业意见。** 法律、医疗、投资、签证和具体岗位的最终决定，应以专业人士和官方文件为准。

## 内容是怎样维护的

正文使用 Markdown 编写，在线阅读页由仓库内工具构建。新增或修改内容需要说明依据、适用范围和最后核实日期，并通过内容结构、链接、元数据与发布检查。

如果你发现规则已经变化、官方链接失效、经验被写得过于绝对，或某个重要路径还没有覆盖，欢迎提交 Issue 或 PR。开始前请阅读 [参与贡献说明](CONTRIBUTING.md)。

<details>
<summary><strong>开发、本地预览与质量检查</strong></summary>

<br>

本地构建与预览：

```bash
python3 tools/build.py
python3 -m http.server 8000 --directory site
```

运行与线上发布相同的完整校验：

```bash
python3 tools/validate_release.py
```

主要目录：

| 位置 | 用途 |
| --- | --- |
| [`book/`](book) | 按人生问题推进的主线正文 |
| [`docs/`](docs) | 时间线、工具、专题、国家地区与职业资料 |
| [`meta/`](meta) | 导航、元数据、写作与证据规范 |
| [`site/`](site) | 在线阅读页的静态前端 |
| [`tools/`](tools) | 构建、校验、审计与测试工具 |
| [`reports/`](reports) | 内容质量、结构和阅读体验审计报告 |

</details>

## 许可

正文（`book/`、`docs/`、`meta/` 和 README）采用 [CC BY 4.0](LICENSE-CONTENT)：署名后可以复制、修改、翻译与商用。站点和工具代码采用 [MIT](LICENSE)。

知识只有在被用起来以后才有价值。如果你想把它带进课堂、社团、公司培训或翻译成其他语言，不需要事先申请。

---

<div align="center">

### 先看清路，再去找机会。

**[用机会手册建立地图](https://sver0411.github.io/OpportunityHandbook/) · [用机会雷达连接现实](https://github.com/Sver0411/OpportunityRadar)**

</div>
