"""接口测试 fixtures

方案说明：
  - 数据库基线由根 conftest.py 的 db_baseline fixture 统一管理（还原干净状态）
  - 本文件的 api_snapshot fixture 在基线之上保障预置测试数据存在
  - setup_login 负责：登录获取 Token + SELECT 查出预置数据 ID
"""
import os
import sys
import logging
import pytest
import allure

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config import Config
from api.config import ApiConfig
from api.client import ApiClient
from api.variable_manager import VariableManager
from api.data_loader import DataLoader
from api.assertor import Assertor
from utils.paths import API_DATASOURCE as DATASOURCE_FILE
from utils.db_snapshot import db_connect, ensure_preset_data
from api.db_assertor import SqlDbAssertor

# 确保 config.yaml 已加载
Config.load(os.path.join(PROJECT_ROOT, "config.yaml"))

# ── 日志 ──
LOG_DIR = os.path.join(PROJECT_ROOT, "log")
os.makedirs(LOG_DIR, exist_ok=True)


class _CaseFilter(logging.Filter):
    """为每条日志自动附加当前用例编号"""
    case_id = "SETUP"

    def filter(self, record):
        record.case_id = self.case_id
        return True


_case_filter = _CaseFilter()
_log_fmt = "%(asctime)s [%(levelname)s] [%(case_id)s] %(message)s"
_log_file = os.path.join(LOG_DIR, f"api_{__import__('datetime').datetime.now():%Y%m%d_%H%M%S}.log")

logger = logging.getLogger("api_test")
logger.setLevel(logging.INFO)
logger.addFilter(_case_filter)
for h in [
    logging.FileHandler(_log_file, encoding="utf-8"),
    logging.StreamHandler(),
]:
    h.setFormatter(logging.Formatter(_log_fmt))
    logger.addHandler(h)

# ── 预置数据定义 ──
_PRESET_ARTICLES = [
    ("my_article_id",       "接口测试-修改用例"),
    ("my_del_article_id",   "接口测试-删除用例"),
    ("flow_article_id",     "接口测试-流程用例专用"),
    ("adm14_article_id",    "接口测试-ADM14删除用"),
    ("adm15_article_id",    "接口测试-ADM15删除用"),
    ("yw_art04_article_id", "接口测试-YW_ART04删除用"),
    ("yw_adm202_article_id","接口测试-YW_ADM202删除用"),
    ("hist04_article_id",   "接口测试-HIST04删除用"),
]
_PRESET_COMMENTS = [
    ("my_comment_id",       "接口测试-删除评论用例"),
    ("flow_comment_id",     "接口测试-流程用例专用评论"),
    ("adm17_comment_id",    "接口测试-ADM17删除用"),
    ("yw_com03_comment_id", "接口测试-YW_COM03删除用"),
    ("yw_com05_comment_id", "接口测试-YW_COM05删除用"),
]


# ============================================================
#  Fixtures
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def api_snapshot(db_baseline):
    """在基线还原之后，幂等保障 API 预置数据存在"""
    logger.info("[快照] 保障预置数据...")
    ensure_preset_data(_PRESET_ARTICLES, _PRESET_COMMENTS)
    yield
    # teardown: db_baseline 会自动还原，无需额外清理


@pytest.fixture(scope="session")
def data_loader():
    """数据加载器"""
    loader = DataLoader(DATASOURCE_FILE)
    yield loader
    loader.close()


@pytest.fixture(scope="session")
def api_config(data_loader):
    """从 Excel 全局配置读取"""
    config_dict = data_loader.load_config()
    return ApiConfig.from_dict(config_dict)


@pytest.fixture(scope="session")
def var_manager():
    """变量管理器（session 级共享）"""
    return VariableManager()


@pytest.fixture(scope="session")
def assertor():
    """断言引擎"""
    return Assertor()


@pytest.fixture(scope="session")
def db_assertor():
    """数据库断言引擎（惰性连接，session 结束时关闭）"""
    _db = SqlDbAssertor()
    yield _db
    _db.close()


@pytest.fixture(scope="session")
def api_client(api_config):
    """HTTP 客户端"""
    client = ApiClient(api_config.base_url, api_config.timeout)
    yield client
    client.close()


