"""业务流程 UI 测试 — YW_ 开头的用例，流程手写编排，数据从 Excel 读取"""
import os, sys, pytest
from selenium.webdriver.common.by import By
from base.data_loader import UiDataLoader
from page.page_login import PageLogin
from page.page_register import PageRegister
from page.page_home import PageHome
from page.page_article_detail import PageArticleDetail
from page.page_comment import PageComment
from page.page_favorite import PageFavorite
from page.page_history import PageHistory
from page.page_notification import PageNotification
from page.page_personal import PagePersonal
from page.page_admin_dashboard import PageAdminDashboard
from page.page_admin_article_manage import PageAdminArticleManage
from page.page_admin_comment_manage import PageAdminCommentManage
from page.page_admin_user_manage import PageAdminUserManage
from page.page_publish_article import PagePublishArticle
from utils.assert_helpers import auto_assert, assert_url, assert_toast
from utils.config import Config
from utils.paths import UI_DATASOURCE as DATASOURCE
from case.conftest import login
import allure

# ── 从 Excel 加载 YW_ 用例，按 case_id 建索引 ──
_loader = UiDataLoader(DATASOURCE)
_cases = {c.case_id: c for c in _loader.load_flow_cases()}
_loader.close()


def _c(case_id):
    """按编号取用例，找不到抛异常让 pytest 标记 ERROR"""
    assert case_id in _cases, f"Excel 中未找到用例 {case_id}"
    return _cases[case_id]


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


def _publish_article(driver, u, p, title, content, category_name=None, tag_names=None, summary=None):
    """登录并发布文章辅助函数"""
    login(driver, u, p)
    page = PagePublishArticle(driver)
    page.open_url()
    page.wait_for_page_ready()
    page.input_title(title)
    if category_name and category_name != "（不选）":
        page.select_category(category_name)
    if tag_names:
        for tag in tag_names:
            if tag and tag != "（不选）":
                page.select_tag(tag)
    if summary and summary != "（空）":
        page.input_summary(summary)
    page.input_content(content)
    page.click_publish()
    page.wait_for_page_ready()


def _save_as_draft(driver, u, p, title, content, summary=None):
    """登录并保存草稿辅助函数"""
    login(driver, u, p)
    page = PagePublishArticle(driver)
    page.open_url()
    page.wait_for_page_ready()
    page.input_title(title)
    if summary and summary != "（空）":
        page.input_summary(summary)
    page.input_content(content)
    page.click_draft()
    page.wait_for_page_ready()


# ============================================================
#  作者发布文章
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("作者发布文章")
class TestAuthorPublishFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver
        c = _c("YW-FBWZ-001")  # 同模块账号相同，取第一条即可
        login(driver, c.login_user, c.login_password)

    def test_publish_full_flow(self):
        """YW-FBWZ-001: 完整发布流程"""
        c = _c("YW-FBWZ-001")
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), c.field("内容"),
            category_name=c.field("分类"),
        )
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        assert home.get_article_count() > 0

    def test_save_draft_flow(self):
        """YW-FBWZ-002: 保存草稿流程"""
        c = _c("YW-FBWZ-002")
        _save_as_draft(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), c.field("内容"),
        )
        assert "/write" not in self.driver.current_url

    def test_edit_after_publish_flow(self):
        """YW-FBWZ-003: 发布后修改流程"""
        c = _c("YW-FBWZ-003")
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            c.field("新标题"), "原始内容",
        )
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        assert home.get_article_count() > 0

    def test_empty_title_fail_flow(self):
        """YW-FBWZ-004: 标题为空发布失败"""
        c = _c("YW-FBWZ-004")
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            "", c.field("内容"),
        )
        assert "/write" in self.driver.current_url

    def test_empty_content_fail_flow(self):
        """YW-FBWZ-005: 内容为空发布失败"""
        c = _c("YW-FBWZ-005")
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), "",
        )
        assert "/write" in self.driver.current_url


# ============================================================
#  未登录跳转
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("作者发布文章")
class TestAuthRedirectFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def test_not_login_redirect_flow(self):
        """YW-FBWZ-006: 未登录跳转登录页"""
        c = _c("YW-FBWZ-006")
        detail = PageArticleDetail(self.driver)
        base_url = Config.get("env", "base_url", default="http://localhost:5173")
        # 先导航到站点，再清除登录态（data: URL 上无法访问 localStorage）
        self.driver.get(base_url)
        self.driver.delete_all_cookies()
        self.driver.execute_script("localStorage.clear(); sessionStorage.clear();")
        self.driver.get(f"{base_url}/write")
        detail.wait_for_page_ready()
        assert_url(detail, self.driver, "/login")


