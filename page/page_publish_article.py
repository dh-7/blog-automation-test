import time
from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager


class PagePublishArticle(BasePage):
    """发布文章页面类（Write.vue，路由 /write 和 /edit/:id）"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 页面标题 ====================
        self.page_header = (By.CSS_SELECTOR, ".page-header h1")

        # ==================== 表单字段 ====================
        self.title_input = (By.CSS_SELECTOR, 'input[placeholder="请输入文章标题"]')
        self.category_select = (By.XPATH, '//label[text()="分类"]/following::div[contains(@class,"el-select")][1]')
        self.tag_select = (By.XPATH, '//label[text()="标签"]/following::div[contains(@class,"el-select")][1]')
        self.summary_input = (By.CSS_SELECTOR, 'textarea[placeholder*="文章摘要"]')
        self.content_input = (By.CSS_SELECTOR, 'textarea[placeholder*="Markdown"]')

        # ==================== 编辑器工具栏 ====================
        self.toolbar_bold = (By.XPATH, '//div[@class="editor-toolbar"]//button//b[text()="B"]/..')
        self.toolbar_italic = (By.XPATH, '//div[@class="editor-toolbar"]//button//i[text()="I"]/..')
        self.toolbar_h1 = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="H1"]')
        self.toolbar_h2 = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="H2"]')
        self.toolbar_code = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="Code"]')
        self.toolbar_quote = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="Quote"]')
        self.toolbar_list = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="List"]')
        self.toolbar_preview = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="预览"]')
        self.toolbar_edit = (By.XPATH, '//div[@class="editor-toolbar"]//button//span[text()="编辑"]')

        # ==================== 操作按钮 ====================
        self.publish_button = (By.XPATH, '//button//span[text()="发布文章"]')
        self.save_edit_button = (By.XPATH, '//button//span[text()="保存修改"]')
        self.draft_button = (By.XPATH, '//button//span[text()="存为草稿"]')

        # ==================== 预览区域 ====================
        self.preview_area = (By.CSS_SELECTOR, ".preview-area")

        # ==================== 下拉选项（动态定位） ====================
        self.dropdown_item = (By.CSS_SELECTOR, ".el-select-dropdown__item")

    def open_url(self):
        """打开发布文章页面（需要登录）"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/write")

    def open_edit_url(self, article_id):
        """打开编辑文章页面（需要登录）"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/edit/{article_id}")

    def login_then_open(self, username, password):
        """先登录再打开发布文章页面"""
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.login(username, password)
        self.open_url()

    def login_then_edit(self, username, password, article_id):
        """先登录再打开编辑文章页面"""
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.login(username, password)
        self.open_edit_url(article_id)

    # ==================== 页面信息 ====================

    def get_page_header(self):
        """获取页面标题（'写文章' 或 '编辑文章'）"""
        return self.get_text(self.page_header)

    def is_edit_mode(self):
        """是否为编辑模式"""
        return self.get_page_header() == "编辑文章"

    # ==================== 表单填写 ====================

    def input_title(self, title):
        """输入文章标题"""
        self.input(self.title_input, title)

    def get_title(self):
        """获取标题输入框的值"""
        return self.find(self.title_input).get_attribute("value")

    def select_category(self, category_name):
        """选择分类"""
        self.click(self.category_select)
        time.sleep(0.5)
        locator = (By.XPATH,
                   f'//div[contains(@class,"el-select-dropdown")]'
                   f'//span[@class="el-select-dropdown__item-text" and text()="{category_name}"]')
        self.click(locator)

    def select_tag(self, tag_name):
        """选择标签（可多次调用选择多个）"""
        self.click(self.tag_select)
        time.sleep(0.5)
        locator = (By.XPATH,
                   f'//div[contains(@class,"el-select-dropdown")]'
                   f'//span[@class="el-select-dropdown__item-text" and text()="{tag_name}"]')
        self.click(locator)
        # 点击空白处关闭下拉
        self.find(self.page_header).click()

    def input_summary(self, summary):
        """输入文章摘要"""
        self.input(self.summary_input, summary)

    def input_content(self, content):
        """输入文章内容（Markdown）"""
        self.input(self.content_input, content)

    def get_content(self):
        """获取内容输入框的值"""
        return self.find(self.content_input).get_attribute("value")

    # ==================== 编辑器工具栏 ====================

    def click_bold(self):
        """点击加粗按钮"""
        self.click(self.toolbar_bold)

    def click_italic(self):
        """点击斜体按钮"""
        self.click(self.toolbar_italic)

    def click_h1(self):
        """点击H1按钮"""
        self.click(self.toolbar_h1)

    def click_h2(self):
        """点击H2按钮"""
        self.click(self.toolbar_h2)

    def click_code(self):
        """点击代码块按钮"""
        self.click(self.toolbar_code)

    def click_quote(self):
        """点击引用按钮"""
        self.click(self.toolbar_quote)

    def click_list(self):
        """点击列表按钮"""
        self.click(self.toolbar_list)

    def toggle_preview(self):
        """切换预览/编辑模式"""
        if self.is_displayed(self.toolbar_preview):
            self.click(self.toolbar_preview)
        else:
            self.click(self.toolbar_edit)

    def is_preview_visible(self):
        """预览区域是否可见"""
        return self.is_displayed(self.preview_area)

    # ==================== 提交操作 ====================

    def click_publish(self):
        """点击发布文章"""
        self.click(self.publish_button)

    def click_save_edit(self):
        """点击保存修改"""
        self.click(self.save_edit_button)

    def click_draft(self):
        """点击存为草稿"""
        self.click(self.draft_button)

    def _fill_form(self, title, content, category_name=None, tag_names=None, summary=None):
        """填写文章表单（内部方法）"""
        self.input_title(title)
        if category_name:
            self.select_category(category_name)
        if tag_names:
            for tag in tag_names:
                self.select_tag(tag)
        if summary:
            self.input_summary(summary)
        self.input_content(content)

    def publish_article(self, title, content, category_name=None, tag_names=None, summary=None):
        """一键发布新文章（填写表单 + 点击发布）"""
        self._fill_form(title, content, category_name, tag_names, summary)
        self.click_publish()
        time.sleep(2)

    def save_edit_article(self, title, content, category_name=None, tag_names=None, summary=None):
        """一键保存修改（编辑模式下填写表单 + 点击保存）"""
        self._fill_form(title, content, category_name, tag_names, summary)
        self.click_save_edit()
        time.sleep(2)

    def save_as_draft(self, title, content, summary=None):
        """一键保存草稿"""
        self.input_title(title)
        if summary:
            self.input_summary(summary)
        self.input_content(content)
        self.click_draft()
        time.sleep(2)


if __name__ == '__main__':
    pg = PagePublishArticle(DriverManager.get_driver())
    pg.login_then_open("zhangsan", "123456")
    print("页面标题:", pg.get_page_header())
    print("是否编辑模式:", pg.is_edit_mode())
