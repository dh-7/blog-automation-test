"""UI 业务流程测试 — 未登录跳转 + 读者浏览与收藏流程（YW-FBWZ-006 / YW-LLSC 系列）（自 test_business_flow_ui.py 拆分）"""
import allure
from selenium.webdriver.common.by import By
from page.page_article_detail import PageArticleDetail
from page.page_favorite import PageFavorite
from page.page_home import PageHome
from utils import db_query
from utils.assert_helpers import assert_url
from utils.config import Config
from case.flow_common import FlowBase, login, _c


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.BLOCKER)
@allure.feature("作者发布文章")
class TestAuthRedirectFlow(FlowBase):

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


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("读者浏览与收藏")
class TestReaderBrowseFavoriteFlow(FlowBase):

    def test_search_and_favorite_flow(self):
        """YW-LLSC-001: 搜索并收藏"""
        c = _c("YW-LLSC-001")
        login(self.driver, c.login_user, c.login_password)
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        home.search(c.field("关键词").split("（")[0])  # 取"Java"部分
        home.wait_for_loading_finish()
        assert home.get_article_count() > 0, "搜索应有结果"
        home.click_article_by_index(0)
        home.wait_for_page_ready()
        import re
        detail = PageArticleDetail(self.driver)
        m = re.search(r"/article/(\d+)", self.driver.current_url)
        assert m, "应进入文章详情页"
        aid = int(m.group(1))
        cnt_before = detail.get_favorite_count()
        db_before = db_query.favorite_row(c.login_user, aid)
        detail.click_favorite()
        detail.wait_for_page_ready()
        assert db_query.favorite_row(c.login_user, aid) and not db_before,             "收藏应写入 DB（操作前无记录，操作后有）"
        import re as _re
        def _num(t):
            m2 = _re.search(r"\d+", str(t))
            return int(m2.group()) if m2 else 0
        assert _num(detail.get_favorite_count()) == _num(cnt_before) + 1,             f"收藏数应+1: {cnt_before} -> {detail.get_favorite_count()}"
        # 我的收藏列表中可见
        fav = PageFavorite(self.driver)
        fav.open_url()
        fav.wait_for_page_ready()
        fav_titles = fav.get_article_titles()
        assert fav_titles, "收藏后我的收藏列表不应为空"

    def test_related_article_flow(self):
        """YW-LLSC-002: 相关文章跳转"""
        c = _c("YW-LLSC-002")
        login(self.driver, c.login_user, c.login_password)
        detail = PageArticleDetail(self.driver)
        # detail.open_url(c.field("文章ID", "1"))
        detail.open_url(f"/article/{c.field('文章ID', '1')}")
        detail.wait_for_page_ready()
        related = detail.get_related_articles()
        assert related, "文章1应有相关文章推荐"
        before_url = self.driver.current_url
        detail.click_related_article(0)
        detail.wait_for_page_ready()
        assert self.driver.current_url != before_url,             "点击相关文章应跳转到另一篇文章"
        assert "/article/" in self.driver.current_url

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
        assert home.get_article_count() > 0, "未登录访客应能浏览文章列表"

    def test_search_empty_result_flow(self):
        """YW-LLSC-006: 搜索无结果"""
        c = _c("YW-LLSC-006")
        login(self.driver, c.login_user, c.login_password)
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        home.search(c.field("关键词"))
        home.wait_for_page_ready()
        # 结果异步刷新，轮询等待列表清空（最多5秒）
        import time
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".article-card")
        for _ in range(10):
            if len(cards) == 0:
                break
            time.sleep(0.5)
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".article-card")
        assert len(cards) == 0,             f"搜索不存在的关键词应显示空列表，实际={len(cards)}条"
