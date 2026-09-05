import os
import yaml


class Config:
    """YAML 配置读取器 — 全局单例，首次 load 后缓存

    支持环境变量覆盖（供 CI 使用），优先级：环境变量 > YAML 文件。
    空字符串视为"用空值覆盖"，例如置空 BLOG_CHROME_PATH 可让
    DriverManager 回落到 Selenium Manager 自动匹配驱动。
    """

    _data = None

    # 环境变量 → 配置键 映射
    _ENV_OVERRIDES = {
        "BLOG_BASE_URL":         ("env", "base_url"),
        "BLOG_API_URL":          ("env", "api_url"),
        "BLOG_HEADLESS":         ("browser", "headless"),
        "BLOG_CHROME_PATH":      ("browser", "chrome_path"),
        "BLOG_DRIVER_PATH":      ("browser", "driver_path"),
        "BLOG_MYSQL_HOST":       ("mysql", "host"),
        "BLOG_MYSQL_PORT":       ("mysql", "port"),
        "BLOG_MYSQL_USER":       ("mysql", "user"),
        "BLOG_MYSQL_PASSWORD":   ("mysql", "password"),
        "BLOG_MYSQL_DATABASE":   ("mysql", "database"),
        "BLOG_ACCOUNT_USERNAME": ("account", "username"),
        "BLOG_ACCOUNT_PASSWORD": ("account", "password"),
    }

    @classmethod
    def load(cls, path=None):
        """加载配置文件，仅首次生效"""
        if cls._data is None:
            if path is None:
                path = os.environ.get("BLOG_TEST_CONFIG") or os.path.join(os.getcwd(), "config.yaml")
            with open(path, encoding="utf-8") as f:
                cls._data = yaml.safe_load(f) or {}
            cls._apply_env_overrides()
        return cls._data

    @classmethod
    def _apply_env_overrides(cls):
        for var, keys in cls._ENV_OVERRIDES.items():
            raw = os.environ.get(var)
            if raw is None:
                continue
            if var == "BLOG_HEADLESS":
                value = raw.strip().lower() in ("1", "true", "yes", "on")
            elif var == "BLOG_MYSQL_PORT":
                value = int(raw)
            else:
                value = raw
            data = cls._data
            for key in keys[:-1]:
                data = data.setdefault(key, {})
            data[keys[-1]] = value

    @classmethod
    def get(cls, *keys, default=None):
        """嵌套取值：Config.get("browser", "chrome_path")"""
        data = cls.load()
        for key in keys:
            if not isinstance(data, dict):
                return default
            data = data.get(key)
            if data is None:
                return default
        return data
