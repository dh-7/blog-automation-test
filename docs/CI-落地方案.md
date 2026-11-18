# 博客自动化项目 CI 落地方案（Jenkins + GitHub ｜ 接口自动化）

> 适用仓库：`blog_automation`（pytest 自动化项目）
> **CI 范围：仅接口自动化（`api_case`）。UI 自动化暂不进 CI**，日后接入方式见第 10 节。
> 本文记录流水线配置方式；上线状态以 Jenkins 实际构建记录为准。

---

## 1. 目标与现状

**目标**：代码推送到仓库后自动执行接口自动化测试，产出 Allure 报告与通过率趋势，失败可追溯（日志），全程无需人工干预。

**项目现状盘点（决定了方案的几个关键点）**：

| 现状 | 对 CI 的影响 |
| --- | --- |
| 被测系统在本机：后端 `localhost:8080`、MySQL `localhost:3306`（接口测试不需要前端） | Jenkins agent 必须能访问这两个服务（最简单：agent 与被测系统同机，或同网段服务器） |
| 接口用例依赖数据库基线：会话开始/结束用 `mysql`/`mysqldump` 还原 `snapshots/blog_db_baseline.sql` | 基线文件必须进 git（已修复 .gitignore）；agent 上需有 MySQL 客户端命令行 |
| 报告体系已集成 Allure | 直接复用：Jenkins 装官方 Allure 插件即可，无需改报告代码 |
| Python 依赖固定在 `requirements.txt`；本地配置含环境相关值 | Jenkins 从脱敏的 `config.example.yaml` 初始化运行配置；数据库密码通过 Jenkins 凭据注入环境变量 |
| 项目仓库托管在 GitHub | Jenkins 使用 GitHub 仓库地址拉取代码，可使用轮询或 Webhook 触发 |

> 说明：`requirements.txt` 保留了 selenium 等 UI 依赖——本地 UI 测试仍要用；CI 多装几个包只多花几秒，换取一份依赖清单管理整个项目。

---

## 2. 仓库相关文件

| 文件 | 说明 |
| --- | --- |
| `Jenkinsfile` | 声明式流水线（仅接口）：环境准备 → 环境自检 → 还原 DB 基线 → 接口测试 → 发布报告 |
| `requirements.txt` | 锁定与本地一致的依赖版本 |
| `ci/check_env.py` | 环境自检。`python ci/check_env.py api` 只查后端 API + MySQL + 基线（CI 用）；不带参数全量检查含前端（本地调试 UI 用） |
| `utils/config.py`（修改） | 支持 `BLOG_*` 环境变量覆盖配置（优先级高于 yaml），空字符串可"清空"某项配置 |
| `config.example.yaml`（新增） | 脱敏的 CI 默认配置模板；流水线每次从模板生成运行配置 |
| `utils/driver_manager.py`（修改） | 无头模式下补 `--window-size=1920,1080`。接口 CI 不依赖浏览器，此改动是为日后 UI 进 CI 预留 |
| `.gitignore`（修改） | 忽略本地 `config.yaml` 和运行产物；保留 `snapshots/blog_db_baseline.sql` 供 CI 还原数据库 |
| `docs/CI-落地方案.md` | 本文档 |

以上为当前项目配置文件。首次运行或修改 CI 设置后，请按第 9 节验收清单实际执行流水线。

---

## 3. 总体架构

```
 ┌──────────┐  push / 轮询   ┌─────────────────────────────────────────────┐
 │  GitHub   │ ────────────▶ │  Jenkins（Windows 节点，与被测系统同机或同网段）│
 │           │               │                                             │
 └──────────┘                │  ① Checkout → ② venv + pip install          │
                             │  ③ 环境自检（后端 API / MySQL / 基线快照）    │
                             │  ④ mysql 还原数据库基线                      │
                             │  ⑤ pytest api_case（接口自动化）             │
                             │  ⑥ JUnit 趋势图 + Allure 报告 + 日志归档     │
                             └─────────────────────────────────────────────┘
```

- **禁止并发构建**：数据库是单实例，Jenkinsfile 已加 `disableConcurrentBuilds()`。
- 触发：Webhook（秒级，需 Jenkins 公网可达）或轮询 SCM（每 5 分钟，内网可用，当前默认）。
- 全程无浏览器参与，agent 不需要安装 Chrome。

---

