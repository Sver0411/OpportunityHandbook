# 导航改为「跳转式」（2026-10-12）

问题（用户反馈）：点左侧目录之后内容是「滑过去」的，希望改成跳转式。

## 定位到的两处原因

| 原因 | 位置 | 表现 |
| --- | --- | --- |
| 平滑滚动 | `site/styles.css` → `html { scroll-behavior: smooth }` | 点目录/锚点后页面**滚动**过去；`scrollIntoView` 也继承了这个行为 |
| 视图切换动画 | `site/styles.css` → `.main > * { animation: oh-fade-up … }`（另加 0.04s / 0.08s 错开延时） | 正文区在切换时**淡入上移**，观感像滑动 |

## 改法

- `scroll-behavior: smooth` → `auto`，并加注释说明「不要改回 smooth」，避免后续被当成「动效」加回来；
- 删掉 `.main > *` 的整段切换动画与延时（改为直接替换内容）。

**保留**的部分：移动端左侧抽屉的滑入滑出（`.sidebar` 的 `transform` 过渡）——那是面板本身的进出，不是导航动效；如果你也想去掉，说一声即可。

## 验证（实测，不是目测）

在冒烟测试的导航用例里加了三条断言，跑无头 Chrome 真实点击：

```
[PASS] 导航为跳转式：无平滑滚动        [scroll-behavior = auto]
[PASS] 导航为跳转式：正文无切换动画    [animation-name = none]
[PASS] 导航为跳转式：首帧即到位        [60ms=593 px, 660ms=593 px]
```

第三条是关键证据：点击目录后的 60 ms 与 660 ms，滚动位置**完全相同**（593px）——
说明是一步到位，而不是平滑滚动。

## 回归看护

这三条断言留在 `tools/smoke_test.py`（导航模式）里，`validate_release.py` 的浏览器冒烟会一起跑；
发布校验 13 项全部通过，`strict` 构建、47 项内容测试、排版探针均通过。


---

## 追加：跳转动效（同日）

去掉全部动画后觉得太生硬，因此加回一个**短促的跳转动效**，与旧版的区别在时长与节奏：

| | 旧版（被否） | 现在 |
| --- | --- | --- |
| 时长 | 220ms（`--dur`） | **120ms**（`--dur-jump`） |
| 位移 | 6px 上移 | **3px 上移** |
| 错开延时 | 第 2、3 块各延时 40ms / 80ms | **无延时，一次完成** |
| 滚动 | 平滑滚动（滑过去） | **瞬移**（`scroll-behavior: auto` 不变） |

```css
@keyframes oh-jump {
  from { opacity: 0; transform: translateY(3px); }
  to   { opacity: 1; transform: none; }
}
.main > * { animation: oh-jump var(--dur-jump) var(--ease) both; }
```

观感是「一跳到位并轻轻落定」，而不是「内容慢慢滑上来」。`prefers-reduced-motion: reduce`
的用户仍会自动跳过（全局兜底已把它降到 0.001ms）。

### 验证

冒烟测试里的三条断言（无头 Chrome 实测）：

```
[PASS] 导航为跳转式：无平滑滚动      [scroll-behavior = auto]
[PASS] 导航为跳转式：切换动效短促    [animation-name=oh-jump, duration=0.12s]
[PASS] 导航为跳转式：首帧即到位      [60ms=596 px, 660ms=596 px]
```

第二条把「动效必须 ≤0.16s 且为 oh-jump」写成了断言——将来若有人把时长改回 0.22s 或
重新加上错开延时，冒烟测试会失败。
