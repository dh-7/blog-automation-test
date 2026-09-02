"""兼容性 shim —— 真实实现已迁移至 utils/excel_loader.py

保留此文件使以下 import 继续工作:
    from base.data_loader import UiDataLoader
    from base.data_loader import UiCase
新代码建议直接:
    from utils.excel_loader import UiCaseLoader, UiCase
"""
from utils.excel_loader import UiCaseLoader as UiDataLoader, UiCase

__all__ = ["UiDataLoader", "UiCase"]
