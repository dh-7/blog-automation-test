import pytest
from base.data_loader import UiDataLoader
from page.page_login import PageLogin
from page.page_personal import PagePersonal
from utils.paths import UI_DATASOURCE as DATASOURCE
from utils.assert_helpers import auto_assert, assert_url
import allure


_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module='修改密码')
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("修改密码")
class TestChangePassword:
    """修改密码 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_change_password(self, driver, case_id, case):
        page = PagePersonal(driver)
        login_page = PageLogin(driver)
        url = case.resolved_path()
        u = case.login_user or 'zhangsan'
        p = case.login_password or '123456'

        # FC-XGMM-001: 修改密码成功后旧密码失效新密码生效
        if case_id == 'FC-XGMM-001':
            page.login_and_open(u, p, url)
            page.change_password('123456', 'newpass123')
            # 验证旧密码失效
            login_page.open_url()
            login_page.input_username('zhangsan')
            login_page.input_password('123456')
            login_page.click_login_button()
            login_page.wait_for_page_ready()
            old_result = login_page.get_fail_result()
            assert old_result, "旧密码登录应失败"
            # 验证新密码生效
            login_page.open_url()
            login_page.input_username('zhangsan')
            login_page.input_password('newpass123')
            login_page.click_login_button()
            login_page.wait_for_login_success()
            assert_url(login_page, driver, '/')
            # 恢复密码为原始值
            page.login_and_open('zhangsan', 'newpass123', url)
            page.change_password('newpass123', '123456')
            return

        # FC-XGMM-002: 修改密码失败-原密码错误
        if case_id == 'FC-XGMM-002':
            page.login_and_open(u, p, url)
            page.change_password('wrongpass', 'newpass123')
            auto_assert(page, driver, case.expected)
            return

        # FC-XGMM-003: 修改密码失败-新密码为空
        if case_id == 'FC-XGMM-003':
            page.login_and_open(u, p, url)
            page.change_password('123456', '')
            auto_assert(page, driver, case.expected)
            return

        # FC-XGMM-004: 修改密码失败-新密码与确认密码不一致
        if case_id == 'FC-XGMM-004':
            page.login_and_open(u, p, url)
            page.click_security_tab()
            page.wait_for_page_ready()
            page.fill_old_password('123456')
            page.fill_new_password('newpass123')
            page.fill_confirm_password('differentpass')
            page.click_change_password()
            auto_assert(page, driver, case.expected)
            page.wait_for_page_ready()
            return

        # FC-XGMM-005: 密码修改成功后需要重新登录
        if case_id == 'FC-XGMM-005':
            page.login_and_open(u, p, url)
            page.change_password('123456', 'newpass123')
            # 验证跳转到登录页
            assert_url(login_page, driver, '/login')
            # 恢复密码
            login_page.login_and_navigate('zhangsan', 'newpass123', url)
            page.change_password('newpass123', '123456')
            return

        # 兜底
        page.login_and_open(u, p, url)
        page.click_security_tab()
        auto_assert(page, driver, case.expected)
        page.wait_for_page_ready()
