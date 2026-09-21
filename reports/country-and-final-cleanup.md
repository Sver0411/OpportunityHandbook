# Country/Region Completion + Final Maintenance Cleanup

生成时间：2026-09-22

本轮定位：把国家 / 地区专题真正补完整，同时完成发布链、规范与旧代码的收尾。
信息架构（Canonical IA）、`navigation.json`、主线顺序与条目映射**全程未改动**。

## 一、国家 / 地区专题

共检查 11 个页面，其中 **10 页重写、1 页（日本）事实核查与补缺**，全部达到 `status: complete`。

| 页面 | 状态 | 主要补充内容 | 主要官方来源 | last_verified |
| --- | --- | --- | --- | --- |
| 中国大陆 | complete（重写） | 学历/学位与全日制/非全日制区分、推免与统考两套规则、奖助贷体系、学信网与 CSCSE 认证、职业资格目录的准入类判定 | moe.gov.cn、yz.chsi.com.cn、chsi.com.cn、zwfw.cscse.edu.cn、mohrss.gov.cn | 2026-09-22 |
| 中国香港 | complete（重写） | 教资会资助院校与自资院校、授课型 vs 研究型（MPhil 是独立学位）、学生签证/进入许可由入境事务处管理、IANG 与永居的区别 | immd.gov.hk、ugc.edu.hk | 2026-09-22 |
| 美国 | complete（重写） | F-1 与签证的区别、I-20、SEVP 认证学校、CPT/OPT/STEM OPT 的概念与边界、TA/RA 是工作不是奖学金、社区学院与转学 | uscis.gov、studyinthestates.dhs.gov、travel.state.gov、educationusa.state.gov | 2026-09-22 |
| 加拿大 | complete（重写） | Study Permit、DLI 与 PGWP 的绑定关系、语言要求（大学/非大学不同）、2024-11-01 后的专业领域限制、co-op 工作许可、PGWP 一生一次 | canada.ca（IRCC 学习许可 / 毕业后工作许可）、educanada.ca | 2026-09-22 |
| 英国 | complete（重写） | CAS 与持牌担保、ATAS 的适用与重申请情形、授课型与研究型硕士的区别、Graduate Route 时长规则（2027-01-01 起非博士 18 个月） | gov.uk（student-visa、graduate-visa、ATAS） | 2026-09-22 |
| 欧洲大陆 | complete（重写） | 明确定位为「制度入口」：欧盟≠欧洲、申根≠欧盟、Bologna、ECTS、Erasmus+、各国规则由本国决定 | education.ec.europa.eu、erasmus-plus.ec.europa.eu、european-union.europa.eu | 2026-09-22 |
| 日本 | complete（补缺） | 补打工规则（资格外活动许可）、毕业后的在留资格切换与「特定活动」、多条奖学金渠道、学历认证与执业资格；保留既有的语言学校/研究生/修士/博士区分 | moj.go.jp/isa、jasso.go.jp、mext.go.jp | 2026-09-22 |
| 韩国 | complete（重写） | 本科与大学院、「大学院=研究生院」的澄清、TOPIK 与英文项目、D-2/D-4 的区别、GKS、时间制就业许可、毕业后求职与就业资格入口 | studyinkorea.go.kr、hikorea.go.kr、moj.go.kr | 2026-09-22 |
| 新加坡 | complete（重写） | 自治大学与私立院校的区别、Coursework/Research 学位、Student's Pass（ICA/SOLAR）、Tuition Grant 的服务承诺风险、EP/S Pass 入口 | ica.gov.sg、mom.gov.sg、moe.gov.sg | 2026-09-22 |
| 澳大利亚 | complete（重写） | CRICOS 注册、CoE、OSHC 是签证条件、subclass 500、485 两个 stream 与年龄/时长变化、职业评估与执业注册 | immi.homeaffairs.gov.au（500 / 485）、cricos.education.gov.au、studyaustralia.gov.au | 2026-09-22 |
| 新西兰 | complete（重写） | NZQCF 层级（Level 7/8/9/10）、学生签证打工时数与研究型学位例外、PSWV 的资格与时长规则、Level 7 及以下的工作相关性限制 | immigration.govt.nz、nzqa.govt.nz、studywithnewzealand.govt.nz、mbie.govt.nz | 2026-09-22 |

