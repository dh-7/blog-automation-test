from selenium.webdriver.common.by import By
from base import BasePage
import allure


class PagePersonal(BasePage):
    """个人中心页面类 — 元素定位 + 原子操作"""

    page_path = '/profile'

    def __init__(self, driver):
        super().__init__(driver)
        # 用户卡片
        self.user_name = (By.CSS_SELECTOR, ".user-name")
        self.user_desc = (By.CSS_SELECTOR, ".user-desc")
        # 左侧菜单
        self.menu_my_articles = (By.XPATH, '//nav//a[contains(@href,"/profile") and contains(text(),"我的文章")]')
        self.menu_drafts = (By.XPATH, '//a[contains(@href,"/profile/drafts") and contains(text(),"草稿箱")]')
        self.menu_comments = (By.XPATH, '//a[contains(@href,"/profile/comments") and contains(text(),"评论管理")]')
        self.menu_favorites = (By.XPATH, '//a[contains(@href,"/profile/favorites") and contains(text(),"收藏夹")]')
        self.menu_history = (By.XPATH, '//a[contains(@href,"/profile/history") and contains(text(),"阅读历史")]')
        self.menu_settings = (By.XPATH, '//a[contains(@href,"/profile/settings") and contains(text(),"个人设置")]')
        # 主内容区
        self.page_title = (By.CSS_SELECTOR, ".page-title")
        self.empty_state = (By.CSS_SELECTOR, ".empty-state")
        self.article_items = (By.CSS_SELECTOR, ".article-item")
        self.article_titles = (By.CSS_SELECTOR, ".article-title")
        self.article_actions = (By.CSS_SELECTOR, ".article-actions")
        # 评论管理
        self.comment_items = (By.CSS_SELECTOR, ".comment-item")
        self.comment_contents = (By.CSS_SELECTOR, ".comment-content")
        # 个人设置 - 个人资料
        self.settings_tabs = (By.CSS_SELECTOR, ".tab-item")
        self.nickname_input = (By.CSS_SELECTOR, 'input[placeholder="请输入昵称"]')
        self.bio_input = (By.CSS_SELECTOR, 'textarea[placeholder="介绍一下自己..."]')
        self.avatar_input = (By.CSS_SELECTOR, 'input[placeholder="请输入头像图片URL"]')
        self.email_input = (By.CSS_SELECTOR, 'input[placeholder="aether@example.com"]')
        self.save_button = (By.XPATH, '//button//span[text()="保存设置"]')
        # 个人设置 - 账户安全
        self.security_tab = (By.XPATH, '//div[contains(@class,"tab-item") and contains(text(),"账户安全")]')
        self.old_password_input = (By.CSS_SELECTOR, 'input[placeholder="请输入原密码"]')
        self.new_password_input = (By.CSS_SELECTOR, 'input[placeholder="请输入新密码"]')
        self.confirm_password_input = (By.CSS_SELECTOR, 'input[placeholder="请确认新密码"]')
        self.change_password_button = (By.XPATH, '//button[contains(.,"修改密码")]')
    def get_user_name(self):
        return self.get_text(self.user_name)

    def get_user_desc(self):
        return self.get_text(self.user_desc)

    # ==================== 左侧菜单 ====================

    @allure.step("点击我的文章")
    def click_my_articles(self):
        self.click(self.menu_my_articles)

    @allure.step("点击草稿箱")
    def click_drafts(self):
        self.click(self.menu_drafts)

    @allure.step("点击评论管理")
    def click_comments(self):
        self.click(self.menu_comments)

    @allure.step("点击收藏夹")
    def click_favorites(self):
        self.click(self.menu_favorites)

    @allure.step("点击阅读历史")
    def click_history(self):
        self.click(self.menu_history)

    @allure.step("点击个人设置")
    def click_settings(self):
        self.click(self.menu_settings)

    # ==================== 文章列表 ====================

    def get_page_title(self):
        return self.get_text(self.page_title)

    def is_empty(self):
        return self.is_displayed(self.empty_state)

    def get_article_titles(self):
        return [el.text for el in self.find_all(self.article_titles)]

    def get_published_count(self):
        """读取统计栏"已发布"数量"""
        el = self.find((By.XPATH, '//span[contains(text(),"已发布")]/strong'))
        return int(el.text.strip()) if el else 0

    def get_draft_count(self):
        """读取统计栏"草稿"数量"""
        el = self.find((By.XPATH, '//span[contains(text(),"草稿")]/strong'))
        return int(el.text.strip()) if el else 0

    @allure.step("点击文章")
    def click_article_by_index(self, index):
        items = self.find_all(self.article_titles)
        items[index].click()

    @allure.step("点击编辑文章")
    def click_edit_by_index(self, index):
        """点击第N篇文章的编辑按钮（从0开始）"""
        self.find(self.article_items)
        locator = (By.XPATH,
                   f'(//div[contains(@class,"article-actions")])[{index + 1}]'
                   f'//button//span[text()="编辑"]')
        self.click(locator)

    @allure.step("点击删除文章")
    def click_delete_by_index(self, index):
        """点击第N篇文章的删除按钮（从0开始）"""
        self.find(self.article_items)
        locator = (By.XPATH,
                   f'(//div[contains(@class,"article-actions")])[{index + 1}]'
                   f'//button//span[text()="删除"]')
        self.click(locator)

    # ==================== 评论管理 ====================

    def get_comment_contents(self):
        return [el.text for el in self.find_all(self.comment_contents)]

    @allure.step("点击删除评论")
    def click_delete_comment_by_index(self, index):
        items = self.find_all(self.comment_items)
        items[index].find_element(By.XPATH, './/button//span[text()="删除"]').click()

    # ==================== 个人设置 - 个人资料 ====================

    @allure.step("填写昵称")
    def fill_nickname(self, nickname):
        self.input_replace(self.nickname_input, nickname)

    @allure.step("填写简介")
    def fill_bio(self, bio):
        self.input_replace(self.bio_input, bio)

    @allure.step("填写邮箱")
    def fill_email(self, email):
        self.input_replace(self.email_input, email)

    @allure.step("点击保存设置")
    def click_save(self):
        self.click(self.save_button)

    # ==================== 个人设置 - 账户安全 ====================

    @allure.step("点击账户安全")
    def click_security_tab(self):
        """点击账户安全标签页"""
        self.click(self.security_tab)

    @allure.step("填写原密码")
    def fill_old_password(self, pwd):
        """填写原密码"""
        self.input_replace(self.old_password_input, pwd)

    @allure.step("填写新密码")
    def fill_new_password(self, pwd):
        """填写新密码"""
        self.input_replace(self.new_password_input, pwd)

    @allure.step("填写确认密码")
    def fill_confirm_password(self, pwd):
        """填写确认密码"""
        self.input_replace(self.confirm_password_input, pwd)

    @allure.step("点击修改密码")
    def click_change_password(self):
        """点击修改密码按钮"""
        self.click(self.change_password_button)

    @allure.step("修改密码")
    def change_password(self, old_pwd, new_pwd):
        """修改密码的便捷方法：填写原密码、新密码、确认密码，点击修改

        Args:
            old_pwd: 原密码
            new_pwd: 新密码
        """
        self.click_security_tab()
        self.wait_for_page_ready()
        self.fill_old_password(old_pwd)
        self.fill_new_password(new_pwd)
        self.fill_confirm_password(new_pwd)
        self.click_change_password()
        self.wait_for_page_ready()

    # ==================== 个人信息修改（便捷方法） ====================

    def _get_input_value(self, locator):
        """读取 input/textarea 的当前值"""
        el = self.find(locator)
        return el.get_attribute("value") or ""

    def _get_textarea_value(self, locator):
        """读取 textarea 的当前值"""
        el = self.find(locator)
        return el.get_attribute("value") or ""

    @allure.step("修改个人信息")
    def change_profile(self, new_nick=None, new_email=None, new_bio=None):
        """修改个人信息的便捷方法：进入设置页，读取原值，填写新值，保存

        Args:
            new_nick:  新昵称（None 则不修改）
            new_email: 新邮箱（None 则不修改）
            new_bio:   新简介（None 则不修改）

        Returns:
            (orig_nick, orig_email, orig_bio) — 原始值，用于恢复
        """
        self.click_settings()
        self.wait_for_page_ready()

        # 读取原始值
        orig_nick = self._get_input_value(self.nickname_input)
        orig_email = self._get_input_value(self.email_input)
        orig_bio = self._get_textarea_value(self.bio_input)

        # 填写新值
        if new_nick is not None:
            self.fill_nickname(new_nick)
        if new_email is not None:
            self.fill_email(new_email)
        if new_bio is not None:
            self.fill_bio(new_bio)

        self.click_save()
        self.wait_for_page_ready()
        return orig_nick, orig_email, orig_bio

    @allure.step("恢复个人信息")
    def restore_profile(self, orig_nick, orig_email, orig_bio):
        """恢复个人信息到原始值

        Args:
            orig_nick:  原始昵称
            orig_email: 原始邮箱
            orig_bio:   原始简介
        """
        self.click_settings()
        self.wait_for_page_ready()
        self.fill_nickname(orig_nick)
        self.fill_email(orig_email)
        self.fill_bio(orig_bio)
        self.click_save()
        self.wait_for_page_ready()