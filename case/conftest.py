"""UI测试 conftest"""
import os
import pytest
import allure
from page.page_login import PageLogin
from utils.config import Config
from utils.logger import set_case_id as _set_case_id

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def login(driver, username, password):
    """登录辅助函数 — 供 case/ 下各 test 文件共用

    内部使用 PageLogin.login()：点击登录后等待 URL 离开 /login 再返回，
    避免"登录跳转未完成就立即导航"导致的竞态失败。
    """
    login_page = PageLogin(driver)
    login_page.login(username, password)


@pytest.fixture(autouse=True)
def _auto_case_id(request):
    """自动从测试参数中提取 case_id 并设置到日志"""
    case_id = "SETUP"
    # 从 parametrize 参数中取 case_id
    if hasattr(request.node, 'callspec'):
        params = request.node.callspec.params
        if 'case_id' in params:
            case_id = str(params['case_id'])
    _set_case_id(case_id)
    yield
    _set_case_id("SETUP")


@pytest.fixture(scope="session", autouse=True)
def ui_env_config():
    """写入 UI 测试的 Allure 环境变量"""
    _allure_results = os.path.join(PROJECT_ROOT, "report", "allure-results-ui")
    if os.path.isdir(_allure_results):
        _env_file = os.path.join(_allure_results, "environment.properties")
        _base_url = Config.get("env", "base_url", default="http://localhost:5173")
        _api_url = Config.get("env", "api_url", default="http://localhost:8080")
        _db_name = Config.get("mysql", "database", default="blog_db")
        _browser = Config.get("browser", "chrome_path", default="Chrome")
        _headless = Config.get("browser", "headless", default=False)
        with open(_env_file, "w", encoding="utf-8") as ef:
            ef.write(f"base.url={_base_url}\n")
            ef.write(f"api.url={_api_url}\n")
            ef.write(f"database={_db_name}\n")
            ef.write(f"browser={_browser}\n")
            ef.write(f"headless={_headless}\n")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图并附加到 Allure 报告"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver")
        if driver:
            try:
                screenshot = driver.get_screenshot_as_png()
                allure.attach(screenshot, name="失败截图",
                              attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass
