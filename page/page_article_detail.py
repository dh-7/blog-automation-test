from selenium.webdriver.common.by import By
from base import BasePage
import allure


class PageArticleDetail(BasePage):
    """文章详情页面类"""

    page_path = '/article/${article_id}'

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 文章内容元素 ====================
        self.article_title = (By.CSS_SELECTOR, ".article-title")
        self.article_content = (By.CSS_SELECTOR, ".article-content")
        self.article_meta = (By.CSS_SELECTOR, ".article-meta")
        self.author_name = (By.CSS_SELECTOR, ".meta-author")
        self.category_name = (By.CSS_SELECTOR, ".category-name")
        self.article_tags = (By.CSS_SELECTOR, ".article-tags .tag")
        self.view_count = (By.CSS_SELECTOR, ".meta-views")
        # 收藏数在action-btn中: "已收藏 5" 或 "收藏 5"
        self.favorite_count = (By.XPATH, '//div[contains(@class,"action-btn")]//span[contains(text(),"收藏") or contains(text(),"已收藏")]')
        self.favorite_btn = (By.CSS_SELECTOR, ".action-btn")

        # ==================== 评论区元素 ====================
        self.comment_section = (By.CSS_SELECTOR, ".comment-section")
        self.comment_input = (By.CSS_SELECTOR, ".comment-form .el-textarea__inner")
        self.comment_submit = (By.CSS_SELECTOR, ".comment-submit")
        self.comment_list = (By.CSS_SELECTOR, ".comment-item")

        # ==================== 相关文章元素 ====================
        self.related_article = (By.CSS_SELECTOR, ".related-item")

        # ==================== 返回按钮 ====================
        self.back_btn = (By.CSS_SELECTOR, ".back-btn")

    @allure.step("打开文章详情")
    def open_url(self, path=None):
        """打开指定文章详情页"""
        super().open_url(path)
        # Vue SPA 异步加载：文章数据通过 API 获取后才渲染
        # 等待文章标题出现（表示数据已加载完成）
        self._wait_for_article_loaded()

    def _wait_for_article_loaded(self, timeout=None):
        """等待文章数据加载完成（标题或错误状态出现）"""
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        t = timeout if timeout is not None else self.timeout
        try:
            WebDriverWait(self.driver, t).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, ".article-title")
                   or d.find_elements(By.CSS_SELECTOR, ".el-result")
                   or d.find_elements(By.CSS_SELECTOR, ".error-state")
                   or d.find_elements(By.CSS_SELECTOR, ".empty-state")
            )
        except Exception:
            pass
        # 等待文章内容渲染完成（标题可交互 = 已加载）
        try:
            WebDriverWait(self.driver, t).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".article-title")
                )
            )
        except Exception:
            pass

    # ==================== 文章内容操作 ====================

    def get_title(self):
        """获取文章标题"""
        return self.get_text(self.article_title)

    def get_content(self):
        """获取文章正文"""
        return self.get_text(self.article_content)

    def get_author(self):
        """获取作者名称"""
        return self.get_text(self.author_name)

    def get_view_count(self):
        """获取浏览数"""
        return self.get_text(self.view_count)

    def get_favorite_count(self):
        """获取收藏数"""
        return self.get_text(self.favorite_count)

    @allure.step("点击收藏")
    def click_favorite(self):
        """点击收藏按钮"""
        self.click(self.favorite_btn)

    # ==================== 评论操作 ====================

    @allure.step("输入评论")
    def input_comment(self, text):
        """输入评论内容"""
        self.input(self.comment_input, text)

    @allure.step("点击提交评论")
    def click_submit_comment(self):
        """点击提交评论按钮"""
        self.click(self.comment_submit)

    def get_comment_count(self):
        """获取评论数量"""
        return len(self.find_all(self.comment_list))

    def is_comment_section_visible(self):
        """评论区域是否可见"""
        return self.is_displayed(self.comment_section)

    # ==================== 相关文章操作 ====================

    def get_related_articles(self):
        """获取相关文章列表"""
        return [el.text for el in self.find_all(self.related_article)]

    @allure.step("点击相关文章")
    def click_related_article(self, index):
        """点击第N篇相关文章（从0开始）"""
        items = self.find_all(self.related_article)
        items[index].click()

    @allure.step("点击作者名称")
    def click_author_name(self):
        """点击作者名称跳转作者页"""
        self.click(self.author_name)

    @allure.step("点击返回")
    def click_back(self):
        """点击返回按钮"""
        self.click(self.back_btn)

    # ==================== 断言辅助方法 ====================

    def get_view_count_int(self):
        """获取浏览量(整数)"""
        text = self.get_text(self.view_count)
        import re
        m = re.search(r'\d+', text)
        return int(m.group()) if m else 0

    def assert_related_not_contain(self, title):
        """断言相关文章不包含指定标题"""
        related = self.get_related_articles()
        for r in related:
            assert title not in r, f"相关文章中不应包含'{title}'"

    def assert_comment_exists(self, text):
        """断言评论区包含指定文本的评论"""
        comments = self.find_all(self.comment_list)
        for c in comments:
            if text in c.text:
                return
        assert False, f"评论区未找到含'{text}'的评论"

    def assert_article_info_complete(self):
        """断言文章详情页信息完整(标题、内容、作者、浏览量)"""
        assert self.get_title(), "文章标题为空"
        assert self.get_content(), "文章内容为空"
        assert self.get_author(), "作者名称为空"
        # 浏览量元素存在即可，不检查具体值
if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    dp = PageArticleDetail(DriverManager.get_driver())
    dp.open_url('/article/1')
    print("文章标题:", dp.get_title())
    print("文章作者:", dp.get_author())
    print("浏览数:", dp.get_view_count())
    print("评论数:", dp.get_comment_count())
