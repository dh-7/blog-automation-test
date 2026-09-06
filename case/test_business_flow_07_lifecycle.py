"""UI 业务流程测试 — 文章生命周期流程（YW-SMZQ 系列）（自 test_business_flow_ui.py 拆分）"""
import allure
from selenium.webdriver.common.by import By
from page.page_admin_article_manage import PageAdminArticleManage
from page.page_article_detail import PageArticleDetail
from page.page_home import PageHome
from page.page_personal import PagePersonal
from utils import db_query
from case.flow_common import FlowBase, login, _c, _publish_article, _save_as_draft, _publish_disposable


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.BLOCKER)
@allure.feature("文章生命周期")
class TestArticleLifecycleFlow(FlowBase):

    def test_full_lifecycle_flow(self):
        """YW-SMZQ-001: 完整生命周期"""
        c = _c("YW-SMZQ-001")
        login(self.driver, c.login_user, c.login_password)
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), c.field("文章内容"),
            category_name=c.field("分类"),
        )
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        titles = home.get_all_article_titles()
        assert any(c.field("标题") in t for t in titles),             f"发布后新文章'{c.field('标题')}'应在列表中可见"
        # ── 生命周期收尾：删除文章，验证不可见且关联数据清理 ──
        import re
        aid = db_query.article_id_by_title(c.field("标题"))
        assert aid, "新文章应已入库"
        p_page = PagePersonal(self.driver)
        p_page.open_url()
        p_page.wait_for_page_ready()
        p_page.click_my_articles()
        p_page.wait_for_page_ready()
        my_titles = p_page.get_article_titles()
        idx_list = [i for i, t in enumerate(my_titles) if c.field("标题") in t]
        assert idx_list, f"我的文章中应能看到'{c.field('标题')}'"
        p_page.click_delete_by_index(idx_list[0])
        p_page.wait_for_confirm_dialog()
        p_page.confirm_dialog()
        p_page.wait_for_page_ready()
        assert db_query.article_field(aid, "deleted") == 1, "删除后文章应软删除"
        bad = db_query.article_cascade_cleaned(aid)
        assert not bad, f"删除后关联数据未清理: {bad}"

    def test_draft_to_publish_flow(self):
        """YW-SMZQ-002: 草稿→发布状态切换"""
        c = _c("YW-SMZQ-002")
        login(self.driver, c.login_user, c.login_password)
        _save_as_draft(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), c.field("文章内容"),
        )
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        titles = home.get_all_article_titles()
        assert c.field("标题") not in titles, "草稿不应出现在公开列表"
        # DB 回查：状态为草稿；"我的文章"中可见
        aid = db_query.article_id_by_title(c.field("标题"))
        assert aid, "草稿应已入库"
        assert db_query.article_field(aid, "status") == 0, "草稿状态应为0"
        p_page = PagePersonal(self.driver)
        p_page.open_url()
        p_page.wait_for_page_ready()
        p_page.click_my_articles()
        p_page.wait_for_page_ready()
        assert any(c.field("标题") in t for t in p_page.get_article_titles()),             "草稿应在'我的文章'中可见"

    def test_non_author_no_permission_flow(self):
        """YW-SMZQ-003: 非作者无权修改删除"""
        c = _c("YW-SMZQ-003")
        article_id = c.field("文章ID")
        login(self.driver, c.login_user, c.login_password)

        # 1. 验证无法编辑他人文章：详情页不应显示编辑按钮
        detail = PageArticleDetail(self.driver)
        detail.open_url(f"/article/{article_id}")
        detail.wait_for_page_ready()
        edit_btns = self.driver.find_elements(By.XPATH,
            '//button//span[text()="编辑"]')
        assert len(edit_btns) == 0, "非作者在详情页不应看到编辑按钮"
        target_title = detail.get_title()

        # 2. 验证无法删除他人文章：个人中心"我的文章"不应包含他人文章
        from page.page_personal import PagePersonal
        p_page = PagePersonal(self.driver)
        p_page.open_url()
        p_page.wait_for_page_ready()
        titles = p_page.get_article_titles()
        assert target_title not in titles, "非作者在个人中心不应看到他人文章"

    def test_admin_delete_visible_flow(self):
        """YW-SMZQ-004: 管理员删除后作者不可见"""
        c = _c("YW-SMZQ-004")
        # 自造一篇文章作为删除目标（避免误删种子文章，污染后续用例）
        target_title = "一次性-SMZQ004-待删除文章"
        _publish_disposable(self.driver, "zhangsan", "123456", target_title)
        admin_page = PageAdminArticleManage(self.driver)
        admin_page.login_and_open(c.login_user, c.login_password)
        admin_page.input_search(target_title)
        admin_page.click_search()
        admin_page.wait_for_loading_finish()
        assert admin_page.get_row_count() > 0, f"后台应能搜索到'{target_title}'"
        admin_page.click_delete_by_index(0)
        admin_page.wait_for_confirm_dialog()
        admin_page.confirm_delete()
        admin_page.wait_for_loading_finish()
        home = PageHome(self.driver)
        home.login_and_open("zhangsan", "123456")
        titles = home.get_all_article_titles()
        assert target_title not in titles, "管理员删除的文章不应在作者端可见"

    def test_deleted_article_no_comment_flow(self):
        """YW-SMZQ-005: 删除文章后无法评论"""
        c = _c("YW-SMZQ-005")
        # 自造一篇文章作为删除目标（避免误删种子文章，污染后续用例）
        target_title = "一次性-SMZQ005-待删除文章"
        _publish_disposable(self.driver, "zhangsan", "123456", target_title)
        admin_page = PageAdminArticleManage(self.driver)
        admin_page.login_and_open("admin", "admin123")
        admin_page.input_search(target_title)
        admin_page.click_search()
        admin_page.wait_for_loading_finish()
        assert admin_page.get_row_count() > 0, f"后台应能搜索到'{target_title}'"
        article_id = admin_page.get_article_id(0)
        admin_page.click_delete_by_index(0)
        admin_page.wait_for_confirm_dialog()
        admin_page.confirm_delete()
        admin_page.wait_for_loading_finish()
        # 尝试访问已删除文章的详情页
        detail = PageArticleDetail(self.driver)
        detail.open_url(f"/article/{article_id}")
        detail.wait_for_page_ready()
        # 页面应显示错误/空状态，评论区不应可用
        comment_form = self.driver.find_elements(By.CSS_SELECTOR, ".comment-form")
        page_source = self.driver.page_source
        has_error = "不存在" in page_source or "404" in page_source or len(comment_form) == 0
        assert has_error, "已删除文章不应显示评论区"
