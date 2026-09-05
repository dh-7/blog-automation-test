from selenium.webdriver.common.by import By
from base import BasePage
import allure


class PageAdminArticleManage(BasePage):
    """管理员-文章管理页面类 — 元素定位 + 原子操作"""

    page_path = '/admin/articles'

    def __init__(self, driver):
        super().__init__(driver)
        # 搜索区域
        self.search_input = (By.CSS_SELECTOR, 'input[placeholder="搜索文章标题..."]')
        self.search_button = (By.XPATH, '//div[contains(@class,"el-input-group")]//button')
        self.total_tag = (By.CSS_SELECTOR, "#app > div > main > div > div > div > div:nth-child(1) > span > span")
        # 表格元素
        self.table_rows = (By.CSS_SELECTOR, ".el-table__row")
        self.table = (By.CSS_SELECTOR, ".el-table")
        # 分页
        self.pagination = (By.CSS_SELECTOR, ".el-pagination")
        self.prev_page = (By.CSS_SELECTOR, ".el-pagination .btn-prev")
        self.next_page = (By.CSS_SELECTOR, ".el-pagination .btn-next")
        self.page_numbers = (By.CSS_SELECTOR, ".el-pagination .number")
    @allure.step("输入搜索关键词")
    def input_search(self, keyword):
        self.input(self.search_input, keyword)

    @allure.step("点击搜索")
    def click_search(self):
        self.click(self.search_button)

    @allure.step("清空搜索")
    def clear_search(self):
        self.clear(self.search_input)

    # ==================== 表格数据读取 ====================

    def get_total_text(self):
        return self.get_text(self.total_tag)

    def get_total_count(self):
        text = self.get_total_text()
        return int(''.join(filter(str.isdigit, text)))

    def get_table_rows(self):
        """获取表格所有行，空表时返回空列表"""
        try:
            from selenium.webdriver.support.wait import WebDriverWait
            WebDriverWait(self.driver, 5).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".el-table__row")) > 0
                   or len(d.find_elements(By.CSS_SELECTOR, ".el-table__empty-text")) > 0
            )
        except Exception:
            pass
        rows = self.driver.find_elements(By.CSS_SELECTOR, ".el-table__row")
        return rows

    def get_row_count(self):
        return len(self.get_table_rows())

    def get_cell_text(self, row_index, col_index):
        rows = self.get_table_rows()
        cells = rows[row_index].find_elements(By.CSS_SELECTOR, ".el-table__cell, td")
        return cells[col_index].text.strip()

    def get_article_id(self, row_index):
        return self.get_cell_text(row_index, 0)

    def get_article_title(self, row_index):
        return self.get_cell_text(row_index, 1)

    def get_article_author(self, row_index):
        return self.get_cell_text(row_index, 2)

    def get_article_category(self, row_index):
        return self.get_cell_text(row_index, 3)

    def get_article_status(self, row_index):
        return self.get_cell_text(row_index, 4)

    def get_all_article_titles(self):
        titles = []
        for i in range(self.get_row_count()):
            titles.append(self.get_article_title(i))
        return titles

    # ==================== 删除操作 ====================

    @allure.step("点击删除文章")
    def click_delete_by_index(self, row_index):
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, './/button[contains(.,"删除")]')
        btn.click()

    @allure.step("按标题删除文章")
    def click_delete_by_title(self, title):
        locator = (By.XPATH,
                   f'//tr[.//a[contains(text(),"{title}")]]'
                   f'//button[contains(.,"删除")]')
        self.click(locator)

    @allure.step("确认删除")
    def confirm_delete(self):
        self.confirm_dialog()

    @allure.step("取消删除")
    def cancel_delete(self):
        self.cancel_dialog()

    # ==================== 分页操作 ====================

    def has_pagination(self):
        return self.is_displayed(self.pagination)

    @allure.step("点击上一页")
    def click_prev_page(self):
        self.click(self.prev_page)

    @allure.step("点击下一页")
    def click_next_page(self):
        self.click(self.next_page)

    @allure.step("点击页码")
    def click_page_number(self, number):
        locator = (By.XPATH, f'//ul[@class="el-pager"]//li[text()="{number}"]')
        self.click(locator)

    def get_current_page(self):
        locator = (By.CSS_SELECTOR, ".el-pager .number.is-active")
        return self.get_text(locator)

    # ==================== 便捷方法 ====================

    @allure.step("搜索文章")
    def search_article(self, title):
        """搜索文章标题，返回是否在结果中找到

        Args:
            title: 文章标题

        Returns:
            bool — 搜索结果中是否包含该标题
        """
        self.input_search(title)
        self.click_search()
        self.wait_for_loading_finish()
        titles = self.get_all_article_titles()
        return title in titles

    @allure.step("清空搜索并刷新")
    def clear_search_and_refresh(self):
        """清空搜索并刷新列表"""
        self.clear_search()
        self.click_search()
        self.wait_for_loading_finish()