from selenium.webdriver.common.by import By
from base import BasePage


class PageAdminCommentManage(BasePage):
    """管理员-评论管理页面类 — 元素定位 + 原子操作"""

    page_path = '/admin/comments'

    def __init__(self, driver):
        super().__init__(driver)
        # 页面标题区域
        self.page_label = (By.XPATH, '//span[@style and contains(text(),"所有评论")]')
        self.total_tag = (By.CSS_SELECTOR, ".el-tag .el-tag__content")
        # 表格元素
        self.table_rows = (By.CSS_SELECTOR, ".el-table__row")
    def get_total_text(self):
        return self.get_text(self.total_tag)

    def get_total_count(self):
        text = self.get_total_text()
        return int(''.join(filter(str.isdigit, text)))

    # ==================== 表格数据读取 ====================

    def get_table_rows(self):
        return self.find_all(self.table_rows)

    def get_row_count(self):
        return len(self.get_table_rows())

    def get_cell_text(self, row_index, col_index):
        rows = self.get_table_rows()
        cells = rows[row_index].find_elements(By.CSS_SELECTOR, ".el-table__cell, td")
        return cells[col_index].text.strip()

    def get_comment_id(self, row_index):
        return self.get_cell_text(row_index, 0)

    def get_comment_content(self, row_index):
        return self.get_cell_text(row_index, 1)

    def get_comment_user(self, row_index):
        return self.get_cell_text(row_index, 2)

    def get_comment_article(self, row_index):
        return self.get_cell_text(row_index, 3)

    def get_comment_time(self, row_index):
        return self.get_cell_text(row_index, 4)

    def get_all_comment_contents(self):
        return [self.get_comment_content(i) for i in range(self.get_row_count())]

    # ==================== 删除操作 ====================

    def click_delete_by_index(self, row_index):
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, './/button[contains(.,"删除")]')
        btn.click()

    def click_delete_by_content(self, content):
        locator = (By.XPATH,
                   f'//tr[.//td[contains(text(),"{content}")]]'
                   f'//button[contains(.,"删除")]')
        self.click(locator)

    def confirm_delete(self):
        self.confirm_dialog()

    def cancel_delete(self):
        self.cancel_dialog()

    def delete_first_row(self):
        """删除第一行评论并确认"""
        self.click_delete_by_index(0)
        self.confirm_delete()
        self.wait_for_loading_finish()