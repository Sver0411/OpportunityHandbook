# Knowledge Depth Expansion — Final Report

日期：2026-09-29  
范围：OpportunityHandbook 全库知识纵深扩展与第二次深度校正

## 一、最终状态

这轮工作的目标不是继续把 `book/` 写长，而是让读者能从“知道一条路”继续下钻到“真正会做”。

当前深度层：

| 层级 | 已写 |
| --- | ---: |
| Deep Dive | **64** |
| Case | **12** |
| Playbook | **14** |
| Tool / Template | **28** |
| Career Guide | **23** |
| Country Playbook | **11** |

所有已规划深度文档均为 complete；`status: planned` 为 0。

但本轮不再把 “planned=0” 当作内容完成证明。覆盖情况见 [Knowledge Depth Matrix](knowledge-depth.md)，内容本身另做人工与结构审查。

## 二、为什么又做了一次深度校正

第一版 Knowledge Depth 层成功把 Book → Manual → Deep Dive → Case / Playbook → Tool 的结构搭起来，但抽查后发现三个明显问题：

1. **Career Guide 名字很深，正文仍像职业卡片。** 22 个岗位页大多只有概览内容，而且使用完全相同的 H2 骨架；
2. **Country Playbook 仍更像国家简介 Plus。** 有制度入口，但不足以支持真实申请判断；
3. **Playbook 出现假精确。** 固定周数、固定投递量、固定人数、固定百分比被写成通用流程；
4. **部分 Deep Dive 过度推理。** 例如从 JD 的“稳定性建设”直接推出 on-call，从 “Java 或 Go”猜团队迁移；
5. **FDE 漏写，Funding 没有真正的 Deep Dive。**

因此这一轮直接改正文，而不是再增加“计划文件”。

## 三、Career Guide：从职业卡片改成真实工作指南

原有 22 个 Career Guide 全部增加了岗位特有的纵深内容，并重写统一模板标题。

本轮重点补入的内容包括：

- **软件工程**：需求到上线、兼容/回滚/监控/事故、不同层级的问题所有权；
- **前端**：状态、网络、权限、性能、可访问性与多端边界；
- **后端**：状态变化、幂等、失败恢复、请求链路、容量与稳定性；
- **嵌入式**：MCU/BSP/Driver/Embedded Linux/汽车的区别，真实传感器 bring-up 与故障链；
- **硬件**：原理图 → PCB → Bring-up → 验证 → 试产 → 量产；
- **算法**：数据 → baseline → 训练 → 误差分析 → 推理成本 → 上线监控；
- **数据分析 / 数据工程**：指标口径与决策、可信数据供应链与恢复；
- **产品**：把模糊需求变成可验证假设；
- **QA / SRE**：风险与可靠性，而不是工具清单；
- **Solutions / Support**：POC 范围、客户问题收敛、升级与复用；
- **Research Engineer / Researcher**：研究不确定性与工程确定性的交界、独立研究者职责；
- **制造 / 设计 / 财务 / 咨询 / 教师 / 公共部门 / 技能职业**：各自的真实工作闭环、评价证据与职业边界。

同时新增 [Forward Deployed Engineer（FDE）](../docs/career-guides/FDE.md)，明确它与 Software Engineer、Solutions Engineer、Technical Consultant 的区别，并展开 discovery → scoping → prototype → eval → production rollout → adoption → product feedback 的完整链路。

## 四、Country Playbook：从国家介绍改成申请机制

11 个国家/地区手册全部做了第二次深化，不再只讲“学制、签证、成本”。

例如：

- **日本**：募集要项优先、研究生路线的真实作用、导师联系、过去问、入试、资金与就业双时间线；
- **美国**：MS/PhD/Professional/Thesis 不同招生逻辑、研究生态与单导师风险、自费硕士到底买到什么；
- **英国**：一年制项目的真实节奏、conditional offer、Graduate Route 与实际招聘分开判断；
- **加拿大**：学校价值与身份路径拆开、Co-op 不等于保证 placement、省份/城市差异；
- **澳大利亚 / 新西兰**：专业认证、地域、就业与动态签证规则；
- **欧洲大陆**：明确“欧洲”不是单一制度，按国家制度继续拆分；
- **中国大陆 / 中国香港 / 新加坡 / 韩国**：分别补通道、研究型/授课型、资助、语言与真实就业机制。

所有时效规则仍以官方当年信息为准，不在 Handbook 中把易变数字固化成长期事实。

## 五、Playbook：从日历驱动改成检查点驱动

原有 10 个 Playbook 全部审查。

