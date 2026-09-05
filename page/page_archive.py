from selenium.webdriver.common.by import By
from base import BasePage
import allure


class PageArchive(BasePage):
    """归档页面类 — 元素定位 + 原子操作"""

    page_path = '/archive'

    def __init__(self, driver):
        super().__init__(driver)
        # 页面信息
        self.page_title = (By.CSS_SELECTOR, ".page-title")
        self.page_desc = (By.CSS_SELECTOR, ".page-desc")
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")
        # 归档列表
        self.year_groups = (By.CSS_SELECTOR, ".year-group")
        self.year_titles = (By.CSS_SELECTOR, ".year-title")
        self.month_items = (By.CSS_SELECTOR, ".month-item")
        self.month_names = (By.CSS_SELECTOR, ".month-name")
        self.month_counts = (By.CSS_SELECTOR, ".month-count")
        self.month_articles = (By.CSS_SELECTOR, ".month-articles")
        self.article_items = (By.CSS_SELECTOR, ".article-item")
        self.article_titles = (By.CSS_SELECTOR, ".article-title")
        self.article_dates = (By.CSS_SELECTOR, ".article-date")
        # 侧边栏
        self.category_items = (By.CSS_SELECTOR, ".category-item")
        self.category_names = (By.CSS_SELECTOR, ".category-name")
        self.hot_article_items = (By.CSS_SELECTOR, ".hot-article-item")
        self.hot_titles = (By.CSS_SELECTOR, ".hot-title")

    def get_page_title(self):
        return self.get_text(self.page_title)

    def is_empty(self):
        return self.is_displayed(self.empty_state)

    # ==================== 归档列表 ====================

    def get_year_titles(self):
        return [el.text for el in self.find_all(self.year_titles)]

    def get_month_names(self):
        return [el.text.strip() for el in self.find_all(self.month_names)]

    @allure.step("点击月份")
    def click_month_by_name(self, name):
        locator = (By.XPATH, f'//span[@class="month-name" and text()="{name}"]/ancestor::div[@class="month-item"]')
        self.click(locator)

    def get_month_article_titles(self):
        els = self.find_all(self.article_titles)
        return [el.text for el in els]

    def get_month_article_dates(self):
        """获取展开月份下所有文章的日期（日），如 ['27日', '28日']"""
        els = self.find_all(self.article_dates)
        return [el.text.strip() for el in els]

    @allure.step("点击归档文章")
    def click_month_article_by_title(self, title):
        locator = (By.XPATH, f'//div[@class="month-articles"]//span[@class="article-title" and text()="{title}"]/ancestor::div[@class="article-item"]')
        self.click(locator)

    # ==================== 侧边栏 ====================

    def get_category_names(self):
        return [el.text.strip() for el in self.find_all(self.category_names)]

    @allure.step("点击分类")
    def click_category_by_name(self, name):
        locator = (By.XPATH, f'//div[@class="category-item"]//span[@class="category-name" and contains(text(),"{name}")]')
        self.click(locator)

    def get_hot_article_titles(self):
        return [el.text.strip() for el in self.find_all(self.hot_titles)]

    @allure.step("点击热门文章")
    def click_hot_article_by_index(self, index):
        items = self.find_all(self.hot_article_items)
        items[index].click()
