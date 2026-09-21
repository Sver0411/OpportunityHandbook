# Final Consolidation Report

生成时间：2026-09-22

本轮定位：**Final Content Consolidation** —— 不扩张结构，把现有 303 个 complete 条目
从「结构完整」提升到「正文达到长期公开维护标准」。信息架构（Canonical IA）、
`meta/navigation.json`、栏目顺序、nav_id 与条目映射全程未改动。

## 1. 指标对照

| 指标 | 本轮开始时 | 本轮结束时 |
| --- | --- | --- |
| complete 条目 | 303 | 303 |
| P0（有效正文 < 120 字） | 124 | **0** |
| P1（120–250 字，人工审查清单） | 39 | 17 |
| 旧模板残留（legacy template） | 0 | 0 |
| 缺 summary | 0 | 0 |
| Markdown 错误 | 0 → 回退到 110（批处理副作用，已修复） | **0** |
| stage suspicious（职场章节无工作阶段） | 0 | 0 |
| stage overbroad（职场中后期仍挂学生阶段） | 1 | **0** |
| stage invalid（非法或空 stages） | 0 | 0 |
| IA missing / broken / orphan / duplicate | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| 单元测试 | 47 项通过 | 47 项通过 |
| 浏览器冒烟 | 通过 | 通过 |
| CI（内容校验） | success | success |
| Pages 部署 | success | success |

## 2. 内容补写（本轮主体工作）

按优先级分三批补写，共 **124 篇**，全部按各自问题组织，没有使用统一模板：

- **P0-A 重要决策类 31 篇**：实习和项目/科研怎么选、科研还是产业、能否并行多条路线、
  主线与备选、选导师、海外实习、招聘 JD 怎么读、薪资总包、毁约、降低岗位要求、
  换城市、继续升学、空窗期、第一次选择错了、技术还是管理；跳槽动机/时机/平薪/涨薪、
  换行业、换城市、转行前判断、可迁移行业经验、Side Project 转行、工作后读硕士、
  MBA/MPA、第二硕士、海外教育、职业中断回归、第二职业。
  判断型文章统一给出：先看什么 → 偏向 A/B 的条件 → 双方成本 → 回退难度 → 低成本验证。
- **P0-B 职业成长类 20 篇**：理解业务、和领导合作、Ownership、承担更大项目、证明成果、
  业务影响、继续学习、个人项目/开源、内部转岗、海外工作、第一次带人、Team Lead、
  招聘、绩效、专业深度、跨团队影响、行业影响、长期不晋升、再次没方向。
  行动型文章给出可直接照做的步骤与自检标准。
- **P0-C 概念与短条目 73 篇**：开源四词条（PR / Documentation / Review / 贡献定义）、
  Demo、数据测试指标、用户反馈、社团、专业协会、Meetup、Speaker、Organizer、
  竞赛与科研概念词条、02 章学业与技能（含创作型与行动型）、05 章校招执行（渠道 /
  简历 / 面试 / Offer）、01 章路线与成本、04 章资助词条（Scholarship / Fellowship /
  Grant / Stipend / Fee Waiver）、08 章副业与创业词条。概念类保持 200–400 字量级，
  按「它是什么 / 什么时候有用 / 怎么做 / 最容易犯什么错」组织。

长度参考（不设硬约束）：概念词条 200–400 字，判断型 400–800 字，复杂决策 800 字以上。

## 3. stages 精确化

- 06/07/08 三章 **83 条** stages 从「追加式修复」改为按「这个问题通常发生在哪个阶段」
  重写：第一次带人 → `[work_1_3, work_3_5]`；Staff / Principal → `[work_3_5, senior]`；
  绩效 → `[work_1_3, work_3_5, senior]`；转行类 → 加入 `career_change` 等；
  「工作后读硕士 / MBA / 第二硕士 / 海外教育」去掉本科与硕士在读阶段。
- 05 校招章节按定义保留学生阶段（college / undergraduate / master / phd / new_grad），
  不再统一追加 `work_1_3`。
- `tools/metadata_audit.py` 新增第二类检查 **stage_overbroad**（职场中后期条目仍混入
  学生阶段），仅报告不自动修改。

## 4. CI 结构：hard gate 与 depth audit 分离

```
python3 tools/check_content_quality.py --hard    # 阻塞：旧模板 / 缺 summary / P0 过薄
python3 tools/check_content_quality.py --depth   # 只报告：生成 reports/content-depth.md
```

