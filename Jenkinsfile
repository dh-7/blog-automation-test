// Jenkins 声明式流水线 — 博客系统接口自动化测试（仅 API）
//
// 前提（agent 为 Windows 节点）：
//   - 已安装 Python 3.12+、Git，且在系统 PATH 中
//   - agent 能访问被测后端(8080) 与 MySQL(3306)，且 mysql/mysqldump 命令行可用
//   - 已安装插件：Allure Jenkins Plugin
//   - 已创建凭据：Secret text，ID 为 blog-db-password（专用测试数据库账号密码）
//   - 接口自动化不需要 Chrome/浏览器
pipeline {
    agent { label 'windows' }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()   // 被测系统/数据库是单实例，禁止并发构建互相踩数据
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '10'))
    }

    // 触发方式二选一：
    //   1) Webhook（推荐，要求 GitHub 能访问到 Jenkins）：在任务里勾选
    //      "GitHub hook trigger for GITScm polling"，并注释掉下面的 pollSCM
    //   2) 轮询 SCM（内网 Jenkins 用，默认）：每 5 分钟检查一次代码变更
    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        // 构建级 Python 虚拟环境（放在 workspace 下，依赖随 requirements.txt 自动更新）
        PYTHON = '.venv\\Scripts\\python.exe'

        // ── 运行时配置覆盖（优先级高于 config.yaml，机制见 utils/config.py）──
        // 被测环境/数据库不在 agent 本机时再覆盖：
        // BLOG_API_URL     = 'http://192.168.1.100:8080'
        // BLOG_MYSQL_HOST  = '192.168.1.100'

        // 数据库密码不进仓库：Jenkins 凭据中创建 Secret text，ID = blog-db-password
        BLOG_MYSQL_PASSWORD = credentials('blog-db-password')

        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('环境准备') {
            steps {
                bat 'python --version'
                // config.yaml 是本地文件且不提交仓库；每次构建都用脱敏模板初始化
                bat 'copy /Y config.example.yaml config.yaml'
                bat 'if not exist .venv python -m venv .venv'
                bat '%PYTHON% -m pip install --upgrade pip -q'
                bat '%PYTHON% -m pip install -r requirements.txt -q'
            }
        }

        stage('环境自检') {
            steps {
                // 后端 API/MySQL/基线快照任一不可用则快速失败（api 范围不检查前端）
                bat '%PYTHON% ci\\check_env.py api'
            }
        }

        stage('还原数据库基线') {
            steps {
                // 接口用例依赖基线中的表结构与预置数据（root conftest 的 db_baseline fixture 同样依赖它）
                bat '%PYTHON% -c "from utils.db_snapshot import restore_baseline; restore_baseline()"'
            }
        }

        stage('接口自动化测试') {
            steps {
                bat '%PYTHON% -m pytest api_case -v --tb=short --alluredir=report/allure-results-api --clean-alluredir --junitxml=report/junit-api.xml'
            }
        }
    }

    post {
        always {
            // JUnit 结果 → Jenkins 内置趋势图（任务首页可见历史通过率）
            junit testResults: 'report/junit-*.xml', allowEmptyResults: true
            // Allure 报告（接口自动化结果）
            allure([
                includeProperties: false,
                jdk: '',
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'report/allure-results-api']]
            ])
            // 运行日志留档
            archiveArtifacts artifacts: 'log/*.log', allowEmptyArchive: true
        }
        failure {
            // 建议接入邮件/钉钉/企业微信通知，示例见 docs/CI-落地方案.md 第 7 节
            echo '构建失败：请查看 Allure 报告与环境自检日志定位问题'
        }
    }
}
