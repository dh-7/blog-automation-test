import logging
import os
import sys
from datetime import datetime


class _CaseFilter(logging.Filter):
    """为每条日志自动附加当前用例编号"""
    case_id = "SETUP"

    def filter(self, record):
        record.case_id = self.case_id
        return True


# 全局 filter 实例，供外部 set_case_id 使用
_case_filter = _CaseFilter()


def set_case_id(case_id: str):
    """设置当前用例编号，后续日志会自动附加此标识"""
    _case_filter.case_id = case_id


class Logger:
    """日志工具 — 控制台 + 按运行分文件，全局单例"""

    _instance = None

    @classmethod
    def get_logger(cls, log_dir="log", level="INFO"):
        if cls._instance is None:
            cls._instance = logging.getLogger("ui_auto")
            cls._instance.setLevel(getattr(logging, level.upper()))
            cls._instance.addFilter(_case_filter)

            if not cls._instance.handlers:
                fmt = logging.Formatter(
                    "%(asctime)s [%(levelname)s] [%(case_id)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )

                # 控制台输出（stdout，避免红色）
                sh = logging.StreamHandler(sys.stdout)
                sh.setFormatter(fmt)
                cls._instance.addHandler(sh)

                # 文件输出（按运行时间命名）
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"ui_{datetime.now():%Y%m%d_%H%M%S}.log")
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(fmt)
                cls._instance.addHandler(fh)

        return cls._instance