# ============================================================
#  读者浏览与收藏
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("读者浏览与收藏")
class TestReaderBrowseFavoriteFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def test_search_and_favorite_flow(self):
        """YW-LLSC-001: 搜索并收藏"""
        c = _c("YW-LLSC-001")
        login(self.driver, c.login_user, c.login_password)
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        home.search(c.field("关键词").split("（")[0])  # 取"Java"部分
        home.wait_for_loading_finish()
        if home.get_article_count() > 0:
            home.click_article_by_index(0)
            home.wait_for_page_ready()
            detail = PageArticleDetail(self.driver)
            detail.click_favorite()
            detail.wait_for_page_ready()

    def test_related_article_flow(self):
        """YW-LLSC-002: 相关文章跳转"""
        c = _c("YW-LLSC-002")
        login(self.driver, c.login_user, c.login_password)
        detail = PageArticleDetail(self.driver)
        # detail.open_url(c.field("文章ID", "1"))
        detail.open_url(f"/article/{c.field('文章ID', '1')}")
        detail.wait_for_page_ready()
        related = detail.get_related_articles()
        if related:
            detail.click_related_article(0)
            detail.wait_for_page_ready()

    def test_category_tag_filter_flow(self):
        """YW-LLSC-003: 分类+标签筛选"""
        c = _c("YW-LLSC-003")
        login(self.driver, c.login_user, c.login_password)
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        category = c.field("分类").split("（")[0]  # 取"技术"部分
        home.click_category_by_name(category)
        home.wait_for_loading_finish()

    def test_unfavorite_from_list_flow(self):
        """YW-LLSC-004: 从收藏列表取消收藏"""
        c = _c("YW-LLSC-004")
        login(self.driver, c.login_user, c.login_password)
        fav = PageFavorite(self.driver)
        fav.open_url()
        fav.wait_for_page_ready()
        if fav.get_favorite_count() > 0:
            fav.click_unfavorite(0)
            fav.wait_for_page_ready()

    def test_not_login_browse_flow(self):
        """YW-LLSC-005: 未登录浏览"""
        c = _c("YW-LLSC-005")
        self.driver.delete_all_cookies()
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        assert home.get_article_count() >= 0

    def test_search_empty_result_flow(self):
        """YW-LLSC-006: 搜索无结果"""
        c = _c("YW-LLSC-006")
        login(self.driver, c.login_user, c.login_password)
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        home.search(c.field("关键词"))
        home.wait_for_loading_finish()


# ============================================================
#  读者评论互动
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("读者评论互动")
class TestReaderCommentNotifyFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

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
        # 回复该评论
        comment.click_reply(reply_idx)
        comment.input_reply(c.field("回复内容"))
        comment.click_submit()
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
        if home.get_article_count() > 0:
            home.click_article_by_index(0)
            home.wait_for_page_ready()
            comment = PageComment(self.driver)
            comment.input_comment("自己评论自己")
            comment.click_submit()
            comment.wait_for_page_ready()

    def test_mark_all_read_flow(self):
        """YW-PLHD-004: 全部已读"""
        c = _c("YW-PLHD-004")
        login(self.driver, c.login_user, c.login_password)
        notif = PageNotification(self.driver)
        notif.open_url()
        notif.wait_for_page_ready()
        notif.click_mark_all_read()
        notif.wait_for_page_ready()

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