处理原则：

- 每页覆盖**该国家实际存在**的信息维度（教育体系 / 申请方式 / 语言考试 / 学费与资助 / 身份与签证 / 打工规则 / 毕业后路径 / 学历与执业资格 / 易混淆概念），不套统一模板；
- **不写死分数、金额、时长**：变化快的规则一律指向官方页面，只给制度框架与查询路径；
- 全部改为「部分项目……」「常见的一种形式是……」「具体以目标项目当年官方页面为准」这类有边界的表述；
- 禁止伪全国统一规则：所有规则都注明由哪个部门管理、以哪个页面为准；
- `last_verified` 统一为**本轮实际核实日期 2026-09-22**。

### 行业页的状态修正

12 个行业 / 职业页（`docs/careers/`）目前只写到入口级：按新的状态语义改为 **`status: partial`**，不再用 `complete` 掩盖覆盖不足（partial 仍会出现在导航与搜索中）。同时清掉它们正文里的旧章节引用（「见第二章」「见第五章」），改为当前条目链接。

## 二、规范一致性

| 项目 | 结果 |
| --- | --- |
| README 旧正文模型残留 | 0（已改写为「按问题自然组织」，并新增六条共享纪律与三种形态示例） |
| meta 旧模板残留 | 0（`条目格式.md` 的「固定字段的正文」已改；`写作规范.md` 的「十个固定字段」已改） |
| 旧章节引用 | 0（`写作规范.md`、`证据与来源规范.md` 的第 02 章/第 11 章说法已替换为具体条目链接；`docs/careers/*` 的中文数字章节引用已全部替换） |
| `docs/` 状态语义 | 已在 `meta/条目格式.md` 与 `docs/README.md` 明确 complete / partial / planned 的含义 |
| Documentation Consistency | **PASS**（`tools/check_docs_consistency.py`，检查 74 个文件） |

新增 `tools/check_docs_consistency.py`：把「同一套字段」「十个固定字段」「一句话：」「第 02 章」「第二章」等已废弃表述列为 FAIL 条件，
防止未来贡献者按旧模型写作。

## 三、发布链（CI 与 Pages 统一）

- 新增 **`tools/validate_release.py`**：统一执行
  构建与元数据（`build.py --strict`）→ Canonical IA → Markdown → 文档一致性 → 内容硬门 → 内容规则测试
  （`tools/smoke_test.py` 在本地可用，CI 用 `--quick` 跳过浏览器依赖）。
- `ci.yml` 与 `pages.yml` **都改为调用同一个 `validate_release.py --quick`**，不再各自维护命令列表。

### 注入测试（验证「不合格内容不能上线」）

| 注入内容 | 预期 | 实测结果 |
| --- | --- | --- |
| 在条目正文里加入 `- 一句话：…`（旧模板字段） | 阻断 | `check_content_quality --hard` 报「旧模板残留：1」→ `validate_release` **FAIL**（内容质量硬门） |
| 把 `navigation.json` 的某个 `entry_id` 改成不存在的 id | 阻断 | 构建与 IA 校验失败 → `validate_release` **FAIL**（构建与元数据校验、Canonical IA 一致性） |

两次注入测试后均已撤销，恢复后 `validate_release.py --quick` 回到 **PASS（6 项全部通过）**。

## 四、声明审计升级

`tools/audit_claims.py` 重写为分类审计：

- **absolute**：唯一 / 一定 / 必须 / 绝对 / 永远 / 肯定 / 只要 / 不会 / 几乎 …
- **statistical**：多数（人/行业/岗位/项目/企业）/ 通常 / 普遍 / 往往 / 显著 / 大幅 / 成功率 / 更容易 / 更可能 / 平均 / 比例 / 概率 …
- **recommendation**：最好 / 优先 / 更重要 / 应该 / 最有效 / 更划算 / 首选 …

