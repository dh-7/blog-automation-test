"""统一的数据库快照管理

三层结构:
  1. baseline_snapshot.sql — 干净基线（表结构+种子数据，不含测试预置数据）
  2. ensure_preset_data()  — 幂等保障预置数据存在（INSERT前先查）
  3. restore_baseline()    — 还原到干净基线

用法:
  # 首次初始化（DB干净时执行一次）
  python -c "from utils.db_snapshot import export_baseline; export_baseline()"

  # 测试中由 fixture 自动调用，无需手动使用
"""
import os
import subprocess
import logging
import pymysql
from utils.config import Config

logger = logging.getLogger("db_snapshot")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "snapshots")
BASELINE_FILE = os.path.join(SNAPSHOT_DIR, "blog_db_baseline.sql")


# ============================================================
#  DB 配置（从 config.yaml 读取）
# ============================================================

def _db_config():
    """读取数据库配置（每次调用实时读取，避免模块加载时序问题）"""
    return {
        "host":     Config.get("mysql", "host",     default="localhost"),
        "port":     Config.get("mysql", "port",     default=3306),
        "user":     Config.get("mysql", "user",     default="root"),
        "password": Config.get("mysql", "password", default=""),
        "database": Config.get("mysql", "database", default="blog_db"),
    }


def _env():
    """构造 mysql/mysqldump 的环境变量"""
    cfg = _db_config()
    e = os.environ.copy()
    e["MYSQL_PWD"] = cfg["password"]
    return e


def _mysql_cmd(tool="mysql"):
    """构造 mysql/mysqldump 基础命令"""
    cfg = _db_config()
    return [tool, f"-h{cfg['host']}", f"-P{cfg['port']}", f"-u{cfg['user']}"]


# ============================================================
#  公共 DB 连接
# ============================================================

def db_connect():
    """创建 pymysql 连接（供 setup_login 等外部模块使用）"""
    cfg = _db_config()
    return pymysql.connect(
        host=cfg["host"], port=cfg["port"],
        user=cfg["user"], password=cfg["password"],
        database=cfg["database"], charset="utf8mb4",
    )


# ============================================================
#  基线快照导出/还原
# ============================================================

def export_baseline():
    """导出当前 DB 为基线快照（一次性手动生成，应提交到 Git）

    要求：在 DB 处于干净状态时执行（无测试残留数据）
    """
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    cfg = _db_config()
    dump_cmd = _mysql_cmd("mysqldump") + [
        "--single-transaction", "--routines", "--triggers", cfg["database"],
    ]
    try:
        with open(BASELINE_FILE, "w", encoding="utf-8") as f:
            subprocess.run(dump_cmd, stdout=f, stderr=subprocess.PIPE,
                           env=_env(), check=True)
        logger.info(f"[基线快照] 已导出: {BASELINE_FILE}")
        print(f"[基线快照] 已导出: {BASELINE_FILE}")
    except FileNotFoundError:
        msg = "[基线快照] 未找到 mysqldump 命令，无法导出"
        logger.error(msg)
        raise RuntimeError(msg)
    except subprocess.CalledProcessError as e:
        msg = f"[基线快照] 导出失败: {e.stderr.decode()}"
        logger.error(msg)
        raise RuntimeError(msg)


def restore_baseline():
    """从基线快照还原数据库

    每次测试 session 开始/结束时调用，保证 DB 处于干净状态。
    如果基线文件不存在，抛出异常提示用户先生成。
    """
    if not os.path.exists(BASELINE_FILE):
        raise FileNotFoundError(
            f"[基线快照] 文件不存在: {BASELINE_FILE}\n"
            f"请先初始化数据库并执行:\n"
            f"  python -c \"from utils.db_snapshot import export_baseline; export_baseline()\""
        )
    cfg = _db_config()
    cmd = _mysql_cmd("mysql") + [cfg["database"]]
    try:
        with open(BASELINE_FILE, "r", encoding="utf-8") as f:
            subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE,
                           env=_env(), check=True)
        logger.info("[基线快照] 已还原")
    except FileNotFoundError:
        msg = "[基线快照] 未找到 mysql 命令，无法还原"
        logger.error(msg)
        raise RuntimeError(msg)
    except subprocess.CalledProcessError as e:
        msg = f"[基线快照] 还原失败: {e.stderr.decode()}"
        logger.error(msg)
        raise RuntimeError(msg)


