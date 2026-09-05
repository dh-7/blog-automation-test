from selenium.webdriver.common.by import By
from base import BasePage
import allure


class PageFavorite(BasePage):
    """我的收藏页面类"""

    page_path = '/profile/favorites'

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 收藏列表元素 ====================
        self.favorite_items = (By.CSS_SELECTOR, ".article-item")
        self.article_title = (By.CSS_SELECTOR, ".article-title")
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")
        # Profile.vue 中取消收藏按钮是 <el-button>，无 .unfavorite-btn class
        self.unfavorite_btn = (By.XPATH, '//div[contains(@class,"article-actions")]//button[contains(.,"取消收藏")]')
    def get_favorite_count(self):
        """获取收藏数量"""
        return len(self.find_all(self.favorite_items))

    def get_article_titles(self):
        """获取所有收藏文章标题"""
        return [el.text for el in self.find_all(self.article_title)]

    @allure.step("点击取消收藏")
    def click_unfavorite(self, index):
        """点击第N篇文章的取消收藏按钮（从0开始）"""
        items = self.find_all(self.unfavorite_btn)
        items[index].click()

    def is_empty(self):
        """判断收藏列表是否为空"""
        return self.is_displayed(self.empty_state)

    @allure.step("点击收藏文章")
    def click_article(self, index):
        """点击第N篇收藏文章"""
        items = self.find_all(self.favorite_items)
        items[index].click()
if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    fp = PageFavorite(DriverManager.get_driver())
    fp.open_url()
    print("收藏数:", fp.get_favorite_count())
    print("收藏文章:", fp.get_article_titles())