并按「证据类型 × 措辞类型」分级：`experience_based` 条目里的**统计式断言**单列为 `experience-statistical`（最该改的一类），可用
`python3 tools/audit_claims.py --only-expensive` 查看。

本轮实测：命中 597 处（statistical 343 / recommendation 143 / absolute 111），其中
**经验性判断里的统计式断言 133 处**，无强证据的其他建议判断 129 处。

本轮实际改写 **9 处**（均属最该改的一类）：

| 原表述 | 改后 |
| --- | --- |
| 多数成功转行走的是两三步的台阶 | 一次跳到位的转行并不常见；一种更稳妥的做法是通过一到多个过渡性机会逐步接近目标岗位 |
| 多数晋升失败不是能力不够，而是…… | 晋升受阻时，至少值得先检查两件事 |
| 多数岗位建议至少一年以上 | 不少用人方会关注停留时间过短的问题，一般建议至少一年以上 |
| 多数独立产品前两年收入寥寥 | 独立产品在早期通常收入有限 |
| 多数创作者的收入来自后两者 | 对不少创作者而言，后两者比播放量本身更重要 |
| 内容创作通常一年以后才有稳定收入 | 稳定收入往往需要长期持续更新之后才可能出现，具体因人因领域而异 |
| 多数在职者首选在职 | 在职路径通常更稳妥 |
| 多数行业的博士溢价不覆盖机会成本 | 行业差异很大，需要按目标岗位单独核实 |
| Accelerator 通常是三到六个月、带投资、Demo Day | 典型形态是数月密集项目 + 小额投资 + Demo Day（如 YC 模式），不同机构差异很大 |

剩余 133 处中，多数是**有边界的对冲表达**（如「这句话往往比怎么做更值得先读」「多数院系按加权成绩排名」），
属于可接受的经验性措辞；列入人工复核清单，不追求清零。

## 五、旧 fields renderer 清理

删除已废弃的字段渲染链路：

- `tools/build_site.py`：移除 `FIELD_LABEL_RE`、`COLLAPSIBLE_FIELDS`、`_split_field_blocks()`、`prepare_entry_body()`，条目正文改为直接 `mdrender.render()`；
- `site/styles.css`：移除 `.entry ul.fields`、`.field-collapsible`、`.detail-body` 等相关样式与「十个字段」注释；
- 回归：Markdown 列表、有序列表、来源列表、表格、代码、引用、内部/外部链接在站点中的渲染均正常（构建、47 项单测与浏览器冒烟全部通过）。

## 六、最终状态

| 指标 | 结果 |
| --- | --- |
| Canonical IA | 402/402 解析，missing / broken / orphan / duplicate 全 0 |
| P0（<120 字） | 0 |
| P1（120–250 字） | 17（保留，不追求清零） |
| 旧模板残留 | 0 |
| 缺 summary | 0 |
| Markdown 错误 | 0 |
| stages suspicious / overbroad / invalid | 0 / 0 / 0 |
| 文档一致性 | PASS |
| 发布校验（本地） | PASS（6 项） |
| 47 项单测 · 浏览器冒烟 | 通过 |
| CI · Pages | 均调用同一个 `validate_release.py`，任一失败即阻断发布 |

## 七、仍需人工复核

- **P1 17 篇**：多为概念型条目，长度在认可区间，是否扩写按阅读体验判断；
- **行业页 12 个**保持 `partial`：本轮按要求不批量扩写，后续逐行业深化；
- **声明审计剩余 133 处统计式措辞**：属有边界的经验表达，列入抽查清单；
- 国家页中的规则（尤其 PGWP、485、PSWV、Graduate Route、Tuition Grant）**变化频繁**，
  维护时应以本文档记录的方式逐项重核，而不是整体复制旧版本。
