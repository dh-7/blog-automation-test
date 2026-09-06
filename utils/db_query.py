"""数据库查询辅助 — 供 UI 用例做"前后对比 / DB 回查"类显式断言

设计目的：消灭"计算了前后状态却不比较"和"页面有元素就算过"的假通过。
用例的写法模式：操作前取 DB 状态 → UI 操作 → 操作后再取 DB 状态 → assert 满足预期。
"""
import pymysql
from utils.config import Config


def _conn():
    return pymysql.connect(
        host=Config.get("mysql", "host", default="localhost"),
        port=Config.get("mysql", "port", default=3306),
        user=Config.get("mysql", "user", default="root"),
        password=Config.get("mysql", "password", default=""),
        database=Config.get("mysql", "database", default="blog_db"),
        charset="utf8mb4",
    )


def fetch_all(sql, params=None):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=None):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def scalar(sql, params=None, default=None):
    row = fetch_one(sql, params)
    return row[0] if row else default


# ==================== 领域查询 ====================

def user_id(username):
    return scalar("SELECT id FROM user WHERE username=%s AND deleted=0", (username,))


def username_by_nickname(nickname):
    return scalar("SELECT username FROM user WHERE nickname=%s AND deleted=0", (nickname,))


def article_field(article_id, col):
    """读取文章字段，col 限定白名单防止拼接注入"""
    assert col in ("title", "content", "summary", "status", "view_count", "deleted")
    return scalar(f"SELECT {col} FROM article WHERE id=%s", (article_id,))


def article_id_by_title(title):
    """按标题取文章ID（取最新的，兼容用例复用同名标题发布多篇文章）"""
    return scalar(
        "SELECT id FROM article WHERE title=%s AND deleted=0 ORDER BY id DESC",
        (title,))


def unread_notification_count(username):
    return scalar(
        "SELECT COUNT(*) FROM notification n JOIN user u ON n.user_id=u.id "
        "WHERE u.username=%s AND n.is_read=0", (username,), 0)


def latest_notification(username):
    """最近一条通知 (type, content)，无通知返回 None"""
    return fetch_one(
        "SELECT n.type, n.content FROM notification n JOIN user u ON n.user_id=u.id "
        "WHERE u.username=%s ORDER BY n.id DESC LIMIT 1", (username,))


def notifications_ordered_desc(username, limit=10):
    """按时间从新到旧排列的通知 (type, content) 列表（与后端列表接口同序）"""
    return fetch_all(
        "SELECT n.type, n.content FROM notification n JOIN user u ON n.user_id=u.id "
        "WHERE u.username=%s ORDER BY n.create_time DESC, n.id DESC LIMIT %s",
        (username, limit))


def has_notification_type(username, ntype):
    return scalar(
        "SELECT COUNT(*) FROM notification n JOIN user u ON n.user_id=u.id "
        "WHERE u.username=%s AND n.type=%s", (username, ntype), 0) > 0


def published_article_count(author_id):
    return scalar(
        "SELECT COUNT(*) FROM article WHERE author_id=%s AND status=1 AND deleted=0",
        (author_id,), 0)


def author_without_published():
    """优先取"只有草稿"的作者，其次没有任何已发布文章的用户；无则返回 None"""
    row = fetch_one(
        "SELECT u.id FROM user u WHERE u.deleted=0 AND "
        "(SELECT COUNT(*) FROM article a WHERE a.author_id=u.id AND a.status=1 AND a.deleted=0)=0 "
        "ORDER BY (SELECT COUNT(*) FROM article a2 WHERE a2.author_id=u.id AND a2.status=0 AND a2.deleted=0) DESC "
        "LIMIT 1")
    return row[0] if row else None


def dashboard_counts():
    """后台仪表盘三项统计的期望值（口径已与实际页面校准：deleted=0 计数）"""
    return {
        "文章总数": scalar("SELECT COUNT(*) FROM article WHERE deleted=0", None, 0),
        "用户总数": scalar("SELECT COUNT(*) FROM user WHERE deleted=0", None, 0),
        "评论总数": scalar("SELECT COUNT(*) FROM comment WHERE deleted=0", None, 0),
    }


def category_article_counts():
    """{分类名: 已发布未删除文章数}，与前台分类侧栏计数同口径"""
    rows = fetch_all(
        "SELECT c.name, COUNT(a.id) FROM category c "
        "LEFT JOIN article a ON a.category_id=c.id AND a.status=1 AND a.deleted=0 "
        "GROUP BY c.id, c.name")
    return {name: cnt for name, cnt in rows}


def category_names():
    return [r[0] for r in fetch_all("SELECT name FROM category")]


def tag_names():
    return [r[0] for r in fetch_all("SELECT name FROM tag")]


def article_titles_by_category(name):
    return [r[0] for r in fetch_all(
        "SELECT a.title FROM article a JOIN category c ON a.category_id=c.id "
        "WHERE c.name=%s AND a.status=1 AND a.deleted=0", (name,))]


def article_titles_by_tag(name):
    return [r[0] for r in fetch_all(
        "SELECT a.title FROM article a JOIN article_tag t2a ON a.id=t2a.article_id "
        "JOIN tag t ON t2a.tag_id=t.id "
        "WHERE t.name=%s AND a.status=1 AND a.deleted=0", (name,))]


def draft_titles():
    return [r[0] for r in fetch_all("SELECT title FROM article WHERE status=0 AND deleted=0")]


def read_time(username, article_id):
    return scalar(
        "SELECT rh.read_time FROM read_history rh JOIN user u ON rh.user_id=u.id "
        "WHERE u.username=%s AND rh.article_id=%s", (username, article_id))


def favorite_row(username, article_id):
    return fetch_one(
        "SELECT uf.id FROM user_favorite uf JOIN user u ON uf.user_id=u.id "
        "WHERE u.username=%s AND uf.article_id=%s", (username, article_id))


def user_comments_contents(username):
    return [r[0] for r in fetch_all(
        "SELECT c.content FROM comment c JOIN user u ON c.user_id=u.id "
        "WHERE u.username=%s AND c.deleted=0", (username,))]


def comment_count(article_id=None):
    if article_id is None:
        return scalar("SELECT COUNT(*) FROM comment WHERE deleted=0", None, 0)
    return scalar("SELECT COUNT(*) FROM comment WHERE article_id=%s AND deleted=0",
                  (article_id,), 0)


def article_cascade_cleaned(article_id):
    """校验删除文章后关联数据已清理；返回未清理的表名列表（空列表=已清理）

    comment 为软删除；user_favorite / read_history 无 deleted 列，应物理清除。
    """
    bad = []
    if scalar("SELECT COUNT(*) FROM comment WHERE article_id=%s AND deleted=0",
              (article_id,), 0) > 0:
        bad.append("comment")
    if scalar("SELECT COUNT(*) FROM user_favorite WHERE article_id=%s",
              (article_id,), 0) > 0:
        bad.append("user_favorite")
    if scalar("SELECT COUNT(*) FROM read_history WHERE article_id=%s",
              (article_id,), 0) > 0:
        bad.append("read_history")
    return bad
