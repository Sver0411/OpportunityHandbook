# Full-Site Final Audit

生成时间：2026-09-22

本轮定位：**Full-Site Final Consolidation**。不新增功能与目录，只解决已存在页面的
正文质量、导航质量、metadata 准确性与事实可靠性。Canonical IA、`meta/navigation.json`
的主结构、402 个节点的父子关系与主线顺序**全程未改动**。

## 一、Navigation / TOC

| 指标 | 修改前 | 修改后 |
| --- | --- | --- |
| Canonical 节点 | 402 | 402（未变） |
| 可解析节点 | 402 | 402 |
| broken target | 0 | 0 |
| orphan / duplicate mapping | 0 / 0 | 0 / 0 |
| **HTML 重复 id** | 每个章节页几十个（`id="来源与更新"` 重复） | **0**（83 个页面全量检查） |
| 右栏 TOC 作用域 | 混入整章所有 H2 与所有条目 H3 | 打开条目时**只显示该条目内部 H2**；打开章节根页显示章节结构 |
| TOC 错跳 | 同名标题会跳到别的条目 | 每个锚点全文档唯一，跳到自己的位置 |

实现方式：

1. **heading id 唯一化**：条目内标题渲染为 `{entry_id}--{slug}`（同一 entry 内重复再追加 `-2`、`-3`）。新增 `mdrender.begin_document()` / `set_id_prefix()`；构建时每个 HTML 文档重置计数。
2. **旧深链不受影响**：条目锚点仍是 `#/doc/.../{entry_id}`，只有条目内部 H2 的锚点变了；检查确认**没有**内部链接指向 H2 锚点（全部指向 entry id），因此零破坏。
3. **右栏作用域**：`buildToc(entryId)` —— 定位到条目时只取该条目内的 H2；章节根页取 `.doc > h2` 与 `.entry > h3`。
4. **新增测试**：`tools/check_html_ids.py`（重复 id 与条目前缀，已接入发布校验）；冒烟测试新增「右侧目录作用域」用例组（03 第一个个人项目 / 04 保研 / 05 Offer 比较 / 06 Mentor / 07 技术还是管理 / 08 自由职业），断言右栏项数等于该条目 H2 数、全部带本条目前缀、锚点全文档唯一、点击后滚动到正确位置。

## 二、Article Naturalization（正文自然化）

`tools/audit_article_structure.py`（新增，report-only）用于发现「批量模板感」。

| 指标 | 修改前 | 修改后 |
| --- | --- | --- |
| 含模板式 H2 的条目 | 116 | **0** |
| 模板式 H2 总数 | 132 | 0 |
| 连续 ≥3 个模板式 H2 的条目 | 2 | 0 |
| 出现次数最多的模板 H2 | 「能换回什么、付出什么」56 次 | — |

处理方式：**逐条按该篇文章的内容改写成各自的小节标题**，不做批量改名。例如

- `paths-military`：能换回什么、付出什么 → 「服役换回的是退役后的通道，代价是几年时间」；
- `hop-same-pay`：能换回什么、付出什么 → 「换方向、平台或环境，而不是换薪资」；
- `mgmt-hiring`：常见误区 → 「把「聊得来」当能力信号」；
- `project-demo`：容易踩的坑 → 「演示最容易做错的地方」。

保留的通用标题：「来源与更新」290 处（统一来源章节，见第五节），以及少数确实贴题的
标题（如某些清单式小节的「五步流程」）。**没有为了指标清零而牺牲可读性。**

## 三、Metadata

| 指标 | 修改前 | 修改后 |
| --- | --- | --- |
| doc front matter **非法 facet** | 存在（`docs/README.md`、`docs/tools/时间线检查表.md` 的 `topics: qualification`）且 CI 未拦截 | **0**（新增文档级 facet 校验，非法取值即 CI FAIL） |
| docs 缺 topics | 0 | 0 |
| entry stage suspicious / overbroad / invalid | 0 / 0 / 0 | 0 / 0 / 0 |
| topic suspicious | 0 | 0 |

