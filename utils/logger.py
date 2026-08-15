import logging
import os
import sys
from datetime import datetime


class Logger:
    """日志工具 — 控制台 + 按日期分文件，全局单例"""

    _instance = None

    @classmethod
    def get_logger(cls, log_dir="log", level="INFO"):
        if cls._instance is None:
            cls._instance = logging.getLogger("ui_auto")
            cls._instance.setLevel(getattr(logging, level.upper()))

            if not cls._instance.handlers:
                fmt = logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )



                # 控制台输出（stdout，避免红色）
                sh = logging.StreamHandler(sys.stdout)
                sh.setFormatter(fmt)
                cls._instance.addHandler(sh)

                # 文件输出（按日期命名）
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"{datetime.now():%Y-%m-%d}.log")
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(fmt)
                cls._instance.addHandler(fh)

        return cls._instance
