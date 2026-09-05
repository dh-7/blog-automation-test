from selenium.webdriver.common.by import By
from base import BasePage
import allure


class PageAdminDashboard(BasePage):
    """管理员仪表盘页面类 — 元素定位 + 原子操作"""

    page_path = '/admin'

    def __init__(self, driver):
        super().__init__(driver)
        # 统计卡片
        self.stat_cards = (By.CSS_SELECTOR, ".stat-card")
        self.stat_numbers = (By.CSS_SELECTOR, ".stat-number")
        self.stat_labels = (By.CSS_SELECTOR, ".stat-label")
        # 快捷操作按钮
        self.btn_manage_articles = (By.XPATH, '//button//span[text()="管理文章"]')
        self.btn_manage_users = (By.XPATH, '//button//span[text()="管理用户"]')

        self.btn_manage_comments = (By.XPATH, '//button//span[text()="管理评论"]')
        self.btn_visit_frontend = (By.XPATH, '//button//span[text()="访问前台"]')
        # 侧边栏导航
        self.menu_dashboard = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[text()="仪表盘"]')
        self.menu_articles = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[text()="文章管理"]')
        self.menu_users = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[text()="用户管理"]')
        self.menu_comments = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[text()="评论管理"]')
        # 页头
        self.page_title = (By.CSS_SELECTOR, ".admin-header h2")
        self.user_display = (By.CSS_SELECTOR, ".admin-user span")
        self.logout_button = (By.XPATH, '//div[@class="admin-user"]//button')
    def get_stat_numbers(self):
        return [el.text for el in self.find_all(self.stat_numbers)]

    def get_stat_labels(self):
        return [el.text for el in self.find_all(self.stat_labels)]

    def get_stat_by_label(self, label):
        locator = (By.XPATH,
                   f'//div[@class="stat-label" and text()="{label}"]'
                   f'/preceding-sibling::div[@class="stat-number"]')
        return self.get_text(locator)

    # ==================== 快捷操作 ====================

    @allure.step("点击管理文章")
    def click_manage_articles(self):
        self.click(self.btn_manage_articles)

    @allure.step("点击管理用户")
    def click_manage_users(self):
        self.click(self.btn_manage_users)

    @allure.step("点击管理评论")
    def click_manage_comments(self):
        self.click(self.btn_manage_comments)

    @allure.step("点击访问前台")
    def click_visit_frontend(self):
        self.click(self.btn_visit_frontend)

    # ==================== 侧边栏导航 ====================

    @allure.step("点击仪表盘菜单")
    def click_menu_dashboard(self):
        self.click(self.menu_dashboard)

    @allure.step("点击文章管理菜单")
    def click_menu_articles(self):
        self.click(self.menu_articles)

    @allure.step("点击用户管理菜单")
    def click_menu_users(self):
        self.click(self.menu_users)

    @allure.step("点击评论管理菜单")
    def click_menu_comments(self):
        self.click(self.menu_comments)

    # ==================== 页头操作 ====================

    def get_page_title(self):
        return self.get_text(self.page_title)

    def get_current_user(self):
        return self.get_text(self.user_display)

    @allure.step("点击退出登录")
    def click_logout(self):
        self.click(self.logout_button)