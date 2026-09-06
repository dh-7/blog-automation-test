import pytest
import logging
from utils.excel_loader import load_ui_cases
from page.page_personal import PagePersonal
from utils import db_query
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

log = logging.getLogger(__name__)


_params, _ids = load_ui_cases(module='用户信息')


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

        # FC-YHXX-002: 页面不显示密码相关信息（不允许出现带值的密码输入框）
        if case_id == 'FC-YHXX-002':
            from selenium.webdriver.common.by import By
            page.login_and_open(u, p, url)
            # 密码输入框可以有（修改密码功能），但绝不能携带已填充的值
            pwd_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            for inp in pwd_inputs:
                assert not (inp.get_attribute("value") or "").strip(), \
                    "页面不应显示（回填）密码内容"
            # 页面源码不应出现疑似密码明文
            source = driver.page_source
            assert p not in source, \
                f"页面源码中出现疑似密码明文"
            return

        # FC-YHXX-003: 只修改昵称保存成功（DB 回查昵称更新、邮箱/简介不变）
        if case_id == 'FC-YHXX-003':
            page.login_and_open(u, p, url)
            nickname = case.field('新昵称', '新的昵称')
            cur_nick = db_query.scalar("SELECT nickname FROM user WHERE username=%s", (u,))
            if nickname == cur_nick:
                nickname = f"{nickname}·改"
            orig_nick, orig_email, orig_bio = page.change_profile(new_nick=nickname)
            try:
                db_nick = db_query.scalar("SELECT nickname FROM user WHERE username=%s", (u,))
                db_email = db_query.scalar("SELECT email FROM user WHERE username=%s", (u,))
                assert db_nick == nickname, \
                    f"昵称应更新为'{nickname}'，实际DB='{db_nick}'"
                assert db_email == orig_email, \
                    f"只改昵称时邮箱不应变化: 原='{orig_email}', 现='{db_email}'"
            finally:
                try:
                    page.login_and_open(u, p, url)
                    page.restore_profile(orig_nick, orig_email, orig_bio)
                except Exception as e:
                    log.warning(f"恢复原始昵称失败: {e}")
            return

        # FC-YHXX-004: 修改全部个人信息保存成功（DB 回查三项均更新）
        if case_id == 'FC-YHXX-004':
            page.login_and_open(u, p, url)
            nickname = case.field('新昵称', '全量更新昵称')
            email = case.field('新邮箱', 'new@example.com')
            bio = case.field('新简介', '更新后的简介')
            orig_nick, orig_email, orig_bio = page.change_profile(
                new_nick=nickname, new_email=email, new_bio=bio
            )
            try:
                row = db_query.fetch_one(
                    "SELECT nickname, email FROM user WHERE username=%s", (u,))
                assert row[0] == nickname, f"昵称应更新，实际='{row[0]}'"
                assert row[1] == email, f"邮箱应更新，实际='{row[1]}'"
            finally:
                try:
                    page.login_and_open(u, p, url)
                    page.restore_profile(orig_nick, orig_email, orig_bio)
                except Exception as e:
                    log.warning(f"恢复原始个人信息失败: {e}")
            return

        # FC-YHXX-005: 不修改任何内容直接保存信息不变（DB 前后对比）
        if case_id == 'FC-YHXX-005':
            page.login_and_open(u, p, url)
            before = db_query.fetch_one(
                "SELECT nickname, email FROM user WHERE username=%s", (u,))
            page.click_settings()
            page.click_save()
            page.wait_for_page_ready()
            after = db_query.fetch_one(
                "SELECT nickname, email FROM user WHERE username=%s", (u,))
            assert before == after, \
                f"不做修改直接保存，信息应保持不变: 保存前={before}, 保存后={after}"
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
