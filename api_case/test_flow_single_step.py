"""业务流程测试 — 单步骤 YW_ 用例"""
import json
import logging
import pytest
import allure

from api.data_loader import DataLoader
from api.conftest import DATASOURCE_FILE
from api.helpers import (
    do_request, assert_and_report, extract_vars, var_snapshot, set_case_id, do_verify,
)

logger = logging.getLogger("api_test")

# ── 加载 YW_ 用例 ──
_loader = DataLoader(DATASOURCE_FILE)
_all_cases = _loader.load_cases()
_yw_cases = [c for c in _all_cases if str(c.get("用例编号", "")).startswith("YW_")]
_loader.close()

SINGLE_STEP_CASES = [
    "YW_ART-04", "YW_ART-06",
    "YW_FAV-02", "YW_FAV-03", "YW_FAV-04", "YW_FAV-05", "YW_FAV-06",
    "YW_COM-04", "YW_COM-05", "YW_COM-07",
    "YW_HIST-01", "YW_HIST-02", "YW_HIST-03", "YW_HIST-04",
    "YW_USR-02", "YW_USR-03",
    "YW_ADM-02", "YW_ADM-03", "YW_ADM-04",
    "YW_ADM2-02", "YW_ADM2-03", "YW_ADM2-05", "YW_ADM2-06",
    "YW_LIFE-02", "YW_LIFE-03", "YW_LIFE-04", "YW_LIFE-05",
    "YW_VIS-01", "YW_VIS-02", "YW_VIS-03",
]

_single_cases = [c for c in _yw_cases if c["用例编号"] in SINGLE_STEP_CASES]
_single_params = [(c["用例编号"], c) for c in _single_cases]
_single_ids = [c["用例编号"] for c in _single_cases]


@allure.epic("接口自动化测试")
@allure.feature("业务流程")
class TestBusinessSingleStep:
    """单步骤业务用例：路径可直接使用，参数化驱动"""

    @pytest.fixture(autouse=True)
    def _init(self, api_client, var_manager, assertor):
        self.client = api_client
        self.vm = var_manager
        self.assertor = assertor

    @pytest.mark.parametrize("case_id,case", _single_params, ids=_single_ids)
    def test_single_step(self, case_id, case):
        set_case_id(case_id)
        title = case.get("用例标题", "")
        module = case.get("所属模块", "")
        priority = case.get("优先级", "中")
        method = case.get("请求方法", "GET")
        path = case.get("接口路径", "")
        headers_str = case.get("请求头", "")
        params_str = case.get("请求参数", "")
        expected_status = case.get("预期状态码")
        expected_body = case.get("预期结果", "")

        allure.dynamic.title(f"[{case_id}] {title}")
        allure.dynamic.feature(module)
        allure.dynamic.story(module)
        allure.dynamic.severity(
            {"高": "critical", "中": "normal", "低": "minor"}.get(priority, "normal"))

        with allure.step(f"发送请求: {method} {path}"):
            resp = do_request(self.client, self.vm, method, path,
                              headers_str, params_str)
            resp_text = json.dumps(resp.body, ensure_ascii=False)[:500]
            resp_info = f"状态码: {resp.status_code}\n耗时: {resp.elapsed_ms:.0f}ms\n响应: {resp_text}"
            allure.attach(resp_info, name="响应详情", attachment_type=allure.attachment_type.TEXT)

        with allure.step(f"执行断言 ({resp.elapsed_ms:.0f}ms)"):
            failures = assert_and_report(resp, expected_status,
                                          expected_body, self.assertor)
            for r in failures:
                allure.attach(
                    r.message, name="断言失败",
                    attachment_type=allure.attachment_type.TEXT)
            if failures:
                fail_msg = chr(10).join(r.message for r in failures)
                pytest.fail(f"断言失败:\n{fail_msg}")

        with allure.step("提取变量"):
            extract_expr = case.get("变量提取", "")
            if extract_expr:
                extract_vars(self.vm, extract_expr, resp.body)
                allure.attach(
                    f"提取表达式: {extract_expr}\n当前变量池: {var_snapshot(self.vm)}",
                    name="变量提取", attachment_type=allure.attachment_type.TEXT)

        # 回查验证：写操作后 GET 确认数据状态
        verify_expr = str(case.get("回查验证", "") or "").strip()
        if verify_expr:
            with allure.step("回查验证"):
                do_verify(self.client, self.vm, self.assertor, verify_expr)

