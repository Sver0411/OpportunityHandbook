# Knowledge Depth Worklog

最后更新：2026-09-29

## 当前层级

| 层级 | 已写 | 待写 |
| --- | ---: | ---: |
| Book | 290 条目 | — |
| Manual | 10 | — |
| Deep Dive | 64 | 0 |
| Case | 12 | 0 |
| Playbook | 14 | 0 |
| Tool / Template | 28 | 0 |
| Career Guide | 23 | 0 |
| Country Playbook | 11 | 0 |

## 本次第二次深度校正

第一版 Knowledge Depth 扩展完成后再次人工抽查，发现“文件存在”和“内容足够深”不是一回事，因此直接继续修改，而没有再开新的 Pilot。

已完成：

- 22 个原有 Career Guide 全量二次深化；
- 22 个 Career Guide 的批量统一 H2 骨架改为岗位特有结构；
- 新增 FDE Career Guide；
- 11 个 Country Playbook 全量二次深化；
- 原有 10 个 Playbook 全量检查，清理无依据固定周数/人数/百分比；
- 新增技能学习、信息访谈、资助申请、证书评估 4 个 Playbook；
- 重写 JD 拆解中的过度推断；
- 新增 Funding Package Deep Dive；
- 深化“教程项目到工程作品”“两个 Offer 怎么选”Case；
- 新增 `audit_depth_quality.py`，把“深度层质量”与“深度层是否存在”分开检查。

## 写作纪律

1. **真实机制优先**：职业页要讲工作链、判断、故障和证据，不堆技能名词；
2. **本地制度优先**：国家页围绕当地真实招生、资助、就业机制组织，不套统一国家模板；
3. **检查点替代假精确**：Playbook 不用固定周数/投递量伪装确定性；
4. **事实和假设分开**：尤其 JD、Offer、导师、行业信息，无法从公开文字确认的内容改成核实问题；
5. **案例允许失败**：Case 不只展示“正确路径 → 成功”，要展示信息不足、失败和修正；
6. **矩阵只看覆盖**：不能拿 `planned=0` 证明正文足够深；
7. **人工审读仍是最终质量判断**：自动审计只负责把风险信号找出来。

## 发布前门禁

继续运行仓库既有：

- `tools/validate_release.py --quick`
- IA 一致性
- Markdown / 文档一致性
- 内容质量硬门
- 内容规则测试
- HTML id
- ROADMAP metadata 一致性
- 外部链接检查

新增：

- `tools/audit_depth_quality.py`（报告级，用于发现浅页、模板化和经验阈值）
