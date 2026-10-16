# 读者视角审查 · 修复记录（25 轮）

修复时间：2026-10-17
基线报告：[reader-perspective-audit-2026-10-17.md](reader-perspective-audit-2026-10-17.md)
范围：`book/` 正文、`tools/` 校验、`reports/` 记录；未改动 `docs/` 与站点代码。

## 一、结果对照

| 指标 | 审查时 | 修复后 |
| --- | ---: | ---: |
| 页内锚点死链 | 204 条（源文件 68 处） | **0 条** |
| 章节级链接跳错页 | 点击后落到「找不到这个入口」 | 全部改为可解析的文档路由 |
| 「相关」自链接 | 10 处 | **0 处** |
| 双稿条目（同一件事写两遍） | 6 条已确认 + 14 条同型候选 | **17 条已合并**，3 条经核对为误报 |
| 条目内重复小节 | 0（但内容重复用不同标题存在） | 0 |
| 「什么时候要谨慎」命名 | 90 处 / 290 种叫法 | **218 处** |
| 正文 <560 字的条目 | 25 条 | 24 条（两条判断型条目已补强） |
| 最长条目的 H2 数 | 14（简历怎么写） | 11（行测怎么准备，编号流程，合理） |
| 发布校验 | 15 项通过（但漏掉 204 处死链） | 15 项通过 + **新增锚点门禁** |

## 二、逐轮清单

| 轮次 | 内容 | 提交 |
| ---: | --- | --- |
| 1 | 新增 `tools/check_anchors.py`：判定同页 id / 前端节点 id / 路由三种可达 | `tools(check)` |
| 2–10 | 逐章修 68 处 `#NN-章名` 死链（01–09 章各一轮） | `content(book)` ×9 |
| 11 | 把锚点检查接入 `validate_release.py`（CI 与 Pages 共用入口） | `tools(check)` |
| 12 | 清掉 10 处指向条目的自链接，顺带整理 3 处「相关」区块排版 | `content(book)` |
| 13 | 合并「简历怎么写」两版（口径冲突：一页/两页、一分钟/30 秒） | `content(book)` |
| 14 | 合并「技术还是管理」两版（5 节逐条对应前半段） | `content(book)` |
| 15 | 合并「怎么设置主线和备选」两版 | `content(book)` |
| 16 | 合并「保研和考研怎么选」两版 | `content(book)` |
| 17 | 合并「真实用户与反馈」两版 | `content(book)` |
| 18 | 合并「Case Interview」两版（含一个句读型标题） | `content(book)` |
| 19 | 合并「职业教育与技能路线」「海外发展」两版 | `content(book)` |
| 20 | 合并「实验与数据」「奖学金与 Funding」「要不要继续升学」 | `content(book)` |
| 21 | 合并 community / 三方 / 什么时候跳 三条 | `content(book)` |
| 22 | 合并 company-types / edu-master / incubator / accelerator / second-career | `content(book)` |
| 23 | 统一收尾小节命名（104 处改名 + 9 处并入） | `content(book)` |
| 24 | 补强 Gap Year、重排避坑段落、合并行为面双稿 | `content(book)` |
| 25 | 全量校验、记录与收尾 | `docs(reports)` |

## 三、关键判断（留档）

### 死链的正确改法

`#01-先决定下一步往哪里走` 用的是文件名，页面里没有这个 id。前端
（`site/app.js` 第 973–982 行）只在同页存在目标 id 时接管点击，否则浏览器改写
hash，触发 `route()` 兜底，把读者带到「找不到这个入口」。

修法不是加 id，而是换成前端能解析的文档路由：

- 分组级 → `#/doc/book/01-先决定下一步往哪里走/选学校与选专业`
  （`chapter_aliases` 存在时，会重写成 `#/chapter/school`）；
- 分组名不对应可解析 route 时 → `#/doc/book/01-…/<该组第一个条目 id>`。

**顺带确认**：章节内 `[文字](#条目id)` 这类锚点是可用的——`reader.js` 的 `guide(id)`
会按节点归属打开概览页，所以不需要改。

### 双稿是怎么被识别的

结构信号：一条目内 H2 数量异常（简历 14、技术还是管理 11），且后半段的小标题
与前半段用词高度重合（阈值 0.5）。这个方法会漏掉「标题措辞不同但内容重复」的情况
（简历条目就漏了），所以对 H2 最多的前 8 条做了人工通读。
另外两条（`paths-gap-year`、`interview-behavioral`）是第 24 轮人工顺带发现的。

合并原则：**保留结构更好的一版做骨架，把另一版独有的信息点并进对应小节，
不要两版都留**；数字冲突必须在合并时定稿。

### 一个反复出现的模式

`job-hunting-resume`、`first-job-company-types`、`startup-incubator`、
`startup-accelerator`、`second-career` 都有同一个痕迹：**第一段引言被写了两遍**，
以及**「相关」区块之后还挂着一段重复结论**。这是两版拼合时留下的边界，
以后新增条目可用这两处做自查点。

## 四、新增的门禁

`tools/check_anchors.py` 已进入 `tools/validate_release.py` 步骤表
（HTML id 唯一性之后）。判定「可达」的三种情况：

1. 同页存在同名 `id`；
2. 锚点是前端阅读模型里的节点 id（`site/data/reader.json` → `reader.map/topics/atlases/resources`）；
3. 以 `/` 开头（`#/doc/…`、`#/chapter/…` 等路由链接）。

当前：3023 条页内锚点、死链 0 条。以后新增这类死链会直接阻塞 CI。

## 五、仍待处理（本轮未做）

- **24 条正文 <560 字的条目**：其中多数是概念型（`opensource-pr`、`project-code-review`、
  `career-management-track`、`overseas-sop-ps` 等），短是合理的；值得再看的判断型条目是
  `overseas-research-proposal`（428）、`research-recommendation-letter`（419）、
  `public-sector-transferable`（493）。
- **避坑章的「坑一～坑六」**保留原名，它们是该条目的内容分层，不是收尾小节。
- `audit_sources` 长期报告 1 条：`03 章 community-student-org` 声称 Official 但没有外部链接，
  属报告级，未处理。
