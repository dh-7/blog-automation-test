"""业务流程测试 — 文章发布与生命周期"""
import json
import logging
import pytest
import allure

from api.helpers import (
    do_request, publish_article, edit_article,
)

logger = logging.getLogger("api_test")


@allure.epic("接口自动化测试")
@allure.feature("业务流程-多步骤")
@allure.story("作者发布文章")
class TestArticleFlow:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, api_config):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.config = api_config

    @allure.title("[YW_ART-01] 完整发布流程：登录→写文章→发布→列表可见")
    def test_publish_full_flow(self):
        title = f"流程测试文章_{int(__import__('time').time())}"
        with allure.step("Step 1: 发布文章"):
            article_id = publish_article(self.client, self.vm, title,
                                          "流程测试内容", category_id=1,
                                          tag_ids=[1])
            self.vm.set("flow_article_id", article_id)
            allure.attach(f"article_id={article_id}", name="发布结果")
        with allure.step("Step 2: 验证文章在已发布列表中可见"):
            resp = do_request(self.client, self.vm, "GET",
                              "/api/articles/published",
                              '{"Content-Type":"application/json"}',
                              json.dumps({"keyword": title}))
            logger.info(f"[YW_ART-01] 查找文章: total={resp.get('data.total')}")
            assert resp.get("code") == 200
            records = resp.get("data.records") or []
            titles = [r.get("title", "") for r in records]
            assert title in titles, f"文章'{title}'未出现在已发布列表中"

    @allure.title("[YW_ART-02] 草稿→编辑→发布流程")
    def test_draft_to_publish_flow(self):
        draft_title = f"草稿测试_{int(__import__('time').time())}"
        with allure.step("Step 1: 保存草稿(status=0)"):
            article_id = publish_article(self.client, self.vm,
                                          draft_title, "草稿内容", status=0)
            self.vm.set("draft_article_id", article_id)
        with allure.step("Step 2: 编辑草稿并发布(status=1)"):
            edit_article(self.client, self.vm, article_id,
                         title=draft_title + "_已编辑",
                         content="编辑后内容", status=1)
        with allure.step("Step 3: 验证文章已发布"):
            resp = do_request(self.client, self.vm, "GET",
                              f"/api/articles/detail/{article_id}",
                              '{"Content-Type":"application/json"}')
            assert resp.get("code") == 200
            assert resp.get("data.article.status") == 1, "文章应为发布状态"

    @allure.title("[YW_ART-03] 发布后修改文章")
    def test_edit_published_article(self):
        with allure.step("Step 1: 发布一篇文章"):
            article_id = publish_article(self.client, self.vm,
                                          "待修改文章", "原始内容")
        with allure.step("Step 2: 修改标题和内容"):
            edit_article(self.client, self.vm, article_id,
                         title="修改后标题", content="修改后内容")
        with allure.step("Step 3: 验证修改结果"):
            resp = do_request(self.client, self.vm, "GET",
                              f"/api/articles/detail/{article_id}",
                              '{"Content-Type":"application/json"}')
            assert resp.get("code") == 200
            assert resp.get("data.article.title") == "修改后标题"
            assert resp.get("data.article.content") == "修改后内容"

    @allure.title("[YW_ART-05] 关联分类和标签发布")
    def test_publish_with_category_tags(self):
        with allure.step("Step 1: 发布文章关联分类和标签"):
            article_id = publish_article(self.client, self.vm,
                            "分类标签测试", "测试内容",
                            category_id=1, tag_ids=[1, 2])
        with allure.step("Step 2: 验证文章可访问"):
            resp = do_request(self.client, self.vm, "GET",
                              f"/api/articles/detail/{article_id}",
                              '{"Content-Type":"application/json"}')
            assert resp.get("code") == 200, f"文章{article_id}应可访问"


@allure.epic("接口自动化测试")
@allure.feature("业务流程-多步骤")
@allure.story("文章生命周期")
class TestArticleLifecycleFlow:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, api_config):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.config = api_config

    @allure.title("[YW_LIFE-01] 草稿→发布→修改→删除完整流程")
    def test_article_lifecycle(self):
        title = f"生命周期测试_{int(__import__('time').time())}"
        with allure.step("Step 1: 创建草稿(status=0)"):
            article_id = publish_article(self.client, self.vm,
                                          title, "生命周期内容", status=0)
            allure.attach(f"草稿ID: {article_id}", name="草稿创建成功")
        with allure.step("Step 2: 草稿改为发布(status=1)"):
            edit_article(self.client, self.vm, article_id,
                         title=title, content="发布内容", status=1)
        with allure.step("Step 3: 修改已发布文章"):
            edit_article(self.client, self.vm, article_id,
                         title=title + "_已修改", content="修改后内容")
        with allure.step("Step 4: 删除文章"):
            resp = do_request(self.client, self.vm, "DELETE",
                              f"/api/articles/{article_id}",
                              '{"Content-Type":"application/json",'
                              '"Authorization":"Bearer ${token}"}')
            assert resp.get("code") == 200
        with allure.step("Step 5: 验证文章已删除"):
            resp2 = do_request(self.client, self.vm, "GET",
                               f"/api/articles/detail/{article_id}",
                               '{"Content-Type":"application/json"}')
            assert resp2.get("code") == 404, "删除后文章应返回404"
