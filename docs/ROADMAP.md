---
nav: false
id: docs-roadmap
title: 内容路线图
type: doc
section: index
order: 3
status: complete
summary: 计划中的专题与条目清单。这些页面尚未撰写正文，因此不出现在在线导航与搜索结果里。
last_verified: 2026-09-21
---

# 内容路线图

这份清单上的内容**还没有写**。它们不出现在在线手册的导航、搜索结果与筛选结果里——目的就是不让读者点进一个只有标题的空页面。

想认领其中某一条：把对应文件里的 `status` 从 `planned` / `todo` 改成 `complete`，补上正文、`summary` 与 `last_verified`，构建会检查格式与来源。

目前计划中：**39** 份专题文档、**110** 条规划中的条目。

## 计划中的专题文档


### 09 专题手册 · 行业与职业

- 公共服务（`docs/careers/公共服务.md`）
- 制造业（`docs/careers/制造业.md`）
- 医疗健康（`docs/careers/医疗健康.md`）
- 商业与金融（`docs/careers/商业与金融.md`）
- 技术与工程（`docs/careers/技术与工程.md`）
- 技能型职业（`docs/careers/技能型职业.md`）
- 教育（`docs/careers/教育.md`）
- 法律与公共事务（`docs/careers/法律与公共事务.md`）
- 生命科学（`docs/careers/生命科学.md`）
- 科研（`docs/careers/科研.md`）
- 设计与创意（`docs/careers/设计与创意.md`）

### 09 专题手册 · 竞赛手册

- Hackathon 与 Game Jam（`docs/competitions/Hackathon与GameJam.md`）
- 商业与创业竞赛（`docs/competitions/商业与创业竞赛.md`）
- 学科竞赛（`docs/competitions/学科竞赛.md`）
- 数据与 AI 竞赛（`docs/competitions/数据与AI竞赛.md`）

### 09 专题手册 · 国家与地区

- 中国香港（`docs/countries/中国香港.md`）
- 加拿大（`docs/countries/加拿大.md`）
- 新加坡（`docs/countries/新加坡.md`）
- 日本（`docs/countries/日本.md`）
- 欧洲大陆（`docs/countries/欧洲大陆.md`）
- 澳大利亚（`docs/countries/澳大利亚.md`）
- 美国（`docs/countries/美国.md`）
- 英国（`docs/countries/英国.md`）
- 韩国（`docs/countries/韩国.md`）

### 09 专题手册 · 科研手册

- 实验设计与数据（`docs/research/实验设计与数据.md`）
- 文献阅读与综述（`docs/research/文献阅读与综述.md`）
- 联系导师与套磁（`docs/research/联系导师与套磁.md`）
- 论文写作与投稿（`docs/research/论文写作与投稿.md`）

### 09 专题手册 · 来源与核实

- 二手来源与识别方法（`docs/sources/二手来源与识别方法.md`）
- 常用官方来源清单（`docs/sources/常用官方来源清单.md`）
- 核实记录（`docs/sources/核实记录.md`）

### 10 时间线与工具 · 路径时间线

- 保研时间线（`docs/timelines/保研时间线.md`）
- 博士申请时间线（`docs/timelines/博士申请时间线.md`）
- 本科四年（`docs/timelines/本科四年.md`）
- 校招时间线（`docs/timelines/校招时间线.md`）
- 留学申请时间线（`docs/timelines/留学申请时间线.md`）
- 科研入门时间线（`docs/timelines/科研入门时间线.md`）
- 考研时间线（`docs/timelines/考研时间线.md`）
- 高中到大学（`docs/timelines/高中到大学.md`）

## 规划中的条目（不进导航与搜索）

- 当你开始面对第一次重要分流：20 条
- 进入职场以后继续积累：20 条
- 开始积累真正能留下来的经历：16 条
- 在学校里先把基础打好：13 条
- 其他同样成立的人生路径：10 条
- 先决定下一步往哪里走：9 条
- 从学校走向第一份工作：7 条
- 当职业开始出现分岔：6 条
- 避坑：5 条
- 从这里开始：4 条

## 怎么参与

见 [CONTRIBUTING.md](../CONTRIBUTING.md) 与 [内容规范](../meta/条目格式.md)。两条硬性要求：

- 每条内容写明依据（官方规则 / 研究 / 行业数据 / 实践经验 / 证据不足），并标注最后核实日期。
- `python3 tools/build.py --strict` 必须通过。
