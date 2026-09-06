import pytest
import allure
from selenium.webdriver.common.by import By
from utils.excel_loader import load_ui_cases
from page.page_login import PageLogin
from page.page_home import PageHome
from utils.assert_helpers import auto_assert, assert_url, assert_toast, assert_form_error
from utils.paths import UI_DATASOURCE as DATASOURCE


_params, _ids = load_ui_cases(module='登录')


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.BLOCKER)
@allure.feature("登录")
class TestLogin:
    """登录功能 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_login(self, driver, case_id, case):
        allure.dynamic.title(f"[{case_id}] {case.title}")
        allure.dynamic.story("登录")
        page = PageLogin(driver)

        # FC-DL-001: 页面元素检查（用户名输入框、密码输入框、登录按钮逐项校验）
        if case_id == 'FC-DL-001':
            with allure.step("打开登录页"):
                page.open_url(case.resolved_path())
                page.wait_for_page_ready()
            with allure.step("验证页面元素"):
                assert driver.find_elements(By.CSS_SELECTOR, 'input[placeholder="请输入用户名"]'),                     "登录页应显示用户名输入框"
                assert driver.find_elements(By.CSS_SELECTOR, 'input[placeholder="请输入密码"]'),                     "登录页应显示密码输入框"
                assert driver.find_elements(By.XPATH, '//button//span[text()="登录"]'),                     "登录页应显示登录按钮"
            return

        # FC-DL-009: 错误用户名和错误密码的提示信息一致
        if case_id == 'FC-DL-009':
            scene1_raw = case.field('场景1', 'notexist999/123456')
            scene2_raw = case.field('场景2', 'zhangsan/wrongpwd')
            u1, p1 = scene1_raw.split('/', 1)
            u2, p2 = scene2_raw.split('/', 1)
            with allure.step("场景1: 错误用户名"):
                page.open_url(case.resolved_path())
                page.wait_for_page_ready()
                page.input_username(u1)
                page.input_password(p1)
                page.click_login_button()
                # get_fail_result 自带等待；此处不能再 wait_for_page_ready（会等过期 3 秒的 toast）
                error1 = page.get_fail_result()
            with allure.step("场景2: 错误密码"):
                page.open_url(case.resolved_path())
                page.wait_for_page_ready()
                page.input_username(u2)
                page.input_password(p2)
                page.click_login_button()
                error2 = page.get_fail_result()
            with allure.step("验证提示信息一致"):
                assert error1 == error2, f"两次错误提示不一致: '{error1}' vs '{error2}'"
                assert "用户名或密码错误" in error1,                     f"提示信息应为'用户名或密码错误'，实际='{error1}'"
            return

        # FC-DL-010: 登录成功后页面显示当前用户的昵称和头像
        if case_id == 'FC-DL-010':
            u = case.login_user or 'zhangsan'
            p = case.login_password or '123456'
            with allure.step(f"登录: {u}"):
                page.open_url(case.resolved_path())
                page.input_username(u)
                page.input_password(p)
                page.click_login_button()
                page.wait_for_login_success()
            with allure.step("验证登录后显示用户信息"):
                if case.role == 'ADMIN':
                    from page.page_admin_dashboard import PageAdminDashboard
                    admin_page = PageAdminDashboard(driver)
                    nickname = admin_page.get_text(admin_page.user_display)
                    assert nickname and nickname.strip(), "管理员登录后应显示用户昵称"
                else:
                    # 验证头像显示
                    user_avatar = driver.find_elements(By.CSS_SELECTOR, '.user-avatar')
                    assert user_avatar, "普通用户登录后导航栏应显示头像"
                    # 点击头像验证下拉菜单
                    user_avatar[0].click()
                    # 等待 dropdown 菜单项出现（替代 sleep 等动画）
                    from selenium.webdriver.support.wait import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, '.el-dropdown-menu__item')
                            )
                        )
                    except Exception:
                        pass
                    # Element Plus el-dropdown 的菜单项
                    dropdown_items = driver.find_elements(By.CSS_SELECTOR, '.el-dropdown-menu__item')
                    if not dropdown_items:
                        # 可能使用不同选择器
                        dropdown_items = driver.find_elements(By.CSS_SELECTOR, '.el-dropdown-menu__item, .el-dropdown__item')
                    dropdown_texts = [item.text for item in dropdown_items]
                    # 至少应有个人中心和退出登录
                    has_profile = any('个人中心' in t for t in dropdown_texts)
                    has_logout = any('退出' in t for t in dropdown_texts)
                    assert has_profile or has_logout, \
                        f"下拉菜单应包含'个人中心'或'退出登录'，实际={dropdown_texts}"
            return

        # 通用登录流程
        username = case.login_user
        password = case.login_password
        with allure.step(f"登录: {username}"):
            page.open_url(case.resolved_path())
            page.input_username(username)
            page.input_password(password)
            page.click_login_button()
            # 登录成功用例需等待跳转完成；登录失败用例停留在登录页，由 auto_assert 校验错误提示
            if "失败" not in case.expected:
                page.wait_for_login_success()
        with allure.step("验证结果"):
            if "失败" not in case.expected and username == "admin":
                # 管理员登录后的"首页"即后台 /admin（应用行为）
                from urllib.parse import urlparse
                path = urlparse(driver.current_url).path
                assert path.startswith("/admin"),                     f"管理员登录后应进入后台，实际 path={path}"
                return
            auto_assert(page, driver, case.expected)
            page.wait_for_page_ready()
