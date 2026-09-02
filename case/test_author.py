"""作者主页模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_login import PageLogin
from page.page_home import PageHome
from page.page_author import PageAuthor
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

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
        author.open_url(case.resolved_path())
        author.wait_for_page_ready()

        auto_assert(author, self.driver, case.expected)