## 4. 阶段一：搭建 Jenkins（Windows）

1. **安装 JDK 17+**（Jenkins LTS 要求），再到 <https://www.jenkins.io/download/> 下载 **Windows LTS 安装包（msi）**。
2. 安装向导关键选择：
   - 端口建议 `18080`（避开被测后端的 8080）。
   - **服务运行账户：选择你自己的域账户/本机账户，不要用默认 LocalSystem**。原因：LocalSystem 看不到用户级 PATH（Python、mysql 客户端），这是 Windows 上 Jenkins 最常见的坑。
3. 解锁后选择"安装推荐插件"（已含 Git、Pipeline、Credentials 等）。
4. **安装 Allure 插件**：Manage Jenkins → Plugins → Available → 搜索 `Allure` 安装。
5. **配置 Allure 命令行工具**：Manage Jenkins → Tools → Allure Commandline → Add：
   - Name：`Allure`
   - 勾选 **Install automatically**（默认从 Maven Central 自动下载，agent 无需手工装 Allure）。
6. **创建凭据**：Manage Jenkins → Credentials → System → Global → Add Credentials：
   - Kind：**Secret text**
   - Secret：专用测试数据库密码；请使用仅供 CI 的低权限账号，避免使用 root 账号。
   - ID：`blog-db-password`（与 Jenkinsfile 中一致）
7. **agent 自检**：在该机器上以**服务运行账户**登录验证（不是你的个人会话）：
   ```powershell
   python --version        # 需 3.12+
   git --version
   mysql --version         # 确保在系统 PATH（基线还原用 mysql/mysqldump）
   ```

> 接口自动化 CI **不需要安装 Chrome**；日后要把 UI 测试加进 CI 时再装（见第 10 节）。
> 若以后 Jenkins 部署在 Linux 服务器：同样流程，换用 `sh` 步骤 + `python3 -m venv`，并保证 locale 为 UTF-8（中文 Excel 文件名）。

---

## 5. 阶段二：代码仓库与 Jenkins 建立连接

### GitHub 仓库连接

1. 在 Jenkins Pipeline SCM 配置中填入现有 GitHub 仓库 URL 和目标分支。
2. 私有仓库需在 Jenkins Credentials 中配置 GitHub 拉取凭据。
3. GitHub Webhook（**仅当 Jenkins 公网可达**时可用）：仓库 Settings → Webhooks → Add webhook
   - Payload URL：`http://<Jenkins地址>:18080/github-webhook/`
   - Content type：`application/json`；Trigger：Just the push event。
   - Jenkins 任务中勾选 **GitHub hook trigger for GITScm polling**，并把 Jenkinsfile 里的 `pollSCM` 注释掉。
   - **Jenkins 在内网时的替代**：用 cloudflared/ngrok/frp 做内网穿透，或直接用轮询模式（已默认启用，效果是推送后最多延迟 5 分钟触发）。

---

## 6. 阶段三：创建 Jenkins 流水线任务

1. Jenkins 首页 → **新建任务** → 名称 `blog-api-ci` → 类型选 **流水线（Pipeline）**。
2. （可选）构建触发器：勾选 *GitHub hook trigger for GITScm polling*（webhook 模式才需要）。
3. **Pipeline** 区域：
   - Definition：**Pipeline script from SCM**
   - SCM：Git → Repository URL：GitHub 仓库地址
   - Credentials：第 5 节创建的拉取凭据（公有仓库可免）
   - Branch Specifier：`*/master`
   - Script Path：`Jenkinsfile`
4. 保存 → 左侧 **立即构建（Build Now）** 首跑验证。
5. 首跑后建议在任务配置里确认：构建丢弃策略（Jenkinsfile 已内置保留 30 次）。

---

## 7. 报告与通知

已内置（`post` 段）：

- **JUnit 趋势图**：任务首页直接看历史通过率曲线（`report/junit-*.xml`）。
- **Allure 报告**：构建页左侧 **Allure Report** 按钮（接口自动化结果）。
- **归档**：`log/*.log`（接口测试运行日志）。

通知（可选，把代码块加进 Jenkinsfile `post { failure { ... } }`）：

