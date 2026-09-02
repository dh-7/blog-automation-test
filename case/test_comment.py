"""评论模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_home import PageHome
from page.page_login import PageLogin
from page.page_article_detail import PageArticleDetail
from page.page_comment import PageComment
from utils.assert_helpers import auto_assert, assert_url, assert_toast
from utils.config import Config
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="评论")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("评论功能")
class TestComment:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def _login_and_open_article(self, user, pwd, case):
        login_page = PageLogin(self.driver)
        login_page.login(user, pwd)
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        if home.get_article_count() > 0:
            home.click_article_by_index(0)
            home.wait_for_page_ready()

    @pytest.mark.parametrize("case_id,case", _params, ids=_ids)
    def test_comment(self, case_id, case):
        # 字段显式存在（含"（空）"哨兵）即视为需提交评论；
        # 空内容（如 FC-PL-008）也要点击发表以触发前端校验提示
        has_comment_field = ("评论内容" in case.fields) or ("用户A的评论内容" in case.fields)
        comment_text = case.field("评论内容") or case.field("用户A的评论内容")
        reply_text = case.field("回复内容") or case.field("用户A的回复内容")

        # 未登录访问（FC-PL-009）— 触发动作 = 校验评论交互入口
        # 前端对未登录用户不渲染评论表单（v-if="isLoggedIn"），而是显示
        # "登录 后发表评论"提示条（.login-hint），即评论场景的"提示需要登录"。
        if not case.login_required and "未登录" in case.title:
            home = PageHome(self.driver)
            home.open_url()
            home.wait_for_page_ready()
            if home.get_article_count() > 0:
                home.click_article_by_index(0)
                home.wait_for_page_ready()
            detail = PageArticleDetail(self.driver)
            comment = PageComment(self.driver)
            assert not comment.has_comment_form(), "未登录不应显示评论输入框或发表按钮"
            assert comment.is_login_hint_visible(), "未登录应显示'登录 后发表评论'登录提示"
            return

        # 已登录操作
        user = case.login_user or "zhangsan"
        pwd = case.login_password or "123456"
        self._login_and_open_article(user, pwd, case)

        detail = PageArticleDetail(self.driver)
        comment = PageComment(self.driver)

        # 提交评论（字段显式存在即提交；空内容同样点击发表，触发前端校验）
        if has_comment_field:
            comment.input_comment(comment_text)
            comment.click_submit()
            detail.wait_for_page_ready()
            if comment_text:
                # 精确断言: 评论提交后应出现在评论列表中
                detail.assert_comment_exists(comment_text)
            auto_assert(detail, self.driver, case.expected)
            detail.wait_for_page_ready()

        # 回复评论
        if reply_text and comment.get_comments():
            comment.click_reply(0)
            comment.input_reply(reply_text)
            detail.wait_for_page_ready()

        # FC-PL-006/007: 评论/回复后验证通知已生成
        if case_id in ('FC-PL-006', 'FC-PL-007'):
            from page.page_notification import PageNotification
            notif = PageNotification(self.driver)
            notif.open_url()
            notif.wait_for_page_ready()
            notif_count = notif.get_notification_count()
            assert notif_count > 0, f"评论/回复后通知中心应有通知，实际通知数={notif_count}"
            auto_assert(notif, self.driver, case.expected)
            return

        # FC-PL-010: 我的评论列表只显示自己的评论
        if case_id == 'FC-PL-010':
            from page.page_personal import PagePersonal
            personal = PagePersonal(self.driver)
            personal.open_url('/profile/comments')
            personal.wait_for_page_ready()
            auto_assert(personal, self.driver, case.expected)
            return

        # FC-PL-011: 只能删除自己的评论
        if case_id == 'FC-PL-011':
            # 检查当前用户评论是否有删除按钮
            if comment.get_comments():
                has_delete = comment.has_delete_button(0)
                assert has_delete, "自己的评论应有删除按钮"
            auto_assert(detail, self.driver, case.expected)
            return

        auto_assert(detail, self.driver, case.expected)
