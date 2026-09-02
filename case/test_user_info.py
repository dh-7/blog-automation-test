import pytest
import logging
from base.data_loader import UiDataLoader
from page.page_personal import PagePersonal
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

log = logging.getLogger(__name__)


_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module='用户信息')
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("用户信息")
class TestUserInfo:
    """用户信息 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_user_info(self, driver, case_id, case):
        page = PagePersonal(driver)
        url = case.resolved_path()
        u = case.login_user or 'zhangsan'
        p = case.login_password or '123456'

        # FC-YHXX-001: 个人中心页面显示用户完整信息
        if case_id == 'FC-YHXX-001':
            page.login_and_open(u, p, url)
            auto_assert(page, driver, case.expected)
            return

        # FC-YHXX-002: 页面不显示密码相关信息
        if case_id == 'FC-YHXX-002':
            page.login_and_open(u, p, url)
            page_source = driver.page_source
            assert '密码' not in page_source or 'password' not in page_source.lower(), \
                "页面不应显示密码相关信息"
            auto_assert(page, driver, case.expected)
            return

        # FC-YHXX-003: 只修改昵称保存成功
        if case_id == 'FC-YHXX-003':
            page.login_and_open(u, p, url)
            nickname = case.field('新昵称', '新的昵称')
            orig_nick, orig_email, orig_bio = page.change_profile(new_nick=nickname)
            try:
                auto_assert(page, driver, case.expected)
            finally:
                try:
                    page.login_and_open(u, p, url)
                    page.restore_profile(orig_nick, orig_email, orig_bio)
                except Exception as e:
                    log.warning(f"恢复原始昵称失败: {e}")
            return

        # FC-YHXX-004: 修改全部个人信息保存成功
        if case_id == 'FC-YHXX-004':
            page.login_and_open(u, p, url)
            nickname = case.field('新昵称', '全量更新昵称')
            email = case.field('新邮箱', 'new@example.com')
            bio = case.field('新简介', '更新后的简介')
            orig_nick, orig_email, orig_bio = page.change_profile(
                new_nick=nickname, new_email=email, new_bio=bio
            )
            try:
                auto_assert(page, driver, case.expected)
            finally:
                try:
                    page.login_and_open(u, p, url)
                    page.restore_profile(orig_nick, orig_email, orig_bio)
                except Exception as e:
                    log.warning(f"恢复原始个人信息失败: {e}")
            return

        # FC-YHXX-005: 不修改任何内容直接保存信息不变
        if case_id == 'FC-YHXX-005':
            page.login_and_open(u, p, url)
            page.click_settings()
            page.click_save()
            auto_assert(page, driver, case.expected)
            page.wait_for_page_ready()
            return

        # FC-YHXX-006: 未登录用户访问个人中心跳转登录页
        if case_id == 'FC-YHXX-006':
            page.open_url(url)
            page.wait_for_page_ready()
            auto_assert(page, driver, case.expected)
            return

        # 兜底
        page.login_and_open(u, p, url)
        auto_assert(page, driver, case.expected)
