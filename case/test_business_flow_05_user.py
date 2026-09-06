"""UI 业务流程测试 — 个人信息与密码管理流程（YW-GRXX 系列）（自 test_business_flow_ui.py 拆分）"""
import allure
from page.page_login import PageLogin
from page.page_personal import PagePersonal
from utils.assert_helpers import assert_url
from case.flow_common import FlowBase, login, _c


@allure.epic("UI自动化测试")
@allure.severity(allure.severity_level.NORMAL)
@allure.feature("个人信息与密码管理")
class TestUserInfoFlow(FlowBase):

    def test_modify_info_flow(self):
        """YW-GRXX-001: 修改个人信息"""
        c = _c("YW-GRXX-001")
        login(self.driver, c.login_user, c.login_password)
        personal = PagePersonal(self.driver)
        personal.open_url()
        personal.wait_for_page_ready()
        personal.click_settings()
        personal.wait_for_page_ready()
        personal.fill_nickname(c.field("新昵称"))
        personal.fill_email(c.field("新邮箱"))
        personal.fill_bio(c.field("新简介"))
        personal.click_save()
        personal.wait_for_page_ready()
        # 保存应有成功提示，且重新加载后字段回显所填值
        toast = personal.wait_for_toast("成功", timeout=3)
        assert toast, "保存个人信息应提示成功"
        personal.open_url()
        personal.wait_for_page_ready()
        personal.click_settings()
        personal.wait_for_page_ready()
        from selenium.webdriver.common.by import By
        nick_val = self.driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入昵称"]').get_attribute("value")
        assert nick_val == c.field("新昵称"),             f"重新加载后昵称应回显新值: '{nick_val}' != '{c.field('新昵称')}'"

    def test_change_password_flow(self):
        """YW-GRXX-002: 修改密码成功并验证新旧密码完整流程"""
        c = _c("YW-GRXX-002")
        old_pwd, new_pwd = c.field('原密码'), c.field('新密码')
        personal = PagePersonal(self.driver)
        lp = PageLogin(self.driver)

        login(self.driver, c.login_user, c.login_password)            # ① 原密码登录

        # ② 修改密码：原密码 → 新密码（复用现有便捷方法）
        personal.open_url(c.page_path + '/settings')
        personal.wait_for_page_ready()
        personal.change_password(old_pwd, new_pwd)
        personal.wait.until(lambda d: PageLogin.page_path in d.current_url)  # 等跳转登录页

        # ③ 旧密码登录失败：错误提示可见（get_fail_result 内置等待）+ 停留登录页
        lp.open_url()
        lp.input_username(c.login_user)
        lp.input_password(old_pwd)
        lp.click_login_button()
        lp.get_fail_result()                                          # 等待"用户名或密码错误"toast
        assert PageLogin.page_path in self.driver.current_url, "旧密码应登录失败"

        # ④ 新密码登录成功：复用 login()（内置等待离开 /login）
        login(self.driver, c.login_user, new_pwd)
        assert PageLogin.page_path not in self.driver.current_url, "新密码应登录成功"

        # ⑤ 恢复原密码：新密码 → 原密码
        personal.open_url(c.page_path + '/settings')
        personal.wait_for_page_ready()
        personal.change_password(new_pwd, old_pwd)
        personal.wait.until(lambda d: PageLogin.page_path in d.current_url)

    def test_wrong_old_password_flow(self):
        """YW-GRXX-003: 原密码错误失败"""
        c = _c("YW-GRXX-003")
        wrong_pwd = c.field("原密码", "wrongpass").split("（")[0]
        new_pwd = c.field("新密码", "newpass456")
        from utils import db_query as _dbq
        _pwd_hash_before = _dbq.scalar("SELECT password FROM user WHERE username=%s",
                                       (c.login_user,))
        login(self.driver, c.login_user, c.login_password)
        personal = PagePersonal(self.driver)
        personal.open_url('/profile/settings')
        personal.wait_for_page_ready()
        personal.click_security_tab()
        personal.wait_for_page_ready()
        personal.fill_old_password(wrong_pwd)
        personal.fill_new_password(new_pwd)
        personal.fill_confirm_password(new_pwd)
        personal.click_change_password()
        # 立即捕获 toast（3 秒即逝，不能先 wait_for_page_ready）
        toast = personal.quick_wait_toast("原密码", timeout=6, interval=0.2)
        assert toast, "原密码错误应有错误提示（toast 含'原密码'）"
        assert "/settings" in self.driver.current_url, "原密码错误应留在设置页"
        # DB 回查：密码未变更
        assert _dbq.scalar("SELECT COUNT(*) FROM user WHERE username=%s AND password=%s",
                           (c.login_user, _pwd_hash_before)) == 1,             "原密码错误时密码不应被修改"

    def test_empty_new_password_flow(self):
        """YW-GRXX-004: 新密码为空失败"""
        c = _c("YW-GRXX-004")
        old_pwd = c.field("原密码", "123456")
        login(self.driver, c.login_user, c.login_password)
        personal = PagePersonal(self.driver)
        personal.open_url('/profile/settings')
        personal.wait_for_page_ready()
        personal.click_security_tab()
        personal.wait_for_page_ready()
        personal.fill_old_password(old_pwd)
        # 新密码留空
        personal.click_change_password()
        personal.wait_for_page_ready()
        toast = personal.wait_for_toast("填写", timeout=5)
        if not toast:
            toast = personal.wait_for_toast("密码", timeout=3)
        assert toast, "新密码为空应有校验提示"
        assert "/settings" in self.driver.current_url, "新密码为空应留在设置页"

    def test_not_login_redirect_flow(self):
        """YW-GRXX-005: 未登录跳转"""
        c = _c("YW-GRXX-005")
        self.driver.delete_all_cookies()
        personal = PagePersonal(self.driver)
        personal.open_url()
        personal.wait_for_page_ready()
        assert_url(personal, self.driver, "/login")
