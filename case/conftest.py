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
        if 'case' in params:
            case = params['case']
            if hasattr(case, 'module') and case.module:
                allure.dynamic.story(case.module)

    _set_case_id(case_id)

    yield
    _set_case_id("SETUP")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """将每个测试用例的执行包装在 allure step 中，以便报告中显示用例标题

    对于数据驱动测试：step 标题为 [case_id] case.title
    对于业务流测试：step 标题为测试方法的 docstring 第一行或方法名
    """
    # 获取测试标题
    title = None

    # 从动态数据获取
    if hasattr(item, 'callspec'):
        params = item.callspec.params
        if 'case_id' in params and 'case' in params:
            case = params['case']
            cid = params.get('case_id', '')
            if hasattr(case, 'title') and case.title:
                title = f"[{cid}] {case.title}"

    # 从 docstring 获取
    if not title and item.function.__doc__:
        title = item.function.__doc__.strip().split('\n')[0]

    if not title:
        title = item.name

    # 设置 Allure 动态标题（用于测试用例的名称，而非 step 名称）
    allure.dynamic.title(title)

    with allure.step(title):
        yield


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
    """测试失败时自动截图并附加到 Allure 报告

    增强：成功时也附加截图（仅限 passed 状态），便于人工确认页面状态
    """
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        driver = item.funcargs.get("driver")
        if driver:
            try:
                screenshot = driver.get_screenshot_as_png()
                if report.failed:
                    allure.attach(screenshot, name="失败截图",
                                  attachment_type=allure.attachment_type.PNG)
                elif report.passed:
                    # 成功时也附加截图，便于人工确认（可选，去掉注释即可启用）
                    # allure.attach(screenshot, name="最终页面",
                    #               attachment_type=allure.attachment_type.PNG)
                    pass
            except Exception:
                pass
