from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
import allure


class PageNotification(BasePage):
    """通知页面类"""

    page_path = '/notifications'

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 通知列表元素 ====================
        self.notification_items = (By.CSS_SELECTOR, ".notification-item")
        self.notification_content = (By.CSS_SELECTOR, ".notification-content")
        self.notification_type = (By.CSS_SELECTOR, ".notification-type")
        self.notification_time = (By.CSS_SELECTOR, ".notification-time")
        self.read_status = (By.CSS_SELECTOR, ".read-status")

        # ==================== 操作按钮元素 ====================
        self.mark_all_read = (By.XPATH, '//div[contains(@class,"notification-actions")]//button[contains(.,"全部已读")]')
        # Layout.vue 中删除按钮是 <el-button type="danger">，无 .delete-btn class
        self.delete_btn = (By.XPATH, '//div[contains(@class,"notification-meta")]//button[contains(.,"删除")]')
        self.clear_all_btn = (By.XPATH, '//div[contains(@class,"notification-actions")]//button[contains(.,"清空")]')

        # ==================== 导航栏通知元素 ====================
        self.badge = (By.CSS_SELECTOR, ".el-badge__content")
        self.notification_bell = (By.CSS_SELECTOR, ".notification-bell .el-badge")
        # 未读通知数字角标（导航栏中）
        self.nav_unread_badge = (By.CSS_SELECTOR, '.notification-bell .el-badge__content')
        # 未读蓝点（通知列表中）
        self.unread_dot = (By.CSS_SELECTOR, '.unread-dot')

    @allure.step("打开通知面板")
    def open_url(self, path=None):
        """打开通知页面"""
        base_url = Config.get("env", "base_url")
        _path = path or self.page_path
        # 通知是 Layout.vue 中的弹出面板，先打开首页再点击铃铛
        self.driver.get(base_url)
        self.wait_for_page_ready()
        self.click_bell()
        # 等待通知面板加载完成（el-popover 异步渲染 + API 请求）
        self._wait_for_panel_ready()

    # ==================== 通知列表操作 ====================

    def get_notification_count(self):
        """获取通知数量；无通知（空列表）时返回 0，不抛异常

        注意：不能用 find_all（presence_of_all_elements_located 要求至少匹配 1 个元素，
        空列表会抛 TimeoutException）。直接 find_elements 即时返回实际数量。
        """
        return len(self.driver.find_elements(*self.notification_items))

    def get_notification_text(self, index):
        """获取第N条通知内容（从0开始）"""
        items = self.find_all(self.notification_content)
        return items[index].text

    @allure.step("点击通知")
    def click_notification(self, index):
        """点击第N条通知"""
        items = self.find_all(self.notification_items)
        items[index].click()

    # ==================== 批量操作 ====================

    @allure.step("点击全部已读")
    def click_mark_all_read(self):
        """点击全部标记已读"""
        self.click(self.mark_all_read)

    @allure.step("点击删除通知")
    def click_delete(self, index):
        """点击第N条通知的删除按钮"""
        items = self.find_all(self.delete_btn)
        items[index].click()

    def has_clear_all_button(self, timeout=3):
        """判断"清空"按钮是否可见（前端仅在有通知时渲染该按钮，见 Layout.vue v-if）

        等待面板加载完成（清空按钮随通知列表异步渲染），避免加载完成前误判。
        """
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_elements(*self.clear_all_btn)
                and d.find_elements(*self.clear_all_btn)[0].is_displayed()
            )
            return True
        except Exception:
            return False

    @allure.step("点击清空通知")
    def click_clear_all(self):
        """点击清空全部按钮；按钮不存在（无通知可清空）时返回 False"""
        if not self.has_clear_all_button():
            return False
        self.click(self.clear_all_btn)
        return True

    # ==================== 通知角标操作 ====================

    def get_badge_count(self):
        """获取通知角标数字"""
        return self.get_text(self.badge)

    @allure.step("点击铃铛图标")
    def click_bell(self):
        """点击导航栏铃铛图标"""
        self.click(self.notification_bell)

    def has_unread(self):
        """判断是否有未读通知"""
        return self.is_displayed(self.badge)

    def wait_for_count(self, expected_count, timeout=None):
        """等待通知数量变为期望值（如清空后变为 0）；超时返回 False"""
        from selenium.webdriver.support.ui import WebDriverWait
        t = timeout if timeout is not None else self.timeout
        try:
            WebDriverWait(self.driver, t).until(
                lambda d: len(d.find_elements(*self.notification_items)) == expected_count
            )
            return True
        except Exception:
            return False

    def _wait_for_panel_ready(self, timeout=None):
        """等待通知面板内容加载完成"""
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        t = timeout if timeout is not None else self.timeout
        # 先等面板 DOM 出现
        panel_loc = (By.CSS_SELECTOR, ".notification-panel")
        try:
            WebDriverWait(self.driver, t).until(
                EC.visibility_of_element_located(panel_loc)
            )
        except Exception:
            pass
        # 等待面板内容加载完成（替代 sleep）
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, ".notification-panel .notification-item")
                   or d.find_elements(By.CSS_SELECTOR, ".notification-panel .empty-text")
                   or d.find_elements(By.CSS_SELECTOR, ".notification-panel .el-empty")
            )
        except Exception:
            pass
if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    np = PageNotification(DriverManager.get_driver())
    np.open_url()
    print("通知数:", np.get_notification_count())
    print("角标数:", np.get_badge_count())
