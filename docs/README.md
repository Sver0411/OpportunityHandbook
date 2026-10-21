---
nav: false
id: docs-index
title: 专题索引
type: doc
section: index
order: 2
status: complete
stages: [highschool, secondary_vocational, college, undergraduate, master, phd, new_grad, work_1_3, work_3_5, senior, career_change]
topics: [explore, study, job, research, competition, skill, community, startup]
summary: 专题手册与工具索引：它们不承担人生主线，只作为查询入口。
last_verified: 2026-09-21
---

# 专题索引

正文（`book/`）回答“值不值得、怎么选”，专题（`docs/`）提供按时间、国家与行业组织的可查资料。两者的条目格式与来源要求相同。

## 分工规则

| 目录 | 负责 | 例子 |
| --- | --- | --- |
| `book/` | 判断、方法、路线、决策框架 | 怎么找导师、科研值不值得、什么比赛值得参加 |
| `docs/` | 参考资料、专题细化、时间线、国家与地区、行业、模板与工具 | 日本修士制度、保研时间线、Offer 对比表、导师邮件模板 |

如果专题里已经有一份判断，**不要在 `docs/` 再写一遍**：专题只补专门资料，判断部分引用主指南的对应条目，避免两处说法分叉。

还没写的专题集中列在 [内容路线图](ROADMAP.md)，这些页面不会出现在导航与搜索结果里。

## 状态字段（status）对 `docs/` 的含义

`docs/` 下的专题页（含时间线、国家与地区、行业与职业、工具与模板）使用同一套状态语义：

- **complete**：本页预定的范围已经基本覆盖，可以作为独立专题使用；主要制度入口都有官方来源，没有占位内容。
- **partial**：已经有真实可用的内容，但专题范围仍明显未覆盖完整（例如行业页只写了入口，还未细化到岗位与技能要求）。
- **planned**：只有规划，没有可用正文；这类页面不进导航与搜索。

判断依据是**内容是否真的够用**，不是页面是否被创建。行业类专题在不具备条件时应保持 `partial`，不要为了数字好看标成 `complete`。

## 时间线 `docs/timelines/`

把某一件事的截止日期与准备节奏排成一条线。时间线最容易过期，因此每条都必须标注 `last_verified`，并在政策变化时优先复核。

- [高中到大学](timelines/高中到大学.md)
- [中职升学时间线](timelines/中职升学时间线.md)
- [专升本时间线](timelines/专升本时间线.md)
- [本科四年](timelines/本科四年.md)
- [保研时间线](timelines/保研时间线.md)
- [考研时间线](timelines/考研时间线.md)
- [考公时间线](timelines/考公时间线.md)
- [留学申请时间线](timelines/留学申请时间线.md)
- [留学语言考试时间线](timelines/留学语言考试时间线.md)
- [四六级时间线](timelines/四六级时间线.md)
- [博士申请时间线](timelines/博士申请时间线.md)
- [教师资格与教师编时间线](timelines/教师资格与教师编时间线.md)
- [法考与实习律师时间线](timelines/法考与实习律师时间线.md)
- [规培与执业医师时间线](timelines/规培与执业医师时间线.md)
- [会计与金融证书路径](timelines/会计与金融证书路径.md)
- [城市选择时间线](timelines/城市选择时间线.md)
- [硕士阶段时间线](timelines/硕士阶段时间线.md)
- [博士阶段时间线](timelines/博士阶段时间线.md)
- [海外在读与身份转换时间线](timelines/海外在读与身份转换时间线.md)
- [科研入门时间线](timelines/科研入门时间线.md)
- [实习准备时间线](timelines/实习准备时间线.md)
- [校招时间线](timelines/校招时间线.md)
- [银行校招时间线](timelines/银行校招时间线.md)
- [国企与央企校招时间线](timelines/国企央企校招时间线.md)
- [入职第一年](timelines/入职第一年.md)
- [在职学历提升时间线](timelines/在职学历提升时间线.md)
- [转行时间线](timelines/转行时间线.md)
- [海外工作与签证时间线](timelines/海外工作与签证时间线.md)
- [离职与纠纷维权](timelines/离职与纠纷维权.md)

## 学习方法 `docs/learning/`

- [用 AI 学习与工作](learning/用AI学习与工作.md)
- [账号、数据与隐私](learning/账号数据与隐私.md)

## 权益与制度 `docs/rights/`

