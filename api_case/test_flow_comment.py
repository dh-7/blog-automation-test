"""业务流程测试 — 读者评论互动"""
import json
import logging
import pytest
import allure
import time

from api.helpers import do_request, get_latest_comment_id

logger = logging.getLogger("api_test")


@allure.epic("接口自动化测试")
@allure.feature("业务流程-多步骤")
@allure.story("读者评论互动")
class TestCommentFlow:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, api_config):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.config = api_config

    @allure.title("[YW_COM-03] 创建并删除自己的评论")
    def test_delete_own_comment_flow(self):
        """动态创建评论后删除，避免依赖易失效的固定预置评论 ID。"""
        article_id = int(self.vm.get("article_id", "1"))
        content = f"流程测试-删除自己的评论-{int(time.time() * 1000)}"
        headers = ('{"Content-Type":"application/json",'
                   '"Authorization":"Bearer ${token}"}')

        with allure.step("Step 1: 创建当前用户评论"):
            create_resp = do_request(
                self.client, self.vm, "POST", "/api/comments", headers,
                json.dumps({"content": content, "articleId": article_id}),
            )
            assert create_resp.get("code") == 200, (
                f"创建评论失败: {create_resp.body}")

        with allure.step("Step 2: 查询并确认评论 ID"):
            list_resp = do_request(
                self.client, self.vm, "GET",
                f"/api/comments/article/{article_id}",
                '{"Content-Type":"application/json",'
                '"Authorization":"Bearer ${token}"}',
            )
            assert list_resp.get("code") == 200, (
                f"查询评论失败: {list_resp.body}")
            comments = list_resp.get("data") or []
            target = next((c for c in comments if c.get("content") == content), None)
            assert target and target.get("id"), (
                f"未找到刚创建的评论: {content}")
            comment_id = target["id"]

        with allure.step(f"Step 3: 删除评论 {comment_id}"):
            delete_resp = do_request(
                self.client, self.vm, "DELETE", f"/api/comments/{comment_id}",
                headers,
            )
            assert delete_resp.get("code") == 200, (
                f"删除自己的评论失败: {delete_resp.body}")

        with allure.step("Step 4: 回查评论已删除"):
            verify_resp = do_request(
                self.client, self.vm, "GET",
                f"/api/comments/article/{article_id}",
                '{"Content-Type":"application/json",'
                '"Authorization":"Bearer ${token}"}',
            )
            assert verify_resp.get("code") == 200, (
                f"删除后查询评论失败: {verify_resp.body}")
            remaining = verify_resp.get("data") or []
            assert not any(c.get("id") == comment_id for c in remaining), (
                f"评论 {comment_id} 删除后仍出现在列表中")

    @allure.title("[YW_COM-01] 登录→发评论→回复→查看评论树")
    def test_comment_tree_flow(self):
        article_id = self.vm.get("article_id", "1")
        with allure.step("Step 1: 发表根评论"):
            resp = do_request(self.client, self.vm, "POST", "/api/comments",
                              '{"Content-Type":"application/json",'
                              '"Authorization":"Bearer ${token}"}',
                              json.dumps({"content": "流程测试根评论",
                                          "articleId": int(article_id),
                                          "parentId": None}))
            assert resp.get("code") == 200
            comment_id = get_latest_comment_id(self.client, self.vm, article_id)
            self.vm.set("flow_comment_id", comment_id)
        with allure.step("Step 2: 回复评论"):
            resp2 = do_request(self.client, self.vm, "POST", "/api/comments",
                       '{"Content-Type":"application/json",'
                       '"Authorization":"Bearer ${token}"}',
                       json.dumps({"content": "流程测试回复",
                                   "articleId": int(article_id),
                                   "parentId": comment_id,
                                   "replyUserId": 1}))
            assert resp2.get("code") == 200
        with allure.step("Step 3: 查看评论树"):
            resp3 = do_request(self.client, self.vm, "GET",
                              f"/api/comments/article/{article_id}",
                              '{"Content-Type":"application/json"}')
            assert resp3.get("code") == 200
            comments = resp3.get("data") or []
            root_ids = [c.get("id") for c in comments]
            assert comment_id in root_ids, f"根评论{comment_id}应存在"

    @allure.title("[YW_COM-02] 评论后通知文章作者")
    def test_comment_notification_flow(self):
        article_id = self.vm.get("article_id", "1")
        with allure.step("Step 1: 对文章发表评论"):
            resp = do_request(self.client, self.vm, "POST", "/api/comments",
                              '{"Content-Type":"application/json",'
                              '"Authorization":"Bearer ${token}"}',
                              json.dumps({"content": "通知测试评论",
                                          "articleId": int(article_id)}))
            assert resp.get("code") == 200
        with allure.step("Step 2: 验证通知已生成"):
            resp2 = do_request(self.client, self.vm, "GET",
                               "/api/notifications/unread-count",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${admin_token}"}')
            assert resp2.get("code") == 200
            assert resp2.get("data", 0) > 0, "应有未读通知"

    @allure.title("[YW_COM-06] 回复评论通知被回复者")
    def test_reply_notification_flow(self):
        article_id = self.vm.get("article_id", "1")
        comment_id = self.vm.get("comment_id", "1")
        with allure.step("Step 1: 回复评论（带replyUserId）"):
            resp = do_request(self.client, self.vm, "POST", "/api/comments",
                       '{"Content-Type":"application/json",'
                       '"Authorization":"Bearer ${token}"}',
                       json.dumps({"content": "回复通知测试",
                                   "articleId": int(article_id),
                                   "parentId": int(comment_id),
                                   "replyUserId": 1}))
            assert resp.get("code") == 200
        with allure.step("Step 2: 验证通知已生成"):
            resp2 = do_request(self.client, self.vm, "GET",
                               "/api/notifications/unread-count",
                               '{"Content-Type":"application/json",'
                               '"Authorization":"Bearer ${admin_token}"}')
            assert resp2.get("code") == 200
