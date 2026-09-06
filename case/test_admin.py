import re
import pytest
from selenium.webdriver.common.by import By
from base.data_loader import UiDataLoader
from page.page_admin_dashboard import PageAdminDashboard
from page.page_admin_article_manage import PageAdminArticleManage
from page.page_admin_comment_manage import PageAdminCommentManage
from page.page_admin_user_manage import PageAdminUserManage
from page.page_login import PageLogin
from utils import db_query
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure


_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module='后台管理')
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


def _extract_id(raw):
    """从 Excel 用户ID 值中提取数字ID，如 '2（zhangsan）' -> 2"""
    m = re.match(r'\d+', str(raw))
    return int(m.group(0)) if m else None


def _extract_username(raw):
    """从 Excel 用户ID 值中提取用户名，如 '2（zhangsan）' -> 'zhangsan'"""
    m = re.search(r'[\uff08(](\w+)[\uff09)]', str(raw))
    return m.group(1) if m else None


@allure.epic("UI自动化测试")
@allure.feature("后台管理")
class TestAdmin:
    """后台管理 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_admin(self, driver, case_id, case):
        url = case.resolved_path()
        u = case.login_user or 'admin'
        p = case.login_password or 'admin123'

        # ---- Group 1: 页面显示测试 (001-004) ----

        if case_id in ('FC-HTGL-001', 'FC-HTGL-002', 'FC-HTGL-003', 'FC-HTGL-004'):
            page_map = {
                'FC-HTGL-001': PageAdminDashboard,
                'FC-HTGL-002': PageAdminUserManage,
                'FC-HTGL-003': PageAdminArticleManage,
                'FC-HTGL-004': PageAdminCommentManage,
            }
            page = page_map[case_id](driver)
            page.login_and_open(u, p, url)
            # FC-HTGL-001: 仪表盘应显示三项统计且均为非负数字
            if case_id == 'FC-HTGL-001':
                nums = [e.text for e in driver.find_elements(By.CSS_SELECTOR, ".stat-number")]
                labels = [e.text for e in driver.find_elements(By.CSS_SELECTOR, ".stat-label")]
                assert len(nums) >= 3, f"仪表盘应显示三项统计，实际={len(nums)}项"
                import re
                for label, num in zip(labels, nums):
                    assert re.search(r"\d+", num), f"统计项'{label}'应为数字，实际='{num}'"
                assert any("文章" in l for l in labels), "统计应包含文章数"
                assert any("用户" in l for l in labels), "统计应包含用户数"
                assert any("评论" in l for l in labels), "统计应包含评论数"
                return
            # FC-HTGL-002: 用户管理表格验证（el-table中的列标题）
            if case_id == 'FC-HTGL-002':
                from selenium.webdriver.support.wait import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, '.el-table'))
                )
                table = driver.find_elements(By.CSS_SELECTOR, '.el-table')
                assert table, "用户管理页面应显示表格"
                # el-table 的列头在 .el-table__header-wrapper th 中
                headers = driver.find_elements(By.CSS_SELECTOR, '.el-table__header-wrapper th .cell')
                header_texts = [h.text.strip() for h in headers]
                for keyword in ['ID', '用户名', '昵称', '邮箱', '注册时间']:
                    assert any(keyword in ht for ht in header_texts), \
                        f"表格应包含'{keyword}'列，实际列头={header_texts}"
                # 验证表格有数据行
                rows = driver.find_elements(By.CSS_SELECTOR, '.el-table__body-wrapper tr')
                assert len(rows) > 0, "用户表格应至少有一行数据"
                return
            # FC-HTGL-004: 评论管理表格验证（el-table中的列标题）
            if case_id == 'FC-HTGL-004':
                from selenium.webdriver.support.wait import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, '.el-table'))
                )
                table = driver.find_elements(By.CSS_SELECTOR, '.el-table')
                assert table, "评论管理页面应显示表格"
                headers = driver.find_elements(By.CSS_SELECTOR, '.el-table__header-wrapper th .cell')
                header_texts = [h.text.strip() for h in headers]
                for keyword in ['评论', '文章', '评论用户', '时间']:
                    assert any(keyword in ht for ht in header_texts), \
                        f"表格应包含'{keyword}'相关列，实际列头={header_texts}"
                # 表格行随 API 异步渲染，轮询等待
                from selenium.webdriver.support.ui import WebDriverWait
                try:
                    WebDriverWait(driver, 8).until(
                        lambda d: len(d.find_elements(
                            By.CSS_SELECTOR, '.el-table__body-wrapper tr')) > 0)
                except Exception:
                    pass
                rows = driver.find_elements(By.CSS_SELECTOR, '.el-table__body-wrapper tr')
                assert len(rows) > 0, "评论表格应至少有一行数据"
                return
            # FC-HTGL-003: 后台文章列表应包含草稿文章（与 DB 草稿清单交叉验证）
            if case_id == 'FC-HTGL-003':
                drafts = db_query.draft_titles()
                assert drafts, "前置数据缺失：DB 中无草稿文章，无法验证'含草稿'"
                found_any = page.search_article(drafts[0])
                assert found_any, f"后台文章列表应包含草稿文章'{drafts[0]}'（含草稿）"
                return
            auto_assert(page, driver, case.expected)
            return

        # ---- FC-HTGL-005: 管理员修改用户昵称和邮箱成功 ----

        if case_id == 'FC-HTGL-005':
            page = PageAdminUserManage(driver)
            page.login_and_open(u, p, url)
            uid = _extract_id(case.field('用户ID'))
            new_nick = case.field('新昵称')
            new_email = case.field('新邮箱')
            orig_nick, orig_email = page.edit_user_by_id(uid, new_nick, new_email)
            try:
                assert page.get_nickname_by_id(uid) == new_nick
                assert page.get_email_by_id(uid) == new_email
            finally:
                page.login_and_open(u, p, url)
                page.restore_user_by_id(uid, orig_nick, orig_email)
            return

        # ---- FC-HTGL-006: 管理员修改用户角色成功 ----

        if case_id == 'FC-HTGL-006':
            pytest.skip('前端未实现角色编辑功能')

        # ---- FC-HTGL-007: 管理员重置用户密码成功 ----

        if case_id == 'FC-HTGL-007':
            page = PageAdminUserManage(driver)
            page.login_and_open(u, p, url)
            uid = _extract_id(case.field('用户ID'))
            target_user = _extract_username(case.field('用户ID'))
            page.reset_password_by_id(uid, 'testpass123')
            try:
                if target_user:
                    login_page = PageLogin(driver)
                    # 旧密码应失效
                    login_page.open_url()
                    login_page.input_username(target_user)
                    login_page.input_password('123456')
                    login_page.click_login_button()
                    login_page.wait_for_page_ready()
                    assert '/login' in driver.current_url,                         "重置密码后旧密码不应能登录成功"
                    # 新密码应可登录
                    login_page.login_and_navigate(target_user, 'testpass123', url)
            finally:
                page.login_and_open(u, p, url)
                page.reset_password_by_id(uid, '123456')
            return

        # ---- FC-HTGL-008: 管理员删除任意文章及关联数据 ----

        if case_id == 'FC-HTGL-008':
            page = PageAdminArticleManage(driver)
            page.login_and_open(u, p, url)
            target_title = case.field('标题')
            if target_title:
                # 先搜索确认文章存在（避免分页导致找不到）
                found = page.search_article(target_title)
                assert found, f"文章'{target_title}'应存在于列表中"
                page.click_delete_by_title(target_title)
            else:
                page.click_delete_by_index(0)
            page.wait_for_confirm_dialog()
            page.confirm_delete()
            page.wait_for_loading_finish()
            # 清空搜索后验证文章已消失
            if target_title:
                page.clear_search_and_refresh()
            titles_after = page.get_all_article_titles()
            assert target_title not in titles_after, f"文章'{target_title}'应已从列表消失"
            # DB 回查：关联评论/收藏/阅读历史一并清理
            aid = db_query.scalar("SELECT id FROM article WHERE title=%s", (target_title,))
            if aid:
                assert db_query.article_field(aid, 'deleted') == 1, "文章应已软删除"
                bad = db_query.article_cascade_cleaned(aid)
                assert not bad, f"关联数据未清理: {bad}"
            return

        # ---- FC-HTGL-009: 管理员删除任意评论成功 ----

        if case_id == 'FC-HTGL-009':
            page = PageAdminCommentManage(driver)
            page.login_and_open(u, p, url)
            count_before = page.get_row_count()
            assert count_before > 0, "评论列表应有数据"
            page.delete_first_row()
            page.wait_for_page_ready()
            count_after = page.get_row_count()
            assert count_after < count_before, \
                f"删除后评论应减少: 删除前{count_before}, 删除后{count_after}"
            return

        # ---- FC-HTGL-010: 管理员可访问后台所有功能 ----

        if case_id == 'FC-HTGL-010':
            page = PageAdminDashboard(driver)
            page.login_and_open(u, p, url)
            from selenium.webdriver.support.ui import WebDriverWait
            def _url_has(part):
                return lambda d: part in d.current_url
            page.click_manage_articles()       # 跳转到 /admin/articles
            assert WebDriverWait(driver, 8).until(_url_has("/admin/articles")),                 f"管理员应可访问文章管理，实际URL={driver.current_url}"
            page.open_url()                    # 返回 /admin
            page.click_manage_users()          # 跳转到 /admin/users
            assert WebDriverWait(driver, 8).until(_url_has("/admin/users")),                 f"管理员应可访问用户管理，实际URL={driver.current_url}"
            page.open_url()                    # 返回 /admin
            page.click_manage_comments()       # 跳转到 /admin/comments
            assert WebDriverWait(driver, 8).until(_url_has("/admin/comments")),                 f"管理员应可访问评论管理，实际URL={driver.current_url}"
            page.open_url()                    # 返回 /admin
            page.click_menu_dashboard()        # 回到仪表盘
            assert '/admin' in driver.current_url,                 f"应回到仪表盘，实际URL={driver.current_url}"
            return

        # ---- FC-HTGL-011/012: 权限测试 ----

        if case_id in ('FC-HTGL-011', 'FC-HTGL-012'):
            if case_id == 'FC-HTGL-011':
                target_u = case.login_user
                target_p = case.login_password
                page = PageAdminDashboard(driver)
                page.login_and_open(target_u, target_p, url)
                # 普通用户访问后台应被重定向到登录页或首页
                current_url = driver.current_url
                # 无条件断言：要么被重定向离开后台，要么页面明确提示无权限
                assert '/admin' not in current_url or '无权' in driver.page_source,                     f"普通用户应无法访问后台，实际URL={current_url}"
                return
            else:
                page = PageAdminDashboard(driver)
                page.open_url(url)
                auto_assert(PageLogin(driver), driver, case.expected)
            return

        # 兜底: 通用断言
        auto_assert(PageAdminDashboard(driver), driver, case.expected)
