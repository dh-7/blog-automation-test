"""CI 环境自检：流水线在跑测试前，先确认被测系统与数据库可达。

用法:
    python ci/check_env.py        # 全量检查（含前端，供 UI 测试流水线/本地调试用）
    python ci/check_env.py api    # 仅检查接口自动化所需依赖（后端 API + MySQL + 基线）

检查项：
  1. 后端（env.api_url）端口可达
  2. MySQL 可连接
  3. 数据库基线快照文件存在
  4. （仅全量模式）前端（env.base_url）端口可达
任一失败则 exit 1，让流水线在"环境没起来"时快速失败，
而不是跑出一整片用例失败、干扰问题定位。
"""
import os
import sys
import socket
from urllib.parse import urlparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.config import Config
from utils.db_snapshot import BASELINE_FILE, db_connect


def check_tcp(url, name):
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=5):
            print(f"[PASS] {name}: {host}:{port} 可达")
            return True
    except OSError as e:
        print(f"[FAIL] {name}: {host}:{port} 不可达 ({e})")
        return False


def check_mysql():
    try:
        conn = db_connect()
        conn.close()
        print("[PASS] MySQL 连接成功")
        return True
    except Exception as e:
        print(f"[FAIL] MySQL 连接失败: {e}")
        return False


def check_baseline():
    if os.path.exists(BASELINE_FILE):
        print(f"[PASS] 基线快照存在: {BASELINE_FILE}")
        return True
    print(f"[FAIL] 基线快照不存在: {BASELINE_FILE}（需提交到仓库，或手工执行 export_baseline 生成）")
    return False


def main():
    Config.load(os.path.join(PROJECT_ROOT, "config.yaml"))
    scope = sys.argv[1] if len(sys.argv) > 1 else "all"
    results = [
        check_tcp(Config.get("env", "api_url", default=""), "后端 API"),
        check_mysql(),
        check_baseline(),
    ]
    if scope != "api":
        # UI 测试才需要前端；接口自动化 CI 传 api 参数跳过
        results.insert(0, check_tcp(Config.get("env", "base_url", default=""), "前端"))
    failed = results.count(False)
    print(f"\n自检结果: {len(results) - failed}/{len(results)} 项通过")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
