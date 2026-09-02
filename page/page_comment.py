from selenium.webdriver.common.by import By
from base import BasePage


class PageComment(BasePage):
    """评论组件页面类"""

    def __init__(self, driver):
        """初始化方法"""
        super().__init__(driver)
        # ==================== 评论列表元素 ====================
        self.comment_items = (By.CSS_SELECTOR, ".comment-item")
        self.comment_content = (By.CSS_SELECTOR, ".comment-content")
        self.comment_author = (By.CSS_SELECTOR, ".username")
        self.comment_time = (By.CSS_SELECTOR, ".comment-time")

        # ==================== 回复元素 ====================
        # CommentItem.vue 中回复按钮是 <el-button>，无 .reply-btn class
        self.reply_btn = (By.XPATH, '//div[contains(@class,"comment-actions")]//button[contains(.,"回复")]')
        # 回复输入框：el-input type="textarea" 渲染为 .el-textarea__inner
        self.reply_input = (By.CSS_SELECTOR, ".reply-form .el-textarea__inner")

        # ==================== 删除元素 ====================
        # CommentItem.vue 中删除按钮是 <el-button type="danger">，无 .delete-btn class
        self.delete_btn = (By.XPATH, '//div[contains(@class,"comment-actions")]//button[contains(.,"删除")]')

        # ==================== 评论详情元素 ====================
        # 评论者头像（CommentItem.vue 中 el-avatar）
        self.comment_avatar = (By.CSS_SELECTOR, '.comment-header .el-avatar')
        # 回复目标用户名（"回复 XXX"）
        self.reply_target = (By.CSS_SELECTOR, '.reply-to')

        # ==================== 评论输入元素 ====================
        self.comment_input = (By.CSS_SELECTOR, ".comment-form .el-textarea__inner")
        self.submit_btn = (By.XPATH, '//button[contains(.,"发表评论")]')
        # 未登录时前端不渲染评论表单（ArticleDetail.vue v-if="userStore.isLoggedIn"），
        # 而是显示登录提示条 .login-hint（"登录 后发表评论"），即评论的"请先登录"入口
        self.login_hint = (By.CSS_SELECTOR, ".login-hint")

    # ==================== 评论列表操作 ====================

    def get_comments(self):
        """获取所有评论元素列表"""
        return self.find_all(self.comment_items)

    def get_comment_text(self, index):
        """获取第N条评论内容（从0开始）"""
        items = self.find_all(self.comment_content)
        return items[index].text

    def get_comment_author(self, index):
        """获取第N条评论的作者"""
        items = self.find_all(self.comment_author)
        return items[index].text

    # ==================== 回复操作 ====================

    def click_reply(self, index):
        """点击第N条评论的回复按钮"""
        items = self.find_all(self.reply_btn)
        items[index].click()

    def input_reply(self, text):
        """输入回复内容"""
        # 等待回复表单出现（点击回复按钮后异步渲染）
        self.wait_for_reply_form()
        self.input(self.reply_input, text)

    def wait_for_reply_form(self, timeout=None):
        """等待回复输入框出现"""
        from selenium.webdriver.support import expected_conditions as EC
        t = timeout if timeout is not None else self.timeout
        from selenium.webdriver.support.wait import WebDriverWait
        WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(self.reply_input)
        )

    # ==================== 删除操作 ====================

    def click_delete(self, index):
        """点击第N条评论的删除按钮"""
        items = self.find_all(self.delete_btn)
        items[index].click()

    def has_delete_button(self, index):
        """判断第N条评论是否有删除按钮"""
        try:
            items = self.find_all(self.comment_items)
            # CommentItem.vue 中删除按钮是 el-button[type="danger"] 包含 "删除" 文本
            delete_btns = items[index].find_elements(By.XPATH, './/div[contains(@class,"comment-actions")]//button[contains(.,"删除")]')
            return len(delete_btns) > 0
        except Exception:
            return False

    # ==================== 评论输入操作 ====================

    def input_comment(self, text):
        """输入评论内容"""
        self.input(self.comment_input, text)

    def click_submit(self):
        """点击发表按钮（重渲染竞态防护：stale 自动重新查找重试）"""
        from selenium.common.exceptions import StaleElementReferenceException
        for _ in range(3):
            try:
                self.wait_for_clickable(self.submit_btn)
                self.find(self.submit_btn).click()
                return
            except StaleElementReferenceException:
                self.wait_for_page_ready()
        # 兜底最后一次
        self.click(self.submit_btn)

    # ==================== 未登录访客交互校验 ====================

    def has_comment_form(self):
        """是否存在评论输入表单（未登录时前端不渲染，应不存在）"""
        return self.is_present(self.comment_input) or self.is_present(self.submit_btn)

    def is_login_hint_visible(self):
        """未登录时是否显示'登录 后发表评论'登录提示条"""
        return self.is_present(self.login_hint) and self.find(self.login_hint).is_displayed()


if __name__ == '__main__':
    from utils.driver_manager import DriverManager
    cp = PageComment(DriverManager.get_driver())
    print("评论数:", len(cp.get_comments()))