本轮修正：

- `meta.py` 增加**文档级 facet 校验**（`stages/topics/outputs/evidence` 必须命中枚举；`type: doc` 必须有 `stages`，章节页不强制，`nav: false` 的内部页跳过）；
- 专题手册 topics 从「全部 `[explore]`」改为按内容标注：科研→`research`、竞赛→`competition`、项目与作品→`project`、开源→`project, community`、技能/证书→`skill`、语言与考试→`skill, study`、奖学金与资助→`funding`、社群→`community`、创业与自由职业→`startup`；
- 专题手册 stages 收紧到真实发生阶段（如科研 `[undergraduate, master, phd]`、竞赛 `[highschool, secondary_vocational, college, undergraduate, master]`）；
- 时间线 stages 全面重设（高中到大学 `[highschool, secondary_vocational]`、本科四年 `[undergraduate]`、保研 `[undergraduate]`、考研 `[undergraduate, new_grad, work_1_3]`、校招 `[college, undergraduate, master, phd, new_grad]`、转行 `[work_1_3, work_3_5, senior, career_change]` …）；
- 工具页按用途修正（导师筛选表→`research, study`；求职追踪表→`job` 且 stages 补齐校招阶段；职业资本盘点表与转行 Bridge Plan→`job, explore` 且 stages 移到工作阶段）；
- `metadata_audit.py` 扩展到 docs front matter（非法 facet、缺 topics）。

**注入测试**：临时把 `docs/tools/时间线检查表.md` 的 `topics` 改成 `qualification` →
`validate_release.py` 直接失败（构建与元数据校验、内容规则测试），撤销后回到 PASS。

## 四、Timelines

新增 `tools/audit_timeline.py`，输出 `reports/timeline-review.md`（只报告不阻塞）。

| 页面 | 是否修改 | 原问题 | 修改方式 | 依据类型 |
| --- | --- | --- | --- | --- |
| 高中到大学 | 是 | 「出分后 72 小时」像通用时间线；「因漏确认滑档的案例并不少」无来源 | 改为「出分后：立即进入志愿填报窗口」，明确各省时间/批次/确认方式不同；删除无来源断言 | Experience-based |
| 本科四年 | 是 | 缺边界说明 | 开头补「常见节奏，不必按格执行；资格与考试以当年规定为准」 | Experience-based |
| 保研时间线 | 是 | 「名额由前三年成绩决定」「夏令营是主战场」「九月是补录、名额明显少」 | 改为「资格来自前几年累积 + 最后一学年集中选择」，夏令营/预推免标注为「若目标院校有」并说明以学院通知为准，明确最终以推免服务系统待录取为准 | Official（研招网）+ Experience |
| 考研时间线 | 是 | 把出分/国家线/复试月份写成固定规则 | 保留复习节奏，日期改为「常见节奏」并注明以教育部、研招网与招生单位公布为准 | Official |
| 校招时间线 | 是 | 「提前批 6–8 月、秋招 9–11 月、春招 3–4 月」刚性；「内推能确保简历被看到」 | 标题改为「常见范围：X–Y 月」，开头声明不存在全国统一日历；内推改为「可能提高被查看的机会，不保证筛选通过」 | Experience-based |
| 留学申请时间线 | 是 | 实际是研究生倒排模板却写成「留学申请时间线」 | 开头明确「研究生申请通用倒排框架，不是统一申请日历」，并指向各国专题 | Experience-based |
| 博士申请时间线 | 是 | 「国内申请考核制与海外 PhD 都建议先联系导师」过度泛化 | 改为区分「要求导师接收/导师制强的项目」与「委员会制项目」，国内按院系办法 | Official + Experience |
| 科研入门时间线 | 是 | 阶段像硬性日程 | 开头明确「示意节奏，不要求按月份逐格执行」 | Experience-based |
| 转行时间线 | 是 | 阶段像硬性日程 | 同上，并说明个人起点与行业门槛差异很大 | Experience-based |

