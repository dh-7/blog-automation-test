import pytest
from selenium.webdriver.common.by import By
from utils.excel_loader import load_ui_cases
from page.page_home import PageHome
from page.page_category import PageCategory
from utils import db_query
from utils.paths import UI_DATASOURCE as DATASOURCE
from utils.assert_helpers import auto_assert, assert_url
import allure


_params, _ids = load_ui_cases(module='文章列表')


@allure.epic("UI自动化测试")
@allure.feature("文章列表")
class TestArticleList:
    """文章列表 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_article_list(self, driver, case_id, case):
        page = PageHome(driver)
        page.open_url(case.resolved_path())
        page.wait_for_page_ready()

        # FC-WZLB-001: 文章列表每条显示完整信息（标题、摘要、作者、分类、标签、发布时间、浏览量）
        if case_id == 'FC-WZLB-001':
            cards = page.find_all(page.article_cards)
            assert len(cards) > 0, "首页应显示文章列表"
            for i, card in enumerate(cards[:5]):
                assert card.find_elements(By.CSS_SELECTOR, ".article-title"), f"卡片{i}缺标题"
                assert card.find_elements(By.CSS_SELECTOR, ".article-summary"), f"卡片{i}缺摘要"
                assert card.find_elements(By.CSS_SELECTOR, ".article-meta"), f"卡片{i}缺元信息"
            return

        # FC-WZLB-002: 分页组件正确显示（页码、总条数、每页条数）
        if case_id == 'FC-WZLB-002':
            assert page.is_displayed(page.pagination), "分页组件应正确显示"
            numbers = page.find_all(page.page_numbers)
            assert len(numbers) >= 1, "分页组件应显示页码"
            return

        # FC-WZLB-003: 列表只显示已发布文章，草稿不显示（与 DB 草稿清单交叉验证）
        if case_id == 'FC-WZLB-003':
            titles = page.get_all_article_titles()
            assert len(titles) > 0, "列表应显示已发布文章"
            drafts = db_query.draft_titles()
            assert drafts, "前置数据缺失：DB 中无草稿文章，无法验证草稿被排除"
            for d in drafts:
                assert d not in titles, f"草稿文章'{d}'不应出现在公开文章列表"
            return

        # FC-WZLB-004: 打开文章列表默认显示第一页10条
        if case_id == 'FC-WZLB-004':
            count = page.get_article_count()
            # 如果总文章数>=10，当前页应恰好10条；否则等于实际数
            assert count > 0, "首页应显示文章"
            assert count <= 10, f"默认每页应显示不超过10条文章，实际={count}"
            auto_assert(page, driver, case.expected)
            return

        # FC-WZLB-005: 点击第2页显示第2页文章（与第1页不同）
        if case_id == 'FC-WZLB-005':
            page1_titles = page.get_all_article_titles()
            page.click_page_number(2)
            page.wait_for_page_ready()
            page2_titles = page.get_all_article_titles()
            assert page1_titles != page2_titles, "第2页文章应与第1页不同"
            auto_assert(page, driver, case.expected)
            return

        # FC-WZLB-006: 输入关键词搜索文章
        if case_id == 'FC-WZLB-006':
            keyword = case.field('关键词', 'Java')
            page.search(keyword)
            page.wait_for_page_ready()
            # 搜索结果应包含相关文章（后端可能搜索标题+内容+摘要）
            titles = page.get_all_article_titles()
            assert len(titles) > 0, f"搜索'{keyword}'应有结果"
            # 验证搜索结果相关性：至少一篇文章标题或内容包含关键词
            page_texts = page.get_all_article_texts()
            found = False
            for text in page_texts:
                if keyword.lower() in text.lower():
                    found = True
                    break
            assert found, f"搜索'{keyword}'的结果中应至少有一篇文章包含该关键词"
            auto_assert(page, driver, case.expected)
            return

        # FC-WZLB-007: 选择分类筛选文章（结果必须都属于该分类，与 DB 交叉验证）
        if case_id == 'FC-WZLB-007':
            category = case.field('选择分类', '技术')
            cat_page = PageCategory(driver)
            cat_page.open_url(case.resolved_path())
            cat_page.wait_for_page_ready()
            cat_page.click_category_by_name(category)
            cat_page.wait_for_page_ready()
            shown = cat_page.get_all_article_titles()
            assert shown, f"分类'{category}'下应有文章"
            allowed = set(db_query.article_titles_by_category(category))
            for t in shown:
                assert t in allowed, \
                    f"分类筛选结果'{t}'不属于分类'{category}'（DB可显示={len(allowed)}篇）"
            return

        # FC-WZLB-008: 选择标签筛选文章（结果必须都带有该标签，与 DB 交叉验证）
        if case_id == 'FC-WZLB-008':
            tag = case.field('选择标签', 'Java')
            cat_page = PageCategory(driver)
            cat_page.open_url(case.resolved_path())
            cat_page.wait_for_page_ready()
            cat_page.click_tag_by_name(tag)
            cat_page.wait_for_page_ready()
            shown = cat_page.get_all_article_titles()
            assert shown, f"标签'{tag}'下应有文章"
            allowed = set(db_query.article_titles_by_tag(tag))
            for t in shown:
                assert t in allowed, \
                    f"标签筛选结果'{t}'未携带标签'{tag}'（DB可显示={len(allowed)}篇）"
            return

        # FC-WZLB-009: 同时选择分类并输入关键词筛选（分类严格约束 + 关键词至少命中一篇）
        if case_id == 'FC-WZLB-009':
            category = case.field('选择分类', '技术')
            keyword = case.field('关键词', 'Spring')
            cat_page = PageCategory(driver)
            cat_page.open_url(case.resolved_path())
            cat_page.wait_for_page_ready()
            cat_page.click_category_by_name(category)
            cat_page.wait_for_page_ready()
            # 输入关键词（分类页搜索框，与首页搜索框同 placeholder）
            from selenium.webdriver.common.keys import Keys
            box = driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='搜索']")
            assert box, "分类页应有搜索输入框用于组合筛选"
            box[0].send_keys(keyword)
            box[0].send_keys(Keys.ENTER)
            cat_page.wait_for_page_ready()
            shown = cat_page.get_all_article_titles()
            assert shown, f"分类'{category}'+关键词'{keyword}'应有筛选结果"
            allowed = set(db_query.article_titles_by_category(category))
            for t in shown:
                assert t in allowed, \
                    f"组合筛选结果'{t}'不属于分类'{category}'"
            assert any(keyword.lower() in t.lower() for t in shown), \
                f"组合筛选结果中应至少一篇标题含'{keyword}'，实际={shown}"

        # FC-WZLB-010: 搜索不存在的关键词显示空列表
        if case_id == 'FC-WZLB-010':
            keyword = case.field('关键词', 'xyznotexist999')
            page.search(keyword)
            page.wait_for_page_ready()
            assert page.is_empty(), "搜索不存在的关键词应显示空列表"
            auto_assert(page, driver, case.expected)
            return

        # 兜底
        auto_assert(page, driver, case.expected)
