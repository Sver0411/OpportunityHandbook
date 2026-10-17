# 读者视角修复记录（15 轮）

修复时间：2026-10-17
基线审查：[reader-usability-round3-2026-10-17.md](reader-usability-round3-2026-10-17.md)
范围：`book/` 正文、`tools/ia_canonical.py`、`tools/reader_navigation.py`、`tools/tests/`、`meta/home-questions.md`、三篇 `docs/`、`docs/ROADMAP.md`
节奏：一轮一提交、一轮一推送（共 15 轮，16 次提交）

---

## 一、指标对照

| 指标 | 修复前 | 修复后 |
| --- | ---: | ---: |
| 「相关」区块由模板生成（同一块被 ≥4 条共用） | 51 条 / 7 块 | **0**（最多 3 条同组复用） |
| 「什么时候要谨慎」不在篇末 | 66 条 | **0** |
| 跨小节重复句（相似度 > 0.6） | 13 条 | **5 条**，逐条人工确认为误报（同一事实分别出现在「做法」与「谨慎」两节） |
| 裸术语标题（必须先知道词才能点） | 27 条 | **0**（余 7 条为 GPA、MVP、SOP/PS 等通用缩写） |
| 避坑章结构 | 13 条平铺、无导读 | **6 组 + 章首导读 + 分组表** |
| 00 章分流表覆盖处境 | 17 种 | **22 种** |
| 首页问题无答案 | 5 条 | **0** |
| 正文条目 | 417 | **419**（新增入党与学生干部、校际交换与联合培养） |
| 来源审计 | ①6 ②1 ③1 | **全 0** |
| 发布校验 | 15 项通过（带 1 项路线图漂移） | **15 项全通过** |
| 内容规则测试 | 76 项 OK | **76 项 OK** |

---

## 二、逐轮清单

| 轮次 | 内容 | 提交 |
| ---: | --- | --- |
| 1 | 54 条「相关」换成本篇相邻内容；66 条谨慎小节移到篇末；15 章补导读与索引；00 章分流表补 6 种处境；合并 5 条双稿；首页问题 2 处 | `34e2b92` |
| 2 | 暑期实习删掉重复的「按校招节奏提前一季准备」；读博条把「决定前四件事」并为三件 | `90c0ad4` |
| 3 | 内推、技术还是管理、换行业三条合并重复小节 | `5150f96` |
| 4 | 三条条目清掉重复的边界提醒（Team Lead / 技能反推 / 长期求职） | `93a1555` |
| 5 | 避坑章拆成 6 组：改 IA 缩进、章节 `##`、`GROUP_TASKS["15"]`、重建导航；15 章的两条按 id 归属而非标题 | `281f1b0` |
| 6 | 首批 10 个裸术语标题改写（Demo / Issue / PR / Documentation / Review / Maintainer / Ownership / Mentor / Team Lead / Manager） | `fe5147a` |
| 7 | 第二批 10 个（RA / Research Internship / Off-cycle / Research Intern / Scholarship / Fellowship / Grant / Stipend / Fee Waiver / Travel Grant） | `defe9c4` |
| 8 | 第三批 10 个（Student Chapter / Meetup / Networking / Organizer / Speaker / Reviewer / Incubator / Accelerator / Bridge / Side Project） | `b853201` |
| 9 | 分流表接三张工具表；补齐 5 条首页问题的空答案 | `a00db13` |
| 10 | 新增「入党与学生干部」；IA 基线上调（462→463、417→418） | `aa91136` `18cb0e7` |
| 11 | 新增「校际交换与联合培养」；基线 464/419 | `06ac401` |
| 12 | 修「后者」远距离指代；补社区条目的官方来源；健康条目标注 Research-backed；补家庭沟通的来源小节；删掉 05 章末混进条目的章级收尾 | `a057616` |
| 13 | 三篇偏短 docs 补对照案例（信息访谈问法对照、评审意见改写、学过 vs 会）；清掉社保条目的重复句 | `5628b4f` |
| 14 | 随新增条目重建 `docs/ROADMAP.md`；完整校验 15 项通过 | `ba8182f` |
| 15 | 实习经历条目删掉重复示例；本记录 | 见末次提交 |

