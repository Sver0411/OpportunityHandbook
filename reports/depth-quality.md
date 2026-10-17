# Depth Quality Audit

本报告检查的是已有深度文档是否值得人工再读，不用字数自动宣布合格。
长度、标题数、关键词都只是检索信号；最终判断必须读正文。

## 层级规模

| 层级 | 文档数 |
| --- | ---: |
| Deep Dive | 66 |
| Case | 15 |
| Playbook | 20 |
| Career Guide | 23 |
| Country Playbook | 11 |

## 建议人工复核

只有同时命中至少两个风险信号才进入这里，避免把短而完整的文章机械判差。

| 文档 | 层级 | 有效字符 | H2 | 原因 |
| --- | --- | ---: | ---: | --- |
| docs/competition-playbooks/时间分配与版本管理.md | Deep Dive | 996 | 9 | 正文较短；缺案例/对照信号 |
| docs/competition-playbooks/读规则与评分函数.md | Deep Dive | 1062 | 8 | 正文较短；缺案例/对照信号；缺失败/边界信号 |
| docs/learning/读官方文档.md | Deep Dive | 1065 | 7 | 正文较短；缺失败/边界信号 |
| docs/networking/会议与线下活动.md | Deep Dive | 1132 | 9 | 正文较短；缺案例/对照信号；缺失败/边界信号 |
| docs/research-deep/消融实验.md | Deep Dive | 1175 | 7 | 正文较短；缺失败/边界信号 |
| docs/admissions/推荐信.md | Deep Dive | 1184 | 8 | 正文较短；缺案例/对照信号 |
| docs/certifications/判断体系.md | Deep Dive | 1210 | 8 | 正文较短；缺案例/对照信号 |
| docs/cases/留学选校.md | Case | 1217 | 12 | 正文较短；缺失败/边界信号 |
| docs/entrepreneurship/现金流与合同.md | Deep Dive | 1233 | 8 | 正文较短；缺案例/对照信号 |
| docs/playbooks/第一次核对合同与社保.md | Playbook | 1255 | 8 | 正文较短；缺案例/对照信号；缺失败/边界信号 |
| docs/open-source/评审与合并.md | Deep Dive | 1268 | 9 | 正文较短；缺案例/对照信号 |
| docs/networking/联系陌生人.md | Deep Dive | 1290 | 9 | 正文较短；缺失败/边界信号 |
| docs/networking/关系维护与内推.md | Deep Dive | 1293 | 10 | 正文较短；缺案例/对照信号；缺失败/边界信号 |
| docs/learning/掌握程度的判断.md | Deep Dive | 1295 | 10 | 正文较短；缺案例/对照信号 |
| docs/open-source/第一个Issue.md | Deep Dive | 1301 | 9 | 正文较短；缺失败/边界信号 |
| docs/playbooks/第一次信息访谈.md | Playbook | 1305 | 10 | 正文较短；缺案例/对照信号 |
| docs/learning/账号数据与隐私.md | Deep Dive | 1313 | 7 | 正文较短；缺案例/对照信号；缺失败/边界信号 |
| docs/cases/第一次看心理科.md | Case | 1328 | 9 | 正文较短；缺失败/边界信号 |
| docs/research-deep/数据与可复现.md | Deep Dive | 1328 | 8 | 正文较短；缺案例/对照信号；缺失败/边界信号 |
| docs/playbooks/第一次评估证书.md | Playbook | 1341 | 8 | 正文较短；缺失败/边界信号 |
| docs/certifications/考试准备.md | Deep Dive | 1348 | 9 | 正文较短；缺案例/对照信号 |
| docs/research-deep/Baseline设计.md | Deep Dive | 1382 | 8 | 正文较短；缺案例/对照信号；缺失败/边界信号 |
| docs/admissions/研究计划拆解.md | Deep Dive | 1393 | 13 | 正文较短；缺案例/对照信号 |
| docs/career-growth/晋升材料.md | Deep Dive | 1577 | 10 | 缺案例/对照信号；缺失败/边界信号 |
| docs/projects/MVP与范围控制.md | Deep Dive | 1618 | 10 | 缺案例/对照信号；缺失败/边界信号 |
| docs/playbooks/第一次准备专升本.md | Playbook | 1714 | 14 | 缺案例/对照信号；缺失败/边界信号 |
| docs/playbooks/第一次考四六级.md | Playbook | 1740 | 12 | 缺案例/对照信号；缺失败/边界信号 |
| docs/playbooks/第一次准备考研.md | Playbook | 2721 | 14 | 缺案例/对照信号；缺失败/边界信号 |

