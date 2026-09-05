from selenium.webdriver.common.by import By
from base import BasePage
import allure


class PageAbout(BasePage):
    """关于页面类"""

    page_path = '/about'

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 顶部Banner元素 ====================
        self.hero_title = (By.CSS_SELECTOR, ".hero-title")
        self.hero_subtitle = (By.CSS_SELECTOR, ".hero-subtitle")

        # ==================== 数据统计元素 ====================
        self.stat_cards = (By.CSS_SELECTOR, ".stat-card")
        self.stat_numbers = (By.CSS_SELECTOR, ".stat-number")
        self.stat_labels = (By.CSS_SELECTOR, ".stat-label")

        # ==================== 平台特色元素 ====================
        self.feature_items = (By.CSS_SELECTOR, ".feature-item")

        # ==================== 技术栈元素 ====================
        self.tech_tags = (By.CSS_SELECTOR, ".tech-tag")

        # ==================== 联系方式元素 ====================
        self.contact_items = (By.CSS_SELECTOR, ".contact-item")
        self.github_link = (By.CSS_SELECTOR, ".contact-item a")
    def get_hero_title(self):
        """获取Banner标题"""
        return self.get_text(self.hero_title)

    def get_hero_subtitle(self):
        """获取Banner副标题"""
        return self.get_text(self.hero_subtitle)

    # ==================== 数据统计操作 ====================

    def get_stat_number_by_label(self, label):
        """根据标签获取统计数值（如 '注册用户'、'原创文章'）"""
        locator = (By.XPATH, f'//div[@class="stat-label" and text()="{label}"]/preceding-sibling::div[@class="stat-number"]')
        return self.get_text(locator)

    def get_all_stats(self):
        """获取所有统计数据，返回 {标签: 数值} 字典"""
        labels = [el.text for el in self.find_all(self.stat_labels)]
        numbers = [el.text for el in self.find_all(self.stat_numbers)]
        return dict(zip(labels, numbers))

    # ==================== 平台特色操作 ====================

    def get_feature_names(self):
        """获取所有特色功能名称"""
        locator = (By.CSS_SELECTOR, ".feature-item h3")
        return [el.text for el in self.find_all(locator)]

    # ==================== 技术栈操作 ====================

    def get_tech_tags(self):
        """获取所有技术栈标签"""
        return [el.text for el in self.find_all(self.tech_tags)]

    # ==================== 联系方式操作 ====================

    def get_contact_texts(self):
        """获取所有联系方式文本"""
        return [el.text.strip() for el in self.find_all(self.contact_items)]

    @allure.step("点击GitHub链接")
    def click_github_link(self):
        """点击GitHub链接"""
        self.click(self.github_link)
if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    ap = PageAbout(DriverManager.get_driver())
    ap.open_url()
    print("Banner标题:", ap.get_hero_title())
    print("Banner副标题:", ap.get_hero_subtitle())
    print("数据统计:", ap.get_all_stats())
    print("平台特色:", ap.get_feature_names())
    print("技术栈:", ap.get_tech_tags())
    print("联系方式:", ap.get_contact_texts())
