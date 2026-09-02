import re
import time
from api.utils import resolve_path
 

class VariableManager:
    """管理接口关联中的变量存取"""

    def __init__(self):
        self._pool: dict = {}

    def set(self, key: str, value):
        """存入变量"""
        self._pool[key] = value

    def get(self, key: str, default=None):
        """读取变量"""
        return self._pool.get(key, default)

    def extract(self, extract_expr: str, response_data: dict):
        """从响应JSON中提取变量

        Args:
            extract_expr: 提取表达式，如 "token=data.token;user_id=data.user.id"
            response_data: 响应体JSON（已转为dict）
        """
        if not extract_expr or not extract_expr.strip():
            return

        for item in extract_expr.split(";"):
            item = item.strip()
            if "=" not in item:
                continue
            var_name, json_path = item.split("=", 1)
            var_name = var_name.strip()
            json_path = json_path.strip()
            value = self._resolve_path(json_path, response_data)
            if value is not None:
                self._pool[var_name] = value

    def replace(self, text: str) -> str:
        """替换字符串中的 ${变量名} 为实际值"""
        if not text:
            return text

        def _replacer(match):
            var_name = match.group(1)
            if var_name == "timestamp":
                return str(int(time.time() * 1000))
            value = self._pool.get(var_name)
            if value is None:
                return match.group(0)  # 找不到变量，保留原样
            return str(value)

        return re.sub(r"\$\{(\w+)\}", _replacer, text)

    def replace_dict(self, data: dict) -> dict:
        """递归替换字典中所有字符串值的 ${变量}"""
        if not data:
            return data
        result = {}
        for k, v in data.items():
            new_key = self.replace(k) if isinstance(k, str) else k
            if isinstance(v, str):
                result[new_key] = self.replace(v)
            elif isinstance(v, dict):
                result[new_key] = self.replace_dict(v)
            elif isinstance(v, list):
                result[new_key] = [
                    self.replace_dict(i) if isinstance(i, dict)
                    else self.replace(i) if isinstance(i, str)
                    else i
                    for i in v
                ]
            else:
                result[new_key] = v
        return result

    def clear(self):
        """清空变量池"""
        self._pool.clear()

    @staticmethod
    def _resolve_path(path: str, data: dict):
        """解析 data.token 这样的路径，从嵌套dict中取值"""
        return resolve_path(path, data)
