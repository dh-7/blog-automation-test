import pytest
from base.data_loader import UiDataLoader
from page.page_publish_article import PagePublishArticle
from utils.paths import UI_DATASOURCE as DATASOURCE
from utils.assert_helpers import auto_assert, assert_url
from case.conftest import login
import allure


_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module='修改文章')
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("修改文章")
class TestEditArticle:
    """修改文章 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_edit_article(self, driver, case_id, case):
        page = PagePublishArticle(driver)
        edit_url = case.resolved_path()
        u = case.login_user or 'zhangsan'
        p = case.login_password or '123456'

        # FC-XGWZ-001: 修改页面自动回显原有信息
        if case_id == 'FC-XGWZ-001':
            login(driver, u, p)
            page.open_url(edit_url)
            page.wait_for_page_ready()
            # 验证编辑模式，原有信息应自动回显
            assert page.is_edit_mode(), "应进入编辑模式"
            auto_assert(page, driver, case.expected)
            return

        # FC-XGWZ-002: 修改自己的文章标题和内容成功
        if case_id == 'FC-XGWZ-002':
            title = case.field('新标题', '修改后的标题')
            content = case.field('新内容', '修改后的内容')
            login(driver, u, p)
            page.open_url(edit_url)
            page.wait_for_page_ready()
            page.input_title(title)
            page.input_content(content)
            page.click_save_edit()
            auto_assert(page, driver, case.expected)
            page.wait_for_page_ready()
            return

        # FC-XGWZ-003: 只修改标题其他字段保持原样
        if case_id == 'FC-XGWZ-003':
            title = case.field('新标题', '只改标题')
            # 只传标题，内容传空表示保持原样
            login(driver, u, p)
            page.open_url(edit_url)
            page.wait_for_page_ready()
            page.input_title(title)
            page.input_content('')
            page.click_save_edit()
            auto_assert(page, driver, case.expected)
            page.wait_for_page_ready()
            return

        # FC-XGWZ-004: 尝试修改别人的文章提示无权
        if case_id == 'FC-XGWZ-004':
            title = case.field('新标题', '尝试修改')
            content = case.field('新内容', '尝试修改内容')
            # 使用非文章所有者的账号登录尝试编辑
            other_user = case.login_user or 'lisi'
            other_pass = case.login_password or '123456'
            login(driver, other_user, other_pass)
            page.open_url(edit_url)
            page.wait_for_page_ready()
            page.input_title(title)
            page.input_content(content)
            page.click_save_edit()
            auto_assert(page, driver, case.expected)
            page.wait_for_page_ready()
            return

        # FC-XGWZ-005: 访问已删除文章的修改页面提示不存在
        if case_id == 'FC-XGWZ-005':
            # 尝试打开不存在的文章编辑页面
            case.fields['文章ID'] = case.field('已删除文章的ID', '999')
            login(driver, u, p)
            page.open_url(case.resolved_path())
            page.wait_for_page_ready()
            auto_assert(page, driver, case.expected)
            return

        # 兜底
        title = case.field('新标题', '')
        content = case.field('新内容', '')
        login(driver, u, p)
        page.open_url(edit_url)
        page.wait_for_page_ready()
        page.input_title(title)
        page.input_content(content)
        page.click_save_edit()
        auto_assert(page, driver, case.expected)
        page.wait_for_page_ready()
