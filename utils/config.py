import os
import yaml


class Config:
    """YAML 配置读取器 — 全局单例，首次 load 后缓存"""

    _data = None

    @classmethod
    def load(cls, path=None):
        """加载配置文件，仅首次生效"""
        if cls._data is None:
            if path is None:
                path = os.path.join(os.getcwd(), "config.yaml")
            with open(path, encoding="utf-8") as f:
                cls._data = yaml.safe_load(f) or {}
        return cls._data

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
