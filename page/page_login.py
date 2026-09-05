from selenium.webdriver.common.by import By
import allure
from base import BasePage


class PageLogin(BasePage):
    """登录页面类 — 元素定位 + 原子操作"""

    page_path = '/login'

    def __init__(self, driver):
        super().__init__(driver)
        # 页面元素
        self.username = (By.CSS_SELECTOR, 'input[placeholder="请输入用户名"]')
        self.password = (By.XPATH, '//input[@placeholder="请输入密码"]')
        self.login_button = (By.XPATH, '//button//span[text()="登录"]')
        self.success_result = (By.XPATH, '//a[contains(@href,"/write")]')
        self.fail_result = (By.CSS_SELECTOR, ".el-message--error .el-message__content")

    @allure.step("输入用户名")
    def input_username(self, username):
        """输入用户名"""
        self.input(self.username, username)

    @allure.step("输入密码")
    def input_password(self, password):
        """输入密码"""
        self.input(self.password, password)

    @allure.step("点击登录按钮")
    def click_login_button(self):
        """点击登录按钮"""
        self.click(self.login_button)

    @allure.step("等待登录成功")
    def wait_for_login_success(self, timeout=None):
        """等待登录成功：URL 离开 /login（前端登录成功会路由跳转）

        登录失败（如 v-model 未同步导致校验不通过）会停留在登录页，
        此时等待超时并抛出异常，让失败即时暴露而不是静默继续。
        """
        from selenium.webdriver.support.ui import WebDriverWait
        t = timeout or self.timeout
        WebDriverWait(self.driver, t).until(
            lambda d: "/login" not in d.current_url
        )
        self.wait_for_page_ready()

    def get_success_result(self):
        """获取成功结果文本"""
        return self.find(self.success_result).text

    def get_fail_result(self):
        """获取失败结果文本"""
        return self.find(self.fail_result).text

    # ==================== 业务方法 ====================

    @allure.step("登录 {1}")
    def login(self, username, password, timeout=None):
        """完整登录流程：打开登录页 → 填写表单 → 点击登录 → 等待跳转成功

        关键：点击登录后必须等待 URL 离开 /login（前端登录接口返回且 token
        写入后才路由跳转），否则立即导航会导致竞态——页面仍停留在登录页，
        后续元素定位全部超时。
        """
        self.open_url()
        self.input_username(username)
        self.input_password(password)
        self.click_login_button()
        self.wait_for_login_success(timeout)

    @allure.step("登录并跳转")
    def login_and_navigate(self, username, password, target_url):
        """登录后跳转到指定URL"""
        from utils.config import Config
        base_url = Config.get('env', 'base_url')
        self.login(username, password)
        self.driver.get(base_url.rstrip('/') + target_url)
        self.wait_for_page_ready()
