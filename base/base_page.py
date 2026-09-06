import os
from datetime import datetime

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

from utils.config import Config
from utils.logger import Logger

log = Logger.get_logger()


class BasePage:
    """页面操作基类 — 封装 Selenium 常用操作，所有 PageObject 继承此类"""

    page_path = None  # 子类必须覆盖，如 '/login'、'/admin/articles'

    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    # ==================== 页面导航 ====================

    @allure.step("打开页面")
    def open_url(self, path=None):
        """打开页面（使用 page_path 或指定 path）"""
        base_url = Config.get("env", "base_url")
        url = f"{base_url}{path or self.page_path}"
        self.driver.get(url)

    @allure.step("登录并打开")
    def login_and_open(self, username, password, path=None):
        """登录并打开本页面"""
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.input_username(username)
        login_page.input_password(password)
        login_page.click_login_button()
        # 等待登录成功：URL 离开 /login（路由跳转完成，说明登录接口已返回成功且 token 已写入）
        # 替代硬编码 time.sleep：条件满足立即继续，登录失败时正确超时
        WebDriverWait(self.driver, self.timeout).until(
            lambda d: "/login" not in d.current_url
        )
        self.open_url(path)
        self.wait_for_page_ready()

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

    @allure.step("点击")
    def click(self, loc):
        """点击元素"""
        self.find(loc).click()
        log.info(f"点击: {loc}")

    @allure.step("输入")
    def input(self, loc, text):
        """输入文本（先清空再输入）

        Vue v-model 竞态防护：
        - send_keys 输入过快时，受控组件可能未把输入值提交到表单模型，
          立即点击提交会读到空值（偶发登录/表单提交失败）；
        - 读回校验，若 Vue 重渲染吞掉末位字符则补齐；
        - blur 触发 change 事件，确保 v-model 已把最终值同步到表单模型。
        """
        el = self.find(loc)
        el.clear()
        el.send_keys(text)
        # 读回校验，补齐可能丢失的字符（Vue 受控组件偶发吞字符）
        try:
            entered = el.get_attribute("value") or ""
            if entered != text:
                missing = text[len(entered):] if text.startswith(entered) else text
                el.send_keys(missing)
        except Exception:
            pass
        # blur 提交 v-model（触发 change 事件，确保表单模型已更新）
        try:
            self.driver.execute_script("arguments[0].blur();", el)
        except Exception:
            pass
        log.info(f"输入: {loc} -> {text}")

    @allure.step("替换输入")
    def input_replace(self, loc, text):
        """替换输入：点击聚焦 → Ctrl+A 全选 → 输入新值

        用于可能已有旧值的输入框：clear() 对部分受控组件不生效，
        Ctrl+A 全选后直接输入可确保旧值被完整覆盖。
        """
        from selenium.webdriver.common.keys import Keys
        el = self.find(loc)
        el.click()
        el.send_keys(Keys.CONTROL, 'a')
        el.send_keys(text)
        log.info(f"替换输入: {loc} -> {text}")

    @allure.step("清空")
    def clear(self, loc):
        """清空输入框"""
        self.find(loc).clear()
        log.info(f"清空: {loc}")

    @allure.step("获取文本")
    def get_text(self, loc):
        """获取元素可见文本"""
        text = self.find(loc).text
        log.info(f"获取文本: {loc} -> {text}")
        return text

    @allure.step("获取属性")
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

    def is_present(self, loc, timeout=3):
        """元素是否出现在 DOM 中（短等待，不抛异常）

        用于"应不存在/应存在"的否定断言：
        - 元素在 timeout 内出现 → 返回 True
        - 元素一直不存在 → 返回 False（不会抛异常拖慢用例）
        """
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.wait import WebDriverWait
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(loc)
            )
            return True
        except Exception:
            return False

    # ==================== 确认弹框（Element Plus el-message-box） ====================

    _CONFIRM_OK = (By.XPATH, '//div[@class="el-message-box"]//button//span[normalize-space()="确定" or normalize-space()="确定清空"]')
    _CONFIRM_CANCEL = (By.XPATH, '//div[@class="el-message-box"]//button//span[text()="取消"]')

    def wait_for_confirm_dialog(self, timeout=None):
        """等待 Element Plus 确认弹窗出现，返回弹窗元素"""
        t = timeout if timeout is not None else self.timeout
        loc = (By.CSS_SELECTOR, ".el-message-box")
        return WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(loc)
        )

    @allure.step("确认弹窗")
    def confirm_dialog(self, timeout=None):
        """点击确认弹框的"确定"按钮"""
        t = timeout or self.timeout
        WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(self._CONFIRM_OK)
        ).click()
        log.info("点击确认弹框: 确定")

    @allure.step("取消弹窗")
    def cancel_dialog(self, timeout=None):
        """点击确认弹框的"取消"按钮"""
        t = timeout or self.timeout
        WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(self._CONFIRM_CANCEL)
        ).click()
        log.info("点击确认弹框: 取消")

    # ==================== 浏览器操作 ====================


    @allure.step("刷新页面")
    def refresh(self):
        """刷新页面"""
        self.driver.refresh()
        log.info("刷新页面")

    @allure.step("后退")
    def back(self):
        """浏览器后退"""
        self.driver.back()
        log.info("后退")

    @allure.step("前进")
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

    @allure.step("截图")
    def take_screenshot(self, name=None, save_dir="report"):
        """截图保存，返回文件路径"""
        os.makedirs(save_dir, exist_ok=True)
        if name is None:
            name = f"{datetime.now():%Y%m%d_%H%M%S}"
        path = os.path.join(save_dir, f"{name}.png")
        self.driver.save_screenshot(path)
        log.info(f"截图: {path}")
        return path

    # ==================== 显式等待（替代 time.sleep） ====================

    def wait_for_clickable(self, loc, timeout=None):
        """等待元素可点击"""
        t = timeout if timeout is not None else self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(loc)
        )

    def wait_for_invisible(self, loc, timeout=None):
        """等待元素不可见（loading 遮罩、toast 消失等）"""
        t = timeout if timeout is not None else self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.invisibility_of_element_located(loc)
        )

    def wait_for_text_in_element(self, loc, text, timeout=None):
        """等待元素中出现指定文本"""
        t = timeout if timeout is not None else self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.text_to_be_present_in_element(loc, text)
        )

    @allure.step("等待URL包含")
    def wait_for_url_contains(self, url_part, timeout=None):
        """等待 URL 包含指定字符串（页面跳转后调用）"""
        t = timeout if timeout is not None else self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.url_contains(url_part)
        )

    def _wait_for_vue_ready(self, timeout=3):
        """等待 Vue 应用初始化完成（__vue_app__ 挂载到 #app）

        非 Vue 页面会静默跳过，不阻塞。
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script(
                    "var app = document.getElementById('app');"
                    "return app && !!app.__vue_app__;"
                )
            )
        except Exception:
            pass  # 非 Vue 页面或超时，不阻塞

    @allure.step("等待页面加载完成")
    def wait_for_page_ready(self, timeout=None):
        """等待页面完全加载（document.readyState == complete + Vue 渲染完成）

        对 Vue SPA 单页应用，document.readyState 变为 complete 时 Vue 组件可能
        尚未渲染完毕。本方法额外等待 Vue 的 nextTick / 空闲帧，确保 DOM 已更新。
        """
        t = timeout if timeout is not None else self.timeout
        WebDriverWait(self.driver, t).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # 等待 Vue 应用初始化（替代硬编码 sleep）
        self._wait_for_vue_ready(timeout=min(t, 3))
        # 等待 Vue 渲染周期完成（两帧 rAF 确保 DOM 已更新）
        try:
            WebDriverWait(self.driver, min(t, 3)).until(
                lambda d: d.execute_script(
                    "return new Promise(r => requestAnimationFrame(() => "
                    "requestAnimationFrame(() => r(true))))"
                )
            )
        except Exception:
            pass  # 非 Vue 页面或超时，不阻塞

    @allure.step("等待加载结束")
    def wait_for_loading_finish(self, timeout=None):
        """等待 Element Plus loading 遮罩消失"""
        loc = (By.CSS_SELECTOR, ".el-loading-mask")
        try:
            return self.wait_for_invisible(loc, timeout=timeout)
        except TimeoutException:
            return True  # loading 从未出现，视为已完成

    def find_toast(self, text):
        """立刻查找包含指定文本的 toast，不等待。找到返回文本，否则返回 None"""
        els = self.driver.find_elements(By.CSS_SELECTOR, '.el-message__content')
        for el in els:
            if text in el.text:
                return el.text
        return None

    def quick_wait_toast(self, text, timeout=3, interval=0.2):
        """短间隔轮询查找 toast，比 WebDriverWait 更快响应

        Args:
            text: 要查找的文本
            timeout: 最大等待秒数
            interval: 轮询间隔秒数

        Returns:
            toast 文本，超时返回 None
        """
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            els = self.driver.find_elements(By.CSS_SELECTOR, '.el-message__content')
            for el in els:
                if text in el.text:
                    return el.text
            time.sleep(interval)
        return None

    @allure.step("等待提示消息")
    def wait_for_toast(self, text, timeout=None):
        """等待 Element Plus toast 消息出现，返回消息文本；超时返回 None"""
        # 先立刻查找（toast 可能已经出现）
        found = self.find_toast(text)
        if found:
            return found
        # 再等待
        t = timeout if timeout is not None else self.timeout
        loc = (By.XPATH,
               f'//p[contains(@class,"el-message__content") '
               f'and contains(text(),"{text}")]')
        try:
            el = WebDriverWait(self.driver, t).until(
                EC.visibility_of_element_located(loc)
            )
            return el.text
        except TimeoutException:
            return None

    def find_form_error(self, text=None):
        """立刻查找表单验证错误，不等待。找到返回文本，否则返回 None"""
        els = self.driver.find_elements(By.CSS_SELECTOR, '.el-form-item__error')
        for el in els:
            if not text or text in el.text:
                return el.text
        return None

    def wait_for_form_error(self, text=None, timeout=None):
        """等待表单验证错误出现，返回错误文本；超时返回 None"""
        # 先立刻查找
        found = self.find_form_error(text)
        if found:
            return found
        # 再等待
        t = timeout if timeout is not None else self.timeout
        if text:
            loc = (By.XPATH,
                   f'//div[contains(@class,"el-form-item__error") '
                   f'and contains(text(),"{text}")]')
        else:
            loc = (By.CSS_SELECTOR, ".el-form-item__error")
        try:
            el = WebDriverWait(self.driver, t).until(
                EC.visibility_of_element_located(loc)
            )
            return el.text
        except TimeoutException:
            return None
