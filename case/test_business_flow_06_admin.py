"""UI 业务流程测试 — 管理员管理用户/文章/评论流程（YW-GLY / YW-GLWZ 系列）（自 test_business_flow_ui.py 拆分）"""
import allure
import pytest
from page.page_admin_article_manage import PageAdminArticleManage
from page.page_admin_comment_manage import PageAdminCommentManage
from page.page_admin_dashboard import PageAdminDashboard
from page.page_admin_user_manage import PageAdminUserManage
from page.page_login import PageLogin
from utils import db_query
from utils.assert_helpers import assert_url
from case.flow_common import FlowBase, login, _c, _publish_disposable


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("管理员管理用户")
class TestAdminManageUserFlow(FlowBase):

    def test_admin_modify_user_flow(self):
        """YW-GLY-001: 管理员修改用户信息"""
        c = _c("YW-GLY-001")
        user_page = PageAdminUserManage(self.driver)
        user_page.login_and_open(c.login_user, c.login_password)
        uid = user_page._extract_id(c.field("目标用户ID", "2（zhangsan）"))
        new_nick = c.field("新昵称")
        new_email = c.field("新邮箱")
        orig_nick, orig_email = user_page.edit_user_by_id(uid, new_nick, new_email)
        try:
            assert user_page.get_nickname_by_id(uid) == new_nick,                 f"昵称应更新为'{new_nick}'"
            assert user_page.get_email_by_id(uid) == new_email,                 f"邮箱应更新为'{new_email}'"
        finally:
            # 恢复原昵称/邮箱，避免污染后续用例（昵称被通知/评论断言依赖）
            user_page.login_and_open(c.login_user, c.login_password)
            user_page.restore_user_by_id(uid, orig_nick, orig_email)

    def test_admin_change_role_flow(self):
        """YW-GLY-002: 管理员修改用户角色"""
        c = _c("YW-GLY-002")
        pytest.skip("前端未实现角色编辑功能（UserManage.vue无角色编辑列）")

    def test_admin_reset_password_flow(self):
        """YW-GLY-003: 管理员重置密码"""
        c = _c("YW-GLY-003")
        new_pwd = "newpass456"
        user_page = PageAdminUserManage(self.driver)
        user_page.login_and_open(c.login_user, c.login_password)
        target_uid = user_page._extract_id(c.field("目标用户ID", "2（zhangsan）"))
        target_user = user_page._extract_username(c.field("目标用户ID", "2（zhangsan）"))
        # 重置密码
        user_page.reset_password_by_id(target_uid, new_pwd)
        # 验证新密码能登录
        if target_user:
            login_page = PageLogin(self.driver)
            login_page.login_and_navigate(target_user, new_pwd, "/")
            assert "/login" not in self.driver.current_url, f"新密码应能登录 {target_user}"
        # 恢复原密码
        user_page.login_and_open(c.login_user, c.login_password)
        user_page.reset_password_by_id(target_uid, "123456")

    def test_normal_user_no_admin_flow(self):
        """YW-GLY-004: 普通用户无后台权限"""
        c = _c("YW-GLY-004")
        # 用 Excel 中配置的"登录用户"登录后访问后台
        login(self.driver, c.login_user, c.login_password)
        dashboard = PageAdminDashboard(self.driver)
        dashboard.open_url()
        dashboard.wait_for_page_ready()
        assert "/admin" not in self.driver.current_url or \
               "无权" in self.driver.page_source

    def test_not_login_admin_redirect_flow(self):
        """YW-GLY-005: 未登录访问后台"""
        c = _c("YW-GLY-005")
        self.driver.delete_all_cookies()
        dashboard = PageAdminDashboard(self.driver)
        dashboard.open_url()
        dashboard.wait_for_page_ready()
        assert_url(dashboard, self.driver, "/login")


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("管理员管理文章与评论")
class TestAdminManageArticleCommentFlow(FlowBase):

    def test_admin_search_delete_article_flow(self):
        """YW-GLWZ-001: 搜索删除文章"""
        c = _c("YW-GLWZ-001")
        # 自造一次性文章作为删除目标（避免误删种子文章，污染后续用例）
        target_title = "一次性-GLWZ001-待删除文章"
        target_aid = _publish_disposable(self.driver, c.login_user, c.login_password, target_title)
        article_page = PageAdminArticleManage(self.driver)
        article_page.login_and_open(c.login_user, c.login_password)
        article_page.input_search(target_title)
        article_page.click_search()
        article_page.wait_for_loading_finish()
        assert article_page.get_row_count() > 0, f"后台应能搜索到'{target_title}'"
        article_page.click_delete_by_index(0)
        article_page.wait_for_confirm_dialog()
        article_page.confirm_delete()
        article_page.wait_for_loading_finish()
        import time as _t
        deleted = False
        for _ in range(10):
            if db_query.article_field(target_aid, "deleted") == 1:
                deleted = True
                break
            _t.sleep(0.5)
        assert deleted, "删除后文章应软删除"
        bad = db_query.article_cascade_cleaned(target_aid)
        assert not bad, f"关联数据未清理: {bad}"

    def test_admin_delete_comment_flow(self):
        """YW-GLWZ-002: 删除评论"""
        c = _c("YW-GLWZ-002")
        comment_page = PageAdminCommentManage(self.driver)
        comment_page.login_and_open(c.login_user, c.login_password)
        total_before = db_query.comment_count()
        assert total_before > 0, "后台评论列表应有数据"
        comment_page.click_delete_by_index(0)
        comment_page.wait_for_confirm_dialog()
        comment_page.confirm_delete()
        comment_page.wait_for_loading_finish()
        total_after = db_query.comment_count()
        assert total_after == total_before - 1,             f"删除评论后总数应-1: {total_before}->{total_after}"

    def test_admin_stats_consistent_flow(self):
        """YW-GLWZ-003: 统计数据一致"""
        c = _c("YW-GLWZ-003")
        dashboard = PageAdminDashboard(self.driver)
        dashboard.login_and_open(c.login_user, c.login_password)
        import re
        stats = dashboard.get_stat_numbers()
        assert len(stats) >= 3, f"仪表盘应显示三项统计，实际={stats}"
        ui_vals = sorted(int(re.search(r"\d+", s).group()) for s in stats)
        expected = db_query.dashboard_counts()
        db_vals = sorted(expected.values())
        assert ui_vals == db_vals,             f"统计数据与实际不一致: UI={ui_vals}, DB={db_vals}"

    def test_normal_user_no_article_manage_flow(self):
        """YW-GLWZ-004: 普通用户无文章管理权限"""
        c = _c("YW-GLWZ-004")
        login(self.driver, c.login_user, c.login_password)
        dashboard = PageAdminDashboard(self.driver)
        dashboard.open_url()
        dashboard.wait_for_page_ready()
        assert "/admin" not in self.driver.current_url or \
               "无权" in self.driver.page_source

    def test_normal_user_no_comment_manage_flow(self):
        """YW-GLWZ-005: 普通用户无评论管理权限"""
        c = _c("YW-GLWZ-005")
        login(self.driver, c.login_user, c.login_password)
        dashboard = PageAdminDashboard(self.driver)
        dashboard.open_url()
        dashboard.wait_for_page_ready()
        assert "/admin" not in self.driver.current_url or \
               "无权" in self.driver.page_source

    def test_not_login_admin_manage_redirect_flow(self):
        """YW-GLWZ-006: 未登录访问后台管理"""
        c = _c("YW-GLWZ-006")
        self.driver.delete_all_cookies()
        dashboard = PageAdminDashboard(self.driver)
        dashboard.open_url()
        dashboard.wait_for_page_ready()
        assert_url(dashboard, self.driver, "/login")
