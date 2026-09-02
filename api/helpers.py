"""接口测试公共辅助函数

从 test_api.py 和 test_business_flow.py 中提取的共享逻辑：
  - do_request:     发送请求（变量替换 + 参数解析）
  - assert_and_report: 执行断言，返回失败列表
  - extract_vars:   从响应中提取变量
  - get_latest_article_id: 获取用户最新文章 ID
  - replace_vars:   变量替换（支持 str / dict）
  - parse_params:   解析请求参数（GET→params, 其他→json_body）
  - var_snapshot:   变量池快照（用于 allure 附加）
"""
import json
import logging

from api.utils import parse_json

logger = logging.getLogger("api_test")


def set_case_id(case_id: str):
    """设置当前用例编号，后续日志会自动附加此标识"""
    for f in logger.filters:
        if hasattr(f, "case_id"):
            f.case_id = case_id
            return


def do_request(client, vm, method, path, headers_str=None, params_str=None):
    """发送请求并返回 ApiResponse，自动处理变量替换。

    Args:
        client:      ApiClient 实例
        vm:          VariableManager 实例
        method:      HTTP 方法
        path:        接口路径（支持 ${var}）
        headers_str: 请求头 JSON 字符串（支持 ${var}）
        params_str:  请求参数 JSON 字符串（支持 ${var}）

    Returns:
        ApiResponse
    """
    headers = parse_json(headers_str)
    if headers:
        headers = vm.replace_dict(headers)
    path = vm.replace(path)

    params, json_body = None, None
    data = parse_json(params_str)
    # 保留空 JSON 对象：{} 与“未提供请求体”语义不同。
    if data is not None:
        data = vm.replace_dict(data)
        if method.upper() == "GET":
            params = data
        else:
            json_body = data

    _assert_no_unresolved_vars(path, headers, params, json_body)
    return client.send(
        method=method, path=path, headers=headers,
        params=params, json_body=json_body,
    )


def _assert_no_unresolved_vars(*values):
    """请求发送前阻止未替换的 ${var} 进入接口，避免错误请求意外通过。"""
    def find(value, location="request"):
        if isinstance(value, str):
            return [location] if "${" in value else []
        if isinstance(value, dict):
            found = []
            for key, item in value.items():
                found.extend(find(key, f"{location}.key"))
                found.extend(find(item, f"{location}.{key}"))
            return found
        if isinstance(value, list):
            found = []
            for index, item in enumerate(value):
                found.extend(find(item, f"{location}[{index}]"))
            return found
        return []

    locations = []
    for index, value in enumerate(values):
        locations.extend(find(value, f"request[{index}]"))
    if locations:
        raise AssertionError(f"请求包含未解析变量: {', '.join(locations)}")


def assert_and_report(resp, expected_status, expected_body, assertor):
    """执行断言，返回失败结果列表。

    Args:
        resp:             ApiResponse
        expected_status:  预期状态码（int 或 None）
        expected_body:    预期结果表达式（; 分隔）
        assertor:         Assertor 实例

    Returns:
        list[AssertResult] — 仅包含失败项
    """
    results = assertor.assert_response(
        expected_status=int(expected_status) if expected_status else None,
        expected_body=expected_body,
        actual_status=resp.status_code,
        actual_body=resp.body,
    )
    # 对成功响应施加接口级最低契约，避免仅 code=200 的假通过。
    if expected_status and int(expected_status) == 200 and resp.status_code == 200:
        for expr in _default_contracts(resp):
            result = assertor._eval_expr(expr, resp.body)
            results.append(result)
    for r in results:
        if r.passed:
            logger.info(f"  断言: {r.message}")
        else:
            logger.error(f"  断言失败: {r.message}")
    return [r for r in results if not r.passed]


