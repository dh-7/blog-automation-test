"""站点统计模块 UI 测试 — 数据驱动"""
import os, sys, pytest
from selenium.webdriver.common.by import By
from page.page_home import PageHome
from utils import db_query
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
from base.data_loader import UiDataLoader
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="站点统计")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


def _stat_map(driver):
    """读取统计区 {标签: 数字}（后台仪表盘 .stat-card / 关于页 .stats-grid 通用）"""
    import re
    nums = driver.find_elements(By.CSS_SELECTOR, ".stat-number")
    labels = driver.find_elements(By.CSS_SELECTOR, ".stat-label")
    result = {}
    for i in range(min(len(nums), len(labels))):
        m = re.search(r"\d+", nums[i].text)
        result[labels[i].text.strip()] = int(m.group()) if m else None
    return result


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

        # FC-ZDTJ-001: 后台仪表盘显示三项统计数据（每项为非负数字）
        if case_id == 'FC-ZDTJ-001':
            u = case.login_user or 'admin'
            p = case.login_password or 'admin123'
            login(self.driver, u, p)
            home.open_url(case.resolved_path())
            home.wait_for_page_ready()
            stats = _stat_map(self.driver)
            assert len(stats) >= 3, f"仪表盘应显示三项统计，实际={stats}"
            for label, num in stats.items():
                assert num is not None and num >= 0, f"统计项'{label}'应为非负数字，实际={num}"
            return

        # FC-ZDTJ-002: 统计数据与实际数据一致（UI 数字与 DB 逐项对比）
        if case_id == 'FC-ZDTJ-002':
            u = case.login_user or 'admin'
            p = case.login_password or 'admin123'
            login(self.driver, u, p)
            # 仪表盘统计位于后台，数据源的'/'路径仅指站点入口
            home.open_url('/admin')
            home.wait_for_page_ready()
            stats = _stat_map(self.driver)
            expected = db_query.dashboard_counts()
            for label, db_value in expected.items():
                assert label in stats, f"仪表盘缺少统计项'{label}'，实际={list(stats)}"
                assert stats[label] == db_value, \
                    f"统计项'{label}'与实际数据不一致: UI={stats[label]}, DB={db_value}"
            return

        # FC-ZDTJ-003: 未登录用户也能看到站点统计数据
        # （站点统计实际呈现于"关于"页 .stats-grid，未登录可访问）
        if case_id == 'FC-ZDTJ-003':
            from utils.config import Config as _Cfg
            base_url = _Cfg.get("env", "base_url", default="http://localhost:5173")
            # 先回到站点域，再清登录态（about:blank/data: 页无法操作 localStorage）
            self.driver.get(base_url.rstrip('/') + '/')
            home.wait_for_page_ready()
            self.driver.delete_all_cookies()
            self.driver.execute_script("localStorage.clear(); sessionStorage.clear();")
            self.driver.get(base_url.rstrip('/') + '/about')
            home.wait_for_page_ready()
            stats = _stat_map(self.driver)
            assert len(stats) >= 3, \
                f"未登录应能看到站点统计数据（关于页），实际统计项={stats}"
            for label, num in stats.items():
                assert num is not None and num >= 0, f"统计项'{label}'应为非负数字"
            return

        home.open_url(case.resolved_path())
        home.wait_for_page_ready()

        # 检查统计区域是否显示
        stats_loc = ("css selector", ".stat-card, .stats-section, .site-stats")
        try:
            home.wait_for_clickable(stats_loc, timeout=5)
        except Exception:
            pass

        auto_assert(home, self.driver, case.expected)
