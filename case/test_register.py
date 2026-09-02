import pytest
from selenium.webdriver.common.by import By
from base.data_loader import UiDataLoader
from page.page_register import PageRegister
from page.page_login import PageLogin
from utils.paths import UI_DATASOURCE as DATASOURCE
from utils.assert_helpers import auto_assert, assert_url, assert_toast, assert_form_error
import allure


_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module='注册')
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("注册")
class TestRegister:
    """注册功能 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_register(self, driver, case_id, case):
        page = PageRegister(driver)

        # FC-ZC-001: 注册页面元素显示完整性
        if case_id == 'FC-ZC-001':
            page.open_url(case.resolved_path())
            page.wait_for_page_ready()
            auto_assert(page, driver, case.expected)
            return

        # FC-ZC-013: 注册成功后默认为普通用户角色
        # 预期: 角色为USER（普通用户），不是ADMIN
        if case_id == 'FC-ZC-013':
            username = case.login_user or ''
            nickname = case.field('昵称', '测试用户')
            email = case.field('邮箱', 'test@example.com')
            password = case.login_password or '123456'
            confirm_password = case.field('确认密码', password)
            page.open_url(case.resolved_path())
            page.input_username(username)
            page.input_nickname(nickname)
            page.input_email(email)
            page.input_password(password)
            page.input_confirm_password(confirm_password)
            page.click_register_button()
            page.wait_for_page_ready()
            assert_url(page, driver, '/login')
            # 登录新账号，验证不是管理员（不应有后台管理入口）
            login_page = PageLogin(driver)
            login_page.input_username(username)
            login_page.input_password(password)
            login_page.click_login_button()
            login_page.wait_for_login_success()
            # 管理员登录后导航栏会显示"后台管理"链接，普通用户不会
            # 点击头像展开下拉菜单检查
            user_avatar = driver.find_elements(By.CSS_SELECTOR, '.user-avatar')
            if user_avatar:
                user_avatar[0].click()
                # 等待 dropdown 菜单出现（替代 sleep）
                from selenium.webdriver.support.wait import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                try:
                    WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, '[class*="dropdown-menu"]')
                        )
                    )
                except Exception:
                    pass
                admin_menu_items = driver.find_elements(By.XPATH,
                    '//*[contains(@class,"dropdown-menu")]//*[contains(text(),"后台管理")]')
                assert len(admin_menu_items) == 0, \
                    "新注册用户应为普通用户角色，下拉菜单不应显示后台管理入口"
            auto_assert(page, driver, case.expected)
            return

        # FC-ZC-014: 注册后可直接用新账号登录系统
        if case_id == 'FC-ZC-014':
            username = case.login_user or ''
            nickname = case.field('昵称', '测试用户')
            email = case.field('邮箱', 'test@example.com')
            password = case.login_password or '123456'
            confirm_password = case.field('确认密码', password)
            page.open_url(case.resolved_path())
            page.input_username(username)
            page.input_nickname(nickname)
            page.input_email(email)
            page.input_password(password)
            page.input_confirm_password(confirm_password)
            page.click_register_button()
            page.wait_for_page_ready()
            assert_url(page, driver, '/login')
            # 登录后检查导航栏显示用户信息
            login_page = PageLogin(driver)
            login_page.input_username(username)
            login_page.input_password(password)
            login_page.click_login_button()
            login_page.wait_for_login_success()
            auto_assert(page, driver, case.expected)
            return

        # 通用注册流程
        username = case.login_user or ''
        nickname = case.field('昵称', '测试用户')
        email = case.field('邮箱', 'test@example.com')
        password = case.login_password or ''
        confirm_password = case.field('确认密码', password)
        page.open_url(case.resolved_path())
        page.input_username(username)
        page.input_nickname(nickname)
        page.input_email(email)
        page.input_password(password)
        page.input_confirm_password(confirm_password)
        page.click_register_button()
        auto_assert(page, driver, case.expected)
        page.wait_for_page_ready()
