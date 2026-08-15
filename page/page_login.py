from selenium.webdriver.common.by import By
import time
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager


class PageLogin(BasePage):
    """登录页面类"""

    def __init__(self, driver):
        """初始化方法"""
        # 获取driver对象
        # driver = DriverTools.get_driver()
        super().__init__(driver)
        # 设置页面实例属性
        self.username = (By.CSS_SELECTOR,'input[placeholder="请输入用户名"]')
        self.password = (By.XPATH,'//input[@placeholder="请输入密码"]')
        # self.login_button = (By.XPATH,'//button[@type="button"]')
        self.login_button = (By.XPATH,'//button//span[text()="登录"]')

        # 成功结果元素属性
        self.success_result = (By.XPATH, '//*[@id="app"]/div/header/div/div/a/text()')
        # 失败结果元素属性 #err > span
        self.fail_result = (By.CSS_SELECTOR, "#message_10 > p")


    def open_url(self):
        """打开网页"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/login")


    def login(self, username, password):
        """登录"""
        # 输入账号
        self.input(self.username, username)
        # 输入密码
        self.input(self.password, password)
        # 点击登录
        self.click(self.login_button)
        time.sleep(2)


    def get_success_result(self):
        """获取成功结果"""
        return self.find(self.success_result).text

    def get_fail_result(self):
        """获取失败结果"""
        return self.find(self.fail_result).text


if __name__ == '__main__':
    # 创建对象
    lg = PageLogin(DriverManager.get_driver())
    # 打开页面
    lg.open_url()
    # 操作登录
    lg.login("zhangsan","123456")