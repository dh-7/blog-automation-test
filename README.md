# 博客系统自动化测试项目

使用 pytest、Selenium 和 requests 为博客系统编写 UI 与 API 自动化测试，覆盖主要用户操作、管理员功能和文章生命周期。

## 项目结构

```text
api/          API 客户端、响应断言、变量关联和数据库断言
api_case/     API 参数化用例与多步骤业务流程
base/         Selenium 页面基类、表格操作和数据加载兼容层
case/         UI 功能用例与业务流程
ci/           CI 环境检查脚本
data/         手工测试用例和 UI/API 自动化数据源
docs/         Jenkins CI 配置说明
page/         前台与后台页面对象
snapshots/    测试数据库基线快照
utils/        配置、Excel、浏览器、日志和数据库工具
```

主要数据文件：

| 文件 | 用途 |
| --- | --- |
| `data/博客系统-测试用例.xlsx` | UI 功能测试与业务流程用例清单 |
| `data/博客系统-自动化测试数据源.xlsx` | UI 自动化使用的数据、账号和接口清单 |
| `data/博客系统-接口测试用例.xlsx` | API 功能测试与业务流程用例清单 |
| `data/博客系统-接口自动化数据源.xlsx` | API 参数化自动化数据、配置和断言说明 |

## 环境准备

- Python 3.12 或兼容版本；依赖版本见 `requirements.txt`。
- 可访问的博客前端、API 和专用 MySQL 测试数据库。默认地址分别是 `http://localhost:5173` 和 `http://localhost:8080`。
- MySQL 命令行工具 `mysql`；生成数据库快照时还需要 `mysqldump`。
- UI 测试需要 Chrome 和匹配的 ChromeDriver。
- Allure HTML 报告需要额外安装 Allure 命令行工具；`allure-pytest` 已包含在 Python 依赖中。

测试会话开始和结束时，根目录 `conftest.py` 会恢复 `snapshots/blog_db_baseline.sql`。该操作会覆盖目标数据库中的测试数据；务必使用专用测试库，不要连接生产或个人数据。基线恢复依赖数据库已创建且测试账号有相应权限。

### 安装

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml
```

编辑本地 `config.yaml`，设置浏览器、MySQL 和 UI 测试账号。API 测试账号配置目前来自 `data/博客系统-接口自动化数据源.xlsx` 的“全局配置”工作表。项目内示例账号仅适用于本地演示服务；请按自己的测试环境调整。

## 运行测试

```powershell
# UI 自动化
python -m pytest case -v

# API 自动化
python -m pytest api_case -v

# UI 与 API 全部运行
python -m pytest case api_case -v
```

`pytest.ini` 默认只配置 `case/`。因此直接运行 `python -m pytest` 不包含 API 用例；运行 API 或全量测试时请显式指定目录。也可用 `python run.py`、`python run.py api` 或 `python run.py all` 生成 Allure 测试结果；Jenkins 中直接运行 pytest 并用 JUnit XML 判断结果。

## 配置

首次运行前复制 `config.example.yaml` 为本地 `config.yaml`，修改环境地址、浏览器位置和 MySQL 连接。`utils/config.py` 支持以下环境变量覆盖 YAML 中对应设置：

| 环境变量 | 配置 |
| --- | --- |
| `BLOG_BASE_URL`、`BLOG_API_URL` | 前端和 API 地址 |
| `BLOG_HEADLESS`、`BLOG_CHROME_PATH`、`BLOG_DRIVER_PATH` | 浏览器模式与可执行文件路径 |
| `BLOG_MYSQL_HOST`、`BLOG_MYSQL_PORT`、`BLOG_MYSQL_USER`、`BLOG_MYSQL_PASSWORD`、`BLOG_MYSQL_DATABASE` | MySQL 连接 |
| `BLOG_ACCOUNT_USERNAME`、`BLOG_ACCOUNT_PASSWORD` | UI 测试账号 |

不要提交本地 `config.yaml`、真实凭据或个人机器路径。公开仓库前也应检查 Excel 测试数据中的账号是否只用于演示环境。

## 测试能力

- Selenium Page Object、显式等待和失败截图。
- API Excel 参数化、响应断言、变量提取和接口回查。
- API 写操作后的数据库状态校验。
- Allure 测试步骤、报告和 Jenkins 流水线配置。

Jenkins 部署方式与流水线前置条件见 [`docs/CI-落地方案.md`](docs/CI-落地方案.md)。该文档提供配置和验收步骤；请以 Jenkins 实际构建记录为准判断流水线是否已通过。