def _default_contracts(resp):
    """根据响应形态返回最低业务契约表达式。"""
    body = resp.body if isinstance(resp.body, dict) else {}
    data = body.get("data")
    contracts = []
    if not isinstance(body, dict) or "code" not in body:
        return ["code exists"]
    if isinstance(data, dict) and "records" in data:
        contracts.extend(["data.records type=list", "data.total type=int"])
    if isinstance(data, dict) and "article" in data:
        contracts.append("data.article type=dict")
    if isinstance(data, dict) and "token" in data:
        contracts.extend(["data.token not_empty", "data.user type=dict"])
    return contracts


def do_verify(client, vm, assertor, verify_expr: str):
    """执行回查验证：写操作后 GET/POST 确认数据状态。

    格式: "GET /api/path → code=200;data.xxx=yyy"
          "POST /api/path → code=200;data exists"

    Args:
        client:     ApiClient 实例
        vm:         VariableManager 实例（变量替换）
        assertor:   Assertor 实例（断言执行）
        verify_expr: 回查表达式

    Raises:
        AssertionError: 断言失败时抛出
    """
    import allure

    parts = verify_expr.split("→")
    req_part = parts[0].strip()
    assert_part = parts[1].strip() if len(parts) > 1 else ""

    # 解析请求方法和路径
    method, path = req_part.split(" ", 1)
    method = method.strip().upper()
    path = path.strip()

    # 自动带认证头（根据路径判断使用哪个 token）
    if "/admin/" in path:
        headers_str = ('{"Content-Type":"application/json",'
                       '"Authorization":"Bearer ${admin_token}"}')
    else:
        headers_str = ('{"Content-Type":"application/json",'
                       '"Authorization":"Bearer ${token}"}')

    # 发送回查请求
    resp = do_request(client, vm, method, path, headers_str)
    allure.attach(
        f"回查请求: {method} {path}\n"
        f"状态码: {resp.status_code}\n"
        f"响应: {json.dumps(resp.body, ensure_ascii=False)[:500]}",
        name="回查响应",
        attachment_type=allure.attachment_type.TEXT,
    )

    if not assert_part:
        return

    # 替换断言表达式中的变量
    assert_part = vm.replace(assert_part)

    # 分离 HTTP 状态码断言和响应体断言
    expected_status = None
    body_exprs = []
    for expr in assert_part.split(";"):
        expr = expr.strip()
        if not expr:
            continue
        # code=xxx 作为 HTTP 状态码断言
        if expr.startswith("code=") and not "." in expr.split("=")[0]:
            try:
                expected_status = int(expr.split("=")[1])
            except (ValueError, IndexError):
                body_exprs.append(expr)
        else:
            body_exprs.append(expr)

    # 执行断言
    body_str = ";".join(body_exprs) if body_exprs else ""
    failures = assert_and_report(resp, expected_status, body_str, assertor)

    if failures:
        for r in failures:
            allure.attach(
                r.message,
                name="回查断言失败",
                attachment_type=allure.attachment_type.TEXT,
            )
        fail_msg = "\n".join(r.message for r in failures)
        raise AssertionError(f"回查验证失败:\n{fail_msg}")


def extract_vars(vm, extract_expr, resp_body):
    """从响应体中提取变量到变量池。"""
    if extract_expr:
        vm.extract(extract_expr, resp_body)


def get_latest_article_id(client, vm):
    """从"我的文章"列表获取最新文章 ID。

    API 创建文章不返回 ID，需要从列表接口获取。

    Args:
        client: ApiClient 实例
        vm:     VariableManager 实例（需要 token）

    Returns:
        int 或 None
    """
    resp = client.send(
        method="GET", path="/api/articles/mine",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {vm.get('token')}",
        },
    )
    if resp.status_code == 200:
        data = resp.body.get("data")
        if isinstance(data, list):
            articles = data
        elif isinstance(data, dict):
            articles = data.get("records", [])
        else:
            articles = []
        if articles:
            return articles[0].get("id")
    return None


