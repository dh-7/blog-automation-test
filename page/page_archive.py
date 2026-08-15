from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
from page import *

class PageArchive(BasePage):
    """归档页面类"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 页面信息元素 ====================
        self.page_title = (By.CSS_SELECTOR, ".page-title")
        self.page_desc = (By.CSS_SELECTOR, ".page-desc")
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")

        # ==================== 归档列表元素 ====================
        self.year_groups = (By.CSS_SELECTOR, ".year-group")
        self.year_titles = (By.CSS_SELECTOR, ".year-title")
        self.month_items = (By.CSS_SELECTOR, ".month-item")
        self.month_names = (By.CSS_SELECTOR, ".month-name")
        self.month_counts = (By.CSS_SELECTOR, ".month-count")
        self.month_articles = (By.CSS_SELECTOR, ".month-articles")
        self.article_items = (By.CSS_SELECTOR, ".article-item")
        self.article_titles = (By.CSS_SELECTOR, ".article-title")

        # ==================== 侧边栏元素 ====================
        self.category_items = (By.CSS_SELECTOR, ".category-item")
        self.category_names = (By.CSS_SELECTOR, ".category-name")
        self.hot_article_items = (By.CSS_SELECTOR, ".hot-article-item")
        self.hot_titles = (By.CSS_SELECTOR, ".hot-title")

    def open_url(self):
        """打开归档页面"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/archive")

    def login_then_open(self, username, password):
        """先登录再打开归档页"""
        import time
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.login(username, password)
        time.sleep(1)
        self.open_url()
        time.sleep(1)

    # ==================== 页面信息操作 ====================

    def get_page_title(self):
        """获取页面标题"""
        return self.get_text(self.page_title)

    def is_empty(self):
        """判断是否有归档文章"""
        return self.is_displayed(self.empty_state)

    # ==================== 归档列表操作 ====================

    def get_year_titles(self):
        """获取所有年份标题"""
        return [el.text for el in self.find_all(self.year_titles)]

    def get_month_names(self):
        """获取所有月份名称"""
        return [el.text.strip() for el in self.find_all(self.month_names)]

    def click_month_by_name(self, name):
        """点击指定月份展开/收起（如 '07月'）"""
        locator = (By.XPATH, f'//span[@class="month-name" and text()="{name}"]/ancestor::div[@class="month-item"]')
        self.click(locator)

    def get_month_article_titles(self):
        """获取当前展开月份下的文章标题列表"""
        els = self.find_all(self.article_titles)
        return [el.text for el in els]

    def click_month_article_by_title(self, title):
        """点击展开月份下的指定文章"""
        locator = (By.XPATH, f'//div[@class="month-articles"]//span[@class="article-title" and text()="{title}"]/ancestor::div[@class="article-item"]')
        self.click(locator)

    # ==================== 侧边栏操作 ====================

    def get_category_names(self):
        """获取侧边栏分类名称"""
        return [el.text.strip() for el in self.find_all(self.category_names)]

    def click_category_by_name(self, name):
        """点击侧边栏指定分类"""
        locator = (By.XPATH, f'//div[@class="category-item"]//span[@class="category-name" and contains(text(),"{name}")]')
        self.click(locator)

    def get_hot_article_titles(self):
        """获取热门文章标题列表"""
        return [el.text.strip() for el in self.find_all(self.hot_titles)]

    def click_hot_article_by_index(self, index):
        """点击第N篇热门文章（从0开始）"""
        items = self.find_all(self.hot_article_items)
        items[index].click()


if __name__ == '__main__':
    from utils.driver_manager import DriverManager

    ap = PageArchive(DriverManager.get_driver())
    ap.login_then_open("zhangsan", "123456")
    print("页面标题:", ap.get_page_title())
    print("年份列表:", ap.get_year_titles())
    print("月份列表:", ap.get_month_names())
    print("分类列表:", ap.get_category_names())
    print("热门文章:", ap.get_hot_article_titles())
