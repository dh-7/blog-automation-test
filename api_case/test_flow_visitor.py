"""业务流程测试 — 访客浏览与注册"""
import json
import logging
import pytest
import allure

from api.helpers import do_request

logger = logging.getLogger("api_test")


@allure.epic("接口自动化测试")
@allure.feature("业务流程-多步骤")
class TestVisitorFlow:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, api_config):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.config = api_config

    @allure.story("读者浏览与收藏")
    @allure.title("[YW_FAV-01] 访客浏览→登录→收藏完整流程")
    def test_visitor_to_favorite_flow(self):
        article_id = self.vm.get("article_id", "1")
        with allure.step("Step 1: 未登录浏览文章列表"):
            resp = do_request(self.client, self.vm, "GET",
                              "/api/articles/published",
                              '{"Content-Type":"application/json"}')
            assert resp.get("code") == 200
        with allure.step("Step 2: 登录后收藏文章"):
            resp2 = do_request(self.client, self.vm, "POST",
                       f"/api/favorites/toggle/{article_id}",
                       '{"Content-Type":"application/json",'
                       '"Authorization":"Bearer ${token}"}',
                       json.dumps({"articleId": int(article_id)}))
            assert resp2.get("code") == 200
        with allure.step("Step 3: 验证收藏状态"):
            resp3 = do_request(self.client, self.vm, "GET",
                               f"/api/favorites/check/{article_id}",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${token}"}')
            assert resp3.get("code") == 200
            assert resp3.get("data.isFavorited") == True, "应为已收藏状态"

    @allure.story("站点访客浏览")
    @allure.title("[YW_VIS-04] 访客注册→登录→发布文章完整流程")
    def test_visitor_register_publish_flow(self):
        import time
        username = f"visitor_{int(time.time())}"
        with allure.step("Step 1: 注册新用户"):
            resp = do_request(self.client, self.vm, "POST",
                              "/api/auth/register",
                              '{"Content-Type":"application/json"}',
                              json.dumps({"username": username,
                                          "password": "visitor123"}))
            assert resp.get("code") == 200
        with allure.step("Step 2: 登录"):
            resp2 = do_request(self.client, self.vm, "POST",
                               "/api/auth/login",
                               '{"Content-Type":"application/json"}',
                               json.dumps({"username": username,
                                           "password": "visitor123"}))
            assert resp2.get("code") == 200
            visitor_token = resp2.get("data.token")
            assert visitor_token, "登录未返回token"
            self.vm.set("visitor_token", visitor_token)
        with allure.step("Step 3: 发布文章"):
            resp3 = self.client.send(
                method="POST", path="/api/articles",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {visitor_token}"},
                json_body={"title": "访客发布的文章",
                           "content": "注册后第一篇文章", "status": 1})
            assert resp3.get("code") == 200
        with allure.step("Step 4: 验证文章已发布"):
            resp4 = self.client.send(
                method="GET", path="/api/articles/mine",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {visitor_token}"})
            assert resp4.status_code == 200
            articles = resp4.get("data") or []
            titles = [a.get("title") for a in articles]
            assert "访客发布的文章" in titles, "文章应出现在我的文章列表"
