from selenium.webdriver.common.by import By
from base import BasePage
import allure


class PageAdminUserManage(BasePage):
    """管理员-用户管理页面类 — 元素定位 + 原子操作"""

    page_path = '/admin/users'

    def __init__(self, driver):
        super().__init__(driver)
        # 表格元素
        self.table_rows = (By.CSS_SELECTOR, ".el-table__row")
        # 编辑用户弹窗
        self.edit_dialog = (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-dialog__title") and text()="编辑用户"]/ancestor::div[contains(@class,"el-dialog")]')
        self.edit_nickname = (By.XPATH, '//div[contains(@class,"el-dialog")]//label[text()="昵称"]/following::input[1]')
        self.edit_email = (By.XPATH, '//div[contains(@class,"el-dialog")]//label[text()="邮箱"]/following::input[1]')
        self.edit_save_btn = (By.XPATH, '//div[contains(@class,"el-dialog")]//button//span[text()="保存"]')
        self.edit_cancel_btn = (By.XPATH, '//div[contains(@class,"el-dialog")]//button//span[text()="取消"]')
        # 重置密码弹窗
        self.reset_pwd_dialog = (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-dialog__title") and text()="重置密码"]/ancestor::div[contains(@class,"el-dialog")]')
        self.reset_pwd_input = (By.CSS_SELECTOR, 'input[type="password"][placeholder="请输入新密码"]')
        self.reset_pwd_confirm = (By.XPATH, '//div[contains(@class,"el-dialog")]//button//span[text()="确认重置"]')
        self.reset_pwd_cancel = (By.XPATH, '//div[contains(@class,"el-dialog")]//button//span[text()="取消"]')
    def wait_for_edit_dialog(self, timeout=None):
        """等待编辑用户弹窗出现"""
        t = timeout if timeout is not None else self.timeout
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        return WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(self.edit_nickname)
        )

    def wait_for_reset_pwd_dialog(self, timeout=None):
        """等待重置密码弹窗出现"""
        t = timeout if timeout is not None else self.timeout
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        return WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(self.reset_pwd_input)
        )

    # ==================== 表格数据读取 ====================

    def get_table_rows(self):
        return self.find_all(self.table_rows)

    def get_row_count(self):
        return len(self.get_table_rows())

    def get_cell_text(self, row_index, col_index):
        rows = self.get_table_rows()
        cells = rows[row_index].find_elements(By.CSS_SELECTOR, ".el-table__cell, td")
        return cells[col_index].text.strip()

    def get_user_id(self, row_index):
        return self.get_cell_text(row_index, 0)

    def get_username(self, row_index):
        return self.get_cell_text(row_index, 1)

    def get_nickname(self, row_index):
        return self.get_cell_text(row_index, 2)

    def get_email(self, row_index):
        return self.get_cell_text(row_index, 3)

    def get_register_time(self, row_index):
        return self.get_cell_text(row_index, 4)

    def get_all_usernames(self):
        return [self.get_username(i) for i in range(self.get_row_count())]

    # ==================== 编辑用户操作 ====================

    @allure.step("点击编辑用户")
    def click_edit_by_index(self, row_index):
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, './/button[contains(.,"编辑")]')
        btn.click()

    @allure.step("按用户名编辑用户")
    def click_edit_by_username(self, username):
        locator = (By.XPATH,
                   f'//tr[.//td[contains(text(),"{username}")]]'
                   f'//button//span[text()="编辑"]')
        self.click(locator)

    @allure.step("输入编辑昵称")
    def input_edit_nickname(self, nickname):
        el = self.find(self.edit_nickname)
        el.click()
        from selenium.webdriver.common.keys import Keys
        el.send_keys(Keys.CONTROL, 'a')
        el.send_keys(nickname)

    @allure.step("输入编辑邮箱")
    def input_edit_email(self, email):
        el = self.find(self.edit_email)
        el.click()
        from selenium.webdriver.common.keys import Keys
        el.send_keys(Keys.CONTROL, 'a')
        el.send_keys(email)

    @allure.step("点击保存编辑")
    def click_edit_save(self):
        self.click(self.edit_save_btn)

    @allure.step("取消编辑")
    def click_edit_cancel(self):
        self.click(self.edit_cancel_btn)

    # ==================== 重置密码操作 ====================

    @allure.step("点击重置密码")
    def click_reset_pwd_by_index(self, row_index):
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, './/button[contains(.,"重置密码")]')
        btn.click()

    @allure.step("按用户名重置密码")
    def click_reset_pwd_by_username(self, username):
        locator = (By.XPATH,
                   f'//tr[.//td[contains(text(),"{username}")]]'
                   f'//button//span[text()="重置密码"]')
        self.click(locator)

    @allure.step("输入新密码")
    def input_new_password(self, password):
        el = self.find(self.reset_pwd_input)
        el.click()
        from selenium.webdriver.common.keys import Keys
        el.send_keys(Keys.CONTROL, 'a')
        el.send_keys(password)

    @allure.step("确认重置")
    def click_reset_confirm(self):
        self.click(self.reset_pwd_confirm)

    @allure.step("取消重置")
    def click_reset_cancel(self):
        self.click(self.reset_pwd_cancel)

    # ==================== 便捷方法 ====================

    def _find_row_by_id(self, uid):
        """按用户ID查找表格行索引

        Args:
            uid: 用户ID (int 或 str)

        Returns:
            行索引 (int)，未找到返回 -1
        """
        uid_str = str(uid)
        rows = self.get_table_rows()
        for i, row in enumerate(rows):
            cells = row.find_elements(By.CSS_SELECTOR, ".el-table__cell, td")
            if cells and cells[0].text.strip() == uid_str:
                return i
        return -1

    @staticmethod
    def _extract_id(raw):
        """从 Excel 用户ID 值中提取数字ID，如 '2（zhangsan）' -> 2"""
        import re
        m = re.match(r'\d+', str(raw))
        return int(m.group(0)) if m else None

    @staticmethod
    def _extract_username(raw):
        """从 Excel 用户ID 值中提取用户名，如 '2（zhangsan）' -> 'zhangsan'"""
        import re
        m = re.search(r'[\uff08(](\w+)[\uff09)]', str(raw))
        return m.group(1) if m else None

    def get_nickname_by_id(self, uid):
        """按用户ID获取昵称

        Args:
            uid: 用户ID

        Returns:
            昵称字符串，未找到返回 None
        """
        row_idx = self._find_row_by_id(uid)
        if row_idx < 0:
            return None
        return self.get_nickname(row_idx)

    def get_email_by_id(self, uid):
        """按用户ID获取邮箱

        Args:
            uid: 用户ID

        Returns:
            邮箱字符串，未找到返回 None
        """
        row_idx = self._find_row_by_id(uid)
        if row_idx < 0:
            return None
        return self.get_email(row_idx)

    @allure.step("编辑用户")
    def edit_user_by_id(self, uid, new_nick, new_email):
        """按用户ID编辑昵称和邮箱

        Args:
            uid:       用户ID
            new_nick:  新昵称
            new_email: 新邮箱

        Returns:
            (orig_nick, orig_email) — 原始值，用于恢复
        """
        row_idx = self._find_row_by_id(uid)
        if row_idx < 0:
            raise AssertionError(f"未找到用户ID={uid}的行")

        # 读取原始值
        orig_nick = self.get_nickname(row_idx)
        orig_email = self.get_email(row_idx)

        # 点击编辑
        self.click_edit_by_index(row_idx)
        self.wait_for_edit_dialog()

        # 修改为新值
        self.input_edit_nickname(new_nick)
        self.input_edit_email(new_email)
        self.click_edit_save()
        self.wait_for_loading_finish()

        return orig_nick, orig_email

    @allure.step("恢复用户信息")
    def restore_user_by_id(self, uid, orig_nick, orig_email):
        """恢复用户信息到原始值

        Args:
            uid:        用户ID
            orig_nick:  原始昵称
            orig_email: 原始邮箱
        """
        row_idx = self._find_row_by_id(uid)
        if row_idx < 0:
            return
        self.click_edit_by_index(row_idx)
        self.wait_for_edit_dialog()
        self.input_edit_nickname(orig_nick)
        self.input_edit_email(orig_email)
        self.click_edit_save()
        self.wait_for_loading_finish()

    @allure.step("重置密码")
    def reset_password_by_id(self, uid, new_pwd):
        """按用户ID重置密码

        Args:
            uid:     用户ID
            new_pwd: 新密码
        """
        row_idx = self._find_row_by_id(uid)
        if row_idx < 0:
            raise AssertionError(f"未找到用户ID={uid}的行")

        self.click_reset_pwd_by_index(row_idx)
        self.wait_for_reset_pwd_dialog()
        self.input_new_password(new_pwd)
        self.click_reset_confirm()
        self.wait_for_loading_finish()