def get_latest_comment_id(client, vm, article_id):
    """从文章评论列表获取最新评论 ID。

    POST /api/comments 创建评论不返回 ID，需要从列表接口获取。

    Args:
        client:     ApiClient 实例
        vm:         VariableManager 实例（需要 token）
        article_id: 文章 ID

    Returns:
        int 或 None
    """
    resp = client.send(
        method="GET", path=f"/api/comments/article/{article_id}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {vm.get('token')}",
        },
    )
    if resp.status_code == 200:
        data = resp.body.get("data")
        if isinstance(data, list):
            comments = data
        elif isinstance(data, dict):
            comments = data.get("records", [])
        else:
            comments = []
        if comments:
            return comments[0].get("id")
    return None


def replace_vars(vm, data):
    """替换变量（支持 str 和 dict）。

    字符串中的 ${var} 替换后，如果结果是合法 JSON 则自动解析为 dict。
    """
    if isinstance(data, str):
        replaced = vm.replace(data)
        # 替换后如果是 JSON 字符串，自动解析为 dict
        parsed = parse_json(replaced)
        return parsed if parsed is not None else replaced
    elif isinstance(data, dict):
        return vm.replace_dict(data)
    return data


def parse_params(vm, method, params_str):
    """解析请求参数：GET → params, 其他 → json_body。自动替换变量。

    Args:
        vm:         VariableManager 实例
        method:     HTTP 方法
        params_str: JSON 字符串

    Returns:
        (params, json_body) — 未使用的一方为 None
    """
    data = parse_json(params_str)
    if data is None:
        return None, None
    data = vm.replace_dict(data)
    if method.upper() == "GET":
        return data, None
    else:
        return None, data


def var_snapshot(vm):
    """返回当前变量池的快照字符串（隐藏敏感值）。"""
    pool = vm._pool
    if not pool:
        return "(空)"
    items = []
    for k, v in pool.items():
        val_str = str(v)
        if len(val_str) > 30:
            val_str = val_str[:15] + "..." + val_str[-10:]
        items.append(f"  {k} = {val_str}")
    return "{\n" + "\n".join(items) + "\n}"

# ============================================================
#  多步骤流程 helper (从 test_business_flow.py 提取)
# ============================================================

# 公共请求头模板
_AUTH_HEADERS = '{"Content-Type":"application/json","Authorization":"Bearer ${token}"}'


def publish_article(client, vm, title, content, status=1,
                    category_id=None, tag_ids=None):
    """发布/保存草稿文章，返回 article_id。

    Args:
        client:      ApiClient
        vm:          VariableManager
        title:       文章标题
        content:     文章内容
        status:      0=草稿, 1=发布
        category_id: 分类 ID (可选)
        tag_ids:     标签 ID 列表 (可选)

    Returns:
        int — 新文章 ID
    """
    body = {"title": title, "content": content, "status": status}
    if category_id is not None:
        body["categoryId"] = category_id
    if tag_ids is not None:
        body["tagIds"] = tag_ids
    resp = do_request(client, vm, "POST", "/api/articles",
                      _AUTH_HEADERS, json.dumps(body))
    assert resp.get("code") == 200, f"发布失败: {resp.body}"
    return get_latest_article_id(client, vm)


def edit_article(client, vm, article_id, title=None, content=None,
                 status=None):
    """编辑已发布文章。

    Args:
        client:     ApiClient
        vm:         VariableManager
        article_id: 文章 ID
        title:      新标题 (可选)
        content:    新内容 (可选)
        status:     新状态 (可选)
    """
    body = {"id": article_id}
    if title is not None:
        body["title"] = title
    if content is not None:
        body["content"] = content
    if status is not None:
        body["status"] = status
    resp = do_request(client, vm, "PUT", "/api/articles",
                      _AUTH_HEADERS, json.dumps(body))
    assert resp.get("code") == 200, f"编辑失败: {resp.body}"
    return resp


