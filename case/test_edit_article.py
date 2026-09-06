import pytest
from utils.excel_loader import load_ui_cases
from page.page_publish_article import PagePublishArticle
from utils import db_query
from utils.paths import UI_DATASOURCE as DATASOURCE
from utils.assert_helpers import auto_assert, assert_url
from case.conftest import login
import allure


_params, _ids = load_ui_cases(module='修改文章')


@allure.epic("UI自动化测试")
@allure.feature("修改文章")
class TestEditArticle:
    """修改文章 — 数据驱动测试"""

    def _js_set_input(self, driver, loc, value):
        """JS 直接设置输入框值并派发 input/change 事件

        编辑页输入框预填旧值，Vue 受控组件会把 el.clear() 的清空"弹回"，
        send_keys 会追加而非替换；JS 设值可一次性可靠替换。
        """
        from selenium.webdriver.common.by import By
        el = driver.find_element(*loc)
        driver.execute_script(
            "const el = arguments[0], val = arguments[1];"
            "el.value = val;"
            "el.dispatchEvent(new Event('input', {bubbles: true}));"
            "el.dispatchEvent(new Event('change', {bubbles: true}));",
            el, value)

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_edit_article(self, driver, case_id, case):
        page = PagePublishArticle(driver)
        edit_url = case.resolved_path()
        u = case.login_user or 'zhangsan'
        p = case.login_password or '123456'

        # FC-XGWZ-001: 修改页面自动回显原有信息（输入框值 == DB 原值）
        if case_id == 'FC-XGWZ-001':
            login(driver, u, p)
            page.open_url(edit_url)
            page.wait_for_page_ready()
            assert page.is_edit_mode(), "应进入编辑模式"
            aid = int(case.field('文章ID'))
            db_title = db_query.article_field(aid, 'title')
            db_content = db_query.article_field(aid, 'content')
            assert page.get_title() == db_title, \
                f"标题未回显: 输入框='{page.get_title()}', DB='{db_title}'"
            assert page.get_content().strip() == db_content.strip(), \
                f"内容未回显: 输入框长度={len(page.get_content())}, DB长度={len(db_content)}"
            return

        # FC-XGWZ-002: 修改自己的文章标题和内容成功（DB 回查）
        if case_id == 'FC-XGWZ-002':
            title = case.field('新标题', '修改后的标题')
            content = case.field('新内容', '修改后的内容')
            aid = int(case.field('文章ID'))
            login(driver, u, p)
            page.open_url(edit_url)
            page.wait_for_page_ready()
            self._js_set_input(driver, page.title_input, title)
            self._js_set_input(driver, page.content_input, content)
            page.click_save_edit()
            page.wait_for_page_ready()
            assert db_query.article_field(aid, 'title') == title, (
                "保存后文章标题应更新为新标题")
            assert db_query.article_field(aid, 'content') == content, (
                "保存后文章内容应更新为新内容")
            return

        # FC-XGWZ-003: 只修改标题其他字段保持原样（DB 回查）
        if case_id == 'FC-XGWZ-003':
            title = case.field('新标题', '只改标题')
            aid = int(case.field('文章ID'))
            orig_content = db_query.article_field(aid, 'content')
            login(driver, u, p)
            page.open_url(edit_url)
            page.wait_for_page_ready()
            self._js_set_input(driver, page.title_input, title)
            page.click_save_edit()
            page.wait_for_page_ready()
            assert db_query.article_field(aid, 'title') == title, (
                "只改标题时新标题应保存")
            assert db_query.article_field(aid, 'content') == orig_content, (
                "只改标题时内容应保持原样")
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
