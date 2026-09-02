import operator
from api.utils import resolve_path
 

class AssertResult:
    """断言结果"""

    def __init__(self, passed: bool, message: str):
        self.passed = passed
        self.message = message

    def __bool__(self):
        return self.passed


class Assertor:
    """断言引擎

    支持的语法：
        code=200                字段等于值
        data.token exists       字段存在
        data.total>0            字段大于值
        data.total<100          字段小于值
        message contains 成功   字段包含字符串
        code!=401               字段不等于值
        多条用 ; 分隔
    """

    # 操作符优先级：先匹配长的
    OPERATORS = [
        ("!=", operator.ne),
        (">=", operator.ge),
        ("<=", operator.le),
        (">", operator.gt),
        ("<", operator.lt),
        ("=", operator.eq),
    ]

    def assert_response(self, expected_status: int, expected_body: str,
                        actual_status: int, actual_body: dict) -> list:
        """执行断言，返回结果列表

        Args:
            expected_status: 预期HTTP状态码
            expected_body: 预期结果表达式（; 分隔多条）
            actual_status: 实际HTTP状态码
            actual_body: 实际响应JSON

        Returns:
            list[AssertResult]
        """
        results = []

        # 1. 断言状态码
        if expected_status:
            passed = actual_status == expected_status
            msg = f"状态码: 期望{expected_status} 实际{actual_status}"
            results.append(AssertResult(passed, msg))

            # 项目 API 约定：HTTP 200 必须返回统一业务响应结构。
            # 防止接口返回空响应/HTML 仍因状态码正确而通过。
            if expected_status == 200 and actual_status == 200:
                has_code = isinstance(actual_body, dict) and "code" in actual_body
                results.append(AssertResult(
                    has_code,
                    f"响应结构: {'包含业务 code' if has_code else '缺少业务 code'}",
                ))

        # 2. 断言响应体
        if expected_body:
            for expr in expected_body.split(";"):
                expr = expr.strip()
                if not expr:
                    continue
                result = self._eval_expr(expr, actual_body)
                results.append(result)

        return results

    def _eval_expr(self, expr: str, body: dict) -> AssertResult:
        """解析并执行单条断言表达式"""

        # 检查 exists
        if expr.endswith(" exists"):
            path = expr[:-7].strip()
            value = self._resolve(path, body)
            passed = value is not None and value != "" and value != []
            return AssertResult(passed, f"{path}: {'存在' if passed else '不存在'}")

        # 检查 contains
        if " contains " in expr:
            path, keyword = expr.split(" contains ", 1)
            path, keyword = path.strip(), keyword.strip()
            value = self._resolve(path, body)
            if value is None:
                return AssertResult(False, f"{path}: 不存在，无法检查包含'{keyword}'")
            passed = keyword in str(value)
            return AssertResult(passed, f"{path}: {'包含' if passed else '不包含'} '{keyword}'")

        # 检查 not_contains
        if " not_contains " in expr:
            path, keyword = expr.split(" not_contains ", 1)
            path, keyword = path.strip(), keyword.strip()
            value = self._resolve(path, body)
            if value is None:
                return AssertResult(True, f"{path}: 不存在，视为不包含'{keyword}'")
            passed = keyword not in str(value)
            return AssertResult(passed, f"{path}: {'不包含' if passed else '包含'} '{keyword}'")

        # 类型断言：path type=list|dict|int|string|bool
        if " type=" in expr:
            path, expected_type = (part.strip() for part in expr.split(" type=", 1))
            actual = self._resolve(path, body)
            type_map = {
                "list": list, "dict": dict, "int": int,
                "float": float, "string": str, "str": str, "bool": bool,
            }
            expected_cls = type_map.get(expected_type.lower())
            passed = expected_cls is not None and type(actual) is expected_cls
            return AssertResult(passed, f"{path}: 期望类型={expected_type} 实际类型={type(actual).__name__}")

        # 非空断言：区分字段存在和集合/字符串确实有内容
        if expr.endswith(" not_empty"):
            path = expr[:-10].strip()
            value = self._resolve(path, body)
            passed = value is not None and value != "" and value != [] and value != {}
            return AssertResult(passed, f"{path}: {'非空' if passed else '为空'}")

        # 列表长度断言：path.length>0 或 path.length>=1
        if ".length" in expr:
            for op_str, op_func in self.OPERATORS:
                if op_str in expr:
                    parts = expr.split(op_str, 1)
                    if len(parts) == 2 and parts[0].strip().endswith(".length"):
                        path = parts[0].strip()[:-7]  # 去掉 .length
                        expected_len = parts[1].strip()
                        value = self._resolve(path, body)
                        if not isinstance(value, (list, str)):
                            return AssertResult(False, f"{path}: 不是列表或字符串，无法检查长度")
                        actual_len = len(value)
                        try:
                            expected_num = int(expected_len)
                            passed = op_func(actual_len, expected_num)
                            return AssertResult(passed, f"{path}.length: 期望{op_str}{expected_num} 实际={actual_len}")
                        except ValueError:
                            return AssertResult(False, f"{path}.length: 无法解析期望长度 '{expected_len}'")

        # 检查 != （必须在 = 之前）
        for op_str, op_func in self.OPERATORS:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                if len(parts) == 2:
                    path = parts[0].strip()
                    expected = parts[1].strip()
                    actual = self._resolve(path, body)
                    # 尝试数值比较
                    try:
                        expected_typed = float(expected)
                        actual_typed = float(actual) if actual is not None else None
                    except (ValueError, TypeError):
                        # 布尔值大小写不敏感比较
                        exp_lower = expected.lower() if isinstance(expected, str) else expected
                        act_lower = str(actual).lower() if actual is not None else None
                        if exp_lower in ("true", "false") and act_lower in ("true", "false"):
                            expected_typed = exp_lower
                            actual_typed = act_lower
                        else:
                            expected_typed = expected
                            actual_typed = str(actual) if actual is not None else None
                    passed = op_func(actual_typed, expected_typed) if actual_typed is not None else False
                    return AssertResult(
                        passed,
                        f"{path}: 期望{op_str}{expected} 实际={actual}"
                    )

        # 无法解析
        return AssertResult(False, f"无法解析断言表达式: {expr}")

    @staticmethod
    def _resolve(path: str, data) -> str:
        """按路径取值，如 data.user.role"""
        return resolve_path(path, data)
