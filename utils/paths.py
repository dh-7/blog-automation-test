"""项目路径常量 — 统一管理数据源等文件路径，避免各处硬编码"""
import os
from utils.config import Config

# 项目根目录 (D:/blog_automation)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 初始化配置 (幂等，多次调用无副作用)
Config.load(os.path.join(PROJECT_ROOT, "config.yaml"))


def get_datasource(name="ui"):
    """获取数据源文件绝对路径

    Args:
        name: "ui" 返回 UI 数据源，"api" 返回接口数据源
    """
    key = f"{name}_file"
    filename = Config.get("datasource", key)
    if not filename:
        # config.yaml 未配置时的兜底
        filename = ("data/博客系统-自动化测试数据源.xlsx"
                    if name == "ui"
                    else "data/博客系统-接口自动化数据源.xlsx")
    return os.path.join(PROJECT_ROOT, filename)


# 预定义常量，可直接 import 使用
UI_DATASOURCE = get_datasource("ui")
API_DATASOURCE = get_datasource("api")
