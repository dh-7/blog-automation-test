from selenium.webdriver.common.by import By
from base import BasePage


class PageAuthor(BasePage):
    """作者主页页面类"""

    page_path = '/author/${author_id}'

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 作者信息元素 ====================
        self.author_name = (By.CSS_SELECTOR, ".author-name")
        self.author_avatar = (By.CSS_SELECTOR, ".author-avatar")
        self.author_bio = (By.CSS_SELECTOR, ".author-bio")
        self.article_count = (By.CSS_SELECTOR, ".article-count")
        self.register_time = (By.CSS_SELECTOR, ".register-time")

        # ==================== 文章列表元素 ====================
        self.article_items = (By.CSS_SELECTOR, ".article-item")
        self.article_title = (By.CSS_SELECTOR, ".article-title")
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")
    def get_author_name(self):
        """获取作者名称"""
        return self.get_text(self.author_name)

    def get_author_bio(self):
        """获取作者简介"""
        return self.get_text(self.author_bio)

    def get_article_count(self):
        """获取作者文章数"""
        return self.get_text(self.article_count)

    # ==================== 文章列表操作 ====================

    def get_article_titles(self):
        """获取作者所有文章标题"""
        return [el.text for el in self.find_all(self.article_title)]

    def click_article(self, index):
        """点击第N篇文章（从0开始）"""
        items = self.find_all(self.article_items)
        items[index].click()

    def is_empty(self):
        """判断文章列表是否为空"""
        return self.is_displayed(self.empty_state)
if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    ap = PageAuthor(DriverManager.get_driver())
    ap.open_url('/author/1')
    print("作者名称:", ap.get_author_name())
    print("作者简介:", ap.get_author_bio())
    print("文章数:", ap.get_article_count())
    print("文章列表:", ap.get_article_titles())