审计剩余 10 处命中均为**已标注「常见范围」的标题**或经验节奏（如「3–6 月：定目标、过第一轮」），已列为人工判断项，不再强改。

## 五、公开内容与施工痕迹

| 项目 | 结果 |
| --- | --- |
| 用户可见「计划中 / TODO / 待补 / 施工 / ROADMAP」 | **0**（`科研手册`、`竞赛手册` 的「更细的参考资料（计划中）」已删除；新增硬门：用户可见页面出现施工语言即 CI FAIL） |
| planned 页面是否暴露 | 不暴露：`status: planned` 与 `nav: false` 页面不进导航与搜索，且不参与施工语言检查 |
| README / 规范旧正文模型 | 0（README 改为「按问题自然组织」+ 六条共享纪律；`meta/条目格式.md`、`meta/写作规范.md`、`meta/证据与来源规范.md` 的固定字段与旧章节引用全部更新） |
| `book/00` H1 | 已改为 `# 从这里开始`（与 front matter title 一致；新增硬门：H1 与 title 不一致即 FAIL） |
| 来源章节命名 | 公开页面统一为「来源与更新」（290 处）；工具页原有的「证据与来源」已并入同一写法 |
| 文档一致性 | PASS（`check_docs_consistency.py`，74 个文件） |

## 六、Release Validation（CI 与 Pages 同源）

新增 **`tools/validate_release.py`**，8 项统一校验：
构建与元数据 → Canonical IA → Markdown → 文档一致性 → 内容硬门（旧模板/缺 summary/P0/施工语言/H1）→ 内容规则测试 → **HTML id 唯一性** → 外部链接（仅 404/410 阻塞）。

`ci.yml` 与 `pages.yml` **都调用同一个入口**，不再各自维护命令列表。

### 注入测试汇总（验证「不合格内容不能上线」）

| 注入内容 | 预期 | 实测 |
| --- | --- | --- |
| 条目正文加入 `- 一句话：`（旧模板字段） | 阻断 | 内容硬门报「旧模板残留：1」→ **FAIL** |
| `navigation.json` 的 entry_id 改成不存在的值 | 阻断 | 构建与 IA 校验失败 → **FAIL** |
| 文档 `topics: [qualification]`（非法枚举） | 阻断 | 构建与元数据校验失败 → **FAIL** |
| HTML 重复 id（修复前状态） | 阻断 | `check_html_ids.py` 报重复 → **FAIL**（现为 0） |

四次注入后均已撤销，恢复后 `validate_release.py` 回到 **PASS（8 项）**。

## 七、Front-end 清理

- 删除已废弃的字段渲染链路：`build_site.py` 的 `FIELD_LABEL_RE`、`COLLAPSIBLE_FIELDS`、`_split_field_blocks()`、`prepare_entry_body()`；`styles.css` 的 `.entry ul.fields`、`.field-collapsible`、`.detail-body` 与相关注释；
- 未做大规模 `app.js` 重构，只改了 `buildToc()` 一处；
- 回归：Markdown 列表、有序列表、表格、代码块、引用、内部/外部链接在站点中渲染正常（构建 + 47 项单测 + 浏览器冒烟全部通过）。

## 八、国家 / 地区专题（本轮增量）

11 个页面维持 `complete`，本轮修正：

- **新西兰**：新增「已公布但尚未生效的变化（2026-11-16 起）」小节 —— 新的 **Short-Term Graduate Work Visa**（Level 5–7、全日制 24 周以上、6 个月开放工作权利、一生一次）与 **PSWV 资格扩展至 Level 7 Graduate Diploma（需同时持有学士学位，上限 1 年）**，并明确「现行规则 vs 未生效规则」；来源指向 Immigration New Zealand 的两个具体公告页。
- **美国**：修正 F-1 表述 —— 区分 **visa（入境凭证）** 与 **status（在美合法停留的资格）**，并说明 SEVIS 记录的作用；来源升级到 `studyinthestates.dhs.gov/school-search` 与 `/students`。
- **来源颗粒度提升**：香港（学生签证页 + IANG 页）、新加坡（ICA Student's Pass、MOM Employment Pass / S Pass、MOE Tuition Grant Scheme，并补充「国际学生与永久居民须履行 3 年服务承诺」的官方口径）、日本（ISA 手续总览页）、韩国（法务部居留资格页）。
- 外链检查发现并修正 2 处失效链接（EU ECTS 页面 404、MOE Tuition Grant 路径 404）。