## 重复结构信号

同一目录中 4 篇以上文档拥有完全相同的非通用 H2 序列时列出。它不一定是错误，但值得人工确认是否批量模板化。

没有发现 4 篇以上完全相同的非通用 H2 骨架。

## 数字区间提示

这里只提醒人工判断：数字究竟是制度事实、案例数据，还是被误写成通用规则的经验阈值。

| 文档 | 时间/比例区间命中数 |
| --- | ---: |
| docs/playbooks/第一次准备考研.md | 8 |
| docs/networking/联系陌生人.md | 6 |
| docs/playbooks/第一次考四六级.md | 6 |
| docs/playbooks/第一次准备考公笔试.md | 4 |
| docs/career-growth/在职跳槽.md | 3 |
| docs/career-guides/软件工程师.md | 3 |
| docs/playbooks/第一次技术面试.md | 3 |
| docs/career-guides/咨询.md | 2 |
| docs/career-guides/教师.md | 2 |
| docs/career-guides/研究员与高校教职.md | 2 |
| docs/cases/两个Offer怎么选.md | 2 |
| docs/cases/第一次找技术实习.md | 2 |
| docs/cases/联系导师.md | 2 |
| docs/certifications/考试准备.md | 2 |
| docs/networking/贡献社群.md | 2 |
| docs/playbooks/第一次参加 Hackathon.md | 2 |
| docs/playbooks/第一次处理劳动争议.md | 2 |
| docs/admissions/复试与申请面试.md | 1 |
| docs/career-guides/FDE.md | 1 |
| docs/career-guides/产品经理.md | 1 |
| docs/career-guides/制造业研发.md | 1 |
| docs/career-guides/前端工程师.md | 1 |
| docs/career-guides/后端工程师.md | 1 |
| docs/career-guides/嵌入式工程师.md | 1 |
| docs/career-guides/技术支持与客户成功.md | 1 |
| docs/career-guides/数据分析师.md | 1 |
| docs/career-guides/数据工程师.md | 1 |
| docs/career-guides/测试与质量.md | 1 |
| docs/career-guides/研究工程师.md | 1 |
| docs/career-guides/硬件工程师.md | 1 |
| docs/career-guides/算法工程师.md | 1 |
| docs/career-guides/解决方案与售前.md | 1 |
| docs/career-guides/设计师.md | 1 |
| docs/career-guides/财务与金融分析.md | 1 |
| docs/career-guides/运维与SRE.md | 1 |
| docs/cases/第一次看心理科.md | 1 |
| docs/competition-playbooks/Demo与路演答辩.md | 1 |
| docs/country-playbooks/中国大陆.md | 1 |
| docs/country-playbooks/新加坡.md | 1 |
| docs/country-playbooks/澳大利亚.md | 1 |
| docs/entrepreneurship/从自由职业到工作室.md | 1 |
| docs/entrepreneurship/找问题与用户访谈.md | 1 |
| docs/entrepreneurship/现金流与合同.md | 1 |
| docs/job-search/Offer与合同.md | 1 |
| docs/job-search/简历改造.md | 1 |
| docs/playbooks/第一次写论文.md | 1 |
| docs/playbooks/第一次找实习.md | 1 |
| docs/playbooks/第一次联系导师.md | 1 |
| docs/playbooks/第一次谈薪.md | 1 |
