import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from utils.config import Config


class DriverManager:
    """浏览器驱动管理 — 单例模式，支持 config 字典配置"""

    _driver = None

    @classmethod
    def get_driver(cls, config=None):
        """获取驱动实例，不存在则创建"""
        if cls._driver is None:
            # 未传 config 时自动加载项目根目录的 config.yaml
            if config is None:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config = Config.load(os.path.join(project_root, "config.yaml"))
            cfg = config.get("browser", {})
            options = Options()

            # Chrome 路径
            chrome_path = cfg.get("chrome_path")
            if chrome_path:
                options.binary_location = chrome_path

            # 无头模式
            if cfg.get("headless"):
                options.add_argument("--headless")

            options.add_argument("--start-maximized")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")

            # 驱动路径（优先配置文件，其次 PATH 查找）
            driver_path = cfg.get("driver_path") or shutil.which("chromedriver")
            service = Service(executable_path=driver_path)
            cls._driver = webdriver.Chrome(service=service, options=options)

            # 隐式等待
            cls._driver.implicitly_wait(cfg.get("implicit_wait", 10))

        return cls._driver

    @classmethod
    def quit_driver(cls):
        """关闭驱动"""
        if cls._driver:
            cls._driver.quit()
            cls._driver = None

    @classmethod
    def restart_driver(cls, config=None):
        """重启驱动"""
        cls.quit_driver()
        return cls.get_driver(config)
