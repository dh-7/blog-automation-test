"""UI 业务流程测试 — 作者发布文章流程（YW-FBWZ 系列）（自 test_business_flow_ui.py 拆分）"""
import allure
from selenium.webdriver.common.by import By
from page.page_home import PageHome
from page.page_publish_article import PagePublishArticle
from utils import db_query
from case.flow_common import FlowBase, _c, _publish_article, _save_as_draft


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.BLOCKER)
@allure.feature("作者发布文章")
class TestAuthorPublishFlow(FlowBase):

    login_case_id = "YW-FBWZ-001"  # 同模块账号相同，取第一条即可

    def test_publish_full_flow(self):
        """YW-FBWZ-001: 完整发布流程"""
        c = _c("YW-FBWZ-001")
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), c.field("内容"),
            category_name=c.field("分类"),
        )
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        titles = home.get_all_article_titles()
        assert any(c.field("标题") in t for t in titles),             f"发布成功后新文章'{c.field('标题')}'应出现在列表中"
        assert home.get_article_count() > 0

    def test_save_draft_flow(self):
        """YW-FBWZ-002: 保存草稿流程"""
        c = _c("YW-FBWZ-002")
        _save_as_draft(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), c.field("内容"),
        )
        assert "/write" not in self.driver.current_url
        # DB 回查：状态为草稿；公开列表不可见
        aid = db_query.article_id_by_title(c.field("标题"))
        assert aid, "草稿文章应已入库"
        assert db_query.article_field(aid, "status") == 0, "草稿状态应为0"
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        assert c.field("标题") not in home.get_all_article_titles(),             "草稿不应出现在公开列表"

    def test_edit_after_publish_flow(self):
        """YW-FBWZ-003: 发布后修改流程"""
        c = _c("YW-FBWZ-003")
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            c.field("新标题"), "原始内容",
        )
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        titles = home.get_all_article_titles()
        assert any(c.field("新标题") in t for t in titles),             f"修改后的标题'{c.field('新标题')}'应在列表中可见"
        assert home.get_article_count() > 0

    def test_empty_title_fail_flow(self):
        """YW-FBWZ-004: 标题为空发布失败"""
        c = _c("YW-FBWZ-004")
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            "", c.field("内容"),
        )
        assert "/write" in self.driver.current_url
        from page.page_publish_article import PagePublishArticle
        pub = PagePublishArticle(self.driver)
        import time as _t
        err = None
        for _ in range(16):
            errs = self.driver.find_elements(By.CSS_SELECTOR, ".el-form-item__error")
            if any("标题" in e.text for e in errs):
                err = errs[0]
                break
            _t.sleep(0.5)
        assert err, "标题为空发布应提示'请输入标题'"

    def test_empty_content_fail_flow(self):
        """YW-FBWZ-005: 内容为空发布失败"""
        c = _c("YW-FBWZ-005")
        _publish_article(
            self.driver,
            c.login_user, c.login_password,
            c.field("标题"), "",
        )
        assert "/write" in self.driver.current_url
        from page.page_publish_article import PagePublishArticle
        pub = PagePublishArticle(self.driver)
        import time as _t
        err = None
        for _ in range(16):
            errs = self.driver.find_elements(By.CSS_SELECTOR, ".el-form-item__error")
            if any("内容" in e.text for e in errs):
                err = errs[0]
                break
            _t.sleep(0.5)
        assert err, "内容为空发布应提示'请输入内容'"
