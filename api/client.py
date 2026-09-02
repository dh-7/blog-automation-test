"""HTTP 请求客户端封装"""
import json
import logging
import requests
from api.utils import resolve_path

logger = logging.getLogger("api_test")

# 响应日志截断长度
_RESPONSE_MAX_LEN = 200


class ApiResponse:
    """统一的响应封装"""

    def __init__(self, status_code: int, body: dict, elapsed_ms: float):
        self.status_code = status_code
        self.body = body
        self.elapsed_ms = elapsed_ms

    def json(self) -> dict:
        return self.body

    def get(self, path: str, default=None):
        """按路径取值，如 data.token"""
        return resolve_path(path, self.body, default)


def _mask_body(body: dict) -> dict:
    """脱敏请求体：password 字段替换为 ***"""
    if not body or not isinstance(body, dict):
        return body
    masked = {}
    for k, v in body.items():
        if k.lower() == "password" and isinstance(v, str):
            masked[k] = "***"
        else:
            masked[k] = v
    return masked


def _mask_headers(headers: dict) -> dict:
    """脱敏请求头：Authorization token 只显示前10位"""
    if not headers:
        return headers
    masked = {}
    for k, v in headers.items():
        if k.lower() == "authorization" and isinstance(v, str) and len(v) > 20:
            masked[k] = v[:20] + "***"
        else:
            masked[k] = v
    return masked


class ApiClient:
    """封装 requests.Session，统一处理请求"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def send(self, method: str, path: str, headers: dict = None,
             params: dict = None, json_body: dict = None) -> ApiResponse:
        """发送HTTP请求

        Args:
            method: GET/POST/PUT/DELETE
            path: 接口路径，如 /api/auth/login
            headers: 请求头
            params: query参数（GET请求）
            json_body: JSON body（POST/PUT请求）
        """
        url = self.base_url + path
        method = method.upper()

        # 构建请求摘要
        parts = [f">>> {method} {url}"]
        if params:
            parts.append(f"  Params: {params}")
        if json_body:
            parts.append(f"  Body: {json.dumps(_mask_body(json_body), ensure_ascii=False)}")
        logger.info(" | ".join(parts))

        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=self.timeout,
        )

        try:
            body = response.json()
        except (ValueError, TypeError):
            body = {"raw_text": response.text}

        elapsed_ms = response.elapsed.total_seconds() * 1000

        # 响应摘要：状态码 + 耗时 + 截断的响应体
        resp_text = json.dumps(body, ensure_ascii=False)
        if len(resp_text) > _RESPONSE_MAX_LEN:
            resp_text = resp_text[:_RESPONSE_MAX_LEN] + "..."
        logger.info(f"    → {response.status_code} ({elapsed_ms:.0f}ms) {resp_text}")

        return ApiResponse(
            status_code=response.status_code,
            body=body,
            elapsed_ms=elapsed_ms,
        )

    def close(self):
        self.session.close()
