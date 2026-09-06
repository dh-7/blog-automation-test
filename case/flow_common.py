"""UI 业务流程用例公共支撑 — YW_ 用例索引、登录/发布辅助、FlowBase 基类

自 test_business_flow_ui.py 拆分而来，供 case/test_business_flow_01~08_*.py 共用。

注意：test_notification 等用例依赖会话内的 DB 状态残留（如 PLHD-004"全部已读"
之前的未读通知），因此各流程文件的编号 NN 必须保持与拆分前一致的执行顺序，
且整体文件名前缀需保持在 test_category_tag.py（字母序 c）之前——重命名需谨慎。
"""
import pytest

from selenium.webdriver.common.by import By

from page.page_publish_article import PagePublishArticle
from utils import db_query
from utils.excel_loader import load_ui_flow_cases

from case.conftest import login  # noqa: F401  (re-export，供各流程文件 import)

# ── 从 Excel 加载 YW_ 用例，按 case_id 建索引 ──
_cases = load_ui_flow_cases()


def _c(case_id):
    """按编号取用例，找不到抛异常让 pytest 标记 ERROR"""
    assert case_id in _cases, f"Excel 中未找到用例 {case_id}"
    return _cases[case_id]


def _get_username_by_nickname(nickname):
    """通过昵称查询登录用户名（复用 utils.db_query）"""
    row = db_query.fetch_one(
        "SELECT username FROM user WHERE nickname=%s AND deleted=0", (nickname,))
    return row[0] if row else nickname


def _publish_disposable(driver, u, p, title):
    """发布一篇一次性文章（供删除类用例隔离破坏范围，避免误删种子数据）

    轮询确认文章已入库（发布后写库有短暂延迟），返回文章ID。
    """
    _publish_article(driver, u, p, title, "一次性测试文章内容，删除用例专用")
    import time as _t
    aid = None
    for _ in range(12):
        aid = db_query.article_id_by_title(title)
        if aid:
            return aid
        _t.sleep(0.5)
    toasts = [t.text for t in driver.find_elements(By.CSS_SELECTOR, ".el-message")]
    raise AssertionError(
        f"一次性文章'{title}'发布后未入库（URL={driver.current_url}, toasts={toasts}）")


def _publish_article(driver, u, p, title, content, category_name=None, tag_names=None, summary=None):
    """登录并发布文章辅助函数"""
    login(driver, u, p)
    page = PagePublishArticle(driver)
    page.open_url()
    page.wait_for_page_ready()
    page.input_title(title)
    if category_name and category_name != "（不选）":
        page.select_category(category_name)
    if tag_names:
        for tag in tag_names:
            if tag and tag != "（不选）":
                page.select_tag(tag)
    if summary and summary != "（空）":
        page.input_summary(summary)
    page.input_content(content)
    page.click_publish()
    page.wait_for_page_ready()


def _save_as_draft(driver, u, p, title, content, summary=None):
    """登录并保存草稿辅助函数"""
    login(driver, u, p)
    page = PagePublishArticle(driver)
    page.open_url()
    page.wait_for_page_ready()
    page.input_title(title)
    if summary and summary != "（空）":
        page.input_summary(summary)
    page.input_content(content)
    page.click_draft()
    page.wait_for_page_ready()


class FlowBase:
    """流程用例基类 — 统一注入 self.driver

    子类设置 login_case_id 后，每个测试开始前会以该用例的账号完成登录。
    """

    login_case_id = None

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver
        if self.login_case_id:
            c = _c(self.login_case_id)
            login(driver, c.login_user, c.login_password)
