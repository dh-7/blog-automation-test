"""接口测试 conftest：将 api/ 模块的 fixtures 注册到 pytest 收集路径"""
import os
import sys

# 确保项目根目录在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

_API_RESULTS_DIR = os.path.join(PROJECT_ROOT, "report", "allure-results-api")


# 从 api.conftest 导入所有 session 级 fixtures，使 pytest 能发现它们
from api.conftest import (
    api_snapshot,
    data_loader,
    api_config,
    var_manager,
    assertor,
    db_assertor,
    api_client,
    setup_login,
    DATASOURCE_FILE,
)