```groovy
// 邮件（需装 Email Extension 插件并在系统配置里设好 SMTP）
emailext to: 'you@example.com',
    subject: "[${JOB_NAME}] #${BUILD_NUMBER} ${currentBuild.currentResult}",
    body: "结果: ${currentBuild.currentResult}\nAllure报告: ${BUILD_URL}allure/\n控制台: ${BUILD_URL}console",
    attachLog: false

// 企业微信/钉钉机器人（无需插件，用 python 发，避免 bat 转义地狱）
bat '%PYTHON% -c "import requests,os; requests.post(os.environ[\'WECOM_WEBHOOK\'], json={\'msgtype\':\'text\',\'text\':{\'content\':\'%JOB_NAME% #%BUILD_NUMBER% 接口测试失败\'}})"'
// webhook 地址放 Jenkins 凭据 WECOM_WEBHOOK，同样用 credentials() 注入
```

---

## 8. 常见坑与规避（按踩中概率排序）

| # | 坑 | 规避（方案已内置/操作建议） |
| --- | --- | --- |
| 1 | Jenkins 服务账户（LocalSystem）看不到 Python/mysql 客户端 | 安装时用你的账户跑服务，或全部机器级安装并配**系统** PATH |
| 2 | CI 拉代码后还原基线报"快照不存在" | 已修 `.gitignore`；**记得 `git add snapshots/blog_db_baseline.sql`** |
| 3 | 被测后端没启动，跑出几百条失败 | `ci/check_env.py api` 快速失败，错误信息直接指明哪个服务不可达 |
| 4 | 两次构建间 DB 脏数据互相影响 | 会话级基线还原 + `disableConcurrentBuilds()`。注意：接口用例依赖基线中的预置数据（预置文章/评论/通知），**这步不能省** |
| 5 | 旧版本配置中的凭据可能留在 Git 历史 | 轮换任何曾提交的真实密码；当前流水线从 `config.example.yaml` 生成本地配置，并用 Jenkins Credentials 注入数据库密码 |
| 6 | agent 离线装不了 pip 包 | 换国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`（改 Jenkinsfile 该行即可） |
| 7 | 接口用例打不通后端（跨机部署时） | 在 Jenkinsfile environment 里覆盖 `BLOG_API_URL` / `BLOG_MYSQL_HOST` 指向测试服务器 |

---

## 9. 验收清单

- [ ] 手动 **Build Now** 全绿，控制台可见 4 个 stage（环境准备/自检/还原基线/接口测试）
- [ ] 任务首页出现 JUnit 趋势图；构建页可打开 Allure 报告（接口用例）
- [ ] 故意提交一条会失败的接口用例 → 构建红、Allure 报告可定位失败断言
- [ ] 停掉后端再构建 → 在"环境自检"阶段就红，且日志明确指出 8080 不可达
- [ ] push 代码后 ≤5 分钟自动触发（轮询模式）/ push 后秒级触发（webhook 模式）
- [ ] 连续两次构建 DB 状态一致（基线还原生效）
- [ ] Jenkins 凭据中不存在明文密码；`git log` 中不新增明文密码

---

## 10. 后续演进（跑稳之后再做）

1. **把 UI 自动化加回 CI**（如需要）：
   - agent 安装 Chrome；Jenkinsfile 环境加 `BLOG_HEADLESS = 'true'`（utils/driver_manager.py 已支持无头 + 窗口尺寸）；
   - 加回 stage：`pytest case -v --alluredir=report/allure-results-ui --clean-alluredir --junitxml=report/junit-ui.xml`（接口在前、UI 在后，不能并行）；
   - 环境自检改用全量模式：`ci\check_env.py`（去掉 api 参数，会连前端 5173 一起查）；
   - post 段的 allure results 增加 `[path: 'report/allure-results-ui']`。
2. **分层触发**：push 跑接口套件；如 UI 也进 CI，可定时（`triggers { cron('0 2 * * *') }`）夜间跑全量回归。
3. **PR 门禁**：Jenkins 换 Multibranch Pipeline，配合 GitHub Branch Source，PR 自动触发并回写检查状态。
4. **通知**：接入企业微信/钉钉机器人（第 7 节模板）。
5. **不稳定用例治理**：引入 `pytest-rerunfailures` 对标记用例自动重试，Allure 里看 retry 趋势。
6. **环境解耦**：被测系统部署到独立测试服务器后，只需在 Jenkinsfile 里覆盖 `BLOG_API_URL / BLOG_MYSQL_HOST` 两个变量，agent 与被测系统即可分离。
