# Stage 4 调研：IEEE 投稿系统状态追踪

调研日期：2026-09-16　结论：**B 档（粘贴识别）可行并已实现**；A 档（自动解析链接）不可行；C 档（手动）作为兜底保留。

本文只使用公开资料，未使用任何账号，未调用任何接口。引用内容均为转述，原文请看来源链接。

## 1. IEEE 的投稿入口

IEEE 目前是新旧系统并存、正在迁移的状态：

| 入口 | 作用 | 公开资料要点 |
|---|---|---|
| IEEE Author Portal（ieee.atyponrex.com，基于 Atypon ReX） | 新投稿的主要入口 | IEEE Systems Journal、IEEE Access、IEEE TAP 等要求在这里投稿和查状态；Computer Society 计划 2024 年底前全部迁入；ScholarOne 账号不能登录 Author Portal，需用 IEEE Account |
| ScholarOne Manuscripts（mc.manuscriptcentral.com/xxx-ieee） | 旧系统，仍有期刊和老稿件在用 | 例如 TVT 新投稿走 Author Portal，已在审的旧稿件仍在 ScholarOne 走完；ScholarOne 每个期刊单独注册账号 |
| IEEE Publishing Portal（publishingportal.ieee.org） | 2026 年推出的统一面板 | IEEE 表示今年内会把使用 ScholarOne 的期刊的作者、审稿人活动逐步转到这里管理，页面结构可能继续变化 |
| IEEE Author Gateway | 录用后的生产流程 | 看生产状态、校样等，不属于审稿状态，本工具不涉及 |

资料之间有一处不一致：IEEE 开放获取页面称所有 IEEE 出版物都用 Author Portal，而 IEEE TMI 的编辑指南仍基于 ScholarOne 操作。推测是「作者端已迁、编辑端未迁」的过渡状态，**公开资料无法证实**，不影响结论。

## 2. 状态词

### 2.1 IEEE Author Portal：官方 10 个状态（粒度粗）

来源：IEEE Submission Support 帮助文档「Use the My Submissions Page」。

| 状态 | 含义（转述） | 本工具处理 |
|---|---|---|
| Draft | 尚未提交 | 不导入 |
| Submitted | 已提交，系统分配稿号 | 已投稿 |
| Under Review | 同行评审进行中 | 审稿中 |
| In Revision | 编辑已做决定，要求修改 | 让用户选大修 / 小修 |
| Accepted | 以录用结束 | 已接收 |
| Accepted (Final Files) | 以录用结束（最终稿阶段） | 已接收 |
| Rejected | 以拒稿结束 | 被拒；页面上有 Start resubmission 时让用户选「被拒 / 大修（重投）」 |
| Rescinded | 编辑撤回原决定，新决定待定 | 审稿中，并提示原决定已撤回 |
| Replaced | 被管理员作为新稿重投并取代 | 不修改 |
| Withdrawn | 作者或编辑撤稿 | 已撤稿 |

有作者在 ResearchGate 反映，Author Portal 相比 ScholarOne 看不到编辑分配等细节，基本只有 under review 一个状态。本工具在识别来源为 Author Portal 时会显示这一限制。

### 2.2 ScholarOne：细粒度状态（因期刊配置而异）

| 状态词 | 核实情况 | 本工具处理 |
|---|---|---|
| Awaiting Reviewer Selection / Invitation / Assignment | IEEE TMI 编辑指南给出定义（审稿人未选够 / 未邀请够 / 同意的未够） | 审稿中 |
| Awaiting Reviewer Scores | 公开的 ScholarOne 状态说明中存在 | 审稿中 |
| Awaiting AE Recommendation | 同上：审稿意见已够，等副编辑给建议 | 审稿中 |
| Awaiting EIC Decision | 同上：主编尚未做最终决定 | 审稿中 |
| Under Review | 存在；有期刊反映邀请审稿人后即显示，不同配置行为不同 | 审稿中 |
| Awaiting Admin Processing、Awaiting AE / EIC / Editor Assignment | ScholarOne 通用说明中存在 | 已投稿（编辑处理，尚未送审） |
| 裸词 Awaiting Decision / Awaiting Assignment | 未找到 IEEE 使用裸词的证据 | 按带角色的形式识别；Reviewer Assignment 与 AE / EIC Assignment 分开处理 |

ScholarOne 的状态说明注明各期刊流程不同，部分词可能不出现，因此保留「记住这个说法」作为兜底。

### 2.3 决定词与两个陷阱

IEEE Author Center 把决定分为 Accept、Revise、Reject 三大类，但各期刊具体措辞不同：

1. **Reject 里藏着大修**：IEEE TMI 的选项有 Reject/Resubmit with Major Revision；IEEE Access 的 Reject 分为「修改后可重投一次」和「不允许重投」两种。本工具对 Reject/Resubmit…Major 直接判为大修，并采用「最长、最具体的说法优先」，避免被 Reject 抢先匹配。Author Portal 上两种 Reject 都显示为 Rejected，靠页面上是否有 Start resubmission 区分。
2. **大修重投会换稿号**：IEEE TMI 说明，大修重投分配新稿号，小修修改稿沿用原稿号加 .R1 / .R2。本工具按稿号匹配时忽略 .R1 后缀；稿号对不上时按标题匹配，提示「可能是重投后的新稿号」。

## 3. 整页复制是否可行

