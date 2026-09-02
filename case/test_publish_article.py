import pytest
from base.data_loader import UiDataLoader
from page.page_publish_article import PagePublishArticle
from page.page_article_detail import PageArticleDetail
from utils.paths import UI_DATASOURCE as DATASOURCE
from utils.assert_helpers import auto_assert, assert_url, assert_toast
from case.conftest import login
import allure


_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module='发布文章')
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


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
            auto_assert(page, driver, case.expected)
            return

        # FC-FBWZ-009: 新发布的文章浏览量初始显示为0
        if case_id == 'FC-FBWZ-009':
            title = case.field('标题', '测试文章_浏览量验证')
            content = case.field('内容', '测试内容')
            _publish(driver, u, p, title, content, publish_url)
            # 发布成功后，检查文章详情页浏览量
            detail = PageArticleDetail(driver)
            current_url = driver.current_url
            import re
            article_id_match = re.search(r'/article/(\d+)', current_url)
            if article_id_match:
                view_count = detail.get_view_count()
                import re as regex
                vc = regex.search(r'\d+', str(view_count))
                assert vc and vc.group() == '0', f"新发布文章浏览量应为0，实际={view_count}"
            auto_assert(page, driver, case.expected)
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
            auto_assert(page, driver, case.expected)
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