@pytest.fixture(scope="session", autouse=True)
def setup_login(api_snapshot, api_client, var_manager, api_config):
    """前置登录 + 从 DB 中查询预置数据 ID

    执行顺序（api_snapshot 之后）：
    1. 管理员登录 → admin_token / admin_id
    2. 普通用户登录 → token / user_id
    3. SELECT 查询预置的文章/评论 ID → 写入变量池
    """
        # ── 写入 Allure 环境变量文件 ──
    _allure_results = os.path.join(PROJECT_ROOT, "report", "allure-results-api")
    if os.path.isdir(_allure_results):
        _env_file = os.path.join(_allure_results, "environment.properties")
        _api_url = Config.get("env", "api_url", default="http://localhost:8080")
        _db_name = Config.get("mysql", "database", default="blog_db")
        with open(_env_file, "w", encoding="utf-8") as ef:
            ef.write(f"base.url={api_config.base_url}\n")
            ef.write(f"api.url={_api_url}\n")
            ef.write(f"database={_db_name}\n")
            ef.write(f"test.user={api_config.test_username}\n")
            ef.write(f"admin.user={api_config.admin_username}\n")

    logger.info("=" * 60)
    logger.info("[SETUP] 开始前置登录 + 查询预置数据...")

    # ── 1. 管理员登录 ──
    admin_resp = api_client.send(
        method="POST", path="/api/auth/login",
        headers={"Content-Type": "application/json"},
        json_body={"username": api_config.admin_username, "password": api_config.admin_password},
    )
    if admin_resp.status_code == 200 and admin_resp.get("data.token"):
        var_manager.set("admin_token", admin_resp.get("data.token"))
        var_manager.set("admin_id", admin_resp.get("data.user.id"))
        logger.info(f"[SETUP] 管理员登录成功, admin_id={admin_resp.get('data.user.id')}")
    else:
        logger.error(f"[SETUP] 管理员登录失败: {admin_resp.body}")
        pytest.skip("管理员登录失败，无法执行后续用例")

    # ── 2. 普通用户登录 ──
    user_resp = api_client.send(
        method="POST", path="/api/auth/login",
        headers={"Content-Type": "application/json"},
        json_body={"username": api_config.test_username, "password": api_config.test_password},
    )
    if user_resp.status_code == 200 and user_resp.get("data.token"):
        var_manager.set("token", user_resp.get("data.token"))
        var_manager.set("user_id", user_resp.get("data.user.id"))
        logger.info(f"[SETUP] 普通用户登录成功, user_id={user_resp.get('data.user.id')}")
    else:
        logger.error(f"[SETUP] 普通用户登录失败: {user_resp.body}")
        pytest.skip("普通用户登录失败，无法执行后续用例")

    # ── 3. 查询预置数据的 ID，写入变量池 ──
    uid = var_manager.get("user_id")
    try:
        conn = db_connect()
        cur = conn.cursor()

        # 查询预置文章 ID
        for var_name, title in _PRESET_ARTICLES:
            author = 1 if "流程用例专用" in title else uid
            cur.execute(
                "SELECT id FROM article WHERE title=%s AND author_id=%s AND deleted=0 LIMIT 1",
                (title, author),
            )
            row = cur.fetchone()
            if row:
                var_manager.set(var_name, row[0])
                logger.info(f"[SETUP] {var_name}={row[0]}")

        # 查询预置评论 ID
        for var_name, content in _PRESET_COMMENTS:
            cur.execute(
                "SELECT id FROM comment WHERE content=%s AND user_id=%s AND deleted=0 LIMIT 1",
                (content, uid),
            )
            row = cur.fetchone()
            if row:
                var_manager.set(var_name, row[0])
                logger.info(f"[SETUP] {var_name}={row[0]}")

# 查询 other_id：非 testuser 的评论（供"操作别人数据"用例使用）
        cur.execute(
            "SELECT id FROM comment WHERE user_id != %s AND deleted=0 ORDER BY id LIMIT 1", (uid,)
        )
        row = cur.fetchone()
        if row:
            var_manager.set("other_id", row[0])
            logger.info(f"[SETUP] other_id={row[0]}")

        # 查询通知 ID（用于 NTF 测试）
        cur.execute(
            "SELECT id FROM notification WHERE user_id=%s AND is_read=0 ORDER BY id LIMIT 1",
            (uid,),
        )
        row = cur.fetchone()
        if row:
            var_manager.set("notify_id", row[0])
            logger.info(f"[SETUP] notify_id={row[0]}")
        else:
            # 兜底，但后续测试可能因缺少通知而失败
            logger.warning("[SETUP] 未找到通知，notify_id 未设置")

        conn.close()
    except Exception as e:
        logger.warning(f"[SETUP] 查询预置数据失败: {e}")

    # 兜底：关键变量缺失时用配置中的默认值
    # 文章/评论业务流程的专属夹具不能静默回退到任意 ID。
    required_fixture_vars = [
        "my_article_id", "my_del_article_id", "flow_article_id",
        "yw_com03_comment_id", "yw_com05_comment_id",
    ]
    missing = [name for name in required_fixture_vars if not var_manager.get(name)]
    if missing:
        pytest.fail(f"API 预置夹具缺失，禁止继续测试: {', '.join(missing)}")

    if not var_manager.get("article_id"):
        var_manager.set("article_id", api_config._data.get("article_id", "1"))
    if not var_manager.get("comment_id"):
        var_manager.set("comment_id", api_config._data.get("comment_id", "1"))
    logger.info(f"[SETUP] 变量池: article_id={var_manager.get('article_id')}, "
                f"comment_id={var_manager.get('comment_id')}, user_id={var_manager.get('user_id')}")
    logger.info("=" * 60)

    yield
    # teardown 无需任何清理，db_baseline 会自动还原
