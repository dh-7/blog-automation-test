from selenium.webdriver.common.by import By
import time
from base import BasePage
from utils.config import Config


class PageRegister(BasePage):
    """注册页面类"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # 页面元素定位
        self.username = (By.CSS_SELECTOR, "input[placeholder='3-20位字符']")
        self.nickname = (By.CSS_SELECTOR, "input[placeholder='选填，展示给其他用户']")
        self.email = (By.CSS_SELECTOR, "input[placeholder='选填，用于找回密码']")
        self.password = (By.CSS_SELECTOR, "input[placeholder='6-20位']")
        self.confirm_password = (By.CSS_SELECTOR, "input[placeholder='再次输入密码']")
        self.register_button = (By.XPATH, '//button//span[text()="注册"]')
        self.login_link = (By.XPATH, '//a[text()="去登录"]')
        # 成功结果元素定位
        self.success_result = (By.CSS_SELECTOR, "#message_10 > p")
        # 失败结果元素定位
        self.fail_result = (By.CSS_SELECTOR, ".el-form-item__error")

    def open_url(self):
        """打开注册页面"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/register")

    def register(self, username, nickname, email, password, confirm_password):
        """注册操作"""
        self.input(self.username, username)
        self.input(self.nickname, nickname)
        self.input(self.email, email)
        self.input(self.password, password)
        self.input(self.confirm_password, confirm_password)
        self.click(self.register_button)
        time.sleep(2)

    def get_success_result(self):
        """获取成功结果"""
        return self.find(self.success_result).text

    def get_fail_result(self):
        """获取失败结果"""
        return self.find(self.fail_result).text

    def click_login_link(self):
        """点击去登录链接"""
        self.click(self.login_link)


if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    rg = PageRegister(DriverManager.get_driver())
    rg.open_url()
    rg.register("testuser", "测试昵称", "test@qq.com", "123456", "123456")
