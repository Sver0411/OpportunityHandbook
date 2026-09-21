# -*- coding: utf-8 -*-
"""Canonical IA：在线导航的唯一事实源。

格式（缩进表示层级，`@` 后面是目标）：
    @e:<entry_id>   正文条目（位于 book/）
    @d:<location>   文档（位于 docs/，可带 #anchor）
    @n:<entry_id>   需要新建的正文条目

这个文件只描述「左栏显示什么、顺序、层级、点进去哪里」，与正文结构完全解耦。
"""

# 一级栏目编号与标题（顺序即导航顺序）
TREE = """
00 从这里开始
  这本指南怎么用 @n:guide-how-to-use
  人生并不是只有一条标准路线 @n:guide-no-single-path
  怎么判断一个选择值不值得 @n:judge-worth-it
  怎么比较两个完全不同的机会 @e:judge-compare-two-opportunities
  什么东西值得长期积累 @n:judge-long-term-accumulation
  什么叫机会成本 @e:judge-opportunity-cost
  什么叫可验证成果 @e:judge-verifiable-outcomes
  什么叫未来选择权 @n:judge-optionality
  不知道自己想做什么时怎么办 @e:start-when-no-direction

01 先决定下一步往哪里走
  认识你面前的几条主要路线
    继续读书 @e:paths-continue-study-default
    直接工作 @e:paths-direct-work
    职业教育与技能路线 @e:paths-vocational-and-trades
    海外发展 @e:paths-overseas
    参军与公共服务 @e:paths-military
    Gap Year @e:paths-gap-year
    自由职业 @n:paths-freelance
    创业 @n:paths-startup
  选学校与选专业
    学校和专业哪个更重要 @n:choose-school-vs-major
    城市要不要纳入选择 @n:choose-city
    兴趣应该占多大比重 @n:choose-interest-weight
    就业前景应该怎么看 @n:choose-job-outlook
    转专业 @n:choose-change-major
    辅修与双学位 @n:choose-minor-double-degree
    如果第一次选择不理想怎么办 @n:choose-major-mismatch
  专科与职业教育
    专科毕业后的主要出口 @n:vocational-outcomes
    专升本 @e:study-zhuanshengben
    职业本科 @n:vocational-undergraduate
    学徒制与技能路线 @n:apprenticeship
    技能型职业的发展空间 @n:trades-career-room
  家庭经济与教育成本
    学费与生活费 @n:education-tuition-living
    奖助学金 @e:funding-scholarship-system
    助学贷款 @e:funding-student-loan
    为教育投入多少钱才合理 @n:education-cost-budget
  给自己保留退路
    为什么不要过早把路线锁死 @n:optionality-why-not-lock
    哪些能力可以跨路线使用 @n:optionality-transferable
    走错以后怎么切换 @e:paths-switching-between-paths

02 在学校里先把基础打好
  学业
    GPA 与排名到底重要吗 @n:gpa-matters
    挂科会带来什么影响 @n:failing-courses
    专业课应该学到什么程度 @n:coursework-depth
    通识课有没有价值 @n:general-education-value
    学业、实践和生活怎么平衡 @n:study-life-balance
  开始认识真实世界
    怎么了解一个行业 @n:understand-industry
    怎么了解一个岗位 @n:understand-role
    招聘 JD 应该怎么看 @n:read-jd
    怎么找到真实从业者 @n:find-practitioners
    不知道方向时怎么低成本试错 @e:explore-low-cost-experiments
  通用能力
    信息检索 @n:skill-information-retrieval
    写作 @n:skill-writing
    表达与演讲 @n:skill-presentation
    沟通协作 @n:skill-collaboration
    数据能力 @n:skill-data
    项目管理 @n:skill-project-management
    AI 与数字工具 @n:skill-ai-tools
  专业技能
    什么技能值得学 @e:skill-what-to-learn
    怎么从岗位要求反推技能 @n:skill-reverse-engineer
    学课程还是直接实践 @n:skill-course-or-practice
    怎么判断自己真的掌握了 @n:skill-mastery-check
  语言
    英语为什么仍然重要 @e:skill-english
    四六级与校内英语 @n:english-cet
    IELTS / TOEFL / TOEIC @n:english-standardized-tests
    第二外语 @n:skill-second-language
    如果以后可能留学，什么时候准备 @n:language-timing-for-abroad
  证书
    哪些证书值得考 @e:certificate-what-is-worth-it
    法定准入型证书 @e:skill-occupational-certificates
    行业认证 @e:skill-industry-certification
    厂商认证 @n:certificate-vendor
    不要为了证书而考证 @n:certificate-not-for-certificates

03 开始积累真正能留下来的经历
  项目与作品
    什么才算真正的项目 @e:project-what-is-real
    教程项目有没有价值 @e:project-tutorial
    第一个个人项目怎么开始 @e:project-personal
    团队项目 @e:project-team
    作品集 @e:project-portfolio
    Demo @n:project-demo
    数据、测试和指标 @n:project-data-test-metrics
    真实用户与反馈 @n:project-users-feedback
  竞赛
    要不要参加比赛 @n:competition-should-i-join
    什么比赛值得参加 @e:competition-what-worth-joining
    奖项和过程哪个更重要 @e:competition-award-vs-process
    学科竞赛 @e:competition-mathematical-modeling
    工程竞赛 @n:competition-engineering
    编程与数据竞赛 @e:competition-programming-contest
    商业与创业竞赛 @n:competition-business
    设计与创作竞赛 @n:competition-design-creative
    职业技能竞赛 @n:competition-vocational-skills
  科研初体验
    科研到底是什么 @e:research-what-is-research
    哪些人值得接触科研 @e:research-who-suits
    怎么找到第一次科研机会 @e:research-undergrad-start
    怎么找导师 @e:research-find-supervisor
    怎么判断一个实验室 @e:research-choosing-a-lab
    怎么判断自己是否喜欢科研 @n:research-do-i-like-it
  开源与公共贡献
    什么是开源贡献 @n:opensource-what-is
    第一次贡献怎么开始 @e:opensource-first-contribution
    Issue @e:project-issue-pr
    PR @n:opensource-pr
    Documentation @n:project-documentation
    Review @n:project-code-review
    Maintainer @e:project-maintainer
  社群与活动
    社团有没有价值 @n:community-club-value
    专业协会 @n:community-professional-association
    Student Chapter @e:community-student-chapter
    志愿活动 @e:paths-volunteering
    Meetup @n:community-meetup
    怎么从“参加”变成真正的贡献 @n:community-from-join-to-contribute
  实习准备
    实习有什么用 @e:internship-worth-it
    什么时候开始找第一段实习 @e:internship-types
    没经验怎么找实习 @e:internship-how-to-find
    实习和项目怎么选 @n:internship-vs-project
    实习和科研怎么选 @n:internship-vs-research
    怎么判断一段实习值不值得 @e:internship-remote

04 当你开始面对第一次重要分流
  先决定主线
    升学还是工作 @n:fork-study-or-work
    国内还是海外 @n:fork-home-or-abroad
    科研还是产业 @n:fork-research-or-industry
    可以同时准备几条路线 @n:fork-parallel-tracks
    怎么设置主线和备选 @n:fork-main-and-backup
  国内升学
    读研值不值得 @e:grad-school-worth-it
    保研 @e:study-baoyan
    考研 @e:study-kaoyan
    保研和考研怎么选 @e:baoyan-vs-kaoyan
    学硕和专硕 @e:study-academic-vs-professional
    跨专业 @e:study-cross-major
    选学校 @n:study-choose-school
    选导师 @n:study-choose-supervisor
    复试 @e:study-second-round-interview
    调剂 @e:study-transfer-adjustment
    二战 @e:study-retake-exam
  海外升学
    留学值不值得 @e:overseas-is-it-for-me
    国家和地区怎么选 @n:overseas-choose-country
    授课型与研究型 @e:overseas-taught-vs-research-master
    GPA @n:overseas-gpa
    语言与标化考试 @e:overseas-admission-tests
    推荐信 @e:overseas-recommendation-letters
    SOP / PS @e:overseas-sop-ps
    Research Proposal @e:overseas-research-proposal
    联系教授 @e:overseas-contacting-professors
    奖学金与 Funding @e:overseas-funding
    留学总成本 @e:overseas-total-cost
  深入科研
    RA @n:research-ra
    暑研 @e:research-summer-program
    Research Internship @e:overseas-research-internship
    文献阅读 @e:research-literature-reading
    研究问题 @e:research-question
    实验与数据 @n:research-experiment-data
    论文写作 @e:research-writing-and-submission
    学术会议 @n:research-conference
    推荐信 @n:research-recommendation-letter
  实习进一步升级
    日常实习 @n:internship-daily
    暑期实习 @n:internship-summer
    Off-cycle @e:internship-off-cycle
    留用实习 @e:internship-return-offer
    海外实习 @e:internship-overseas
    Research Intern @e:internship-research-intern
  资助
    Scholarship @n:funding-scholarship
    Fellowship @e:funding-fellowship-grant
    Grant @n:funding-grant
    Stipend @e:funding-stipend
    Fee Waiver @e:funding-fee-waiver
    Travel Grant @e:funding-travel-and-conference-grant
    怎么找全额资助机会 @e:funding-full-funding

05 从学校走向第一份工作
  校招是怎么运作的
    提前批 @n:recruit-early-batch
    秋招 @e:campus-recruiting-timeline
    春招 @n:recruit-spring
    补录 @n:recruit-supplement
    内推 @e:job-hunting-referral
  找岗位
    公司官网 @n:job-channel-company-site
    招聘平台 @n:job-channel-platform
    校友与内推 @n:job-channel-alumni
    招聘会 @n:job-channel-fair
    怎么看招聘 JD @n:job-read-jd
  简历与作品
    简历怎么写 @e:job-hunting-resume
    项目经历怎么写 @n:resume-projects
    实习经历怎么写 @n:resume-internship
    科研经历怎么写 @n:resume-research
    竞赛经历怎么写 @n:resume-competition
    作品集 @n:resume-portfolio
  笔试与面试
    在线测评 @e:job-hunting-written-test
    专业面 @e:job-hunting-interview
    技术面 @n:interview-technical
    Case Interview @n:interview-case
    行为面 @n:interview-behavioral
    HR 面 @n:interview-hr
  Offer
    Offer 怎么比较 @e:offer-comparison
    薪资和总包怎么看 @n:offer-total-comp
    股票与奖金 @n:offer-equity-bonus
    谈薪 @e:job-hunting-salary-negotiation
    三方 @e:job-hunting-tripartite-agreement
    背调 @e:job-hunting-background-check
    毁约 @n:offer-renege
  第一份工作
    第一份工作最应该换回什么 @e:first-job-what-to-trade-for
    大公司还是小公司 @e:first-job-big-vs-small
    国企、民企还是外企 @e:first-job-company-types
    行业还是岗位 @e:first-job-role-vs-industry
    城市还是机会 @e:first-job-city
    工资还是成长 @e:first-job-pay-vs-growth
  如果没有顺利进入下一站
    长期找不到工作怎么办 @e:job-hunting-long-search
    要不要降低岗位要求 @n:job-lower-requirements
    要不要换城市 @n:job-change-city
    要不要继续升学 @n:job-or-further-study
    空窗期怎么处理 @n:job-gap-period
    第一次选择错了怎么办 @n:job-first-choice-wrong

06 进入职场以后继续积累
  刚进入职场
    怎么度过试用期 @n:work-probation
    怎么真正学会一份工作 @n:work-learn-the-job
    怎么理解业务 @n:work-understand-business
    怎么和直属领导合作 @n:work-with-manager
    怎么找职场 Mentor @e:find-workplace-mentor
  从执行到独立负责
    Ownership @n:work-ownership
    怎么承担更大的项目 @n:work-bigger-projects
    怎么证明自己的成果 @n:work-prove-results
    怎么积累业务影响 @n:work-business-impact
    怎么记录职业成果 @n:work-record-achievements
  工作后继续学习
    技能还要不要继续学 @e:work-learn-skills
    工作后考证 @n:work-certificates
    工作后学语言 @n:work-learn-language
    工作后做个人项目 @n:work-side-project
    工作后做开源 @n:work-open-source
    工作后重新读书 @e:work-study-again
  建立行业关系
    Networking @e:community-networking
    专业社群 @n:community-professional-group
    Mentor @n:work-mentor-role
    Organizer @n:community-organizer
    Speaker @n:community-speaker
    Reviewer @n:community-reviewer
    行业影响力 @e:community-industry-influence
  第一次重新选择
    什么时候适合第一次跳槽 @e:career-job-hopping
    什么情况下应该留下 @n:work-when-to-stay
    内部转岗 @n:work-internal-transfer
    工作后读研 @n:work-study-again
    海外工作 @n:work-overseas-job

07 当职业开始出现分岔
  晋升
    Senior 意味着什么 @e:career-senior-ic-track
    晋升标准 @n:promotion-criteria
    晋升材料 @e:career-promotion-package
    怎么证明影响力 @e:career-influence
    长期不晋升怎么办 @n:promotion-stalled
  专家路线
    专业深度 @n:track-ic-depth
    跨团队影响 @n:track-ic-cross-team
    行业影响 @n:track-ic-industry
    Staff / Principal 等角色 @n:track-staff-principal
  管理路线
    第一次带人 @n:mgmt-first-team
    Team Lead @n:mgmt-team-lead
    Manager @e:career-management-track
    招聘 @n:mgmt-hiring
    绩效 @n:mgmt-performance
    技术还是管理 @n:mgmt-ic-or-manager
  跳槽
    为什么跳 @n:hop-why
    什么时候跳 @n:hop-when
    平薪跳槽 @n:hop-same-pay
    涨薪跳槽 @n:hop-higher-pay
    换行业 @n:hop-change-industry
    换城市 @n:hop-change-city
  转行
    转行前先判断什么 @n:switch-before-decide
    为什么不要清零过去经历 @e:career-change-keep-capital
    可迁移技能 @e:career-transferable-capital
    可迁移行业经验 @n:switch-transferable-domain
    Bridge Opportunity @e:career-bridge-opportunity
    Side Project @n:switch-side-project
    降薪转行 @e:career-pay-cut-transition
  再次进入教育体系
    工作后读硕士 @n:edu-master-after-work
    MBA / MPA 等职业学位 @n:edu-mba-mpa
    第二硕士 @n:edu-second-master
    博士 @e:research-phd-worth-it
    海外教育 @n:edu-abroad-again

08 其他同样成立的人生路径
  自由职业
    怎么开始 @e:startup-freelance
    找客户 @n:freelance-clients
    定价 @n:freelance-pricing
    合同 @n:freelance-contract
    收入稳定性 @n:freelance-stability
  副业
    什么副业值得做 @e:startup-side-project
    接单 @n:side-gig-orders
    咨询 @n:side-consulting
    内容创作 @n:side-content
    独立开发 @e:startup-indie-hacker
    小生意 @n:side-small-business
  创业
    创业前应该验证什么 @e:startup-validate-before-quit
    MVP @n:startup-mvp
    第一批用户 @n:startup-first-users
    商业模式 @n:startup-business-model
    Incubator @n:startup-incubator
    Accelerator @n:startup-accelerator
    融资 @e:startup-funding
  副业转主业 @e:side-project-to-main-business
  职业中断后重新进入职场 @n:career-break-return
  第二职业 @n:second-career
  再次不知道方向时怎么办 @n:direction-again

09 专题手册
  科研手册 @d:docs/manuals/科研手册
  竞赛手册 @d:docs/manuals/竞赛手册
  项目与作品手册 @d:docs/manuals/项目与作品手册
  开源手册 @d:docs/manuals/开源手册
  技能学习手册 @d:docs/manuals/技能学习手册
  语言与考试 @d:docs/manuals/语言与考试
  证书 @d:docs/manuals/证书
  奖学金与资助 @d:docs/manuals/奖学金与资助
  社群与行业组织 @d:docs/manuals/社群与行业组织
  创业与自由职业 @d:docs/manuals/创业与自由职业
  国家与地区
    中国大陆 @d:docs/countries/中国大陆
    中国香港 @d:docs/countries/中国香港
    美国 @d:docs/countries/美国
    加拿大 @d:docs/countries/加拿大
    英国 @d:docs/countries/英国
    欧洲大陆 @d:docs/countries/欧洲大陆
    日本 @d:docs/countries/日本
    韩国 @d:docs/countries/韩国
    新加坡 @d:docs/countries/新加坡
    澳大利亚 @d:docs/countries/澳大利亚
    新西兰 @d:docs/countries/新西兰
  行业与职业
    技术与工程 @d:docs/careers/技术与工程
    AI 与数据 @d:docs/careers/AI与数据
    制造 @d:docs/careers/制造
    商业与金融 @d:docs/careers/商业与金融
    设计与创意 @d:docs/careers/设计与创意
    医疗健康 @d:docs/careers/医疗健康
    生命科学 @d:docs/careers/生命科学
    教育 @d:docs/careers/教育
    法律与公共事务 @d:docs/careers/法律与公共事务
    科研与高校 @d:docs/careers/科研与高校
    公共服务 @d:docs/careers/公共服务
    技能型职业 @d:docs/careers/技能型职业

10 时间线与工具
  路径时间线
    高中毕业后的选择 @d:docs/timelines/高中到大学
    本科四年 @d:docs/timelines/本科四年
    保研 @d:docs/timelines/保研时间线
    考研 @d:docs/timelines/考研时间线
    留学申请 @d:docs/timelines/留学申请时间线
    博士申请 @d:docs/timelines/博士申请时间线
    校招 @d:docs/timelines/校招时间线
    科研入门 @d:docs/timelines/科研入门时间线
    转行 @d:docs/timelines/转行时间线
  工具与模板
    机会价值判断表 @d:docs/tools/机会价值判断表
    Offer 对比表 @d:docs/tools/Offer对比表
    导师筛选表 @d:docs/tools/导师筛选表
    联系导师邮件模板 @d:docs/tools/联系导师邮件模板
    留学选校表 @d:docs/tools/留学选校表
    求职追踪表 @d:docs/tools/求职追踪表
    探索复盘模板 @d:docs/tools/探索复盘模板
    职业资本盘点表 @d:docs/tools/职业资本盘点表
    转行 Bridge Plan @d:docs/tools/转行BridgePlan
    时间线检查表 @d:docs/tools/时间线检查表

11 避坑
  升学与留学 @e:trap-guaranteed-admission
  求职与实习 @e:trap-fake-internships-and-paid-research
  科研 @e:trap-predatory-journals
  竞赛 @e:trap-paid-competitions
  证书与培训 @e:trap-certificate-hoarding
  项目与履历 @e:trap-collecting-courses-and-half-projects
  创业与副业 @n:trap-startup-side-gig
  信息差、机会焦虑与从众 @e:trap-information-asymmetry
"""
