import time
from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager


class PageAdminUserManage(BasePage):
    """管理员-用户管理页面类（UserManage.vue，路由 /admin/users）"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 表格元素 ====================
        self.table_rows = (By.CSS_SELECTOR, ".el-table__row")

        # ==================== 编辑用户弹窗 ====================
        self.edit_dialog = (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-dialog__title") and text()="编辑用户"]/ancestor::div[contains(@class,"el-dialog")]')
        self.edit_nickname = (By.XPATH, '//div[contains(@class,"el-dialog")]//label[text()="昵称"]/following::input[1]')
        self.edit_email = (By.XPATH, '//div[contains(@class,"el-dialog")]//label[text()="邮箱"]/following::input[1]')
        self.edit_save_btn = (By.XPATH, '//div[contains(@class,"el-dialog")]//button//span[text()="保存"]')
        self.edit_cancel_btn = (By.XPATH, '//div[contains(@class,"el-dialog")]//button//span[text()="取消"]')

        # ==================== 重置密码弹窗 ====================
        self.reset_pwd_dialog = (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-dialog__title") and text()="重置密码"]/ancestor::div[contains(@class,"el-dialog")]')
        self.reset_pwd_input = (By.CSS_SELECTOR, 'input[type="password"][placeholder="请输入新密码"]')
        self.reset_pwd_confirm = (By.XPATH, '//div[contains(@class,"el-dialog")]//button//span[text()="确认重置"]')
        self.reset_pwd_cancel = (By.XPATH, '//div[contains(@class,"el-dialog")]//button//span[text()="取消"]')

    def open_url(self):
        """打开用户管理页面（需要管理员登录）"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/admin/users")

    def login_then_open(self, username, password):
        """先登录再打开用户管理"""
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.login(username, password)
        self.open_url()

    # ==================== 表格数据读取 ====================

    def get_table_rows(self):
        """获取表格所有行"""
        return self.find_all(self.table_rows)

    def get_row_count(self):
        """获取当前页行数"""
        return len(self.get_table_rows())

    def get_cell_text(self, row_index, col_index):
        """获取指定单元格文本（从0开始）"""
        rows = self.get_table_rows()
        cells = rows[row_index].find_elements(By.CSS_SELECTOR, ".el-table__cell, td")
        return cells[col_index].text.strip()

    def get_user_id(self, row_index):
        """获取指定行的用户ID"""
        return self.get_cell_text(row_index, 0)

    def get_username(self, row_index):
        """获取指定行的用户名"""
        return self.get_cell_text(row_index, 1)

    def get_nickname(self, row_index):
        """获取指定行的昵称"""
        return self.get_cell_text(row_index, 2)

    def get_email(self, row_index):
        """获取指定行的邮箱"""
        return self.get_cell_text(row_index, 3)

    def get_register_time(self, row_index):
        """获取指定行的注册时间"""
        return self.get_cell_text(row_index, 4)

    def get_all_usernames(self):
        """获取当前页所有用户名"""
        return [self.get_username(i) for i in range(self.get_row_count())]

    # ==================== 编辑用户操作 ====================

    def click_edit_by_index(self, row_index):
        """点击指定行的编辑按钮"""
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, './/button[contains(text(),"编辑")]')
        btn.click()

    def click_edit_by_username(self, username):
        """根据用户名找到用户并点击编辑"""
        locator = (By.XPATH,
                   f'//tr[.//td[contains(text(),"{username}")]]'
                   f'//button[contains(text(),"编辑")]')
        self.click(locator)

    def input_edit_nickname(self, nickname):
        """在编辑弹窗中输入昵称"""
        self.input(self.edit_nickname, nickname)

    def input_edit_email(self, email):
        """在编辑弹窗中输入邮箱"""
        self.input(self.edit_email, email)

    def click_edit_save(self):
        """点击编辑弹窗的保存按钮"""
        self.click(self.edit_save_btn)
        time.sleep(1)

    def click_edit_cancel(self):
        """点击编辑弹窗的取消按钮"""
        self.click(self.edit_cancel_btn)

    def edit_user(self, row_index, nickname=None, email=None):
        """编辑指定行的用户信息"""
        self.click_edit_by_index(row_index)
        time.sleep(0.5)
        if nickname is not None:
            self.input_edit_nickname(nickname)
        if email is not None:
            self.input_edit_email(email)
        self.click_edit_save()

    # ==================== 重置密码操作 ====================

    def click_reset_pwd_by_index(self, row_index):
        """点击指定行的重置密码按钮"""
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, './/button[contains(text(),"重置密码")]')
        btn.click()

    def click_reset_pwd_by_username(self, username):
        """根据用户名找到用户并点击重置密码"""
        locator = (By.XPATH,
                   f'//tr[.//td[contains(text(),"{username}")]]'
                   f'//button[contains(text(),"重置密码")]')
        self.click(locator)

    def input_new_password(self, password):
        """在重置密码弹窗中输入新密码"""
        self.input(self.reset_pwd_input, password)

    def click_reset_confirm(self):
        """点击确认重置"""
        self.click(self.reset_pwd_confirm)
        time.sleep(1)

    def click_reset_cancel(self):
        """点击取消重置"""
        self.click(self.reset_pwd_cancel)

    def reset_password(self, row_index, new_password):
        """重置指定行用户的密码"""
        self.click_reset_pwd_by_index(row_index)
        time.sleep(0.5)
        self.input_new_password(new_password)
        self.click_reset_confirm()


if __name__ == '__main__':
    pg = PageAdminUserManage(DriverManager.get_driver())
    pg.login_then_open("admin", "admin123")
    print("用户列表:", pg.get_all_usernames())
    print("行数:", pg.get_row_count())
