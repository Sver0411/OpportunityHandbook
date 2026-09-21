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

如果你想写其中某一条，欢迎直接从仓库里认领：把对应文件里的 `status` 从 `planned` 改成 `complete`，补上正文与 `last_verified`，构建会检查格式与来源。

目前计划中：**39** 份专题文档、**64** 条正在规划中的条目。

## 计划中的专题文档


### 专题 · 行业与职业

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

### 专题 · 竞赛专题

- Hackathon 与 Game Jam（`docs/competitions/Hackathon与GameJam.md`）
- 商业与创业竞赛（`docs/competitions/商业与创业竞赛.md`）
- 学科竞赛（`docs/competitions/学科竞赛.md`）
- 数据与 AI 竞赛（`docs/competitions/数据与AI竞赛.md`）

### 专题 · 国家与地区

- 中国香港（`docs/countries/中国香港.md`）
- 加拿大（`docs/countries/加拿大.md`）
- 新加坡（`docs/countries/新加坡.md`）
- 日本（`docs/countries/日本.md`）
- 欧洲大陆（`docs/countries/欧洲大陆.md`）
- 澳大利亚（`docs/countries/澳大利亚.md`）
- 美国（`docs/countries/美国.md`）
- 英国（`docs/countries/英国.md`）
- 韩国（`docs/countries/韩国.md`）

### 专题 · 科研方法

- 实验设计与数据（`docs/research/实验设计与数据.md`）
- 文献阅读与综述（`docs/research/文献阅读与综述.md`）
- 联系导师与套磁（`docs/research/联系导师与套磁.md`）
- 论文写作与投稿（`docs/research/论文写作与投稿.md`）

### 专题 · 来源与核实

- 二手来源与识别方法（`docs/sources/二手来源与识别方法.md`）
- 常用官方来源清单（`docs/sources/常用官方来源清单.md`）
- 核实记录（`docs/sources/核实记录.md`）

### 专题 · 时间线

- 保研时间线（`docs/timelines/保研时间线.md`）
- 博士申请时间线（`docs/timelines/博士申请时间线.md`）
- 本科四年（`docs/timelines/本科四年.md`）
- 校招时间线（`docs/timelines/校招时间线.md`）
- 留学申请时间线（`docs/timelines/留学申请时间线.md`）
- 科研入门时间线（`docs/timelines/科研入门时间线.md`）
- 考研时间线（`docs/timelines/考研时间线.md`）
- 高中到大学（`docs/timelines/高中到大学.md`）

## 规划中的条目（不进导航与搜索）

- 科研与学术：8 条
- 项目作品与开源：8 条
- 社群、导师与行业影响力：8 条
- 创业、自由职业与副业：8 条
- 奖学金、资助与免费机会：6 条
- 找工作：5 条
- 竞赛与挑战：5 条
- 常见低价值投入与陷阱：5 条
- 十八岁以后有哪些路：3 条
- 不知道自己想做什么：3 条
- 实习与第一份工作：2 条
- 工作后的晋升跳槽与转行：2 条
- 技能、语言与证书：1 条

## 怎么参与

见 [CONTRIBUTING.md](../CONTRIBUTING.md) 与 [内容规范](../meta/条目格式.md)。两条硬性要求：

- 每条内容必须写出依据（官方规则 / 研究 / 行业数据 / 实践经验 / 证据不足），并标注最后核实日期。
- `python3 tools/build.py --strict` 必须通过。