| | Elsevier Editorial Manager | ScholarOne | Author Portal |
|---|---|---|---|
| 页面形态 | 表格 | 表格（Author Dashboard 各队列） | 卡片列表（My Submissions） |
| 整页复制 | 可行 | 可行 | 可行 |
| 主要噪声 | 队列名 | 侧栏队列名（含 Decisions、Revised 等字样） | 按状态筛选的选项（含全部状态词）、「Submitted」日期标签 |

**未经证实的部分**：两个 IEEE 系统复制后文字的确切排版（状态格是否多行、Author Portal 卡片是否显示稿号、稿号格式），公开资料查不到。实现上按容错设计：不依赖固定列顺序，同时支持「状态在稿号前 / 后」、「卡片不显示稿号」几种排版。

## 4. 三档结论

| 档位 | 结论 | 理由 / 代价 / 风险 |
|---|---|---|
| A 自动解析链接 | 不可行 | ① 两个系统都需登录，浏览器跨域限制使纯前端无法读取；② 绕开需要代理服务器并经手登录态，违背无后端、隐私优先；③ 未找到面向作者的公开状态接口；④ 2026 年页面仍在迁移，即使做了也易失效。IEEE 网站条款原文因站点拒绝自动访问未能取得，不作为主证据 |
| B 粘贴识别 | 可行，已实现 | 代价集中在识别模块：新增两套词典、来源识别、噪声过滤、「可重投拒稿」判断。风险：Author Portal 状态粗；期刊配置差异（「记住说法」兜底）；页面改版；尚无真实样本校准（功能保持测试版） |
| C 手动 | 保留 | 已有，无额外工作 |

## 5. 与 Elsevier 版的异同

- **不变**：本机识别、不保存原文、不发请求；追踪链接只存不读；「记住这个说法」；稿号 → 标题 → 新增的匹配顺序；分不清大修小修时让用户选。
- **新增**：
  - 自动判断来源（EM / ScholarOne / Author Portal），判断不出时用全部词典；
  - ScholarOne、Author Portal 两套词典；
  - 「被拒 / 大修（重投）」选择；
  - 筛选项与队列名噪声过滤；
  - Author Portal 粗粒度提示；
  - 识别到的原始说法记在「最近识别」；
  - 从 IEEE 页面识别期刊名。
- **修改**：
  - 匹配规则改为「最长、最具体优先」；
  - 修改稿后缀同时兼容 R1 和 .R1；
  - 标题相同、稿号不同时提示可能是重投，并更新稿号；
  - 入口文案改为同时支持 Elsevier 和 IEEE。
- **确认项的落地**：预置状态中已有「已撤稿」，Withdrawn 直接对应，不需要新增预置状态。

## 6. 来源

- IEEE Submission Support（Author Portal 帮助）：Use the My Submissions Page — https://rex-docs.atypon.com/ieee-rex/author_portal/t_auth_my-submissions.html
- 同上：Start Resubmission of a Rejected Manuscript — https://rex-docs.atypon.com/ieee-rex/author_portal/t_auth_resubmit.html
- IEEE Author Center：IEEE Publishing Portal — https://journals.ieeeauthorcenter.ieee.org/submit-your-article-for-peer-review/ieee-publishing-portal/
- IEEE Author Center：Understanding the Decision Process — https://journals.ieeeauthorcenter.ieee.org/submit-your-article-for-peer-review/understanding-the-decision-process/
- IEEE Author Center：Use the IEEE Author Gateway — https://journals.ieeeauthorcenter.ieee.org/your-role-in-article-production/use-the-ieee-author-gateway/
- IEEE TMI：Instructions to AEs — https://ieeetmi.org/aes-instructions/
- IEEE Access：Stages of Peer Review — https://ieeeaccess.ieee.org/authors/stages-of-peer-review/
- IEEE Access：IEEE Author Portal 说明 — https://ieeeaccess.ieee.org/news/ieee-author-portal-saves-ieee-iaccess-i-authors-time-and-effort/
- IEEE Systems Council：IEEE Systems Journal 投稿说明 — https://ieeesystemscouncil.org/publication/ieee-systems-journal/instructions-for-authors
- IEEE Computer Society：Author Guidelines — https://www.computer.org/publications/author-resources
- IEEE Open Access：Author Workflow — https://open.ieee.org/for-authors/ieee-open-access-author-workflow/
- 第三方投稿指南（TVT 新旧系统并存） — https://manusights.com/blog/ieee-transactions-on-vehicular-technology-submission-process
- ScholarOne 状态说明（Floresta e Ambiente 期刊） — https://www.floram.org/instructions
- ScholarOne 状态说明（Sage 期刊支持） — https://journalssolutions.sagepub.com/en/support/solutions/articles/7000044932
- ScholarOne FAQ（每刊单独账号） — https://clarivate.com/webofsciencegroup/support/scholarone-manuscripts/most-frequently-asked-questions/
- ScholarOne Author Centre 队列名（OUP 投稿说明） — https://academic.oup.com/gbe/pages/submission_online
- ResearchGate 讨论：Author Portal 只显示 under review — https://www.researchgate.net/post/The_new_IEEE_article_submission_website_IEEE_Author_Portal
- ResearchGate 讨论：Awaiting AE Recommendation 含义 — https://www.researchgate.net/post/My_status_has_changed_from_Awaiting_Reviewer_Score_to_Awaiting_AE_Decision_Could_the_Associate_Editor_reject_the_manuscript_at_this_stage
- Political Science Rumors 讨论：Under Review 显示时机因配置而异 — https://www.poliscirumors.com/topic/awaiting-reviewer-assignment
