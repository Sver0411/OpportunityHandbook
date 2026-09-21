# IA Parity Report

生成时间：2026-09-22T01:54:39+08:00

核对对象：`meta/navigation.json`（Canonical IA，唯一事实源）与线上左栏目录（`site/data/index.json` 的 `nav`）。

## 结论

| 指标 | 数量 |
| --- | --- |
| 总节点 | 402 |
| 匹配 | 402 |
| 缺失 | 0 |
| 错位 | 0 |
| 重复 | 0 |
| broken target | 0 |
| orphan content | 0 |

成功标准：缺失 = 0、错位 = 0、重复 = 0、broken target = 0、orphan public content = 0。

## 逐节点核对

- 一级栏目 12 个，与线上左栏顺序逐一比对：全部一致
- 叶子节点 342 个；其中可点击 342 个
- 最大层级深度 3 级（一级 → 二级 → 三级 → 文章）

## 检查命令

```bash
python3 tools/build_navigation.py --report   # Canonical IA 节点与待补目标
python3 tools/check_ia.py                    # Rule A–D 硬校验（CI 要求全 0）
python3 tools/smoke_test.py                  # 浏览器里逐节点验证展开/点击/高亮
python3 tools/ia_report.py                   # 生成本报告
```