- [离职、换工作与社保衔接](rights/离职与社保衔接.md)
- [劳动合同要看哪些条款](rights/劳动合同要看哪些条款.md)
- [被欠薪与劳动仲裁](rights/被欠薪与劳动仲裁.md)
- [遇到纠纷找谁：求助顺序](rights/遇到纠纷找谁.md)

## 工具、案例与操作手册

`docs/tools/`（49 份表格模板）、`docs/cases/`（19 个完整案例）与 `docs/playbooks/`（29 份操作手册）
按用途分别汇总在主线的三章里，避免两处维护：

- [12 工具与模板](../book/12-工具与模板.md)
- [13 完整案例](../book/13-完整案例.md)
- [14 操作手册](../book/14-操作手册.md)

**案例一览**（18 个，都保留失败与返工分支）

- 项目与科研：[第一次做真正项目](cases/第一次做真正项目.md) · [教程项目到工程作品](cases/教程项目到工程作品.md) · [本科生第一次科研](cases/本科生第一次科研.md) · [联系导师的完整过程](cases/联系导师.md) · [第一次开源贡献](cases/第一次开源贡献.md) · [第一次投稿被拒](cases/第一次投稿被拒.md)
- 升学与作品：[留学选校](cases/留学选校.md) · [从竞赛到作品集](cases/从竞赛到作品集.md) · [第一次在职读本科](cases/第一次在职读本科.md)
- 求职：[第一次找技术实习](cases/第一次找技术实习.md) · [第一次在海外找实习](cases/第一次在海外找实习.md) · [两个 Offer 怎么选](cases/两个Offer怎么选.md) · [第一次面试失败](cases/第一次面试失败.md)
- 工作与生活：[第一次转行](cases/第一次转行.md) · [第一次自由职业客户](cases/第一次自由职业客户.md) · [第一次被欠薪](cases/第一次被欠薪.md) · [第一次买保险](cases/第一次买保险.md) · [第一次看心理科](cases/第一次看心理科.md)

**操作手册一览**（29 份）

- 入学与毕业：[大学新生入学与第一个月](playbooks/大学新生入学与第一个月.md) · [研究生入学第一个月](playbooks/研究生入学第一个月.md) · [家里第一个上大学](playbooks/家里第一个上大学.md) · [本科毕业论文与毕业设计](playbooks/本科毕业论文与毕业设计.md) · [毕业去向与离校手续总清单](playbooks/毕业去向与离校手续总清单.md) · [学籍异常与学校事务申诉](playbooks/学籍异常与学校事务申诉.md) · [兼职与校园诈骗风险](playbooks/兼职与校园诈骗风险.md)
- 项目与科研：[第一次做项目](playbooks/第一次做项目.md) · [第一次开源贡献](playbooks/第一次开源贡献.md) · [把一项新技术学到能用](playbooks/第一次学新技术.md) · [第一次参加 Hackathon](../book/14-操作手册.md) · [第一次做实验与记录](playbooks/第一次做实验.md) · [第一次写论文](playbooks/第一次写论文.md) · [第一次联系导师](playbooks/第一次联系导师.md)
- 求职与入职：[第一次找实习](playbooks/第一次找实习.md) · [第一次信息访谈](playbooks/第一次信息访谈.md) · [第一次技术面试](playbooks/第一次技术面试.md) · [第一次谈薪](playbooks/第一次谈薪.md) · [上岸后第一年](playbooks/上岸后第一年.md)
- 考试与证书：[第一次准备考公笔试](playbooks/第一次准备考公笔试.md) · [第一次准备考研](playbooks/第一次准备考研.md) · [第一次考四六级](playbooks/第一次考四六级.md) · [第一次准备专升本](playbooks/第一次准备专升本.md) · [第一次填志愿](playbooks/第一次填志愿.md) · [第一次评估证书](playbooks/第一次评估证书.md)
- 资助、合同与其他：[第一次申请资助](playbooks/第一次申请资助.md) · [第一次接单](playbooks/第一次接单.md) · [第一次核对合同与社保](playbooks/第一次核对合同与社保.md) · [第一次处理劳动争议](playbooks/第一次处理劳动争议.md)

## 国家与地区 `docs/countries/`

按国家与地区写清楚学位类型、申请材料、资金、签证与毕业后安排。**每个国家主题都必须引用官方来源**（移民部门、教育部、大学官方页面），不能只引用中介或论坛信息。

