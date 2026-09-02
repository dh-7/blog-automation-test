"""业务流程测试 — 管理员操作"""
import json
import logging
import pytest
import allure

from api.helpers import do_request, admin_reset_password_flow

logger = logging.getLogger("api_test")


@allure.epic("接口自动化测试")
@allure.feature("业务流程-多步骤")
@allure.story("管理员管理用户")
class TestAdminUserFlow:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, api_config):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.config = api_config

    @allure.title("[YW_ADM-01] 查看用户列表→修改信息→重置密码")
    def test_admin_user_manage_flow(self):
        user_id = self.vm.get("user_id", "35")
        with allure.step("Step 1: 管理员获取用户列表"):
            resp = do_request(self.client, self.vm, "GET", "/api/admin/users",
                              '{"Content-Type":"application/json",'
                              '"Authorization":"Bearer ${admin_token}"}')
            assert resp.get("code") == 200
        with allure.step("Step 2: 修改用户昵称"):
            resp2 = do_request(self.client, self.vm, "PUT",
                       f"/api/admin/users/{user_id}",
                       '{"Content-Type":"application/json",'
                       '"Authorization":"Bearer ${admin_token}"}',
                       json.dumps({"id": int(user_id), "nickname": "管理员修改"}))
            assert resp2.get("code") == 200
        with allure.step("Step 3: 验证昵称已修改"):
            resp3 = do_request(self.client, self.vm, "GET", "/api/admin/users",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${admin_token}"}')
            assert resp3.get("code") == 200
            users = resp3.get("data") or []
            target = next((u for u in users if u.get("id") == int(user_id)), None)
            assert target, f"未找到用户{user_id}"
            assert target.get("nickname") == "管理员修改", f"昵称未更新: {target.get('nickname')}"

    @allure.title("[YW_ADM-05] 重置密码后原密码失效")
    def test_admin_reset_password_old_invalid_flow(self):
        user_id = self.vm.get("user_id")
        admin_reset_password_flow(self.client, self.vm, self.assertor,
                                   user_id, "admin_reset_pwd_05", "123456")

    @allure.title("[ADM-09] 管理员重置用户密码 → [ADM-10]新密码登录 → [ADM-11]旧密码失效")
    def test_admin_reset_password_flow(self):
        user_id = self.vm.get("user_id")
        admin_reset_password_flow(self.client, self.vm, self.assertor,
                                   user_id, "admin_reset_09", "123456")


@allure.epic("接口自动化测试")
@allure.feature("业务流程-多步骤")
@allure.story("管理员管理文章与评论")
class TestAdminContentFlow:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, api_config):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.config = api_config

    @allure.title("[YW_ADM2-01] 查看全部文章→删除文章")
    def test_admin_article_manage_flow(self):
        with allure.step("Step 1: 管理员获取文章列表"):
            resp = do_request(self.client, self.vm, "GET", "/api/admin/articles",
                              '{"Content-Type":"application/json",'
                              '"Authorization":"Bearer ${admin_token}"}')
            assert resp.get("code") == 200
            articles = (resp.get("data") or {}).get("records") or []
            assert len(articles) > 0, "应有文章"
            target_id = articles[-1].get("id")
        with allure.step("Step 2: 删除文章"):
            resp2 = do_request(self.client, self.vm, "DELETE",
                               f"/api/admin/articles/{target_id}",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${admin_token}"}')
            assert resp2.get("code") == 200
        with allure.step("Step 3: 验证文章已删除"):
            resp3 = do_request(self.client, self.vm, "GET",
                               f"/api/articles/detail/{target_id}",
                               '{"Content-Type":"application/json"}')
            assert resp3.get("code") == 404, "文章应已被删除"

    @allure.title("[YW_ADM2-04] 查看全部评论→删除评论")
    def test_admin_comment_manage_flow(self):
        with allure.step("Step 1: 管理员获取评论列表"):
            resp = do_request(self.client, self.vm, "GET", "/api/admin/comments",
                              '{"Content-Type":"application/json",'
                              '"Authorization":"Bearer ${admin_token}"}')
            assert resp.get("code") == 200
            comments = resp.get("data") or []
            if not comments:
                pytest.skip("无评论可删除")
            target_id = comments[-1].get("id")
        with allure.step("Step 2: 删除评论"):
            resp2 = do_request(self.client, self.vm, "DELETE",
                               f"/api/admin/comments/{target_id}",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${admin_token}"}')
            assert resp2.get("code") == 200
