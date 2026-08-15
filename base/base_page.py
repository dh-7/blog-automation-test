import os
from datetime import datetime

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.logger import Logger

log = Logger.get_logger()


class BasePage:
    """页面操作基类 — 封装 Selenium 常用操作，所有 PageObject 继承此类"""

    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    # ==================== 元素查找 ====================

    def find(self, loc):
        """查找可见元素（显式等待）"""
        try:
            return self.wait.until(EC.visibility_of_element_located(loc))
        except Exception as e:
            log.error(f"元素定位超时: {loc} | {e}")
            raise

    def find_all(self, loc):
        """查找一组元素"""
        try:
            return self.wait.until(EC.presence_of_all_elements_located(loc))
        except Exception as e:
            log.error(f"元素组定位超时: {loc} | {e}")
            raise

    # ==================== 元素操作 ====================

    def click(self, loc):
        """点击元素"""
        self.find(loc).click()
        log.info(f"点击: {loc}")

    def input(self, loc, text):
        """输入文本（先清空再输入）"""
        el = self.find(loc)
        el.clear()
        el.send_keys(text)
        log.info(f"输入: {loc} -> {text}")

    def clear(self, loc):
        """清空输入框"""
        self.find(loc).clear()
        log.info(f"清空: {loc}")

    def get_text(self, loc):
        """获取元素可见文本"""
        text = self.find(loc).text
        log.info(f"获取文本: {loc} -> {text}")
        return text

    def get_attribute(self, loc, attr):
        """获取元素属性值"""
        val = self.find(loc).get_attribute(attr)
        log.info(f"获取属性: {loc}[{attr}] -> {val}")
        return val

    # ==================== 元素状态判断 ====================

    def is_displayed(self, loc):
        """元素是否可见"""
        try:
            return self.find(loc).is_displayed()
        except Exception:
            return False

    def is_enabled(self, loc):
        """元素是否可操作"""
        try:
            return self.find(loc).is_enabled()
        except Exception:
            return False

    def is_selected(self, loc):
        """复选框/单选框是否选中"""
        try:
            return self.find(loc).is_selected()
        except Exception:
            return False

    # ==================== 浏览器操作 ====================

    def open_url(self, url):
        """打开 URL"""
        self.driver.get(url)
        log.info(f"打开: {url}")

    def refresh(self):
        """刷新页面"""
        self.driver.refresh()
        log.info("刷新页面")

    def back(self):
        """浏览器后退"""
        self.driver.back()
        log.info("后退")

    def forward(self):
        """浏览器前进"""
        self.driver.forward()
        log.info("前进")

    def get_current_url(self):
        """获取当前 URL"""
        return self.driver.current_url

    def get_title(self):
        """获取页面标题"""
        return self.driver.title

    # ==================== 截图 ====================

    def take_screenshot(self, name=None, save_dir="report"):
        """截图保存，返回文件路径"""
        os.makedirs(save_dir, exist_ok=True)
        if name is None:
            name = f"{datetime.now():%Y%m%d_%H%M%S}"
        path = os.path.join(save_dir, f"{name}.png")
        self.driver.save_screenshot(path)
        log.info(f"截图: {path}")
        return path
