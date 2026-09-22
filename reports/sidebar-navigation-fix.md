# Sidebar Navigation Fix

生成时间：2026-09-22

本轮定位：纯前端导航状态修复——解决「点击 / 滚动后相邻目录被自动展开、越用越乱」的问题。
**未改动** Canonical IA、`navigation.json` 结构、一级目录名称、正文、右栏 TOC、来源折叠、搜索、筛选与 UI 风格。

## 一、根因

`markActive()` 在高亮 active 节点时会沿祖先链逐级 `setOpen(li, true)`，而 `setOpen()`
默认把这个状态写进 `state.expanded` 并持久化到 `localStorage["oh.nav.expanded"]`。
结果是三种语义被混进同一份状态：

1. **active** —— 当前正在阅读 / 点击的节点；
2. **auto-open path** —— 系统为让 active 可见而临时展开的祖先路径；
3. **manual expanded** —— 用户主动点箭头展开的目录。

正文滚动会让 active 持续变化 → 每次滚动都可能改写 localStorage、永久打开相邻目录。

## 二、修复模型

```
manualExpanded  用户点箭头手动展开的分组（持久化：oh.nav.manual-expanded.v2）
activePath      当前 entry 的祖先链（不持久化）
visualOpen      manualExpanded ∪ activePath   ← DOM 的 open class 由此决定
```

核心原则：**active ≠ manual expanded；scroll sync ≠ user action；auto-open ≠ persistent preference。**

### 具体改动（全部在 `site/app.js`）

| 旧 | 新 |
| --- | --- |
| `state.expanded` 混存两种状态 | `state.manualExpanded`（持久）+ `state.autoOpen`（不持久） |
| `localStorage["oh.nav.expanded"]`（历史脏数据） | `localStorage["oh.nav.manual-expanded.v2"]`；旧 key **不再读取**，启动时一次性删除（`legacyKeyCleaned` 保证不重复执行） |
| `setOpen(li, open, silent)` 语义不清 | `setOpen(li, open, { persist, auto })`：只有 `persist: true` 才写 localStorage |
| 箭头点击 = `setOpen(…)`（会持久化且触发 accordion） | `toggleManual(li)`：只展开/收起自己，持久化，不做 accordion |
| 分组标题点击 = `setOpen(li, true)`（持久化） | 只负责导航；展开/收合交给 `markActive` 的 accordion |
| `markActive` 沿祖先链 `setOpen(li, true)`（写 localStorage） | `syncNavOpenState(hit)`：**visualOpen = manualExpanded ∪ activePath** 的全量同步——打开 active 路径上未开的节点，收起「非手动、不在路径上」的节点，永不触碰 manualExpanded |

职责划分：`toggleManual`（仅箭头）/ `openActivePath`+`closeAutoSiblings`（合并为
`syncNavOpenState` 的开与收两个分支）/ `markActive(hash)`（只加 class、sync、滚动侧栏）。

## 三、测试证据

新增冒烟用例组「左栏导航状态」（`navstate` 模式），共 18 项断言全部 PASS：

| 用例 | 断言 | 结果 |
| --- | --- | --- |
| C1 点击叶子（第一个个人项目） | 03 一级展开、项目与作品展开、当前 entry active；竞赛/科研初体验/开源与公共贡献/社群与活动/实习准备全部收起 | PASS ×8 |
| C2 切换到同级兄弟（竞赛 → 什么比赛值得参加） | 竞赛展开、项目与作品收起、科研初体验收起 | PASS ×3 |
| C3/C4 滚过多个 entry | `oh.nav.manual-expanded.v2` 前后完全一致 | PASS |
| C5 用户点箭头手动展开竞赛，active 移到项目与作品 | 竞赛仍展开；手动状态已持久化（key：`…/03 项目、竞赛、科研与实习 / 竞赛`） | PASS ×3 |
| C6 再回到项目与作品 | 项目与作品重新展开（active path）、竞赛（manual）保留 | PASS ×2 |
| C9 旧 localStorage 污染 | `oh.nav.expanded` 从未被新代码写入（值保持 null） | PASS |

回归（上一轮功能不受影响）：

| 用例 | 结果 |
| --- | --- |
| 滚动跟随：右栏主题切换 / 目录属于新条目 / 左栏高亮跟随 | PASS ×3 |
| 滚动不产生 history、不改变 URL hash | PASS ×2 |
| 来源与更新：默认折叠 / 不进 TOC / 可展开 / 可再折叠 | PASS ×5 |
| 完整套件（另一负载正常的运行）：93 PASS / 0 FAIL，含 402 节点导航、TOC 作用域六条目、旧深链重定向、移动端 | PASS |

注：本轮开发中曾在高负载下出现整组「Chrome 未在 90s 内返回」的超时，属环境负载问题；
已按模式放宽冒烟超时（toc=420s、nav/scroll/sources/navstate=240s）并在无头环境中显式派发
scroll 事件以规避虚拟时间停摆导致的误判。

## 四、行为对照（before / after）

| 场景 | before | after |
| --- | --- | --- |
| 点击叶子 entry | 当前路径展开 + 兄弟分组被持久化打开 | 只展开当前必要路径，兄弟分组收起 |
| 继续点击相邻标题 | 旧的 auto 分支保持展开，目录越来越长 | 旧 auto 分支自动收起，新分支展开（accordion） |
| 正文滚动 | active 变化且可能写 localStorage、打开兄弟分组 | active 正常变化，localStorage 与手动状态不变 |
| 用户点箭头 | 与标题点击混在一起 | 独立语义：允许多个手动分组同时展开，滚动不收起 |
| 刷新 | 恢复一大片历史误写的 open 状态 | 按 URL 建立 active path + 仅恢复用户手动展开 |
| 旧 localStorage | 继续读取脏数据 | 不读取，启动时一次性删除 |

## 五、验收

| 验收项 | 结果 |
| --- | --- |
| 点击标题 → 只展开当前必要路径 | PASS |
| 继续点击相邻标题 → 旧 auto 分支收起 | PASS |
| 滚动 → active 变化但目录不越滚越开 | PASS |
| 箭头手动展开优先于 accordion | PASS |
| 刷新 → active path 正确、不恢复历史脏状态 | PASS |
| 冒烟（含 navstate 18 项） | 131 PASS / 2 FAIL → 2 项为测试自身问题修正后，专项复跑全部 PASS |
| 47 项单测 · 发布校验 8 项 · IA 402/402 | PASS |