- [美国](countries/美国.md) · [加拿大](countries/加拿大.md) · [英国](countries/英国.md) · [欧洲大陆](countries/欧洲大陆.md)
- [日本](countries/日本.md) · [韩国](countries/韩国.md) · [新加坡](countries/新加坡.md)
- [中国香港](countries/中国香港.md) · [澳大利亚](countries/澳大利亚.md) · [新西兰](countries/新西兰.md)
- [中国大陆](countries/中国大陆.md)（国内路径的制度与升学结构，与境外页同一套写法）

## 行业与职业 `docs/careers/`

写清一个行业里有哪些岗位、需要什么准入条件、怎么进入、以及转出的可能性。不默认互联网，也不默认计算机专业。

- [技术与工程](careers/技术与工程.md) · [商业与金融](careers/商业与金融.md) · [设计与创意](careers/设计与创意.md)
- [医疗健康](careers/医疗健康.md) · [生命科学](careers/生命科学.md) · [教育](careers/教育.md)
- [法律与公共事务](careers/法律与公共事务.md) · [科研与高校](careers/科研与高校.md) · [制造](careers/制造.md)
- [技能型职业](careers/技能型职业.md) · [公共服务](careers/公共服务.md) · [AI 与数据](careers/AI与数据.md)

## 具体岗位 `docs/career-guides/`

一个行业讲环境与分工，一个岗位讲每天做什么、怎么进、3–5 年后往哪走。每个岗位页都含招聘流程与门槛、面试问什么、常见误区与低成本试法。

- **技术研发**：[软件工程师](career-guides/软件工程师.md) · [前端](career-guides/前端工程师.md) · [后端](career-guides/后端工程师.md) · [算法](career-guides/算法工程师.md) · [数据工程](career-guides/数据工程师.md) · [嵌入式](career-guides/嵌入式工程师.md) · [硬件](career-guides/硬件工程师.md) · [测试与质量](career-guides/测试与质量.md) · [运维与 SRE](career-guides/运维与SRE.md) · [研究工程师](career-guides/研究工程师.md) · [FDE](career-guides/FDE.md) · [解决方案与售前](career-guides/解决方案与售前.md) · [技术支持与客户成功](career-guides/技术支持与客户成功.md)
- **数据与产品**：[数据分析师](career-guides/数据分析师.md) · [产品经理](career-guides/产品经理.md) · [运营](career-guides/运营.md)
- **商业与金融**：[财务与金融分析](career-guides/财务与金融分析.md) · [咨询](career-guides/咨询.md) · [销售](career-guides/销售.md) · [人力资源](career-guides/人力资源.md)
- **公共服务**：[公共部门](career-guides/公共部门.md)
- **教育与科研**：[教师](career-guides/教师.md) · [研究员与高校教职](career-guides/研究员与高校教职.md)
- **医疗健康**：[临床医生](career-guides/临床医生.md) · [护士](career-guides/护士.md)
- **法律**：[律师与法务](career-guides/律师与法务.md)
- **制造与技能**：[制造业研发](career-guides/制造业研发.md) · [技能型职业](career-guides/技能型职业.md)
- **设计与创意**：[设计师](career-guides/设计师.md)

## 科研方法 `docs/research/`

- [文献阅读与综述](research/文献阅读与综述.md)
- [联系导师与套磁](research/联系导师与套磁.md)
- [实验设计与数据](research/实验设计与数据.md)
- [论文写作与投稿](research/论文写作与投稿.md)

## 竞赛专题 `docs/competitions/`

- [学科竞赛](competitions/学科竞赛.md)
- [数据与 AI 竞赛](competitions/数据与AI竞赛.md)
- [商业与创业竞赛](competitions/商业与创业竞赛.md)
- [Hackathon 与 Game Jam](competitions/Hackathon与GameJam.md)

## 来源与核实 `docs/sources/`

- [常用官方来源清单](sources/常用官方来源清单.md)
- [官方入口速查](sources/官方入口速查.md)
- [二手来源与识别方法](sources/二手来源与识别方法.md)
- [核实记录](sources/核实记录.md)

## 当前状态

上述专题里尚未撰写的部分标着 `status: planned`：它们包含 front matter、计划内容与官方来源入口，但正文还没写。这类页面**不会**出现在在线导航、搜索结果与筛选里，只汇总在[内容路线图](ROADMAP.md)。
