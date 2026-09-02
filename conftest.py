import os
import pytest
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager
from utils.db_snapshot import restore_baseline

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session", autouse=True)
def config():
    """加载配置（整个测试会话只加载一次）"""
    return Config.load(os.path.join(PROJECT_ROOT, "config.yaml"))


@pytest.fixture(scope="session", autouse=True)
def db_baseline():
    """统一的数据库基线：测试前还原干净状态，测试后再次还原"""
    restore_baseline()
    yield
    restore_baseline()


@pytest.fixture(scope="function")
def driver(config):
    """浏览器驱动（每个测试函数独立开关）
    改为 scope="session" 可提速，但测试间不隔离
    """
    drv = DriverManager.get_driver(config)
    yield drv
    DriverManager.quit_driver()


@pytest.fixture(scope="function")
def page(driver, config):
    """BasePage 实例"""
    timeout = config.get("env", "timeout", default=10)
    return BasePage(driver, timeout)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            page.take_screenshot(name=f"FAIL_{item.name}")
