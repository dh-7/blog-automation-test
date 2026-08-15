import time
from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager


class PageAdminArticleManage(BasePage):
    """管理员-文章管理页面类（ArticleManage.vue，路由 /admin/articles）"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 搜索区域 ====================
        self.search_input = (By.CSS_SELECTOR, 'input[placeholder="搜索文章标题..."]')
        self.search_button = (By.XPATH, '//div[contains(@class,"el-input-group")]//button')
        self.total_tag = (By.CSS_SELECTOR, "#app > div > main > div > div > div > div:nth-child(1) > span > span")

        # ==================== 表格元素 ====================
        self.table_rows = (By.CSS_SELECTOR, ".el-table__row")
        self.table = (By.CSS_SELECTOR, ".el-table")

        # ==================== 分页 ====================
        self.pagination = (By.CSS_SELECTOR, ".el-pagination")
        self.prev_page = (By.CSS_SELECTOR, ".el-pagination .btn-prev")
        self.next_page = (By.CSS_SELECTOR, ".el-pagination .btn-next")
        self.page_numbers = (By.CSS_SELECTOR, ".el-pagination .number")

        # ==================== 确认弹窗 ====================
        self.confirm_ok = (By.XPATH, '//div[@class="el-message-box"]//button//span[text()="确定"]')
        self.confirm_cancel = (By.XPATH, '//div[@class="el-message-box"]//button//span[text()="取消"]')

    def open_url(self):
        """打开文章管理页面（需要管理员登录）"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/admin/articles")

    def login_then_open(self, username, password):
        """先登录再打开文章管理"""
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.login(username, password)
        self.open_url()

    # ==================== 搜索操作 ====================

    def input_search(self, keyword):
        """输入搜索关键词"""
        self.input(self.search_input, keyword)

    def click_search(self):
        """点击搜索按钮"""
        self.click(self.search_button)

    def search(self, keyword):
        """输入关键词并搜索"""
        self.input_search(keyword)
        self.click_search()
        time.sleep(1)

    def clear_search(self):
        """清空搜索框"""
        self.clear(self.search_input)

    # ==================== 表格数据读取 ====================

    def get_total_text(self):
        """获取总数标签文本（如 '共 42 篇'）"""
        return self.get_text(self.total_tag)

    def get_total_count(self):
        """获取文章总数（数字）"""
        text = self.get_total_text()
        return int(''.join(filter(str.isdigit, text)))

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

    def get_article_id(self, row_index):
        """获取指定行的文章ID"""
        return self.get_cell_text(row_index, 0)

    def get_article_title(self, row_index):
        """获取指定行的文章标题"""
        return self.get_cell_text(row_index, 1)

    def get_article_author(self, row_index):
        """获取指定行的作者名"""
        return self.get_cell_text(row_index, 2)

    def get_article_category(self, row_index):
        """获取指定行的分类名"""
        return self.get_cell_text(row_index, 3)

    def get_article_status(self, row_index):
        """获取指定行的文章状态（'已发布' 或 '草稿'）"""
        return self.get_cell_text(row_index, 4)

    def get_all_article_titles(self):
        """获取当前页所有文章标题"""
        titles = []
        for i in range(self.get_row_count()):
            titles.append(self.get_article_title(i))
        return titles

    # ==================== 删除操作 ====================

    def click_delete_by_index(self, row_index):
        """点击指定行的删除按钮"""
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, './/button[contains(text(),"删除")]')
        btn.click()

    def click_delete_by_title(self, title):
        """根据标题找到文章并点击删除"""
        locator = (By.XPATH,
                   f'//tr[.//a[contains(text(),"{title}")]]'
                   f'//button[contains(text(),"删除")]')
        self.click(locator)

    def confirm_delete(self):
        """确认删除弹窗"""
        self.click(self.confirm_ok)
        time.sleep(1)

    def cancel_delete(self):
        """取消删除弹窗"""
        self.click(self.confirm_cancel)

    def delete_article_by_index(self, row_index):
        """删除指定行的文章（点击删除 + 确认）"""
        self.click_delete_by_index(row_index)
        self.confirm_delete()

    def delete_article_by_title(self, title):
        """根据标题删除文章（点击删除 + 确认）"""
        self.click_delete_by_title(title)
        self.confirm_delete()

    # ==================== 分页操作 ====================

    def has_pagination(self):
        """是否有分页"""
        return self.is_displayed(self.pagination)

    def click_prev_page(self):
        """点击上一页"""
        self.click(self.prev_page)

    def click_next_page(self):
        """点击下一页"""
        self.click(self.next_page)

    def click_page_number(self, number):
        """点击指定页码"""
        locator = (By.XPATH, f'//ul[@class="el-pager"]//li[text()="{number}"]')
        self.click(locator)

    def get_current_page(self):
        """获取当前页码"""
        locator = (By.CSS_SELECTOR, ".el-pager .number.is-active")
        return self.get_text(locator)


if __name__ == '__main__':
    pg = PageAdminArticleManage(DriverManager.get_driver())
    pg.login_then_open("admin", "admin123")
    print("总数:", pg.get_total_text())
    print("当前页行数:", pg.get_row_count())
    print("文章标题:", pg.get_all_article_titles())