def user_change_password_flow(client, vm, assertor, username,
                               old_pwd, new_pwd):
    """用户修改密码→验证旧密码失效→验证新密码生效→恢复密码。

    完整的密码修改测试流程，finally 中自动恢复原始密码。

    Args:
        client:  ApiClient
        vm:      VariableManager
        assertor: Assertor
        username: 登录用户名
        old_pwd:  原密码
        new_pwd:  新密码
    """
    try:
        # Step 1: 修改密码
        resp = do_request(client, vm, "PUT", "/api/user/password",
                          _AUTH_HEADERS,
                          json.dumps({"oldPassword": old_pwd,
                                      "newPassword": new_pwd}))
        assert resp.get("code") == 200, f"修改密码失败: {resp.body}"

        # Step 2: 旧密码登录应失败
        resp2 = client.send(
            method="POST", path="/api/auth/login",
            headers={"Content-Type": "application/json"},
            json_body={"username": username, "password": old_pwd},
        )
        results = assertor.assert_response(
            expected_status=401, expected_body="code=401",
            actual_status=resp2.status_code, actual_body=resp2.body)
        failures = [r for r in results if not r.passed]
        assert not failures, f"旧密码应失效: {[r.message for r in failures]}"

        # Step 3: 新密码登录应成功
        resp3 = client.send(
            method="POST", path="/api/auth/login",
            headers={"Content-Type": "application/json"},
            json_body={"username": username, "password": new_pwd},
        )
        assert resp3.status_code == 200 and resp3.get("data.token"),             f"新密码登录应成功: {resp3.body}"
    finally:
        # 恢复密码
        try:
            new_token = client.send(
                method="POST", path="/api/auth/login",
                headers={"Content-Type": "application/json"},
                json_body={"username": username, "password": new_pwd},
            ).get("data.token")
            if new_token:
                client.send(
                    method="PUT", path="/api/user/password",
                    headers={"Content-Type": "application/json",
                             "Authorization": f"Bearer {new_token}"},
                    json_body={"oldPassword": new_pwd,
                               "newPassword": old_pwd},
                )
                logger.info("密码已恢复")
        except Exception as e:
            logger.warning(f"恢复密码失败: {e}")


def admin_reset_password_flow(client, vm, assertor, user_id,
                               new_pwd, orig_pwd):
    """管理员重置密码→验证旧密码失效→验证新密码生效→恢复。

    Args:
        client:   ApiClient
        vm:       VariableManager
        assertor: Assertor
        user_id:  目标用户 ID
        new_pwd:  新密码
        orig_pwd: 原密码 (用于恢复)
    """
    try:
        # Step 1: 管理员重置密码
        resp = do_request(
            client, vm, "PUT",
            f"/api/admin/users/{user_id}/password",
            '{"Content-Type":"application/json",'
            '"Authorization":"Bearer ${admin_token}"}',
            json.dumps({"id": int(user_id), "password": new_pwd}))
        assert resp.get("code") == 200, f"重置密码失败: {resp.body}"

        # Step 2: 旧密码登录应失败
        resp2 = client.send(
            method="POST", path="/api/auth/login",
            headers={"Content-Type": "application/json"},
            json_body={"username": "testuser", "password": orig_pwd},
        )
        results = assertor.assert_response(
            expected_status=401, expected_body="code=401",
            actual_status=resp2.status_code, actual_body=resp2.body)
        failures = [r for r in results if not r.passed]
        assert not failures, f"旧密码应失效: {[r.message for r in failures]}"

        # Step 3: 新密码登录应成功
        resp3 = client.send(
            method="POST", path="/api/auth/login",
            headers={"Content-Type": "application/json"},
            json_body={"username": "testuser", "password": new_pwd},
        )
        assert resp3.status_code == 200 and resp3.get("data.token"),             f"新密码登录应成功: {resp3.body}"
    finally:
        # 恢复密码
        try:
            admin_token = vm.get("admin_token")
            client.send(
                method="PUT",
                path=f"/api/admin/users/{user_id}/password",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {admin_token}"},
                json_body={"id": int(user_id), "password": orig_pwd},
            )
            logger.info("密码已恢复")
        except Exception as e:
            logger.warning(f"恢复密码失败: {e}")