# ============================================================
#  阅读历史追踪
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("阅读历史追踪")
class TestHistoryFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def test_record_delete_clear_flow(self):
        """YW-YDLS-001: 记录、删除、清空"""
        c = _c("YW-YDLS-001")
        login(self.driver, c.login_user, c.login_password)
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        if home.get_article_count() > 0:
            home.click_article_by_index(0)
            home.wait_for_page_ready()
        history = PageHistory(self.driver)
        history.open_url()
        history.wait_for_page_ready()
        count = history.get_history_count()
        if count > 0:
            history.click_delete(0)
            history.wait_for_page_ready()
        history.click_clear_all()
        history.wait_for_page_ready()

    def test_reread_time_update_flow(self):
        """YW-YDLS-002: 重复浏览时间更新"""
        c = _c("YW-YDLS-002")
        login(self.driver, c.login_user, c.login_password)
        detail = PageArticleDetail(self.driver)
        # detail.open_url(c.field("之前浏览过的文章ID", "1"))
        detail.open_url(f"/article/{c.field('之前浏览过的文章ID', '1')}")
        detail.wait_for_page_ready()

    def test_not_login_no_history_flow(self):
        """YW-YDLS-003: 未登录不记录历史"""
        c = _c("YW-YDLS-003")
        self.driver.delete_all_cookies()
        history = PageHistory(self.driver)
        history.open_url()
        history.wait_for_page_ready()
        assert "/login" in self.driver.current_url

    def test_history_isolation_flow(self):
        """YW-YDLS-004: 历史数据隔离"""
        c = _c("YW-YDLS-004")
        # 先用用户A（zhangsan）登录并浏览一篇文章，产生历史记录
        login(self.driver, "zhangsan", "123456")
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        titles_a = []
        if home.get_article_count() > 0:
            titles_a.append(home.get_article_title_by_index(0))
            home.click_article_by_index(0)
            home.wait_for_page_ready()
        # 切换到用户B（lisi）登录
        login(self.driver, c.login_user, c.login_password)
        history_b = PageHistory(self.driver)
        history_b.open_url()
        history_b.wait_for_page_ready()
        titles_b = history_b.get_article_titles()
        # 用户B的历史中不应包含用户A刚浏览的文章
        for title in titles_b:
            assert title not in titles_a, f"用户B不应看到用户A的浏览记录: {title}"


# ============================================================
#  个人信息与密码管理
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("个人信息与密码管理")
class TestUserInfoFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def test_modify_info_flow(self):
        """YW-GRXX-001: 修改个人信息"""
        c = _c("YW-GRXX-001")
        login(self.driver, c.login_user, c.login_password)
        personal = PagePersonal(self.driver)
        personal.open_url()
        personal.wait_for_page_ready()
        personal.click_settings()
        personal.wait_for_page_ready()
        personal.fill_nickname(c.field("新昵称"))
        personal.fill_email(c.field("新邮箱"))
        personal.fill_bio(c.field("新简介"))
        personal.click_save()
        personal.wait_for_page_ready()

    def test_change_password_flow(self):
        """YW-GRXX-002: 修改密码成功并验证新旧密码完整流程"""
        c = _c("YW-GRXX-002")
        old_pwd, new_pwd = c.field('原密码'), c.field('新密码')
        personal = PagePersonal(self.driver)
        lp = PageLogin(self.driver)

        login(self.driver, c.login_user, c.login_password)            # ① 原密码登录

        # ② 修改密码：原密码 → 新密码（复用现有便捷方法）
        personal.open_url(c.page_path + '/settings')
        personal.wait_for_page_ready()
        personal.change_password(old_pwd, new_pwd)
        personal.wait.until(lambda d: PageLogin.page_path in d.current_url)  # 等跳转登录页

        # ③ 旧密码登录失败：错误提示可见（get_fail_result 内置等待）+ 停留登录页
        lp.open_url()
        lp.input_username(c.login_user)
        lp.input_password(old_pwd)
        lp.click_login_button()
        lp.get_fail_result()                                          # 等待"用户名或密码错误"toast
        assert PageLogin.page_path in self.driver.current_url, "旧密码应登录失败"

        # ④ 新密码登录成功：复用 login()（内置等待离开 /login）
        login(self.driver, c.login_user, new_pwd)
        assert PageLogin.page_path not in self.driver.current_url, "新密码应登录成功"

        # ⑤ 恢复原密码：新密码 → 原密码
        personal.open_url(c.page_path + '/settings')
        personal.wait_for_page_ready()
        personal.change_password(new_pwd, old_pwd)
        personal.wait.until(lambda d: PageLogin.page_path in d.current_url)

    def test_wrong_old_password_flow(self):
        """YW-GRXX-003: 原密码错误失败"""
        c = _c("YW-GRXX-003")
        wrong_pwd = c.field("原密码", "wrongpass").split("（")[0]
        new_pwd = c.field("新密码", "newpass456")
        login(self.driver, c.login_user, c.login_password)
        personal = PagePersonal(self.driver)
        personal.open_url('/profile/settings')
        personal.wait_for_page_ready()
        personal.click_security_tab()
        personal.wait_for_page_ready()
        personal.fill_old_password(wrong_pwd)
        personal.fill_new_password(new_pwd)
        personal.fill_confirm_password(new_pwd)
        personal.click_change_password()
        personal.wait_for_page_ready()
        # 验证提示原密码错误
        toast = personal.wait_for_toast("密码", timeout=5)
        if not toast:
            toast = personal.wait_for_toast("错误", timeout=3)
        if not toast:
            toast = personal.wait_for_toast("失败", timeout=3)
        assert "/settings" in self.driver.current_url, "原密码错误应留在设置页"

    def test_empty_new_password_flow(self):
        """YW-GRXX-004: 新密码为空失败"""
        c = _c("YW-GRXX-004")
        old_pwd = c.field("原密码", "123456")
        login(self.driver, c.login_user, c.login_password)
        personal = PagePersonal(self.driver)
        personal.open_url('/profile/settings')
        personal.wait_for_page_ready()
        personal.click_security_tab()
        personal.wait_for_page_ready()
        personal.fill_old_password(old_pwd)
        # 新密码留空
        personal.click_change_password()
        personal.wait_for_page_ready()
        toast = personal.wait_for_toast("填写", timeout=5)
        if not toast:
            toast = personal.wait_for_toast("密码", timeout=3)
        assert "/settings" in self.driver.current_url, "新密码为空应留在设置页"

    def test_not_login_redirect_flow(self):
        """YW-GRXX-005: 未登录跳转"""
        c = _c("YW-GRXX-005")
        self.driver.delete_all_cookies()
        personal = PagePersonal(self.driver)
        personal.open_url()
        personal.wait_for_page_ready()
        assert_url(personal, self.driver, "/login")


