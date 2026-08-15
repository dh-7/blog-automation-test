import time
from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager


class PageAdminCommentManage(BasePage):
    """管理员-评论管理页面类（CommentManage.vue，路由 /admin/comments）"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 页面标题区域 ====================
        self.page_label = (By.XPATH, '//span[@style and contains(text(),"所有评论")]')
        self.total_tag = (By.CSS_SELECTOR, ".el-tag .el-tag__content")

        # ==================== 表格元素 ====================
        self.table_rows = (By.CSS_SELECTOR, ".el-table__row")

        # ==================== 确认弹窗 ====================
        self.confirm_ok = (By.XPATH, '//div[@class="el-message-box"]//button//span[text()="确定"]')
        self.confirm_cancel = (By.XPATH, '//div[@class="el-message-box"]//button//span[text()="取消"]')

    def open_url(self):
        """打开评论管理页面（需要管理员登录）"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/admin/comments")

    def login_then_open(self, username, password):
        """先登录再打开评论管理"""
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.login(username, password)
        self.open_url()

    # ==================== 页面信息 ====================

    def get_total_text(self):
        """获取总数标签文本（如 '共 12 条'）"""
        return self.get_text(self.total_tag)

    def get_total_count(self):
        """获取评论总数（数字）"""
        text = self.get_total_text()
        return int(''.join(filter(str.isdigit, text)))

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

    def get_comment_id(self, row_index):
        """获取指定行的评论ID"""
        return self.get_cell_text(row_index, 0)

    def get_comment_content(self, row_index):
        """获取指定行的评论内容"""
        return self.get_cell_text(row_index, 1)

    def get_comment_user(self, row_index):
        """获取指定行的评论用户名"""
        return self.get_cell_text(row_index, 2)

    def get_comment_article(self, row_index):
        """获取指定行的评论所属文章标题"""
        return self.get_cell_text(row_index, 3)

    def get_comment_time(self, row_index):
        """获取指定行的评论时间"""
        return self.get_cell_text(row_index, 4)

    def get_all_comment_contents(self):
        """获取当前页所有评论内容"""
        return [self.get_comment_content(i) for i in range(self.get_row_count())]

    # ==================== 删除操作 ====================

    def click_delete_by_index(self, row_index):
        """点击指定行的删除按钮"""
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, './/button[contains(text(),"删除")]')
        btn.click()

    def click_delete_by_content(self, content):
        """根据评论内容找到评论并点击删除"""
        locator = (By.XPATH,
                   f'//tr[.//td[contains(text(),"{content}")]]'
                   f'//button[contains(text(),"删除")]')
        self.click(locator)

    def confirm_delete(self):
        """确认删除弹窗"""
        self.click(self.confirm_ok)
        time.sleep(1)

    def cancel_delete(self):
        """取消删除弹窗"""
        self.click(self.confirm_cancel)

    def delete_comment_by_index(self, row_index):
        """删除指定行的评论（点击删除 + 确认）"""
        self.click_delete_by_index(row_index)
        self.confirm_delete()

    def delete_comment_by_content(self, content):
        """根据评论内容删除评论（点击删除 + 确认）"""
        self.click_delete_by_content(content)
        self.confirm_delete()


if __name__ == '__main__':
    pg = PageAdminCommentManage(DriverManager.get_driver())
    pg.login_then_open("admin", "admin123")
    print("总数:", pg.get_total_text())
    print("当前页行数:", pg.get_row_count())
    print("评论内容:", pg.get_all_comment_contents())
