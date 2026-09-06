"""作者主页模块 UI 测试 — 数据驱动"""
import os, sys, pytest
from selenium.webdriver.common.by import By
from page.page_login import PageLogin
from page.page_home import PageHome
from page.page_author import PageAuthor
from utils import db_query
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
from base.data_loader import UiDataLoader
import allure
import re

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="作者主页")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("作者信息")
class TestAuthor:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    @pytest.mark.parametrize("case_id,case", _params, ids=_ids)
    def test_author(self, case_id, case):

        # 需要登录的场景
        if case.login_required:
            user = case.login_user or "admin"
            pwd = case.login_password or "admin123"
            login_page = PageLogin(self.driver)
            login_page.login(user, pwd)

        author = PageAuthor(self.driver)
        # 数据源中作者ID为占位符（${作者ID}），按用例语义动态解析：
        # ZZY-004 需要"没有已发布文章"的作者，其余用作者2（zhangsan，有文章与草稿）
        path = case.resolved_path()
        if "${" in path:
            if case_id == 'FC-ZZY-004':
                no_pub = db_query.author_without_published()
                assert no_pub, "前置数据缺失：DB 中不存在没有已发布文章的用户"
                path = f"/author/{no_pub}"
            elif case_id == 'FC-ZZY-005':
                # 访问"不存在的用户主页"：动态取一个必定不存在的用户ID
                no_user = db_query.scalar(
                    "SELECT COALESCE(MAX(id),0)+1 FROM user")
                path = f"/author/{no_user}"
            else:
                path = "/author/2"
        author.open_url(path)
        author.wait_for_page_ready()

        # FC-ZZY-001: 作者主页显示作者完整信息（头像/昵称/简介/加入时间/文章数量）
        if case_id == 'FC-ZZY-001':
            assert author.get_author_name().strip(), "应显示作者昵称"
            assert author.get_author_bio().strip(), "应显示作者简介"
            stats = self.driver.find_elements(By.CSS_SELECTOR, ".author-stats .stat-item")
            assert stats, "应显示作者统计区（文章数量、加入时间）"
            stats_text = " ".join(s.text for s in stats)
            assert "文章" in stats_text, f"统计区应含文章数量，实际='{stats_text}'"
            assert "加入" in stats_text, f"统计区应含加入时间，实际='{stats_text}'"
            avatar = self.driver.find_elements(By.CSS_SELECTOR, ".el-avatar, .author-avatar img")
            assert avatar, "作者页应显示头像元素"
            return

        # FC-ZZY-002: 文章数量只统计已发布的不含草稿（UI 数字与 DB 已发布数一致）
        if case_id == 'FC-ZZY-002':
            count_ui = None
            for s in self.driver.find_elements(By.CSS_SELECTOR, ".author-stats .stat-item"):
                if "文章" in s.text:
                    m = re.search(r"\d+", s.text)
                    count_ui = int(m.group()) if m else None
            assert count_ui is not None, "作者页应显示文章数量"
            m2 = re.search(r"/author/(\d+)", self.driver.current_url)
            assert m2, f"应处于作者主页，实际URL={self.driver.current_url}"
            expected = db_query.published_article_count(int(m2.group(1)))
            assert count_ui == expected, \
                f"作者文章数应只统计已发布: UI显示={count_ui}, DB已发布={expected}"
            return

        # FC-ZZY-003: 进入作者主页，显示作者信息和已发布文章列表
        if case_id == 'FC-ZZY-003':
            assert "/author/" in self.driver.current_url, \
                f"应进入作者主页，实际URL={self.driver.current_url}"
            assert author.get_author_name().strip(), "作者主页应显示作者信息"
            assert author.get_article_titles(), "作者主页应显示已发布文章列表"
            return

        auto_assert(author, self.driver, case.expected)
