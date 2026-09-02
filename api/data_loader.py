"""兼容性 shim —— 真实实现已迁移至 utils/excel_loader.py

保留此文件使以下 import 继续工作:
    from api.data_loader import DataLoader
新代码建议直接:
    from utils.excel_loader import ApiCaseLoader
"""
from utils.excel_loader import ApiCaseLoader as DataLoader

__all__ = ["DataLoader"]
