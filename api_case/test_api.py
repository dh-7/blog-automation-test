"""接口自动化测试驱动：从Excel读取用例，参数化生成测试"""
import json
import logging
import pytest
import allure

from api.data_loader import DataLoader
from api.client import ApiClient
from api.variable_manager import VariableManager
from api.assertor import Assertor
from api.conftest import DATASOURCE_FILE
from api.helpers import replace_vars, parse_params, var_snapshot, assert_and_report, extract_vars, set_case_id, do_request, do_verify, db_verify

logger = logging.getLogger("api_test")


# ── 读取 Excel 用例数据，用于参数化 ──
_loader = DataLoader(DATASOURCE_FILE)
_all_cases = _loader.load_cases()
_loader.close()

# 过滤掉 YW_ 开头的业务流程用例（单独文件处理）
# 过滤掉需要多步骤执行的用例（改为流程方法处理）
_EXCLUDE_IDS = {"USR-07", "USR-09", "USR-10", "ADM-09", "ADM-10", "ADM-11"}
_normal_cases = [c for c in _all_cases
                 if not str(c.get("用例编号", "")).startswith("YW_")
                 and c.get("用例编号", "") not in _EXCLUDE_IDS]

# 参数化数据：[(case_id, case_dict), ...]
_case_params = [(c["用例编号"], c) for c in _normal_cases]
_case_ids = [c["用例编号"] for c in _normal_cases]


# ── 测试类 ──
@allure.epic("接口自动化测试")
class TestApiAutomation:

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor, db_assertor):
        """注入依赖到测试实例"""
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor
        self.db_assertor = db_assertor

    @pytest.mark.parametrize("case_id,case", _case_params, ids=_case_ids)
    def test_api_case(self, case_id, case):
        """一条 Excel 用例 = 一个 pytest 测试"""
        set_case_id(case_id)
        title = case.get("用例标题", "")
        module = case.get("所属模块", "")
        priority = case.get("优先级", "P1")
        method = case.get("请求方法", "GET")
        path = case.get("接口路径", "")
        headers_str = case.get("请求头", "")
        params_str = case.get("请求参数", "")
        expected_status = case.get("预期状态码")
        expected_body = case.get("预期结果", "")

        # allure 标记
        allure.dynamic.title(f"[{case_id}] {title}")
        allure.dynamic.feature(module)
        allure.dynamic.story(module)
        allure.dynamic.severity(
            {"高": "critical", "中": "normal", "低": "minor",
             "P0": "critical", "P1": "normal", "P2": "minor"}.get(priority, "normal")
        )

        with allure.step(f"准备请求: {method} {path}"):
            # 预览变量替换后的请求参数（do_request 内部会再次处理，这里用于直观展示）
            headers = replace_vars(self.vm, headers_str)
            resolved_path = replace_vars(self.vm, path)
            params, json_body = parse_params(self.vm, method, params_str)
            req_detail = f"Method: {method}\nPath: {resolved_path}"
            if params:
                req_detail += f"\nParams: {json.dumps(params, ensure_ascii=False)}"
            if json_body:
                req_detail += f"\nBody: {json.dumps(json_body, ensure_ascii=False)}"
            allure.attach(req_detail, name="请求参数(解析后)", attachment_type=allure.attachment_type.TEXT)

        # do_request 带有 @allure.step 装饰器，会在报告中生成可点击展开的子步骤
        # 展开后可见“请求详情”和“响应详情”附件
        resp = do_request(self.client, self.vm, method, path, headers_str, params_str)

        with allure.step(f"执行断言 ({resp.elapsed_ms:.0f}ms)"):
            failures = assert_and_report(resp, expected_status, expected_body, self.assertor)
            for r in failures:
                allure.attach(
                    r.message, name="断言失败",
                    attachment_type=allure.attachment_type.TEXT,
                )
            if failures:
                fail_msg = chr(10).join(r.message for r in failures)
                pytest.fail(f"断言失败:\n{fail_msg}")

        with allure.step("提取变量"):
            extract_expr = case.get("变量提取", "")
            if extract_expr:
                extract_vars(self.vm, extract_expr, resp.body)
                allure.attach(
                    f"提取表达式: {extract_expr}\n当前变量池: {var_snapshot(self.vm)}",
                    name="变量提取",
                    attachment_type=allure.attachment_type.TEXT,
                )

        # 回查验证：写操作后 GET 确认数据状态
        verify_expr = str(case.get("回查验证", "") or "").strip()
        if verify_expr:
            with allure.step("回查验证"):
                do_verify(self.client, self.vm, self.assertor, verify_expr)

        # 数据库断言：验证写操作对数据库的影响
        db_expr = str(case.get("数据库断言", "") or "").strip()
        if db_expr:
            with allure.step("数据库断言"):
                db_verify(self.db_assertor, self.vm, db_expr)

