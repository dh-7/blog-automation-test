import pytest
from utils.excel_loader import load_ui_cases
from page.page_publish_article import PagePublishArticle
from page.page_article_detail import PageArticleDetail
from utils.paths import UI_DATASOURCE as DATASOURCE
from utils import db_query
from utils.assert_helpers import auto_assert, assert_url, assert_toast
from case.conftest import login
import allure


_params, _ids = load_ui_cases(module='发布文章')


def _publish(driver, u, p, title, content, publish_url, category_name=None, tag_names=None):
    """登录并发布文章辅助函数"""
    login(driver, u, p)
    page = PagePublishArticle(driver)
    page.open_url(publish_url)
    page.wait_for_page_ready()
    page.input_title(title)
    if category_name and category_name != "（不选）":
        page.select_category(category_name)
    if tag_names:
        for tag in tag_names:
            if tag and tag != "（不选）":
                page.select_tag(tag)
    page.input_content(content)
    page.click_publish()
    page.wait_for_page_ready()


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.BLOCKER)
@allure.feature("发布文章")
class TestPublishArticle:
    """发布文章功能 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_publish_article(self, driver, case_id, case):
        page = PagePublishArticle(driver)
        publish_url = case.resolved_path()
        u = case.login_user or 'zhangsan'
        p = case.login_password or '123456'

        # FC-FBWZ-001: 发布页面元素显示完整性
        if case_id == 'FC-FBWZ-001':
            login(driver, u, p)
            page.open_url(publish_url)
            page.wait_for_page_ready()
            auto_assert(page, driver, case.expected)
            return

        # FC-FBWZ-008: 发布成功后作者自动显示为当前登录用户（检查头像）
        if case_id == 'FC-FBWZ-008':
            title = case.field('标题', '测试文章_作者验证')
            content = case.field('内容', '测试内容')
            _publish(driver, u, p, title, content, publish_url)
            # 发布成功后应跳转到首页
            from page.page_home import PageHome
            home = PageHome(driver)
            # 验证跳转到首页
            current_url = driver.current_url
            base_url = driver.current_url.split('/')[0] + '//' + driver.current_url.split('/')[2]
            assert '/' == current_url.replace(base_url, '') or '/?' in current_url or current_url.endswith('/'), \
                f"发布成功后应跳转到首页，实际URL={current_url}"
            home.wait_for_page_ready()
            # 断言右上角用户头像显示（说明已登录且头像正常展示）
            assert home.is_user_avatar_displayed(), "发布成功后首页右上角应显示用户头像"
            return

        # FC-FBWZ-009: 新发布的文章浏览量初始显示为0
        if case_id == 'FC-FBWZ-009':
            title = case.field('标题', '测试文章_浏览量验证')
            content = case.field('内容', '测试内容')
            _publish(driver, u, p, title, content, publish_url)
            # 通过 DB 定位刚发布的文章，显式打开详情页校验浏览量为 0
            aid = db_query.article_id_by_title(title)
            assert aid, f"新发布文章'{title}'应已入库"
            detail = PageArticleDetail(driver)
            detail.open_url(f'/article/{aid}')
            detail.wait_for_page_ready()
            vc = detail.get_view_count_int()
            assert vc == 0, f"新发布文章浏览量应为0，实际={vc}"
            return

        # FC-FBWZ-004: 不填写摘要系统自动截取正文前150字（DB 回查摘要内容）
        if case_id == 'FC-FBWZ-004':
            title = case.field('标题', '测试文章')
            content = case.field('内容', '测试内容')
            _publish(driver, u, p, title, content, publish_url)
            aid = db_query.article_id_by_title(title)
            assert aid, f"发布的文章'{title}'应已入库"
            summary = db_query.article_field(aid, 'summary') or ''
            assert summary == content[:150],                 f"摘要应自动截取正文前150字: 摘要长度={len(summary)}, 预期长度={len(content[:150])}"
            return

        # FC-FBWZ-005: 不选择分类和标签直接发布成功（详情页无分类无标签）
        if case_id == 'FC-FBWZ-005':
            from selenium.webdriver.common.by import By
            title = case.field('标题', '测试文章')
            _publish(driver, u, p, title, case.field('内容', '正文内容'), publish_url)
            aid = db_query.article_id_by_title(title)
            assert aid, f"发布的文章'{title}'应已入库"
            detail = PageArticleDetail(driver)
            detail.open_url(f'/article/{aid}')
            detail.wait_for_page_ready()
            cat_els = driver.find_elements(By.CSS_SELECTOR, ".category-name")
            assert all(not e.text.strip() for e in cat_els),                 f"文章不应有分类，实际={[e.text for e in cat_els]}"
            tag_els = driver.find_elements(By.CSS_SELECTOR, ".article-tags .tag")
            assert len(tag_els) == 0,                 f"文章不应有标签，实际={[e.text for e in tag_els]}"
            return

        # FC-FBWZ-006: 标题为空发布失败 — 不填标题，依赖Excel数据源中的空值
        if case_id == 'FC-FBWZ-006':
            content = case.field('内容', '测试内容')
            _publish(driver, u, p, '', content, publish_url)
            auto_assert(page, driver, case.expected)
            return

        # FC-FBWZ-007: 内容为空发布失败 — 不填内容，依赖Excel数据源中的空值
        if case_id == 'FC-FBWZ-007':
            title = case.field('标题', '测试文章')
            _publish(driver, u, p, title, '', publish_url)
            auto_assert(page, driver, case.expected)
            return

        # FC-FBWZ-002: 填写完整信息发布文章成功（新文章应出现在列表）
        if case_id == 'FC-FBWZ-002':
            title = case.field('标题', '测试文章标题')
            _publish(driver, u, p, title, case.field('内容', '测试内容'),
                     publish_url, category_name=case.field('分类'))
            from page.page_home import PageHome
            home = PageHome(driver)
            home.wait_for_page_ready()
            titles = home.get_all_article_titles()
            assert any(title in t for t in titles),                 f"发布成功后新文章'{title}'应出现在文章列表中"
            return

        # FC-FBWZ-003: 存为草稿成功
        if case_id == 'FC-FBWZ-003':
            title = case.field('标题', '测试草稿文章')
            content = case.field('内容', '测试内容')
            login(driver, u, p)
            page.open_url(publish_url)
            page.wait_for_page_ready()
            page.input_title(title)
            page.input_content(content)
            page.click_draft()
            page.wait_for_page_ready()
            # DB 回查：该文章为草稿状态（status=0）
            aid = db_query.article_id_by_title(title)
            assert aid, "草稿文章应已入库"
            assert db_query.article_field(aid, 'status') == 0,                 f"存为草稿后 status 应为 0，实际={db_query.article_field(aid, 'status')}"
            # 公开列表不可见
            from page.page_home import PageHome
            home = PageHome(driver)
            home.open_url('/')
            home.wait_for_page_ready()
            assert title not in home.get_all_article_titles(),                 "草稿文章不应出现在公开文章列表"
            return

        # 通用发布文章流程（FC-FBWZ-002 ~ FC-FBWZ-005）
        title = case.field('标题', '测试文章')
        content = case.field('内容', '测试内容')
        category = case.field('分类')

        tag_str = case.field('标签')
        tag_names = [t.strip() for t in tag_str.split(',') if t.strip()] if tag_str else None

        _publish(
            driver, u, p, title, content,
            publish_url,
            category_name=category, tag_names=tag_names
        )
        auto_assert(page, driver, case.expected)
