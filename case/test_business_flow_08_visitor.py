"""UI 业务流程测试 — 站点访客浏览流程（Y-FK 系列）（自 test_business_flow_ui.py 拆分）"""
import allure
from selenium.webdriver.common.by import By
from page.page_article_detail import PageArticleDetail
from page.page_author import PageAuthor
from page.page_comment import PageComment
from page.page_home import PageHome
from case.flow_common import FlowBase, _c


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.NORMAL)
@allure.feature("站点访客浏览")
class TestVisitorFlow(FlowBase):

    def test_visitor_browse_flow(self):
        """YW-FK-001: 访客浏览站点"""
        c = _c("YW-FK-001")
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        assert home.get_article_count() > 0, "访客应能浏览文章列表"
        # 能打开文章详情
        home.click_article_by_index(0)
        home.wait_for_page_ready()
        detail = PageArticleDetail(self.driver)
        assert detail.get_title().strip(), "访客应能浏览文章详情"
        # 站点统计可见（关于页 .stats-grid）
        base = self.driver.current_url.split("/")[0] + "//" + self.driver.current_url.split("/")[2]
        self.driver.get(base + "/about")
        home.wait_for_page_ready()
        stats = self.driver.find_elements(By.CSS_SELECTOR, ".stat-card")
        assert stats, "访客应能看到站点统计数据"

    def test_visitor_category_author_flow(self):
        """YW-FK-002: 访客浏览分类和作者"""
        c = _c("YW-FK-002")
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        categories = home.get_category_names()
        assert len(categories) > 0, "访客应能浏览分类"
        # 作者主页可浏览
        author = PageAuthor(self.driver)
        author.open_url("/author/2")
        author.wait_for_page_ready()
        assert author.get_author_name().strip(), "访客应能浏览作者主页"

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
        # 确保未登录（前序用例可能已登录）
        self.driver.delete_all_cookies()
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
