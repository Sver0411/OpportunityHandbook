# Knowledge Depth Worklog

本文件记录 Knowledge Depth 层的施工进度，按域逐条对照。
机器可读的覆盖矩阵由 `tools/audit_knowledge_depth.py` 生成，见
[`knowledge-depth.md`](knowledge-depth.md)。

最后更新：2026-09-29

---

## 一、层级与目录

| 层级 | 目录（或来源） | 已写 | 待写 |
| --- | --- | --- | --- |
| Book（判断与路线） | `book/`（00–11） | 290 条目 | — |
| Manual（领域地图） | `docs/manuals/` | 10 | — |
| Deep Dive（讲透一个问题） | `docs/projects`、`docs/research-deep`、`docs/job-search`、`docs/career-growth`、`docs/admissions`、`docs/learning`、`docs/open-source`、`docs/competition-playbooks`、`docs/entrepreneurship`、`docs/networking`、`docs/certifications` | 34 | 29 |
| Case（完整走一遍） | `docs/cases/` | 4 | 8 |
| Playbook（照着执行） | `docs/playbooks/` | 3 | 7 |
| Tool / Template | `docs/tools/` | 14 | 14 |
| Career Guide（岗位） | `docs/career-guides/` | 0 | 22 |
| Country Playbook | `docs/country-playbooks/` | 0 | 11 |

待写部分全部以 `status: planned` 存在于仓库中，正文写明覆盖范围；
它们不会出现在导航与搜索里，只汇总在 [`docs/ROADMAP.md`](../docs/ROADMAP.md)。

---

## 二、按域进度

### ✅ 项目与作品（Deep Dive 9/9）

选题与问题定义 · 从教程到作品 · MVP 与范围控制 · 测试与指标体系 ·
日志与故障分析 · README 三档对比 · Demo 制作 · 项目写进简历 · 项目类型专项

### ✅ 科研方法（Deep Dive 8/8）

研究问题的提出 · Baseline 设计 · 消融实验 · 实验设计进阶 · 数据与可复现 ·
论文精读方法 · 同行评审与回复 · 科研失败案例

### ✅ 求职训练（Deep Dive 7/7）

JD 拆解 · 简历改造 · 技术面试 · 行为面试 · 项目面试 · 求职漏斗诊断 · Offer 与合同

### ✅ 学习方法（Deep Dive 4/4）

从零学一项技术 · 读官方文档 · 调试方法 · 掌握程度的判断

### ✅ 职业成长（Deep Dive 3/6）

入职前三个月 · 学会一份工作 · 扩大责任范围
**待写**：晋升材料 · IC 与管理路线 · 在职跳槽

### ✅ 开源协作（Deep Dive 3/6）

读大型代码库 · 评审与合并 · 维护者与治理
**待写**：第一个 Issue · 第一个 PR · Good First Issue

### ⏳ 升学申请（0/4）、竞赛实战（0/5）、创业与自由职业（0/6）、人脉与社群（0/4）、证书与资格（0/3）

均已完成范围界定与文件创建，等待撰写。

### ⏳ 职业指南（0/22）、国家申请手册（0/11）

这是本轮**最大的两块空白**：22 个岗位指南与 11 份国家申请手册已建好文件与范围说明，
尚未撰写正文。它们需要逐岗位、逐国家的材料核实，不建议用统一模板批量生成。

---

## 三、Case / Playbook / Tool 进度

- **Case（4/12）**：第一次做真正项目 · 本科生第一次进实验室 · 第一次找技术实习 · 第一次开源贡献。
  待写：两个 Offer 怎么选 · 第一次转行 · 留学选校 · 联系导师 · 第一次自由职业客户 ·
  第一次面试失败之后 · 从竞赛到作品集 · 教程项目到工程作品；
- **Playbook（3/10）**：第一次做项目 · 第一次联系导师 · 第一次开源贡献。
  待写：第一次找实习 · 第一次参加 Hackathon · 第一次写论文 · 第一次技术面试 · 第一次谈薪 ·
  第一次接单 · 第一次做实验；
- **Tool（14/28，本轮新增 4）**：JD 拆解表 · 项目设计 Canvas · 项目测试计划 · Benchmark 记录表。
  待写：技能 Gap 矩阵 · Failure Log · README 检查表 · 发布检查表 · 面试复盘表 ·
  求职漏斗诊断表 · Research Question Canvas · Baseline 与消融设计表 · 论文精读表 ·
  文献地图 · PR 检查表 · 自由职业报价单 · 客户沟通表 · 实验记录模板。

---

## 四、本地门禁清单（推 CI 前必须全部运行）

`validate_release.py` 里除了外链与浏览器冒烟（较慢），其余都能在本地秒级跑完。
本轮曾因为只跑了 `build --strict` + 测试就直接推送，CI 才暴露出
`docs/projects/选题与问题定义.md` 里出现了被禁用的旧模板表述（“第一句话：”）——
这类问题本地就能拦住：

```bash
python3 tools/build.py --strict            # 构建 + 元数据 + 内部链接
python3 tools/check_ia.py                  # Canonical IA 一致性
python3 tools/check_docs_consistency.py    # 公开文档不得退回旧正文模型（易漏！）
python3 tools/check_markdown_quality.py    # Markdown 格式
python3 tools/check_html_ids.py            # HTML id 唯一性与锚点前缀
python3 tools/check_content_quality.py --hard
python3 tools/metadata_audit.py
python3 tools/audit_duplication.py
python3 tools/check_semantic_links.py
python3 tools/audit_knowledge_depth.py
python3 tools/build_roadmap.py --check     # 路线图与 planned 文档同步
python3 tools/run_tests.py
```

## 五、每批次的施工纪律

1. 写完后立刻 `tools/build.py --strict --no-links`，确认没有链接与元数据问题；
2. 新文档完成后再注册导航（`tools/ia_canonical.py` + `build_navigation.py`），
   并在 `book/09-专题手册.md` / `book/10-时间线与工具.md` 补对应小节；
3. 每完成一个域运行一次 `tools/audit_knowledge_depth.py` 更新矩阵；
4. `tools/build_roadmap.py` 保持 `docs/ROADMAP.md` 与 planned 文档同步（否则 strict 构建会警告）。
