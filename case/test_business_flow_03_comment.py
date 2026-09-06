"""UI 业务流程测试 — 读者评论互动流程（YW-PLHD 系列）（自 test_business_flow_ui.py 拆分）"""
import allure
import pytest
from page.page_article_detail import PageArticleDetail
from page.page_comment import PageComment
from page.page_home import PageHome
from page.page_notification import PageNotification
from utils import db_query
from case.flow_common import FlowBase, login, _c, _get_username_by_nickname


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("读者评论互动")
class TestReaderCommentNotifyFlow(FlowBase):

    def test_comment_triggers_notification_flow(self):
        """YW-PLHD-001: 评论触发通知"""
        c = _c("YW-PLHD-001")
        login(self.driver, c.login_user, c.login_password)
        # 直接打开数据源指定的文章
        detail = PageArticleDetail(self.driver)
        detail.open_url(c.resolved_path())
        detail.wait_for_page_ready()
        # 记录文章作者（通知应发给作者）
        author = detail.get_author()
        assert author != c.login_user, f"文章作者是 {author}，不能是登录用户自己"
        # lisi 发表评论
        comment = PageComment(self.driver)
        comment.input_comment(c.field("用户A的评论内容"))
        comment.click_submit()
        comment.wait_for_page_ready()
        # 切换到作者账号验证通知
        login(self.driver, "admin", "admin123")
        notif = PageNotification(self.driver)
        notif.open_url()
        assert notif.get_notification_count() > 0, "评论后应触发作者通知，但通知列表为空"
        latest = db_query.latest_notification("admin")
        assert latest and latest[0] == "comment",             f"最新通知类型应为 comment，实际={latest}"

    def test_reply_triggers_notification_flow(self):
        """YW-PLHD-002: 回复评论并触发被回复人通知"""
        c = _c("YW-PLHD-002")
        login(self.driver, c.login_user, c.login_password)
        # 直接打开数据源指定的文章
        detail = PageArticleDetail(self.driver)
        detail.open_url(c.resolved_path())
        detail.wait_for_page_ready()
        # 获取第一条评论的作者（被回复人）
        comment = PageComment(self.driver)
        assert len(comment.get_comments()) > 0, "文章应有评论才能进行回复测试"
        # 找到第一条非当前用户的评论
        comments = comment.get_comments()
        reply_to_user = None
        reply_idx = 0
        for i in range(len(comments)):
            author = comment.get_comment_author(i)
            if author != c.login_user:
                reply_to_user = author
                reply_idx = i
                break
        assert reply_to_user is not None, "应存在一条非当前用户的评论才能进行回复测试"
        # 回复该评论（必须点回复表单内的提交按钮，回复才真正提交）
        comment.click_reply(reply_idx)
        comment.input_reply(c.field("回复内容"))
        comment.submit_reply()
        comment.wait_for_page_ready()
        # 切换到被回复人账号验证通知
        reply_to_login_user = _get_username_by_nickname(reply_to_user)
        login(self.driver, reply_to_login_user, "123456")
        notif = PageNotification(self.driver)
        notif.open_url()
        assert notif.get_notification_count() > 0, \
            f"回复后 {reply_to_user} 应收到回复通知，但通知列表为空"

    def test_self_comment_no_notify_flow(self):
        """YW-PLHD-003: 自己评论自己不产生通知"""
        c = _c("YW-PLHD-003")
        login(self.driver, c.login_user, c.login_password)
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        aid = int(c.field("文章ID"))
        detail0 = PageArticleDetail(self.driver)
        detail0.open_url(f"/article/{aid}")
        detail0.wait_for_page_ready()
        if detail0.is_comment_section_visible():
            cnt_before = db_query.comment_count(aid)
            unread_before = db_query.unread_notification_count(c.login_user)
            comment = PageComment(self.driver)
            comment.input_comment("自己评论自己")
            comment.click_submit()
            comment.wait_for_page_ready()
            # 评论应提交成功（DB 评论数+1）
            assert db_query.comment_count(aid) == cnt_before + 1,                 "自己评论自己时评论应提交成功"
            # 不产生通知（DB 未读数不变）
            unread_after = db_query.unread_notification_count(c.login_user)
            assert unread_after == unread_before,                 f"自己评论自己不应产生通知: 未读数 {unread_before}->{unread_after}"

    def test_mark_all_read_flow(self):
        """YW-PLHD-004: 全部已读"""
        c = _c("YW-PLHD-004")

        # ── 前置准备：让其他用户给 zhangsan 的文章评论，产生一条通知 ──
        # 选 zhangsan 的文章（文章 3 "我的 2024 年终总结"，作者为 zhangsan）
        login(self.driver, "lisi", "123456")
        detail = PageArticleDetail(self.driver)
        detail.open_url("/article/3")
        detail.wait_for_page_ready()
        comment = PageComment(self.driver)
        comment.input_comment("自动化测试-为触发通知而评论")
        comment.click_submit()
        comment.wait_for_page_ready()

        # ── 正式流程：切换到 zhangsan，执行全部已读 ──
        login(self.driver, c.login_user, c.login_password)
        notif = PageNotification(self.driver)
        notif.open_url()
        notif.wait_for_page_ready()
        notif.click_mark_all_read()
        notif.wait_for_page_ready()
        # 精确回查：未读数归0
        assert db_query.unread_notification_count(c.login_user) == 0,             "全部已读后未读数应归0"

    def test_empty_comment_fail_flow(self):
        """YW-PLHD-005: 空评论失败"""
        c = _c("YW-PLHD-005")
        login(self.driver, c.login_user, c.login_password)
        # ① 打开数据源指定的文章（/article/1），不再点首页第一篇文章
        detail = PageArticleDetail(self.driver)
        detail.open_url(c.resolved_path())
        detail.wait_for_page_ready()
        # ② 输入空评论并提交
        comment = PageComment(self.driver)
        comment.input_comment("")
        comment.click_submit()
        # ③ 立即精确断言 toast（短轮询，避免 auto_assert 把 3 秒 toast 等过期）
        toast = comment.quick_wait_toast("请输入评论内容", timeout=3, interval=0.1)
        assert toast, "点击发表评论后应提示'请输入评论内容'"
        return

    def test_non_author_delete_fail_flow(self):
        """YW-PLHD-006: 非作者删除评论失败"""
        c = _c("YW-PLHD-006")
        login(self.driver, c.login_user, c.login_password)
        # 直接打开数据源指定的文章
        detail = PageArticleDetail(self.driver)
        detail.open_url(c.resolved_path())
        detail.wait_for_page_ready()
        comment = PageComment(self.driver)
        comments = comment.get_comments()
        assert len(comments) > 0, "文章应有评论"
        # 找到一条非 lisi 的评论
        for i in range(len(comments)):
            author = comment.get_comment_author(i)
            if author != c.login_user:
                assert not comment.has_delete_button(i), \
                    f"非作者不应有删除按钮，但 {author} 的评论上存在删除按钮"
                return
        pytest.skip("未找到非当前用户的评论，无法验证权限")

    def test_not_login_comment_fail_flow(self):
        """YW-PLHD-007: 未登录评论失败"""
        c = _c("YW-PLHD-007")
        self.driver.delete_all_cookies()
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
