from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager
import allure


class PageCategory(BasePage):
    """分类页面类"""

    page_path = '/category'

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 页面标题区域 ====================
        self.category_title = (By.CSS_SELECTOR, ".category-title")
        self.category_desc = (By.CSS_SELECTOR, ".category-desc")

        # ==================== 标签筛选栏 ====================
        self.filter_bar = (By.CSS_SELECTOR, ".filter-bar")
        self.clear_filter_btn = (By.XPATH, '//div[@class="filter-bar"]//button')

        # ==================== 文章列表元素 ====================
        self.article_cards = (By.CSS_SELECTOR, ".article-card")
        self.article_title = (By.CSS_SELECTOR, ".article-title")
        self.article_summary = (By.CSS_SELECTOR, ".article-summary")
        self.article_meta = (By.CSS_SELECTOR, ".article-meta")
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")

        # ==================== 侧边栏-分类列表 ====================
        self.category_items = (By.CSS_SELECTOR, ".category-item")
        self.category_names = (By.CSS_SELECTOR, ".category-name")
        self.category_counts = (By.CSS_SELECTOR, ".category-count")
        self.active_category = (By.CSS_SELECTOR, ".category-item.active")

        # ==================== 侧边栏-标签云 ====================
        self.tag_items = (By.CSS_SELECTOR, ".tag-item")
        self.active_tag = (By.CSS_SELECTOR, ".tag-item.active")
    @allure.step("打开分类页面")
    def open_category_by_id(self, category_id):
        """打开指定分类页面"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/category/{category_id}")

    # ==================== 页面标题区域操作 ====================

    def get_page_title(self):
        """获取页面标题"""
        return self.get_text(self.category_title)

    def get_category_description(self):
        """获取分类描述"""
        return self.get_text(self.category_desc)

    # ==================== 标签筛选栏操作 ====================

    def is_filter_bar_visible(self):
        """标签筛选栏是否可见"""
        return self.is_displayed(self.filter_bar)

    def get_filter_text(self):
        """获取筛选栏文本"""
        return self.get_text(self.filter_bar)

    @allure.step("点击清除筛选")
    def click_clear_filter(self):
        """点击清除筛选按钮"""
        self.click(self.clear_filter_btn)

    # ==================== 文章列表操作 ====================

    def get_article_cards(self):
        """获取所有文章卡片元素列表"""
        return self.find_all(self.article_cards)

    def get_article_count(self):
        """获取当前文章数量"""
        return len(self.get_article_cards())

    @allure.step("点击文章")
    def click_article_by_index(self, index):
        """点击第N篇文章（从0开始）"""
        cards = self.get_article_cards()
        cards[index].click()

    @allure.step("点击文章标题")
    def click_article_by_title(self, title):
        """点击指定标题的文章"""
        locator = (By.XPATH,
                   f'//h2[@class="article-title" and text()="{title}"]'
                   f'/ancestor::div[@class="article-card"]')
        self.click(locator)

    def get_article_title_by_index(self, index):
        """获取第N篇文章标题"""
        titles = self.find_all(self.article_title)
        return titles[index].text

    def get_all_article_titles(self):
        """获取所有文章标题"""
        return [el.text for el in self.find_all(self.article_title)]

    def is_empty(self):
        """判断文章列表是否为空"""
        return self.is_displayed(self.empty_state)

    # ==================== 侧边栏-分类操作 ====================

    def get_category_names(self):
        """获取所有分类名称"""
        return [el.text.strip() for el in self.find_all(self.category_names)]

    def get_category_count_by_index(self, index):
        """获取第N个分类的文章数"""
        counts = self.find_all(self.category_counts)
        return counts[index].text.strip()

    def get_active_category_name(self):
        """获取当前选中分类名称"""
        return self.get_text(self.active_category)

    @allure.step("点击分类")
    def click_category_by_name(self, name):
        """点击指定分类"""
        locator = (By.XPATH,
                   f'//div[@class="category-item"]'
                   f'//span[@class="category-name" and contains(text(),"{name}")]')
        self.click(locator)

    @allure.step("点击分类索引")
    def click_category_by_index(self, index):
        """点击第N个分类（从0开始）"""
        items = self.find_all(self.category_items)
        items[index].click()

    # ==================== 侧边栏-标签云操作 ====================

    def get_tag_names(self):
        """获取所有标签名称"""
        return [el.text.strip() for el in self.find_all(self.tag_items)]

    def get_active_tag_name(self):
        """获取当前选中标签名称"""
        return self.get_text(self.active_tag).strip()

    @allure.step("点击标签")
    def click_tag_by_name(self, name):
        """点击指定标签"""
        locator = (By.XPATH,
                   f'//div[@class="tag-cloud"]'
                   f'/span[@class="tag-item" and normalize-space(text())="{name}"]')
        self.click(locator)

    @allure.step("点击标签索引")
    def click_tag_by_index(self, index):
        """点击第N个标签（从0开始）"""
        tags = self.find_all(self.tag_items)
        tags[index].click()
if __name__ == '__main__':
    pg = PageCategory(DriverManager.get_driver())
    pg.open_url()
    print("页面标题:", pg.get_page_title())
    print("分类列表:", pg.get_category_names())
    print("标签列表:", pg.get_tag_names())
    print("文章数量:", pg.get_article_count())
    print("文章标题:", pg.get_all_article_titles())
