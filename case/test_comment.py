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


def _get_username_by_nickname(nickname):
    """通过昵称查询登录用户名"""
    import pymysql
    conn = pymysql.connect(
        host=Config.get("mysql", "host", default="localhost"),
        port=Config.get("mysql", "port", default=3306),
        user=Config.get("mysql", "user", default="root"),
        password=Config.get("mysql", "password", default=""),
        database=Config.get("mysql", "database", default="blog_db"),
        charset="utf8mb4",
    )
    try:
        cur = conn.cursor()
        cur.execute('SELECT username FROM user WHERE nickname=%s AND deleted=0', (nickname,))
        row = cur.fetchone()
        return row[0] if row else nickname
    finally:
        conn.close()


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

        # FC-PL-006: 评论别人的文章触发作者通知（特殊处理）
        if case_id == 'FC-PL-006':
            user = case.login_user or "lisi"
            pwd = case.login_password or "123456"
            # 登录
            login_page = PageLogin(self.driver)
            login_page.login(user, pwd)
            # 直接打开数据源指定的文章（文章ID=1），不点首页第一篇
            detail = PageArticleDetail(self.driver)
            detail.open_url(case.resolved_path())
            detail.wait_for_page_ready()
            # 验证文章作者不是当前用户（通过登录用户名比较，而非显示名称）
            author_display = detail.get_author()
            author_username = _get_username_by_nickname(author_display)
            assert author_username != user, f"文章作者是 {author_display}，不能是登录用户自己"
            # 发表评论
            comment = PageComment(self.driver)
            comment_text = case.field("用户A的评论内容")
            comment.input_comment(comment_text)
            comment.click_submit()
            detail.wait_for_page_ready()
            if comment_text:
                detail.assert_comment_exists(comment_text)
            # 切换到作者账号验证通知
            from page.page_notification import PageNotification
            author_password = "admin123" if author_username == "admin" else "123456"
            login_page2 = PageLogin(self.driver)
            login_page2.login(author_username, author_password)
            notif = PageNotification(self.driver)
            notif.open_url()
            notif.wait_for_page_ready()
            notif_count = notif.get_notification_count()
            assert notif_count > 0, f"评论后通知中心应有通知，实际通知数={notif_count}"
            auto_assert(notif, self.driver, case.expected)
            return

        # FC-PL-007: 回复某人的评论触发被回复人通知（特殊处理）
        if case_id == 'FC-PL-007':
            user = case.login_user or "lisi"
            pwd = case.login_password or "123456"
            # 登录
            login_page = PageLogin(self.driver)
            login_page.login(user, pwd)
            # 直接打开数据源指定的文章（文章ID=1）
            detail = PageArticleDetail(self.driver)
            detail.open_url(case.resolved_path())
            detail.wait_for_page_ready()
            # 找到第一条非当前用户的评论（通过登录用户名比较，而非显示名称）
            comment = PageComment(self.driver)
            comments = comment.get_comments()
            assert len(comments) > 0, "文章应有评论才能进行回复测试"
            reply_to_user = None
            reply_to_username = None
            reply_idx = 0
            for i in range(len(comments)):
                cauthor_display = comment.get_comment_author(i)  # 显示名称（昵称）
                cauthor_username = _get_username_by_nickname(cauthor_display)  # 登录用户名
                if cauthor_username != user:
                    reply_to_user = cauthor_display
                    reply_to_username = cauthor_username
                    reply_idx = i
                    break
            if reply_to_user is None:
                pytest.skip("文章ID=1没有非当前用户的评论，无法进行回复测试")
            # 回复该评论
            reply_text = case.field("用户A的回复内容")
            comment.click_reply(reply_idx)
            comment.input_reply(reply_text)
            comment.click_submit()
            comment.wait_for_page_ready()
            # 切换到被回复人账号验证通知
            from page.page_notification import PageNotification
            reply_to_password = "admin123" if reply_to_username == "admin" else "123456"
            login_page2 = PageLogin(self.driver)
            login_page2.login(reply_to_username, reply_to_password)
            notif = PageNotification(self.driver)
            notif.open_url()
            notif.wait_for_page_ready()
            notif_count = notif.get_notification_count()
            assert notif_count > 0, f"回复后被回复人通知中心应有通知，实际通知数={notif_count}"
            auto_assert(notif, self.driver, case.expected)
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
