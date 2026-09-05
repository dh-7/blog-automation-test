from selenium.webdriver.common.by import By
import allure
from base import BasePage


class PageRegister(BasePage):
    """注册页面类 — 元素定位 + 原子操作"""

    page_path = '/register'

    def __init__(self, driver):
        super().__init__(driver)
        # 页面元素
        self.username = (By.CSS_SELECTOR, "input[placeholder='3-20位字符']")
        self.nickname = (By.CSS_SELECTOR, "input[placeholder='选填，展示给其他用户']")
        self.email = (By.CSS_SELECTOR, "input[placeholder='选填，用于找回密码']")
        self.password = (By.CSS_SELECTOR, "input[placeholder='6-20位']")
        self.confirm_password = (By.CSS_SELECTOR, "input[placeholder='再次输入密码']")
        self.register_button = (By.XPATH, '//button//span[text()="注册"]')
        self.login_link = (By.XPATH, '//a[text()="去登录"]')
        self.success_result = (By.CSS_SELECTOR, ".el-message--success .el-message__content")
        self.fail_result = (By.CSS_SELECTOR, ".el-message--error .el-message__content")
        self.form_error = (By.CSS_SELECTOR, ".el-form-item__error")

    @allure.step("输入用户名")
    def input_username(self, username):
        """输入用户名"""
        self.input(self.username, username)

    @allure.step("输入昵称")
    def input_nickname(self, nickname):
        """输入昵称"""
        self.input(self.nickname, nickname)

    @allure.step("输入邮箱")
    def input_email(self, email):
        """输入邮箱"""
        self.input(self.email, email)

    @allure.step("输入密码")
    def input_password(self, password):
        """输入密码"""
        self.input(self.password, password)

    @allure.step("输入确认密码")
    def input_confirm_password(self, password):
        """输入确认密码"""
        self.input(self.confirm_password, password)

    @allure.step("点击注册按钮")
    def click_register_button(self):
        """点击注册按钮"""
        self.click(self.register_button)

    @allure.step("点击去登录")
    def click_login_link(self):
        """点击去登录链接"""
        self.click(self.login_link)

    def get_success_result(self):
        """获取成功结果文本"""
        return self.find(self.success_result).text

    def get_fail_result(self):
        """获取失败结果文本（弹窗消息，如用户名已存在）"""
        return self.find(self.fail_result).text

    def get_form_error(self):
        """获取表单验证错误文本（如密码不一致）"""
        return self.find(self.form_error).text
