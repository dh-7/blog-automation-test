"""站点统计模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_home import PageHome
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="站点统计")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("站点统计")
class TestSiteStats:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    @pytest.mark.parametrize("case_id,case", _params, ids=_ids)
    def test_site_stats(self, case_id, case):
        from case.conftest import login
        home = PageHome(self.driver)

        # FC-ZDTJ-001: 后台仪表盘需要管理员登录
        if case_id == 'FC-ZDTJ-001':
            u = case.login_user or 'admin'
            p = case.login_password or 'admin123'
            login(self.driver, u, p)
            home.open_url(case.resolved_path())
            home.wait_for_page_ready()
        else:
            home.open_url(case.resolved_path())
            home.wait_for_page_ready()

        # 检查统计区域是否显示
        stats_loc = ("css selector", ".stat-card, .stats-section, .site-stats")
        try:
            home.wait_for_clickable(stats_loc, timeout=5)
        except Exception:
            pass

        auto_assert(home, self.driver, case.expected)
