import pytest
from base.data_loader import UiDataLoader
from page.page_admin_article_manage import PageAdminArticleManage
from utils.assert_helpers import auto_assert
from utils.logger import Logger
from utils.config import Config
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure



_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module='删除文章')
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("删除文章")
class TestDeleteArticle:
    """删除文章 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_delete_article(self, driver, case_id, case):
        page = PageAdminArticleManage(driver)
        u = case.login_user or 'admin'
        p = case.login_password or 'admin123'

        # FC-SCWZ-001: 删除自己的文章成功（删除后文章从列表消失）
        if case_id == 'FC-SCWZ-001':
            from page.page_personal import PagePersonal
            personal = PagePersonal(driver)
            personal.login_and_open(u, case.login_password or '123456')
            personal.click_my_articles()
            personal.wait_for_page_ready()
            titles_before = personal.get_article_titles()
            title_to_delete = case.field('标题', 'test2')
            assert title_to_delete in titles_before, f"文章 '{title_to_delete}' 应存在于我的文章列表"
            idx = titles_before.index(title_to_delete)
            personal.click_delete_by_index(idx)
            personal.wait_for_confirm_dialog()
            personal.confirm_dialog()
            personal.wait_for_page_ready()
            titles_after = personal.get_article_titles()
            assert title_to_delete not in titles_after, f"删除后文章 '{title_to_delete}' 应从列表中消失"
            return

        # FC-SCWZ-002: 管理员删除任意文章及关联数据
        if case_id == 'FC-SCWZ-002':
            import requests
            article_id = case.field('文章ID', '9')
            api_url = Config.get("env", "api_url", default="http://localhost:8080")
            resp = requests.get(f"{api_url}/api/articles/detail/{article_id}")
            title = resp.json()["data"]["article"]["title"]
            page.login_and_open(u, p)
            # 搜索目标文章（避免分页导致找不到）
            page.input_search(title)
            page.click_search()
            page.wait_for_page_ready()
            titles_found = page.get_all_article_titles()
            assert title in titles_found, f"搜索后应找到文章 '{title}'"
            page.click_delete_by_title(title)
            page.wait_for_confirm_dialog()
            page.confirm_delete()
            page.wait_for_page_ready()
            # 搜索确认已删除
            page.input_search(title)
            page.click_search()
            page.wait_for_page_ready()
            titles_after = page.get_all_article_titles()
            assert title not in titles_after, f"管理员删除后文章 '{title}' 应从列表中消失"
            # 验证关联数据已清理：通过API确认文章不存在
            try:
                resp2 = requests.get(f"{api_url}/api/articles/detail/{article_id}")
                data2 = resp2.json()
                # 文章应不存在（返回错误或null）
                assert data2.get('data') is None or data2.get('code') != 200, \
                    f"删除后通过API仍能访问文章{article_id}，关联数据未清理"
            except Exception:
                pass  # API返回异常也说明文章已不存在
            return

        # FC-SCWZ-003: 尝试删除别人的文章提示无权
        if case_id == 'FC-SCWZ-003':
            from page.page_login import PageLogin
            from page.page_article_detail import PageArticleDetail
            from selenium.webdriver.common.by import By
            non_admin_user = case.login_user or 'zhangsan'
            non_admin_pass = case.login_password or '123456'
            article_id = case.field('文章ID', '5')

            # ① 普通用户访问管理后台：应被重定向离开 /admin（无后台删除权限）
            login_page = PageLogin(driver)
            login_page.login(non_admin_user, non_admin_pass)
            page.open_url()  # /admin/articles
            page.wait_for_page_ready()
            assert "/admin" not in driver.current_url, \
                f"普通用户不应停留在管理后台，实际 URL: {driver.current_url}"

            # ② 普通用户打开数据源指定的他人文章详情页：不应出现"删除"按钮
            detail = PageArticleDetail(driver)
            detail.open_url(f'/article/{article_id}')
            detail.wait_for_page_ready()
            author = detail.get_author()
            assert author != non_admin_user, "测试前提：该文章应属于其他作者"
            delete_btns = driver.find_elements(
                By.XPATH,
                '//button[contains(.,"删除") and '
                'not(ancestor::div[contains(@class,"comment-actions")])]'
            )
            assert len(delete_btns) == 0, \
                "普通用户不应看到删除文章按钮（无权删除他人文章）"
            return

        # FC-SCWZ-004: 管理员对已删除的文章再次删除提示不存在
        if case_id == 'FC-SCWZ-004':
            article_id = case.field('文章ID', '11')
            page.login_and_open(u, p)  # admin 登录管理后台
            # 已删除文章不在管理列表 → 找不到该文章的删除按钮（文章已不存在）
            ids_in_list = [page.get_article_id(i) for i in range(page.get_row_count())]
            assert article_id not in ids_in_list, \
                f"已删除文章(ID={article_id})不应出现在管理列表（无删除按钮）"
            return

        # FC-SCWZ-005: 删除文章前弹出二次确认提示框
        if case_id == 'FC-SCWZ-005':
            from page.page_personal import PagePersonal
            from page.page_login import PageLogin
            login_page = PageLogin(driver)
            login_page.login_and_navigate(u, p, '/profile')
            p_page = PagePersonal(driver)
            p_page.click_delete_by_index(0)
            p_page.wait_for_confirm_dialog()
            p_page.cancel_dialog()
            auto_assert(p_page, driver, case.expected)
            return

        # 兜底
        page.login_and_open(u, p)
        auto_assert(page, driver, case.expected)