## 九、行业 / 职业专题（本轮补完整）

12 个页面从「入口级」补到可独立使用，并从 `partial` 升为 **`complete`**：

| 页面 | 主要补充内容 | 主要官方来源 |
| --- | --- | --- |
| AI 与数据 | 六类岗位（分析/数据科学/数据工程/MLE/算法研究/AI 应用）的日常与门槛差异 | 招聘数据 + 国家数据局 |
| 技术与工程 | 软件与实体工程分开；注册类执业资格提醒 | 人社部、人事考试网、CEEAA |
| 制造 | 研发/工艺/质量/生产供应链四类岗位；特种作业法定资格 | 工信部、应急管理部 |
| 商业与金融 | 银行/券商基金/保险精算/咨询/企业财务/合规；准入类与 CPA 等资格 | 央行、金融监管总局、中注协 |
| 生命科学 | 学术/产业/跨界三条路径；药品与临床合规 | 国家药监局、自然科学基金委 |
| 设计与创意 | 视觉/交互/工业/内容/游戏方向；作品集为核心货币 | 招聘与赛事官方页面 |
| 医疗健康 | 临床与非临床分开；执业资格一条条写清 | 国家卫健委、医学考试中心、药监局 |
| 教育 | 学校教师/高校/培训/教育产品四条路；教师资格与招录 | 教育部、中国教育考试网 |
| 法律与公共事务 | 律师/法务/合规/政策研究/公共事务/公职 | 司法部、国家公务员局 |
| 科研与高校 | 学术与机构路径、评价与资助体系 | 自然科学基金委、教育部 |
| 公共服务 | 公务员/事业单位/基层项目/社会组织四条通道 | 国家公务员局、民政部、共青团中央 |
| 技能型职业 | 准入类资格与职业技能等级的区分、入门与升级路径 | 人社部、技能人才评价工作网、应急管理部 |

每页均包含：方向拆解、日常在做什么、门槛的真实形态（含受监管职业提醒）、怎么用真实
JD 判断门槛、怎么低成本试一次、常见误解、官方信息入口。**未写行业百科、公司大全、
薪资排行或未来预测。**

## 十、最终状态

| 验收项 | 结果 |
| --- | --- |
| Canonical IA | 不变；broken = 0；orphan = 0；duplicate = 0 |
| duplicate HTML id | 0（83 个页面） |
| TOC 错跳 | 0（冒烟用例覆盖 6 个条目） |
| doc facet invalid | 0 |
| metadata 明显错位 | 0（suspicious/overbroad/invalid 全 0） |
| 时间线伪统一规则 | 已清除（剩余命中为已标注的「常见范围」） |
| 模板式 H2 | 0（原 132） |
| 用户可见 planned / TODO / 计划中 | 0 |
| 行业专题 | 12 个 complete 且可独立使用 |
| 国家专题 | 11 个 complete；新西兰含未生效政策小节 |
| 发布校验 | PASS（8 项，CI 与 Pages 同源） |
| 47 项单测 · 浏览器冒烟 | 通过 |

## 十一、仍需人工复核

- `reports/timeline-review.md` 中的 10 处月份命中：判断为「已标注的常见范围」，如你的
  判断标准更严，可继续收紧措辞；
- `reports/content-depth.md` 中 P1（120–250 字）17 篇：属认可区间，是否扩写按阅读体验决定；
- 国家页中 PGWP / 485 / PSWV / Graduate Route / Tuition Grant 等高频变化规则，
  维护时按本报告的记录方式逐项重核，不要整段复制。
