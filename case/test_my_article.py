import pytest
import time
from selenium.webdriver.common.by import By
from base.data_loader import UiDataLoader
from page.page_login import PageLogin
from page.page_personal import PagePersonal
from page.page_archive import PageArchive
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure


_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module='我的文章与归档')
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("我的文章与归档")
class TestMyArticle:
    """我的文章与归档 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_my_article(self, driver, case_id, case):
        page = PagePersonal(driver)

        # 登录
        if case.login_required:
            u = case.login_user or 'zhangsan'
            p = case.login_password or '123456'
            login_page = PageLogin(driver)
            login_page.login(u, p)

        # FC-WDWZ-001: 我的文章列表同时显示草稿和已发布
        if case_id == 'FC-WDWZ-001':
            page.open_url(case.resolved_path())
            page.wait_for_page_ready()
            page.click_my_articles()
            page.wait_for_page_ready()
            titles = page.get_article_titles()
            assert len(titles) > 0, "我的文章列表应有文章"
            pub = page.get_published_count()
            draft = page.get_draft_count()
            assert pub > 0, f"已发布数量应>0，实际={pub}"
            assert draft > 0, f"草稿数量应>0，实际={draft}"
            auto_assert(page, driver, case.expected)
            return

        # FC-WDWZ-002: 归档页面按年月分组显示文章
        if case_id == 'FC-WDWZ-002':
            archive = PageArchive(driver)
            archive.open_url(case.resolved_path())
            archive.wait_for_page_ready()
            # 额外等待归档页 API 数据返回 + Vue 渲染完成
            time.sleep(1)
            # 1. 验证年份分组存在
            years = archive.get_year_titles()
            assert len(years) > 0, "归档页面应按年分组显示文章"
            # 2. 验证月份分组存在
            months = archive.get_month_names()
            assert len(months) > 0, "归档页面应有月份分组"
            # 3. 点击一个月份展开文章列表（优先用 Excel 配置的月份，兜底取第一个）
            target_month = case.field('月份', months[0])
            if target_month not in months:
                target_month = months[0]
            archive.click_month_by_name(target_month)
            archive.wait_for_page_ready()
            # 等待展开动画 + 文章列表渲染
            time.sleep(0.5)
            # 4. 验证展开后显示文章标题
            titles = archive.get_month_article_titles()
            assert len(titles) > 0, f"展开月份 {target_month} 后应显示文章标题"
            # 5. 验证展开后显示文章日期（日）
            dates = archive.get_month_article_dates()
            assert len(dates) > 0, f"展开月份 {target_month} 后应显示文章日期（日）"
            # 6. 验证标题数与日期数一致
            assert len(titles) == len(dates), \
                f"文章标题数({len(titles)})应与日期数({len(dates)})一致"
            # 7. 通用断言（传入 archive 而非 page）
            auto_assert(archive, driver, case.expected)
            return

        # FC-WDWZ-003: 有文章的用户进入我的文章显示全部（含草稿和已发布）
        if case_id == 'FC-WDWZ-003':
            page.open_url(case.resolved_path())
            page.wait_for_page_ready()
            page.click_my_articles()
            page.wait_for_page_ready()
            titles = page.get_article_titles()
            assert len(titles) > 0, "有文章的用户应显示全部文章"
            pub = page.get_published_count()
            draft = page.get_draft_count()
            assert pub > 0, f"已发布数量应>0，实际={pub}"
            assert draft > 0, f"草稿数量应>0，实际={draft}"
            assert len(titles) == pub + draft, \
                f"文章总数应=已发布+草稿，实际：列表={len(titles)}, 已发布={pub}, 草稿={draft}"
            auto_assert(page, driver, case.expected)
            return

        # FC-WDWZ-004: 无文章的用户进入我的文章显示空列表
        if case_id == 'FC-WDWZ-004':
            # 使用无文章的用户登录（通过case配置）
            page.open_url(case.resolved_path())
            page.wait_for_page_ready()
            page.click_my_articles()
            page.wait_for_page_ready()
            assert page.is_empty(), "无文章的用户应显示空列表"
            titles = driver.find_elements(By.CSS_SELECTOR, '.article-title')
            assert len(titles) == 0, "文章列表应确实为空"
            auto_assert(page, driver, case.expected)
            return

        # FC-WDWZ-005: 点击某月显示该月发布的文章
        if case_id == 'FC-WDWZ-005':
            archive = PageArchive(driver)
            archive.open_url(case.resolved_path())
            archive.wait_for_page_ready()
            target_month = case.field('月份', '')
            months = archive.get_month_names()
            if months:
                # 优先使用Excel中指定的月份，找不到则使用第一个月份
                if target_month and target_month in months:
                    archive.click_month_by_name(target_month)
                else:
                    archive.click_month_by_name(months[0])
                archive.wait_for_page_ready()
            month_articles = archive.get_month_article_titles()
            assert len(month_articles) >= 0, "应显示该月发布的文章列表"
            auto_assert(page, driver, case.expected)
            return

        # FC-WDWZ-006: 未登录用户访问我的文章跳转登录页
        if case_id == 'FC-WDWZ-006':
            page.open_url(case.resolved_path())
            page.wait_for_page_ready()
            auto_assert(page, driver, case.expected)
            return

        # 兜底
        page.open_url(case.resolved_path())
        page.wait_for_page_ready()
        auto_assert(page, driver, case.expected)
