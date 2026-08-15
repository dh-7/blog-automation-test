from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager


class PageAdminDashboard(BasePage):
    """管理员仪表盘页面类（Dashboard.vue，路由 /admin）"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 统计卡片 ====================
        self.stat_cards = (By.CSS_SELECTOR, ".stat-card")
        self.stat_numbers = (By.CSS_SELECTOR, ".stat-number")
        self.stat_labels = (By.CSS_SELECTOR, ".stat-label")

        # ==================== 快捷操作按钮 ====================
        self.btn_manage_articles = (By.XPATH, '//button//span[text()="管理文章"]')
        self.btn_manage_users = (By.XPATH, '//button//span[text()="管理用户"]')
        self.btn_manage_comments = (By.XPATH, '//button//span[text()="管理评论"]')
        self.btn_visit_frontend = (By.XPATH, '//button//span[text()="访问前台"]')

        # ==================== 侧边栏导航 ====================
        self.menu_dashboard = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[text()="仪表盘"]')
        self.menu_articles = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[text()="文章管理"]')
        self.menu_users = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[text()="用户管理"]')
        self.menu_comments = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[text()="评论管理"]')

        # ==================== 页头 ====================
        self.page_title = (By.CSS_SELECTOR, ".admin-header h2")
        self.user_display = (By.CSS_SELECTOR, ".admin-user span")
        self.logout_button = (By.XPATH, '//div[@class="admin-user"]//button')

    def open_url(self):
        """打开仪表盘页面（需要管理员登录）"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/admin")

    def login_then_open(self, username, password):
        """先登录再打开仪表盘"""
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.login(username, password)
        self.open_url()

    # ==================== 统计数据 ====================

    def get_stat_numbers(self):
        """获取所有统计数字（文章总数、用户总数、评论总数）"""
        return [el.text for el in self.find_all(self.stat_numbers)]

    def get_stat_labels(self):
        """获取所有统计标签文本"""
        return [el.text for el in self.find_all(self.stat_labels)]

    def get_stat_by_label(self, label):
        """根据标签获取统计数字，如 '文章总数'"""
        locator = (By.XPATH,
                   f'//div[@class="stat-label" and text()="{label}"]'
                   f'/preceding-sibling::div[@class="stat-number"]')
        return self.get_text(locator)

    # ==================== 快捷操作 ====================

    def click_manage_articles(self):
        """点击管理文章"""
        self.click(self.btn_manage_articles)

    def click_manage_users(self):
        """点击管理用户"""
        self.click(self.btn_manage_users)

    def click_manage_comments(self):
        """点击管理评论"""
        self.click(self.btn_manage_comments)

    def click_visit_frontend(self):
        """点击访问前台"""
        self.click(self.btn_visit_frontend)

    # ==================== 侧边栏导航 ====================

    def click_menu_dashboard(self):
        """点击侧边栏-仪表盘"""
        self.click(self.menu_dashboard)

    def click_menu_articles(self):
        """点击侧边栏-文章管理"""
        self.click(self.menu_articles)

    def click_menu_users(self):
        """点击侧边栏-用户管理"""
        self.click(self.menu_users)

    def click_menu_comments(self):
        """点击侧边栏-评论管理"""
        self.click(self.menu_comments)

    # ==================== 页头操作 ====================

    def get_page_title(self):
        """获取页头标题"""
        return self.get_text(self.page_title)

    def get_current_user(self):
        """获取当前登录用户名"""
        return self.get_text(self.user_display)

    def click_logout(self):
        """点击退出"""
        self.click(self.logout_button)


if __name__ == '__main__':
    pg = PageAdminDashboard(DriverManager.get_driver())
    pg.login_then_open("admin", "admin123")
    print("页头标题:", pg.get_page_title())
    print("当前用户:", pg.get_current_user())
    print("统计标签:", pg.get_stat_labels())
    print("统计数字:", pg.get_stat_numbers())
