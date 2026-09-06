"""UI 业务流程测试 — 阅读历史流程（YW-YDLS 系列）（自 test_business_flow_ui.py 拆分）"""
import allure
from selenium.webdriver.common.by import By
from page.page_article_detail import PageArticleDetail
from page.page_history import PageHistory
from page.page_home import PageHome
from utils import db_query
from case.flow_common import FlowBase, login, _c


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.NORMAL)
@allure.feature("阅读历史追踪")
class TestHistoryFlow(FlowBase):

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
        # 记录：浏览完成后历史应非空
        count_before = history.get_history_count()
        assert count_before > 0, "浏览文章后阅读历史应非空"
        # 删除第一条
        history.click_delete(0)
        history.wait_for_page_ready()
        try:
            history.wait_for_confirm_dialog(timeout=3)
            history.confirm_dialog()
        except Exception:
            pass
        history.wait_for_page_ready()
        count_mid = history.get_history_count()
        assert count_mid == count_before - 1,             f"删除单条后历史应-1: {count_before}->{count_mid}"
        # 清空
        history.click_clear_all()
        history.wait_for_page_ready()
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(self.driver, 5).until(
            lambda d: len(self.driver.find_elements(By.CSS_SELECTOR, ".article-item")) == 0
            or len(self.driver.find_elements(By.CSS_SELECTOR, ".empty-state")) > 0
        )
        empty_now = len(self.driver.find_elements(By.CSS_SELECTOR, ".article-item")) == 0
        assert empty_now, "清空后阅读历史应为空"

    def test_reread_time_update_flow(self):
        """YW-YDLS-002: 重复浏览时间更新"""
        c = _c("YW-YDLS-002")
        login(self.driver, c.login_user, c.login_password)
        import time
        aid = int(c.field('之前浏览过的文章ID', '1'))
        detail = PageArticleDetail(self.driver)
        detail.open_url(f"/article/{aid}")
        detail.wait_for_page_ready()
        t1 = db_query.read_time(c.login_user, aid)
        assert t1 is not None, "浏览后应记录阅读历史"
        time.sleep(1.1)  # 秒级时间戳，保证可区分
        detail.open_url(f"/article/{aid}")
        detail.wait_for_page_ready()
        t2 = db_query.read_time(c.login_user, aid)
        assert t2 is not None and t2 > t1,             f"重复浏览后阅读时间应更新: {t1} -> {t2}"

    def test_not_login_no_history_flow(self):
        """YW-YDLS-003: 未登录不记录历史"""
        c = _c("YW-YDLS-003")
        before_total = db_query.scalar("SELECT COUNT(*) FROM read_history")
        # 未登录浏览文章
        self.driver.delete_all_cookies()
        detail = PageArticleDetail(self.driver)
        detail.open_url("/article/1")
        detail.wait_for_page_ready()
        after_total = db_query.scalar("SELECT COUNT(*) FROM read_history")
        assert after_total == before_total,             f"未登录浏览不应记录阅读历史: 全表 {before_total}->{after_total}"
        # 历史页仍应要求登录
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
