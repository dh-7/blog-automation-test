from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import allure
from base import BasePage
from utils.config import Config


class PagePublishArticle(BasePage):
    """发布文章页面类 — 元素定位 + 原子操作"""

    page_path = '/write'

    def __init__(self, driver):
        super().__init__(driver)
        # 页面标题
        self.page_header = (By.CSS_SELECTOR, ".page-header h1")
        # 表单字段
        self.title_input = (By.CSS_SELECTOR, 'input[placeholder="请输入文章标题"]')
        self.category_select = (By.XPATH, '//label[text()="分类"]/following::div[contains(@class,"el-select")][1]')
        self.tag_select = (By.XPATH, '//label[text()="标签"]/following::div[contains(@class,"el-select")][1]')
        self.summary_input = (By.CSS_SELECTOR, 'textarea[placeholder*="文章摘要"]')
        self.content_input = (By.CSS_SELECTOR, 'textarea[placeholder*="Markdown"]')
        # 编辑器工具栏
        self.toolbar_bold = (By.XPATH, '//div[@class="editor-toolbar"]//button//b[text()="B"]/..')
        self.toolbar_italic = (By.XPATH, '//div[@class="editor-toolbar"]//button//i[text()="I"]/..')
        self.toolbar_h1 = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="H1"]')
        self.toolbar_h2 = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="H2"]')
        self.toolbar_code = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="Code"]')
        self.toolbar_quote = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="Quote"]')
        self.toolbar_list = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="List"]')
        self.toolbar_preview = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="预览"]')
        self.toolbar_edit = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="编辑"]')
        # 操作按钮
        self.publish_button = (By.XPATH, '//button//span[text()="发布文章"]')
        self.save_edit_button = (By.XPATH, '//button//span[text()="保存修改"]')
        self.draft_button = (By.XPATH, '//button//span[text()="存为草稿"]')
        # 预览区域
        self.preview_area = (By.CSS_SELECTOR, ".preview-area")
        # 下拉选项
        self.dropdown_item = (By.CSS_SELECTOR, ".el-select-dropdown__item")

    @allure.step("打开编辑文章")
    def open_edit_url(self, article_id):
        """打开编辑文章页面"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/edit/{article_id}")

    def _click_dropdown_option(self, option_text):
        """等待下拉面板渲染并点击指定选项"""
        option_locator = (By.XPATH,
                          f'//div[contains(@class,"el-select-dropdown")]'
                          f'//li[contains(@class,"el-select-dropdown__item")]'
                          f'[.//span[normalize-space()="{option_text}"]]')
        self.wait.until(EC.element_to_be_clickable(option_locator)).click()

    # ==================== 页面信息 ====================

    def get_page_header(self):
        """获取页面标题"""
        return self.get_text(self.page_header)

    def is_edit_mode(self):
        """是否为编辑模式"""
        return self.get_page_header() == "编辑文章"

    # ==================== 表单填写 ====================

    @allure.step("输入文章标题")
    def input_title(self, title):
        """输入文章标题"""
        self.input(self.title_input, title)

    def get_title(self):
        """获取标题输入框的值"""
        return self.find(self.title_input).get_attribute("value")

    @allure.step("选择分类")
    def select_category(self, category_name):
        """选择分类"""
        self.click(self.category_select)
        self._click_dropdown_option(category_name)

    @allure.step("选择标签")
    def select_tag(self, tag_name):
        """选择标签"""
        self.click(self.tag_select)
        self._click_dropdown_option(tag_name)
        self.find(self.page_header).click()

    @allure.step("输入文章摘要")
    def input_summary(self, summary):
        """输入文章摘要"""
        self.input(self.summary_input, summary)

    @allure.step("输入文章内容")
    def input_content(self, content):
        """输入文章内容"""
        self.input(self.content_input, content)

    def get_content(self):
        """获取内容输入框的值"""
        return self.find(self.content_input).get_attribute("value")

    # ==================== 编辑器工具栏 ====================

    @allure.step("点击加粗")
    def click_bold(self):
        self.click(self.toolbar_bold)

    @allure.step("点击斜体")
    def click_italic(self):
        self.click(self.toolbar_italic)

    @allure.step("点击H1")
    def click_h1(self):
        self.click(self.toolbar_h1)

    @allure.step("点击H2")
    def click_h2(self):
        self.click(self.toolbar_h2)

    @allure.step("点击代码块")
    def click_code(self):
        self.click(self.toolbar_code)

    @allure.step("点击引用")
    def click_quote(self):
        self.click(self.toolbar_quote)

    @allure.step("点击列表")
    def click_list(self):
        self.click(self.toolbar_list)

    @allure.step("切换预览")
    def toggle_preview(self):
        if self.is_displayed(self.toolbar_preview):
            self.click(self.toolbar_preview)
        else:
            self.click(self.toolbar_edit)

    def is_preview_visible(self):
        return self.is_displayed(self.preview_area)

    # ==================== 按钮点击 ====================

    @allure.step("点击发布文章")
    def click_publish(self):
        """点击发布文章"""
        self.click(self.publish_button)

    @allure.step("点击保存修改")
    def click_save_edit(self):
        """点击保存修改"""
        self.click(self.save_edit_button)

    @allure.step("点击存为草稿")
    def click_draft(self):
        """点击存为草稿"""
        self.click(self.draft_button)