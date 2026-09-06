"""评论模块 UI 测试 — 数据驱动"""
import os, sys, pytest
from selenium.webdriver.common.by import By
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_home import PageHome
from page.page_login import PageLogin
from page.page_article_detail import PageArticleDetail
from page.page_comment import PageComment
from utils import db_query
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

        # FC-PL-001: 评论区显示评论者完整信息（头像、昵称、内容、时间逐项结构校验）
        if case_id == 'FC-PL-001':
            detail = PageArticleDetail(self.driver)
            comment = PageComment(self.driver)
            detail.open_url(case.resolved_path())
            detail.wait_for_page_ready()
            items = comment.get_comments()
            assert len(items) > 0, "文章1应有种子评论"
            for i in range(len(items)):
                assert comment.get_comment_author(i).strip(), f"评论{i}缺昵称"
                assert comment.get_comment_text(i).strip(), f"评论{i}缺内容"
                assert comment.get_comment_time(i).strip(), f"评论{i}缺时间"
                avatar = items[i].find_elements(By.CSS_SELECTOR, ".el-avatar img, .el-avatar")
                assert avatar, f"评论{i}缺头像"
            return

        # FC-PL-002: 树形评论结构正确，子评论缩进显示在父评论下方
        if case_id == 'FC-PL-002':
            detail = PageArticleDetail(self.driver)
            comment = PageComment(self.driver)
            detail.open_url(case.resolved_path())
            detail.wait_for_page_ready()
            # 真正校验树形结构：存在嵌套在父评论内的子评论（种子数据含2条回复）
            nested_count = comment.get_nested_comment_count()
            assert nested_count > 0, \
                "应存在嵌套在父评论下方的子评论（树形结构），实际嵌套子评论数=0"
            return

        # FC-PL-003: 回复评论显示被回复人的昵称（子评论的"回复 X"应等于父评论作者）
        if case_id == 'FC-PL-003':
            detail = PageArticleDetail(self.driver)
            comment = PageComment(self.driver)
            detail.open_url(case.resolved_path())
            detail.wait_for_page_ready()
            # 顶层评论（排除嵌套的子评论）
            tops = self.driver.find_elements(
                By.XPATH, '//*[contains(@class,"comment-item") '
                          'and not(ancestor::div[contains(@class,"comment-item")])]')
            assert tops, "应有顶层评论"
            reply_seen = 0
            for top in tops:
                username_els = top.find_elements(By.CSS_SELECTOR, ".username")
                if not username_els:
                    continue
                parent_nick = username_els[0].text.strip()
                reply_els = top.find_elements(By.CSS_SELECTOR, ".reply-to")
                for r in reply_els:
                    target = r.text.strip().replace("回复", "").strip()
                    reply_seen += 1
                    assert target, "被回复人昵称为空"
                    assert target == parent_nick, \
                        f"子评论'回复 {target}'与父评论作者'{parent_nick}'不一致"
            assert reply_seen > 0, "种子数据应包含带被回复人昵称的子评论"
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
            # 通知内容应指向本次评论（精确验证，而非仅"有通知"）
            latest = db_query.latest_notification(author_username)
            assert latest and latest[0] == 'comment', \
                f"最新通知类型应为 comment，实际={latest}"
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
            # 回复该评论（必须点回复表单内的提交按钮，回复才真正提交）
            reply_text = case.field("用户A的回复内容")
            comment.click_reply(reply_idx)
            comment.input_reply(reply_text)
            comment.submit_reply()
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
            latest = db_query.latest_notification(reply_to_username)
            assert latest and latest[0] == 'reply', \
                f"最新通知类型应为 reply，实际={latest}"
            return

        # FC-PL-005: 回复某评论成功显示为子评论（必须真正提交回复并验证子评论出现）
        if case_id == 'FC-PL-005':
            user = case.login_user or "zhangsan"
            pwd = case.login_password or "123456"
            login_page = PageLogin(self.driver)
            login_page.login(user, pwd)
            detail = PageArticleDetail(self.driver)
            detail.open_url(case.resolved_path())
            detail.wait_for_page_ready()
            comment = PageComment(self.driver)
            parent_before = comment.get_nested_comment_count()
            comment.click_reply(0)
            comment.input_reply(reply_text)
            comment.submit_reply()
            comment.wait_for_page_ready()
            nested_bodies = comment.get_nested_comment_bodies(0)
            assert any(reply_text in b for b in nested_bodies), \
                f"回复'{reply_text}'应作为第1条评论的子评论显示，实际子评论={nested_bodies}"
            assert comment.get_nested_comment_count() == parent_before + 1, \
                "回复提交后嵌套子评论数应+1"
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
            if case_id == 'FC-PL-004':
                # 已用 assert_comment_exists 精确验证，不再走通用断言
                return
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
            # 精确断言：页面评论内容集合 == DB 中当前登录用户的评论集合
            page_contents = [el.text.strip() for el in self.driver.find_elements(
                By.CSS_SELECTOR, '.comment-content')]
            db_contents = set(db_query.user_comments_contents(user))
            assert page_contents, "我的评论列表应有评论"
            for c in page_contents:
                assert c in db_contents, \
                    f"我的评论列表出现了非当前用户的评论: '{c}'"
            assert len(page_contents) == len(db_contents), \
                f"列表条数({len(page_contents)})与DB中本人评论数({len(db_contents)})不一致"
            return

        # FC-PL-011: 只能删除自己的评论
        if case_id == 'FC-PL-011':
            # 显式打开文章1（数据源指定），避免依赖首页第一篇文章
            detail = PageArticleDetail(self.driver)
            detail.open_url('/article/1')
            detail.wait_for_page_ready()
            # 逐条校验：自己的评论有删除按钮，他人的评论没有
            # （管理员可删任意评论属于管理员场景，本用例以普通用户视角验证）
            me_nickname = db_query.scalar(
                "SELECT nickname FROM user WHERE username=%s", (user,))
            assert me_nickname, f"DB 中未找到用户 {user}"
            authors = comment.get_comment_authors()
            assert authors, "文章1应有评论"
            checked_own = checked_other = 0
            for i, author in enumerate(authors):
                has_del = comment.has_delete_button(i)
                if author == me_nickname:
                    assert has_del, f"自己的评论(第{i}条, {author})应有删除按钮"
                    checked_own += 1
                else:
                    assert not has_del, \
                        f"他人评论(第{i}条, {author})不应显示删除按钮"
                    checked_other += 1
            assert checked_own > 0, "应至少校验到一条自己的评论"
            assert checked_other > 0, "应至少校验到一条他人的评论"
            return

        auto_assert(detail, self.driver, case.expected)
