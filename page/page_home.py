
from selenium.webdriver.common.by import By
from base import BasePage


class PageHome(BasePage):
    """首页页面类"""

    page_path = '/'

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 导航栏元素 ====================
        self.logo = (By.CSS_SELECTOR, "a.logo")
        self.nav_home = (By.XPATH, '//nav//a[text()="首页"]')
        self.nav_archive = (By.XPATH, '//nav//a[text()="归档"]')
        self.nav_category = (By.XPATH, '//nav//a[text()="分类"]')
        self.nav_about = (By.XPATH, '//nav//a[text()="关于"]')
        self.search_input = (By.CSS_SELECTOR, "input[placeholder='搜索文章...']")
        self.login_button = (By.XPATH, '//header//a[contains(@href,"/login")]//button')
        self.register_button = (By.XPATH, '//header//a[contains(@href,"/register")]//button')
        # 用户头像（登录后显示在右上角）
        self.user_avatar = (By.CSS_SELECTOR, '.user-avatar img')
        # Element Plus avatar 组件（可能是 el-avatar 而非 img）
        self.user_avatar_el = (By.CSS_SELECTOR, '.user-avatar .el-avatar')

        # ==================== 文章列表元素 ====================
        self.article_cards = (By.CSS_SELECTOR, ".article-card")
        self.article_title = (By.CSS_SELECTOR, ".article-title")
        self.article_summary = (By.CSS_SELECTOR, ".article-summary")
        self.article_meta = (By.CSS_SELECTOR, ".article-meta")
        self.article_tags = (By.CSS_SELECTOR, ".article-tags .tag")
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")

        # ==================== 分页元素 ====================
        self.pagination = (By.CSS_SELECTOR, ".pagination")
        self.prev_page = (By.CSS_SELECTOR, ".pagination .btn-prev")
        self.next_page = (By.CSS_SELECTOR, ".pagination .btn-next")
        self.page_numbers = (By.CSS_SELECTOR, ".pagination .number")

        # ==================== 侧边栏元素 ====================
        self.category_items = (By.CSS_SELECTOR, ".category-item")
        self.category_names = (By.CSS_SELECTOR, ".category-name")
        self.category_counts = (By.CSS_SELECTOR, ".category-count")
        self.archive_items = (By.CSS_SELECTOR, ".archive-item")
    def click_logo(self):
        """点击Logo回到首页"""
        self.click(self.logo)

    def click_nav_home(self):
        """点击导航-首页"""
        self.click(self.nav_home)

    def click_nav_archive(self):
        """点击导航-归档"""
        self.click(self.nav_archive)

    def click_nav_category(self):
        """点击导航-分类"""
        self.click(self.nav_category)

    def click_nav_about(self):
        """点击导航-关于"""
        self.click(self.nav_about)

    def search(self, keyword):
        """搜索文章"""
        self.input(self.search_input, keyword)
        from selenium.webdriver.common.keys import Keys
        self.find(self.search_input).send_keys(Keys.ENTER)

    def get_user_avatar_src(self):
        """获取右上角用户头像的src属性"""
        el = self.find(self.user_avatar)
        return el.get_attribute('src') if el else None

    def is_user_avatar_displayed(self):
        """判断右上角用户头像是否显示"""
        return self.is_displayed(self.user_avatar)

    def click_login(self):
        """点击登录按钮"""
        self.click(self.login_button)

    def click_register(self):
        """点击注册按钮"""
        self.click(self.register_button)

    # ==================== 文章列表操作 ====================

    def get_article_cards(self):
        """获取所有文章卡片元素列表"""
        return self.find_all(self.article_cards)

    def get_article_count(self):
        """获取当前页文章数量"""
        return len(self.get_article_cards())

    def click_article_by_index(self, index):
        """点击第N篇文章（从0开始）"""
        cards = self.get_article_cards()
        cards[index].click()

    def click_article_by_title(self, title):
        """点击指定标题的文章"""
        locator = (By.XPATH, f'//h2[@class="article-title" and text()="{title}"]/ancestor::div[@class="article-card"]')
        self.click(locator)

    def get_article_title_by_index(self, index):
        """获取第N篇文章标题"""
        titles = self.find_all(self.article_title)
        return titles[index].text

    def get_all_article_titles(self):
        """获取当前页所有文章标题"""
        return [el.text for el in self.find_all(self.article_title)]

    def is_empty(self):
        """判断文章列表是否为空"""
        return self.is_displayed(self.empty_state)

    # ==================== 分页操作 ====================

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
        locator = (By.CSS_SELECTOR, ".pagination .el-pager .number.is-active")
        return self.get_text(locator)

    def is_prev_disabled(self):
        """上一页按钮是否禁用"""
        return not self.find(self.prev_page).is_enabled()

    def is_next_disabled(self):
        """下一页按钮是否禁用"""
        return not self.find(self.next_page).is_enabled()

    # ==================== 侧边栏操作 ====================

    def get_category_names(self):
        """获取所有分类名称"""
        return [el.text.strip() for el in self.find_all(self.category_names)]

    def click_category_by_name(self, name):
        """点击指定分类"""
        locator = (By.XPATH, f'//div[@class="category-item"]//span[@class="category-name" and contains(text(),"{name}")]')
        self.click(locator)

    def get_archive_items(self):
        """获取归档列表文本"""
        return [el.text.strip() for el in self.find_all(self.archive_items)]

    # ==================== 断言辅助方法 ====================

    def get_all_article_texts(self):
        """获取所有文章的完整文本(标题+摘要+作者)"""
        cards = self.find_all(self.article_cards)
        return [c.text for c in cards]

    def assert_articles_contain_keyword(self, keyword):
        """断言当前页所有文章标题都包含关键词"""
        titles = self.get_all_article_titles()
        assert len(titles) > 0, "文章列表为空"
        for t in titles:
            assert keyword in t, f"文章'{t}'不包含关键词'{keyword}'"

    def assert_empty_state(self):
        """断言列表为空状态"""
        empty = self.is_empty() or self.get_article_count() == 0
        assert empty, "预期空列表，但仍有文章"

    def assert_article_count(self, expected_min=1):
        """断言文章数量不少于指定值"""
        count = self.get_article_count()
        assert count >= expected_min, \
            f"预期至少{expected_min}篇文章，实际{count}篇"
if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    hp = PageHome(DriverManager.get_driver())
    hp.open_url()
    print("文章数量:", hp.get_article_count())
    print("文章标题:", hp.get_all_article_titles())
    print("分类列表:", hp.get_category_names())