---

## 三、几个可复用的判断

### 怎么发现「模板化的相关」

对每条条目的「相关」区块取原文做哈希，统计同一块被多少条共用。**≥4 条共用基本就是脚本注入，不是编辑判断。**

原状：51 条共用 7 块。最糟的是 04 章 14 条（读研值不值得、考研、SOP、Research Proposal、暑研、论文写作、科研推荐信……）全部指向「转行前先判断什么」。读者读完 Research Proposal，唯一的下一篇推荐是转行——这不是排序问题，是没有编辑。

### 谨慎小节的位置是承诺

`guide-how-to-use` 写了「哪些情况下应该谨慎，往往比怎么做更值得先读」。这句话只有在**位置固定**时才成立。修复前 66 条把这一节放在中间，后面还接着 1–5 节别的正文。

例外要留住：`paths-freelance` 的「需要提前确认的边界」是兼职与竞业的法律条款，属正文而不是收尾，保留在「什么时候该考虑回去上班」之前。

### 15 章分组踩到的两个坑

1. **条目名与组名撞车**：原条目名就叫「升学与留学」「求职与实习」，与新建组名相同，锚点会冲突；改名为「保录取、内部名额与包过」「收费实习与付费科研」。
2. **归属不能按标题查**：`reader_navigation.py` 里 15 章原本按标题映射任务；分组后标题变了，必须改成按 `record["id"]` 映射，否则构建直接报「assign 15/… to a task」。

改分组要同时动四处：`ia_canonical.py` 缩进、章节 `##` 标题、`GROUP_TASKS`/15 章分支、重建 `meta/navigation.json`。

### 标题改写的规则

保留英文术语（搜索还能命中），后面接「它解决什么」：

- `PR` → `PR：一次可以被验证的贡献`
- `Ownership` → `Ownership：从「做完」到「负责到底」`
- `Grant` → `Grant：项目经费怎么申请`

改标题必须同步 `ia_canonical.py` 的标题列；`meta/navigation.json` 由 `build_navigation.py` 重新生成。

### 校验器的两个盲点（这次顺手补掉）

- `audit_sources.py` 用 `body.split("来源与更新")[-1]` 取来源段。05 章末混入的章级收尾带第二个「来源与更新」，导致末条被误判「声明 Official 但无标注」。已把章级收尾删掉——它本来就是重复的索引信息。
- 页面底部若只有「见 […]」没有正文，首页问题会显得空。这次扫出 5 条，全部补了一句可执行的判断。

---

## 四、还没做的

| 事项 | 说明 |
| --- | --- |
| `docs/` 其余 25 篇复核 | `audit_depth_quality.py` 仍列 25 篇「短 + 缺案例」，多为深度教程，需逐篇读后再补 |
| 5 条重复信号 | `career-break-return`、`job-gap-period`、`work-open-source`、`apprenticeship`、`internship-summer`：同一事实分别写在「做法」与「谨慎」，措辞不同，人工判断保留 |
| 外链 WARN 25 条 | `check_links.py`：PASS 113 / WARN 25 / FAIL 0。WARN 多为证书或反爬站点（如 `scs.gov.cn` 证书名不匹配），需人工确认是否替换入口 |
| 移动端真机 | 只跑了既有冒烟用例，未在真机与窄屏逐页看 |
| 搜索召回 | 抽查 30 个问法无空结果，但未做长尾问法的系统评估 |

---

## 五、验证命令

```bash
python3 tools/build.py --strict --no-links     # 273 文件 / 条目 464 / 完成 419
python3 tools/check_ia.py                       # Broken 0 / Orphan 0
python3 tools/check_anchors.py                  # 页内锚点 3145 条，死链 0
python3 tools/run_tests.py                      # 76 tests OK
python3 tools/validate_release.py --quick       # 15 项 PASS（外链 113/25/0）
```
