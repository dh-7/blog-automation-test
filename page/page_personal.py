from selenium.webdriver.common.by import By
from base import BasePage
from utils.config import Config
from utils.driver_manager import DriverManager

class PagePersonal(BasePage):
    """个人中心页面类"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 用户卡片元素 ====================
        self.user_name = (By.CSS_SELECTOR, ".user-name")
        self.user_desc = (By.CSS_SELECTOR, ".user-desc")

        # ==================== 左侧菜单元素 ====================
        self.menu_my_articles = (By.XPATH, '//nav//a[text()=" 我的文章"]')
        self.menu_drafts = (By.XPATH, '//a[contains(@href,"/profile/drafts") and contains(text(),"草稿箱")]')
        self.menu_comments = (By.XPATH, '//a[contains(@href,"/profile/comments") and contains(text(),"评论管理")]')
        self.menu_favorites = (By.XPATH, '//a[contains(@href,"/profile/favorites") and contains(text(),"收藏夹")]')
        self.menu_history = (By.XPATH, '//a[contains(@href,"/profile/history") and contains(text(),"阅读历史")]')
        self.menu_settings = (By.XPATH, '//a[contains(@href,"/profile/settings") and contains(text(),"个人设置")]')

        # ==================== 主内容区通用元素 ====================
        self.page_title = (By.CSS_SELECTOR, ".page-title")
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")
        self.article_items = (By.CSS_SELECTOR, ".article-item")
        self.article_titles = (By.CSS_SELECTOR, ".article-title")
        self.article_actions = (By.CSS_SELECTOR, ".article-actions")

        # ==================== 评论管理元素 ====================
        self.comment_items = (By.CSS_SELECTOR, ".comment-item")
        self.comment_contents = (By.CSS_SELECTOR, ".comment-content")

        # ==================== 个人设置元素 ====================
        self.settings_tabs = (By.CSS_SELECTOR, ".tab-item")
        self.nickname_input = (By.CSS_SELECTOR, 'input[placeholder="请输入昵称"]')
        self.bio_input = (By.CSS_SELECTOR, 'textarea[placeholder="介绍一下自己..."]')
        self.avatar_input = (By.CSS_SELECTOR, 'input[placeholder="请输入头像图片URL"]')
        self.email_input = (By.CSS_SELECTOR, 'input[placeholder="aether@example.com"]')
        self.save_button = (By.XPATH, '//button//span[text()="保存设置"]')

    def open_url(self):
        """打开个人中心页面"""
        base_url = Config.get("env", "base_url")
        self.driver.get(f"{base_url}/profile")

    def login_then_open(self, username, password):
        """先登录再打开个人中心"""
        import time
        from page.page_login import PageLogin
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.login(username, password)
        time.sleep(1)
        self.open_url()
        time.sleep(1)

    # ==================== 用户卡片操作 ====================

    def get_user_name(self):
        """获取用户昵称"""
        return self.get_text(self.user_name)

    def get_user_desc(self):
        """获取用户简介"""
        return self.get_text(self.user_desc)

    # ==================== 左侧菜单操作 ====================

    def click_my_articles(self):
        """点击-我的文章"""
        self.click(self.menu_my_articles)

    def click_drafts(self):
        """点击-草稿箱"""
        self.click(self.menu_drafts)

    def click_comments(self):
        """点击-评论管理"""
        self.click(self.menu_comments)

    def click_favorites(self):
        """点击-收藏夹"""
        self.click(self.menu_favorites)

    def click_history(self):
        """点击-阅读历史"""
        self.click(self.menu_history)

    def click_settings(self):
        """点击-个人设置"""
        self.click(self.menu_settings)

    # ==================== 文章列表操作 ====================

    def get_page_title(self):
        """获取当前tab标题"""
        return self.get_text(self.page_title)

    def is_empty(self):
        """判断列表是否为空"""
        return self.is_displayed(self.empty_state)

    def get_article_titles(self):
        """获取当前tab下文章标题列表"""
        return [el.text for el in self.find_all(self.article_titles)]

    def click_article_by_index(self, index):
        """点击第N篇文章标题（从0开始）"""
        items = self.find_all(self.article_titles)
        items[index].click()

    def click_edit_by_index(self, index):
        """点击第N篇文章的编辑按钮"""
        actions = self.find_all(self.article_actions)
        actions[index].find_element(By.XPATH, './/button[contains(text(),"编辑")]').click()

    def click_delete_by_index(self, index):
        """点击第N篇文章的删除按钮"""
        actions = self.find_all(self.article_actions)
        actions[index].find_element(By.XPATH, './/button[contains(text(),"删除")]').click()

    # ==================== 评论管理操作 ====================

    def get_comment_contents(self):
        """获取所有评论内容"""
        return [el.text for el in self.find_all(self.comment_contents)]

    def click_delete_comment_by_index(self, index):
        """点击第N条评论的删除按钮"""
        items = self.find_all(self.comment_items)
        items[index].find_element(By.XPATH, './/button[contains(text(),"删除")]').click()

    # ==================== 个人设置操作 ====================

    def fill_nickname(self, nickname):
        """填写昵称"""
        self.input(self.nickname_input, nickname)

    def fill_bio(self, bio):
        """填写简介"""
        self.input(self.bio_input, bio)

    def fill_email(self, email):
        """填写邮箱"""
        self.input(self.email_input, email)

    def click_save(self):
        """点击保存设置"""
        self.click(self.save_button)

    def update_profile(self, nickname, bio, email):
        """一键更新个人资料"""
        self.fill_nickname(nickname)
        self.fill_bio(bio)
        self.fill_email(email)
        self.click_save()

if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    pp = PagePersonal(DriverManager.get_driver())
    pp.login_then_open("zhangsan", "123456")
    print("用户昵称:", pp.get_user_name())
    print("用户简介:", pp.get_user_desc())
    print("页面标题:", pp.get_page_title())
    print("文章列表:", pp.get_article_titles())