# ============================================================
#  预置数据幂等保障
# ============================================================

def ensure_preset_data(preset_articles, preset_comments, admin_username="admin"):
    """幂等保障 API 测试预置数据存在

    与旧版 _ensure_snapshot 的区别:
      - 不再 INSERT→mysqldump→DELETE，直接 INSERT IGNORE 逻辑
      - 动态查询用户 ID，不硬编码
      - 每次都执行（不依赖快照文件是否已存在）

    Args:
        preset_articles:  [(var_name, title), ...]
        preset_comments:  [(var_name, content), ...]
        admin_username:   管理员用户名（用于查询 admin uid）
    """
    conn = db_connect()
    cur = conn.cursor()

    try:
        # 查询 testuser 的实际 ID（不硬编码）
        cur.execute("SELECT id FROM user WHERE username=%s AND deleted=0 LIMIT 1",
                    ("testuser",))
        row = cur.fetchone()
        uid = row[0] if row else 1
        logger.info(f"[预置数据] testuser uid={uid}")

        # 查询 admin 的 ID
        cur.execute("SELECT id FROM user WHERE username=%s AND deleted=0 LIMIT 1",
                    (admin_username,))
        row = cur.fetchone()
        admin_uid = row[0] if row else 1
        logger.info(f"[预置数据] admin uid={admin_uid}")

        inserted_articles = 0
        for _, title in preset_articles:
            author = admin_uid if "流程用例专用" in title else uid
            # 幂等：先查是否存在
            cur.execute(
                "SELECT id FROM article WHERE title=%s AND author_id=%s AND deleted=0 LIMIT 1",
                (title, author),
            )
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO article (title, content, author_id, status, deleted) "
                    "VALUES (%s, %s, %s, 1, 0)",
                    (title, "自动化测试专用", author),
                )
                conn.commit()
                inserted_articles += 1

        # 获取一篇预置文章 ID（用于挂载评论）
        cur.execute(
            "SELECT id FROM article WHERE title=%s AND deleted=0 LIMIT 1",
            ("接口测试-流程用例专用",),
        )
        row = cur.fetchone()
        ref_article_id = row[0] if row else None

        inserted_comments = 0
        if ref_article_id:
            for _, content in preset_comments:
                # 幂等：先查是否存在（含软删除的）
                cur.execute(
                    "SELECT id, deleted FROM comment WHERE content=%s AND article_id=%s AND user_id=%s LIMIT 1",
                    (content, ref_article_id, uid),
                )
                row = cur.fetchone()
                if row is None:
                    # 不存在，新增
                    cur.execute(
                        "INSERT INTO comment (content, article_id, user_id, deleted) "
                        "VALUES (%s, %s, %s, 0)",
                        (content, ref_article_id, uid),
                    )
                    conn.commit()
                    inserted_comments += 1
                elif row[1] == 1:
                    # 存在但被软删除，恢复
                    cur.execute(
                        "UPDATE comment SET deleted=0 WHERE id=%s", (row[0],)
                    )
                    conn.commit()
                    inserted_comments += 1

        # ── 预置通知数据（用于 NTF 测试） ──
        # 幂等：先查询是否存在通知
        cur.execute(
            "SELECT id FROM notification WHERE user_id=%s AND type='system' AND is_read=0 LIMIT 1",
            (uid,),
        )
        if cur.fetchone() is None:
            # 创建一条未读系统通知
            cur.execute(
                "INSERT INTO notification (user_id, from_user_id, type, content, is_read) "
                "VALUES (%s, %s, 'system', '这是一条测试通知', 0)",
                (uid, 0),
            )
            conn.commit()
            logger.info("[预置数据] 新增 1 条通知")

        if inserted_articles or inserted_comments:
            logger.info(f"[预置数据] 新增 {inserted_articles} 篇文章, {inserted_comments} 条评论")
        else:
            logger.info("[预置数据] 全部已存在，无需插入")

    except Exception as e:
        logger.error(f"[预置数据] 保障失败: {e}")
        raise
    finally:
        conn.close()
