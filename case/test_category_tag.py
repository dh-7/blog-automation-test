"""分类与标签模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_home import PageHome
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="分类与标签")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("分类与标签")
class TestCategoryTag:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    @pytest.mark.parametrize("case_id,case", _params, ids=_ids)
    def test_category_tag(self, case_id, case):
        home = PageHome(self.driver)
        home.open_url(case.resolved_path())
        home.wait_for_page_ready()

        category = case.field("选择分类")
        tag = case.field("选择标签")

        if category:
            home.click_category_by_name(category)
            home.wait_for_loading_finish()

        if tag:
            # Tags are typically clickable in the sidebar
            tag_loc = ("xpath", f"//span[contains(@class,'tag') and text()='{tag}']")
            try:
                home.click(tag_loc)
                home.wait_for_loading_finish()
            except Exception:
                pass

        auto_assert(home, self.driver, case.expected)
