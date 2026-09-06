"""el-table 表格操作通用 Mixin

管理端页面（用户/文章/评论管理）的表格读取与行内按钮操作高度相似，
统一收敛到这里。使用方式：

    class PageAdminUserManage(TablePageMixin, BasePage):
        ...

子类约定：
  - 行定位器默认 .el-table__row，特殊表格可在类属性覆盖 table_rows
  - 单元格选择器默认 .el-table__cell, td
"""
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


class TablePageMixin:
    """Element Plus el-table 通用操作（需与 BasePage 一起使用）"""

    # 表格行定位器（子类可覆盖）
    table_rows = (By.CSS_SELECTOR, ".el-table__row")
    # 单元格选择器
    _cell_css = ".el-table__cell, td"

    def get_table_rows(self):
        """获取表格所有行；加载中先轮询等待，空表返回 []

        等待条件：出现数据行，或出现空表提示（.el-table__empty-text）。
        二者都未出现时按空表处理，由上层断言判断是否符合预期。
        """
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_elements(*self.table_rows)
                or d.find_elements(By.CSS_SELECTOR, ".el-table__empty-text")
            )
        except Exception:
            pass
        return self.driver.find_elements(*self.table_rows)

    def get_row_count(self):
        return len(self.get_table_rows())

    def get_cell_text(self, row_index, col_index):
        rows = self.get_table_rows()
        cells = rows[row_index].find_elements(By.CSS_SELECTOR, self._cell_css)
        return cells[col_index].text.strip()

    def find_row_index_by_first_cell(self, value):
        """按第一列文本查找行索引，未找到返回 -1"""
        target = str(value)
        for i, row in enumerate(self.get_table_rows()):
            cells = row.find_elements(By.CSS_SELECTOR, self._cell_css)
            if cells and cells[0].text.strip() == target:
                return i
        return -1

    @allure.step("点击第{row_index}行按钮[{label}]")
    def click_row_button(self, row_index, label):
        """点击指定行内包含 label 文本的按钮"""
        rows = self.get_table_rows()
        btn = rows[row_index].find_element(By.XPATH, f'.//button[contains(.,"{label}")]')
        btn.click()
