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

## 二、按域进度（全部完成）

| 域 | Deep Dive | 状态 |
| --- | --- | --- |
| 项目与作品 | 9 | ✅ 选题与问题定义 · 从教程到作品 · MVP 与范围控制 · 测试与指标体系 · 日志与故障分析 · README 三档 · Demo 制作 · 项目写进简历 · 项目类型专项 |
| 科研方法 | 8 | ✅ 研究问题的提出 · Baseline · 消融 · 实验设计进阶 · 数据与可复现 · 论文精读 · 同行评审与回复 · 科研失败案例 |
| 求职训练 | 7 | ✅ JD 拆解 · 简历改造 · 技术面试 · 行为面试 · 项目面试 · 漏斗诊断 · Offer 与合同 |
| 职业成长 | 6 | ✅ 入职前三个月 · 学会一份工作 · 扩大 scope · 晋升材料 · IC 与管理路线 · 在职跳槽 |
| 升学申请 | 5 | ✅ 选校与短名单 · 推荐信 · SOP 改写 · 研究计划拆解 · 复试与申请面试 |
| 学习方法 | 4 | ✅ 从零学技术 · 读官方文档 · 调试方法 · 掌握程度的判断 |
| 开源协作 | 6 | ✅ 第一个 Issue · 第一个 PR · Good First Issue · 读大型代码库 · 评审与合并 · 维护者与治理 |
| 竞赛实战 | 5 | ✅ 组队与分工 · 读规则与评分函数 · 赛期时间与版本 · Demo 与答辩 · 赛后整理 |
| 创业与自由职业 | 6 | ✅ 找问题与访谈 · 定价与报价 · 分销与获客 · 第一单客户 · 现金流与合同 · 从自由职业到工作室 |
| 人脉与社群 | 4 | ✅ 联系陌生人 · 会议与线下活动 · 关系维护与内推 · 贡献社群 |
| 证书与资格 | 3 | ✅ 六步判断 · 类型对照 · 考试准备 |
| 职业指南 | 22 | ✅ 软件/前端/后端/嵌入式/硬件/算法/数据分析/数据工程/产品/测试/SRE/售前/技术支持/研究工程师/研究员/制造研发/设计师/财务/咨询/教师/公共部门/技能型职业 |
| 国家申请手册 | 11 | ✅ 中国大陆 · 中国香港 · 日本 · 新加坡 · 韩国 · 美国 · 加拿大 · 英国 · 澳大利亚 · 新西兰 · 欧洲大陆 |
| 完整案例 | 12 | ✅ 第一次做真正项目 · 本科生第一次科研 · 第一次找技术实习 · 第一次开源贡献 · 教程项目到工程作品 · 两个 Offer 怎么选 · 第一次转行 · 留学选校 · 联系导师 · 从竞赛到作品集 · 第一次面试失败 · 第一次自由职业客户 |
| 操作手册 | 10 | ✅ 第一次做项目 · 联系导师 · 开源贡献 · 找实习 · 技术面试 · 谈薪 · 接单 · Hackathon · 写论文 · 做实验 |
| 工具与模板 | 28 | ✅ 全部 28 份（含本轮新增 18 份） |

**待写：0。**

---

## 三、施工纪律（本轮踩过的坑）

1. **写完即验**：`build --strict`（内部链接与元数据）、`check_docs_consistency`（禁用表述）、
   `check_markdown_quality`、`check_html_ids`、`check_content_quality --hard`、`run_tests`；
2. **新文档进导航的正确顺序**：先写正文 → 再在 `tools/ia_canonical.py` 建分组 →
   `build_navigation.py` → 在 `book/09`/`book/10` 索引页补同名 `## 小节`
   （分组节点必须有同名 H2，否则 `check_ia` 报 BROKEN TARGET）；
3. **分组已存在后再加文档**要用 `tools/` 侧的 topup 脚本补项（只建组不补项会漏）；
4. 三个反复出现的门禁坑：
   - `status: planned` 文档会被 `check_docs_consistency` 与测试当作公开内容检查 → 施工清单要写明范围且不进导航；
   - 「一句话：」这类旧模板字段标签是**禁用表述**，职业指南开头的「一句话：」直接触雷；
   - H1 必须与 front matter `title` 完全一致（长标题容易漏）。