删除或收窄了大量没有可靠依据的固定阈值，例如：

- “8 周拿实习”
- “每周 8–10 小时”
- “收集 12–15 份 JD”
- “出现率 ≥60% 才算高频”
- “四周内必须合并一次 PR”
- “固定 25/45/20/10% Hackathon 时间分配”
- “联系 8–10 位导师”
- “两周没回复”
- “面试沉默 30 秒”
- “连续三场失败才暂停”

现在的 Playbook 用**进入下一阶段的检查点**决定进度：信息是否足够、最小闭环是否跑通、反馈是否暴露新问题、证据是否可以复现。

另新增四个执行入口：

- [把一项新技术学到“能用”](../docs/playbooks/第一次学新技术.md)
- [第一次做信息访谈](../docs/playbooks/第一次信息访谈.md)
- [第一次申请奖学金或研究资助](../docs/playbooks/第一次申请资助.md)
- [第一次判断一个证书值不值得考](../docs/playbooks/第一次评估证书.md)

## 六、Deep Dive 与 Case 的针对性修复

### JD 拆解

重写 [一份 JD 到底怎么拆](../docs/job-search/JD拆解.md)。

现在明确区分：

- JD 明示事实；
- 招聘偏好；
- 待验证假设。

“稳定性建设”“Java 或 Go”“参与平台建设”等词只能生成**面试核实问题**，不能直接推断 on-call、技术迁移或团队阶段。

### Funding

新增 [全额资助到底怎么找、怎么看、怎么比较](../docs/funding/全额资助与资金包.md)，把“全奖”拆成：

- tuition
- stipend / salary
- insurance
- one-time fees
- RA / TA duties
- continuation conditions

并区分 guaranteed funding、eligible、导师经费、政府奖学金与外部资助。

### 教程项目到工程作品

重写三类完整案例，不再用“固定四步”“必须跑 72 小时”作为统一答案。

现在按五个证据问题推进：真实输入、失败可见、对照、可复现、限制。

### 两个 Offer 怎么选

案例从“整齐信息表直接比较”改为：

未知信息 → 核实来源 → 区分书面事实与个体样本 → 总包/成长/生活 → 敏感性检查 → 回退路径 → 决策后复盘。

## 七、深度审计不再只数文件

原 `audit_knowledge_depth.py` 继续负责层级覆盖。

新增 `tools/audit_depth_quality.py`，用于提示人工复核：

- 正文明显偏短；
- 展开层次少；
- 缺行动/判断信号；
- 缺案例/对照；
- 缺失败/边界；
- 缺证据；
- 同目录大量 H2 骨架完全相同；
- 时间/比例区间可能被误写成通用经验阈值。

它只找值得人工读的页面，不自动宣布文章“合格”。

## 八、当前知识链

现在一个读者可以从：

### 项目
Book → 项目与作品手册 → 测试/日志/README 等 Deep Dive → 三类工程 Case → 项目 Playbook → 测试/Benchmark/README 工具。

### 科研
Book → 科研手册 → RQ/Baseline/Ablation/实验/复现/Peer Review → 科研失败 Case → 实验/论文 Playbook → 研究工具。

### 求职
Book → JD/简历/面试/漏斗/Offer Deep Dive → 找实习/面试/谈薪 Playbook → 求职 Case → 追踪/诊断/复盘工具。

### 职业
行业地图 → 23 个具体 Career Guide → 相关项目/面试/职业成长 Deep Dive。

### 留学
国家概览 → 11 个 Country Playbook → 选校/推荐信/SOP/Research Proposal Deep Dive → 留学选校 Case → 时间线与工具。

### 资助 / 技能 / 社群 / 证书
原本只有解释层的几块已经补上 Deep Dive 或执行 Playbook，不再只有概念介绍。

## 九、仍然保留的边界

- 合成 Case 是教学案例，不伪装成真实个人经历；
- Career Guide 描述的是常见工作形态，不假装所有公司职责一致；
- 国家、签证、资助、资格政策会变化，必须保留核验日期与官方入口；
- 不追求每个知识域机械拥有相同数量的 Case / Tool；
- 短文章可以完整，长文章也可能空洞，因此不把字数作为完成 KPI。

## 十、发布校验

本轮所有改动需继续通过仓库既有 Release Validation；新增深度质量审计作为报告级辅助，不替代人工审读。

最终目标不再是“文件都建了”，而是：

> **读者决定走一条路以后，能继续读到真实工作机制、完整执行过程、失败分支、证据标准和下一步工具。**
