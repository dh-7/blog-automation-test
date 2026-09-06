"""分类与标签模块 UI 测试 — 数据驱动"""
import os, sys, re, time, pytest
from selenium.webdriver.common.by import By
from page.page_category import PageCategory
from utils import db_query
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
from base.data_loader import UiDataLoader
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
        home = PageCategory(self.driver)
        home.open_url(case.resolved_path())
        home.wait_for_page_ready()

        # FC-FQBQ-001: 分类列表显示名称和文章数量（名称集合与 DB 一致，计数与 DB 同口径）
        if case_id == 'FC-FQBQ-001':
            shown = home.get_category_names()
            assert shown, "应显示分类列表"
            assert set(shown) == set(db_query.category_names()), \
                f"分类名称与DB不一致: UI={shown}, DB={db_query.category_names()}"
            # 每个分类显示文章数量（数字）
            items = self.driver.find_elements(By.CSS_SELECTOR, ".category-item")
            for it in items:
                m = re.search(r"\d+", it.text)
                assert m, f"分类'{it.text}'应显示文章数量"
            # 计数与 DB 同口径校验（已发布未删除）
            expected = db_query.category_article_counts()
            for it in items:
                import re as r2
                name = it.find_element(By.CSS_SELECTOR, ".category-name").text.strip()
                m2 = r2.search(r"\d+", it.text)
                ui_count = int(m2.group()) if m2 else None
                assert ui_count == expected.get(name), \
                    f"分类'{name}'文章数与DB不一致: UI={ui_count}, DB={expected.get(name)}"
            return

        # FC-FQBQ-002: 标签列表显示所有标签名称（与 DB 集合一致）
        if case_id == 'FC-FQBQ-002':
            shown = home.get_tag_names()
            assert shown, "应显示标签列表"
            assert set(shown) == set(db_query.tag_names()), \
                f"标签名称与DB不一致: UI={shown}, DB={db_query.tag_names()}"
            return

        category = case.field("选择分类")
        tag = case.field("选择标签")

        # FC-FQBQ-003: 点击某个分类只显示该分类文章（与 DB 交叉验证）
        if case_id == 'FC-FQBQ-003':
            home.click_category_by_name(category)
            home.wait_for_loading_finish()
            time.sleep(0.6)  # 等待列表重渲染，避免 stale element
            shown = home.get_all_article_titles()
            assert shown, f"分类'{category}'下应有文章"
            allowed = set(db_query.article_titles_by_category(category))
            for t in shown:
                assert t in allowed, f"分类筛选结果'{t}'不属于分类'{category}'"
            return

        # FC-FQBQ-004: 点击某个标签只显示该标签文章（与 DB 交叉验证）
        if case_id == 'FC-FQBQ-004':
            home.click_tag_by_name(tag)
            home.wait_for_loading_finish()
            shown = home.get_all_article_titles()
            assert shown, f"标签'{tag}'下应有文章"
            allowed = set(db_query.article_titles_by_tag(tag))
            for t in shown:
                assert t in allowed, f"标签筛选结果'{t}'未携带标签'{tag}'"
            return

        auto_assert(home, self.driver, case.expected)