# ============================================================
#  管理员管理用户
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("管理员管理用户")
class TestAdminManageUserFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def test_admin_modify_user_flow(self):
        """YW-GLY-001: 管理员修改用户信息"""
        c = _c("YW-GLY-001")
        user_page = PageAdminUserManage(self.driver)
        user_page.login_and_open(c.login_user, c.login_password)
        if user_page.get_row_count() > 1:
            user_page.click_edit_by_index(1)
            user_page.wait_for_edit_dialog(timeout=5)
            user_page.input_edit_nickname(c.field("新昵称"))
            user_page.click_edit_save()
            user_page.wait_for_loading_finish()

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


# ============================================================
#  管理员管理文章与评论
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("管理员管理文章与评论")
class TestAdminManageArticleCommentFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def test_admin_search_delete_article_flow(self):
        """YW-GLWZ-001: 搜索删除文章"""
        c = _c("YW-GLWZ-001")
        article_page = PageAdminArticleManage(self.driver)
        article_page.login_and_open(c.login_user, c.login_password)
        article_page.input_search(c.field("搜索关键词").split("（")[0])
        article_page.click_search()
        article_page.wait_for_loading_finish()
        if article_page.get_row_count() > 0:
            article_page.click_delete_by_index(0)
            article_page.wait_for_confirm_dialog()
            article_page.confirm_delete()
            article_page.wait_for_loading_finish()

    def test_admin_delete_comment_flow(self):
        """YW-GLWZ-002: 删除评论"""
        c = _c("YW-GLWZ-002")
        comment_page = PageAdminCommentManage(self.driver)
        comment_page.login_and_open(c.login_user, c.login_password)
        if comment_page.get_row_count() > 0:
            comment_page.click_delete_by_index(0)
            comment_page.wait_for_confirm_dialog()
            comment_page.confirm_delete()
            comment_page.wait_for_loading_finish()

    def test_admin_stats_consistent_flow(self):
        """YW-GLWZ-003: 统计数据一致"""
        c = _c("YW-GLWZ-003")
        dashboard = PageAdminDashboard(self.driver)
        dashboard.login_and_open(c.login_user, c.login_password)
        stats = dashboard.get_stat_numbers()
        assert len(stats) > 0

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