- `--hard` 已把 **P0 < 120 字** 纳入阻塞项（P0 清零后按计划启用）；
- `--depth` 永远 exit 0，P0/P1 清单写入 `reports/content-depth.md`；
- CI（`.github/workflows/ci.yml`）分别执行以上两步，另有 `check_ia`、
  `check_markdown_quality`、`metadata_audit`（报告级）与 `run_tests`。

## 5. Absolute / Overclaim Audit

- 扫描词表：唯一 / 只有 / 必须 / 一定 / 绝对 / 普遍 / 多数 / 通常 / 主战场 / 确保 /
  保证 / 最重要 / 更重要 / 优先 / 不会 / 一定会；
- 本轮实际修改 **6 处**过度绝对表述：
  「读博值得的前提只有一个」→「读博最常见的合理理由，是……」；
  「降薪转行值得接受的条件只有三个」→「至少需要重点检查三个条件……」；
  「不要自费读博」→「如果缺乏稳定资助，需特别谨慎核算长期现金流与机会成本……」；
  「跨团队影响唯一稳定的基础」→「最稳定的基础」；
  「唯一能避免感觉式纠结的办法」→「比较稳妥的办法」；
  「选导师重于选学校」→「在以科研训练为核心的项目里，导师匹配度通常是重要变量……」。
- 其余命中项判定为：官方硬规则（如「法定准入必须持证上岗」）、结构性陈述
  （如「本书只做索引」）或已带条件与来源的表述，保留不动。

## 6. 来源颗粒度

- 关键制度来源从「部委首页」升级为**具体文件页**：教研厅〔2016〕2 号（非全日制统筹）、
  教研厅函〔2019〕1 号、人社部《国家职业资格目录（2021 年版）》答记者问（含 72 项构成）、
  技能人才评价工作网、财教〔2024〕181 号（奖助学金调整），共 4 个文件升级到条款级链接。
- 国家专题本轮按要求**不全面扩写**，只做错误修正与误导性表述清理：日本页重写
  （区分语言学校 / 研究生（非学位生）/ 修士 / 博士，删除伪固定路径），
  其余国家页暂维持入口级厚度，留待逐国维护。

## 7. 仓库整理

- 根目录过程报告迁入 `reports/`：
  `content-depth.md`、`content-quality-round.md`、`ia-parity.md`、
  `ia-writing-refactor.md`、`metadata-audit.md`、`p1-ux-reliability.md`；
  相关脚本的输出路径已同步更新（`ia_report.py`、`metadata_audit.py`、
  `check_content_quality.py`）。
- 一次性迁移脚本迁入 `tools/migrations/`：`apply_articles.py`、`migrate_ia.py`、
  `naturalize.py`、`naturalize_fields.py`、`refactor_book.py`、`restructure_chapters.py`，
  并新增 `tools/migrations/README.md` 说明用途与风险（含「正则必须行有界」的教训）。
  迁移脚本的 `ROOT` 已修正为仓库根，运行时需 `PYTHONPATH=tools`。
- 根目录现在只剩：`README.md`、`LICENSE`、`LICENSE-CONTENT`、`CONTRIBUTING.md`
  与 `book/ docs/ meta/ site/ tools/ reports/`。
- `README.md` 新增「维护工具」一节，列出全部检查命令与报告位置。

## 8. 仍需人工复核的问题（诚实清单）

- **P1（120–250 字）17 篇**：可用但不丰满，清单见 `reports/content-depth.md`。
  这些多为概念型条目，属于本报告认可的长度区间，是否需要扩写按实际阅读体验判断。
- **国家页厚度**：除日本页外，其余国家与行业页仍偏入口级；本轮按要求不做全面扩写。
- **外部链接**：本地构建时有 4 条外链因沙箱代理不可达（github.com、gov.uk、
  summerofcode.withgoogle.com、xszz.cee.edu.cn）与 4 条 SSL 握手告警
  （cpta.com.cn、csls.cdb.com.cn、immigration.govt.nz、npc.gov.cn）；
  CI 对 403/429/5xx 与不可达按非阻塞处理，这些是本地网络环境问题，不是失效链接。

## 9. 回归命令

```bash
python3 tools/build.py --strict --report
python3 tools/check_ia.py
python3 tools/check_markdown_quality.py
python3 tools/check_content_quality.py --hard
python3 tools/check_content_quality.py --depth
python3 tools/metadata_audit.py
python3 tools/run_tests.py
python3 tools/smoke_test.py
```
