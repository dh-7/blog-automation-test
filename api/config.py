"""接口测试配置，从 Excel 全局配置 Sheet 读取"""


class ApiConfig:
    """管理接口测试的全局配置"""

    def __init__(self, config_dict: dict):
        self._data = config_dict

    @classmethod
    def from_dict(cls, config_dict: dict) -> "ApiConfig":
        return cls(config_dict)

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", "http://localhost:8080")

    @property
    def timeout(self) -> int:
        return int(self._data.get("timeout", 30))

    @property
    def test_username(self) -> str:
        return self._data.get("test_username", "testuser")

    @property
    def test_password(self) -> str:
        return self._data.get("test_password", "123456")

    @property
    def admin_username(self) -> str:
        return self._data.get("admin_username", "admin")

    @property
    def admin_password(self) -> str:
        return self._data.get("admin_password", "admin123")
