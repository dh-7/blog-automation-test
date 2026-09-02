from selenium.webdriver.common.by import By
from base import BasePage


class PageHistory(BasePage):
    """浏览历史页面类"""

    page_path = '/profile/history'

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 历史列表元素 ====================
        self.history_items = (By.CSS_SELECTOR, ".article-item")
        self.article_title = (By.CSS_SELECTOR, ".article-title")
        self.read_time = (By.CSS_SELECTOR, ".read-time")
        self.delete_btn = (By.XPATH, './/button[contains(.,"删除")]')
        self.clear_all_btn = (By.XPATH, '//button[contains(.,"清空历史")]')
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")
    def get_history_count(self):
        """获取历史记录数量"""
        return len(self.find_all(self.history_items))

    def get_article_titles(self):
        """获取所有历史文章标题"""
        return [el.text for el in self.find_all(self.article_title)]

    def click_delete(self, index):
        """点击第N条历史记录的删除按钮（从0开始）"""
        items = self.find_all(self.delete_btn)
        items[index].click()
        self.confirm_dialog()

    def find_history_index_by_title(self, title):
        """按标题查找历史记录下标，未找到返回 -1（模糊匹配）

        用于数据源驱动的删除：定位到指定文章对应的历史记录。
        """
        for i, t in enumerate(self.get_article_titles()):
            if title in t:
                return i
        return -1

    def click_delete_by_title(self, title):
        """按标题删除对应历史记录（数据源驱动）

        定位不到指定标题时直接断言失败，避免静默删错记录。
        """
        idx = self.find_history_index_by_title(title)
        assert idx >= 0, f"历史记录中未找到标题: {title}"
        self.click_delete(idx)

    def click_clear_all(self):
        """点击清空全部按钮"""
        self.click(self.clear_all_btn)
        self.confirm_dialog()

    def is_empty(self):
        """判断历史记录是否为空"""
        return self.is_displayed(self.empty_state)

    def get_read_time(self, index):
        """获取第N条记录的阅读时间"""
        items = self.find_all(self.read_time)
        return items[index].text
if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    hp = PageHistory(DriverManager.get_driver())
    hp.open_url()
    print("历史记录数:", hp.get_history_count())
    print("文章标题:", hp.get_article_titles())