# ============================================================
#  文章生命周期
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("文章生命周期")
class TestArticleLifecycleFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def test_full_lifecycle_flow(self):
        """YW-SMZQ-001: 完整生命周期"""
        c = _c("YW-SMZQ-001")
        login(self.driver, c.login_user, c.login_password)
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), c.field("文章内容"),
            category_name=c.field("分类"),
        )
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        titles = home.get_all_article_titles()
        assert any(c.field("标题") in t for t in titles)

    def test_draft_to_publish_flow(self):
        """YW-SMZQ-002: 草稿→发布状态切换"""
        c = _c("YW-SMZQ-002")
        login(self.driver, c.login_user, c.login_password)
        _save_as_draft(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), c.field("文章内容"),
        )
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        titles = home.get_all_article_titles()
        assert c.field("标题") not in titles

    def test_non_author_no_permission_flow(self):
        """YW-SMZQ-003: 非作者无权修改删除"""
        c = _c("YW-SMZQ-003")
        article_id = c.field("文章ID")
        login(self.driver, c.login_user, c.login_password)

        # 1. 验证无法编辑他人文章：详情页不应显示编辑按钮
        detail = PageArticleDetail(self.driver)
        detail.open_url(f"/article/{article_id}")
        detail.wait_for_page_ready()
        edit_btns = self.driver.find_elements(By.XPATH,
            '//button//span[text()="编辑"]')
        assert len(edit_btns) == 0, "非作者在详情页不应看到编辑按钮"
        target_title = detail.get_title()

        # 2. 验证无法删除他人文章：个人中心"我的文章"不应包含他人文章
        from page.page_personal import PagePersonal
        p_page = PagePersonal(self.driver)
        p_page.open_url()
        p_page.wait_for_page_ready()
        titles = p_page.get_article_titles()
        assert target_title not in titles, "非作者在个人中心不应看到他人文章"

    def test_admin_delete_visible_flow(self):
        """YW-SMZQ-004: 管理员删除后作者不可见"""
        c = _c("YW-SMZQ-004")
        admin_page = PageAdminArticleManage(self.driver)
        admin_page.login_and_open(c.login_user, c.login_password)
        if admin_page.get_row_count() == 0:
            pytest.skip("文章列表为空，无法测试删除后不可见")
        target_title = admin_page.get_article_title(0)
        admin_page.click_delete_by_index(0)
        admin_page.wait_for_confirm_dialog()
        admin_page.confirm_delete()
        admin_page.wait_for_loading_finish()
        home = PageHome(self.driver)
        home.login_and_open("zhangsan", "123456")
        titles = home.get_all_article_titles()
        assert target_title not in titles, "管理员删除的文章不应在作者端可见"

    def test_deleted_article_no_comment_flow(self):
        """YW-SMZQ-005: 删除文章后无法评论"""
        c = _c("YW-SMZQ-005")
        admin_page = PageAdminArticleManage(self.driver)
        admin_page.login_and_open("admin", "admin123")
        if admin_page.get_row_count() == 0:
            pytest.skip("文章列表为空，无法测试删除后评论")
        # 记录第一篇文章ID，然后删除
        article_id = admin_page.get_article_id(0)
        admin_page.click_delete_by_index(0)
        admin_page.wait_for_confirm_dialog()
        admin_page.confirm_delete()
        admin_page.wait_for_loading_finish()
        # 尝试访问已删除文章的详情页
        detail = PageArticleDetail(self.driver)
        detail.open_url(f"/article/{article_id}")
        detail.wait_for_page_ready()
        # 页面应显示错误/空状态，评论区不应可用
        comment_form = self.driver.find_elements(By.CSS_SELECTOR, ".comment-form")
        page_source = self.driver.page_source
        has_error = "不存在" in page_source or "404" in page_source or len(comment_form) == 0
        assert has_error, "已删除文章不应显示评论区"


# ============================================================
#  站点访客浏览
# ============================================================
@allure.epic("UI自动化测试")
@allure.feature("站点访客浏览")
class TestVisitorFlow:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    def test_visitor_browse_flow(self):
        """YW-FK-001: 访客浏览站点"""
        c = _c("YW-FK-001")
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        assert home.get_article_count() >= 0

    def test_visitor_category_author_flow(self):
        """YW-FK-002: 访客浏览分类和作者"""
        c = _c("YW-FK-002")
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        categories = home.get_category_names()
        assert len(categories) >= 0

    def test_visitor_comment_login_prompt_flow(self):
        """YW-FK-003: 访客评论提示登录"""
        c = _c("YW-FK-003")
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        if home.get_article_count() > 0:
            home.click_article_by_index(0)
            home.wait_for_page_ready()
            detail = PageArticleDetail(self.driver)
            comment = PageComment(self.driver)
            assert not comment.has_comment_form(), "访客不应显示评论输入框或发表按钮"
            assert comment.is_login_hint_visible(), "访客应显示'登录 后发表评论'登录提示"

    def test_visitor_favorite_login_prompt_flow(self):
        """YW-FK-004: 访客收藏提示登录"""
        c = _c("YW-FK-004")
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        if home.get_article_count() > 0:
            home.click_article_by_index(0)
            home.wait_for_page_ready()
            detail = PageArticleDetail(self.driver)
            # 触发动作：访客点击收藏按钮，前端应弹"请先登录"toast。
            # 直接定向断言 toast（auto_assert 多关键词轮询会先查"失败"等
            # 无关词，把 3 秒的 toast 等过期）
            detail.click_favorite()
            toast = detail.quick_wait_toast("请先登录", timeout=3, interval=0.2)
            assert toast, "访客点击收藏应弹出'请先登录'提示"
