"""接口测试公共工具函数"""
import json as _json


def parse_json(text: str):
    """JSON字符串转dict，空字符串返回None

    自动处理Excel中的Python语法：None→null, True→true, False→false
    """
    if not text or not str(text).strip():
        return None
    try:
        s = str(text)
        s = s.replace(": None", ": null").replace(":None", ":null")
        s = s.replace(": True", ": true").replace(":True", ":true")
        s = s.replace(": False", ": false").replace(":False", ":false")
        return _json.loads(s)
    except (_json.JSONDecodeError, TypeError):
        return None


def resolve_path(path: str, data, default=None):
    """按点分隔路径从嵌套 dict 中取值

    Args:
        path: 点分隔路径，如 "data.token"、"data.user.role"
        data: 嵌套字典
        default: 路径不存在或取值为 None 时的默认值

    Returns:
        路径对应的值，不存在时返回 default

    Examples:
        >>> resolve_path("a.b", {"a": {"b": 1}})
        1
        >>> resolve_path("a.c", {"a": {"b": 1}}, "N/A")
        'N/A'
    """
    parts = path.split(".")
    current = data
    for part in parts:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return default
    return current if current is not None else default
