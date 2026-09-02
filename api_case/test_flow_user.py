"""业务流程测试 — 个人信息与密码管理"""
import json
import logging
import pytest
import allure

from api.helpers import (
    do_request, user_change_password_flow, admin_reset_password_flow,
)

logger = logging.getLogger("api_test")


@allure.epic("接口自动化测试")
@allure.feature("业务流程-多步骤")
@allure.story("个人信息管理")
class TestUserFlow:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, api_config):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.config = api_config

    @allure.title("[YW_USR-01] 获取→修改→验证个人信息完整流程")
    def test_user_info_flow(self):
        new_nickname = f"流程昵称_{int(__import__('time').time())}"
        with allure.step("Step 1: 获取当前用户信息"):
            resp = do_request(self.client, self.vm, "GET", "/api/user/info",
                              '{"Content-Type":"application/json",'
                              '"Authorization":"Bearer ${token}"}')
            assert resp.get("code") == 200
        with allure.step("Step 2: 修改昵称"):
            resp2 = do_request(self.client, self.vm, "PUT", "/api/user/info",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${token}"}',
                               json.dumps({"nickname": new_nickname}))
            assert resp2.get("code") == 200
        with allure.step("Step 3: 验证修改后的信息"):
            resp3 = do_request(self.client, self.vm, "GET", "/api/user/info",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${token}"}')
            actual = resp3.get("data.nickname") or resp3.get("data", {}).get("nickname", "")
            assert actual == new_nickname, f"昵称未更新: 期望{new_nickname} 实际{actual}"

    @allure.title("[YW_USR-02] 修改头像和个人简介")
    def test_user_avatar_bio_flow(self):
        with allure.step("Step 1: 修改头像和个人简介"):
            resp = do_request(self.client, self.vm, "PUT", "/api/user/info",
                              '{"Content-Type":"application/json",'
                              '"Authorization":"Bearer ${token}"}',
                              json.dumps({"avatar": "new.png", "bio": "新简介"}))
            assert resp.get("code") == 200
        with allure.step("Step 2: 验证修改结果"):
            resp2 = do_request(self.client, self.vm, "GET", "/api/user/info",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${token}"}')
            assert resp2.get("code") == 200
            assert resp2.get("data.avatar") == "new.png", "头像应已更新"
            assert resp2.get("data.bio") == "新简介", "简介应已更新"

    @allure.title("[YW_USR-04] 修改密码后旧密码失效")
    def test_user_change_password_old_invalid_flow(self):
        user_change_password_flow(self.client, self.vm, self.assertor,
                                   "testuser", "123456", "test_new_pwd_04")

    @allure.title("[YW_USR-05] 管理员重置用户密码")
    def test_admin_reset_user_password_flow(self):
        user_id = self.vm.get("user_id")
        admin_reset_password_flow(self.client, self.vm, self.assertor,
                                   user_id, "admin_reset_usr05", "123456")


@allure.epic("接口自动化测试")
@allure.feature("业务流程-多步骤")
@allure.story("修改密码")
class TestChangePasswordFlow:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, api_config):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.config = api_config

    @allure.title("[USR-07] 正确原密码修改密码成功 → [USR-09]新密码登录 → [USR-10]旧密码失效")
    def test_change_password_success_flow(self):
        user_change_password_flow(self.client, self.vm, self.assertor,
                                   "testuser", "123456", "newpass123")
