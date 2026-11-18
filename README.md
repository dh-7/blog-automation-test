# 博客系统自动化测试项目

基于 pytest 为博客系统编写 UI 与 API 自动化测试，覆盖常见用户操作、管理员操作和文章生命周期流程。

## 快速开始

### 环境要求

- Python 3.12 或兼容版本；依赖版本见 `requirements.txt`。
- 被测博客系统按 `config.yaml` 配置运行。当前默认前端为 `http://localhost:5173`，API 为 `http://localhost:8080`。
- MySQL 可连接，且测试数据库已初始化。测试会话开始和结束时，根目录 fixture 会调用 `utils/db_snapshot.py` 恢复 `snapshots/blog_db_baseline.sql`；请只配置专用测试数据库。
- UI 测试需要可用的 Chrome 和 WebDriver。当前 `config.yaml` 中配置了本机路径，换机器时需修改配置，或使用 `utils/config.py` 支持的环境变量覆盖。
- 生成可浏览的 Allure 报告还需要安装 Allure 命令行工具；Python 报告插件已列在依赖中。

### 安装依赖

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 运行测试

```powershell
# UI 自动化
python run.py

# API 自动化
python run.py api

# UI 与 API 全部运行
python run.py all

# 仅运行测试，不生成 Allure HTML 报告
python run.py api noreport

# 直接用 pytest 运行指定套件
python -m pytest case -v
python -m pytest api_case -v
```

`pytest.ini` 的默认 `testpaths` 目前只有 `case/`，所以直接执行 `python -m pytest` 只会收集 UI 用例；运行 API 用例或全量测试时请显式指定目录，或使用 `run.py`。`run.py all` 会先运行 UI，再运行 API。

## 测试范围

| 类型 | 目录 | 覆盖内容 |
| --- | --- | --- |
| UI 自动化 | `case/`、`page/`、`base/` | 登录注册、文章与评论、收藏历史、用户信息、后台管理及多步骤业务流程；Selenium 页面操作由 Page Object 封装 |
| API 自动化 | `api_case/`、`api/` | Excel 参数化接口用例、业务流程、响应断言、变量关联、回查和数据库校验 |
| 测试数据 | `data/` | UI/API 自动化数据源及测试用例工作簿 |
| 测试环境与数据 | `config.yaml`、`snapshots/`、`utils/db_snapshot.py` | 被测服务、浏览器、账号、MySQL 配置和数据库基线恢复 |

## 目录与关键文件

| 路径 | 职责 |
| --- | --- |
| `case/` | UI 测试及 UI 业务流程用例 |
| `page/` | 博客前台和管理后台的页面对象 |
| `base/` | 页面基类、表格操作和 UI 数据加载 |
| `api_case/` | API 参数化用例及多步骤业务流程 |
| `api/` | API 客户端、断言、变量管理、Excel 加载和数据库断言 |
| `data/` | 自动化数据源与测试用例 Excel 文件 |
| `utils/` | 配置、浏览器驱动、日志、数据库查询及快照工具 |
| `snapshots/blog_db_baseline.sql` | 测试数据库基线；测试前后恢复所需，请勿当作普通运行产物删除 |
| `ci/check_env.py` | 检查前端/API 端口、MySQL 和基线文件是否可用 |
| `Jenkinsfile` | Jenkins API 测试流水线配置 |
| `docs/CI-落地方案.md` | Jenkins 配置与验收说明 |
| `run.py` | UI/API/全量运行入口及 Allure 报告生成 |
| `requirements.txt` | Python 依赖及版本 |
| `pytest.ini` | pytest 收集规则；默认套件为 `case/` |

## 配置说明

测试环境和数据库参数在 `config.yaml` 中。`utils/config.py` 支持用环境变量覆盖对应配置，环境变量优先级高于 YAML：

| 环境变量 | 配置项 |
| --- | --- |
| `BLOG_BASE_URL`、`BLOG_API_URL` | 前端与 API 地址 |
| `BLOG_HEADLESS`、`BLOG_CHROME_PATH`、`BLOG_DRIVER_PATH` | 浏览器运行方式及 Chrome/WebDriver 路径 |
| `BLOG_MYSQL_HOST`、`BLOG_MYSQL_PORT`、`BLOG_MYSQL_USER`、`BLOG_MYSQL_PASSWORD`、`BLOG_MYSQL_DATABASE` | MySQL 连接配置 |
| `BLOG_ACCOUNT_USERNAME`、`BLOG_ACCOUNT_PASSWORD` | UI 测试账号 |

不要把真实密码、令牌或个人机器路径提交到公开仓库。分享项目之前，应检查 `config.yaml` 和 Git 历史中的凭据，并使用本地配置或环境变量提供敏感值。

## 报告与 CI

`run.py` 将 UI/API 的 Allure 原始结果及 HTML 报告写入 `report/`。`Jenkinsfile` 配置了环境准备、自检、数据库基线恢复、API 测试和报告归档；具体 Jenkins 部署与验收步骤见 `docs/CI-落地方案.md`。流水线配置本身不代表 CI 已在目标 Jenkins 环境验收通过。

当前数据库基线通过共享 MySQL 数据库恢复；不要对该测试库并行运行会互相修改数据的测试任务。根目录 `conftest.py` 的 session 级自动 fixture 会在 UI/API 测试会话开始与结束时恢复基线。
