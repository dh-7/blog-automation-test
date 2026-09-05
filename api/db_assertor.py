"""SQL 形式的数据库断言引擎

替代旧版 DSL 模式，直接写 SQL 语句做断言。

规则：
  - 单条 SQL 返回行 → 通过；不返回行 → 失败
  - 多条断言用 ; 分隔
  - 只允许 SELECT 语句，防止注入
  - ${var} 由 VariableManager 替换（调用方传入）
  - 字符串值需要在 SQL 中自己加引号，如 WHERE username = '${_reg_username}'

示例：
  SELECT 1 FROM article WHERE id = ${my_article_id} AND deleted = 1
  SELECT 1 FROM user WHERE username = '${_reg_username}' AND role = 'USER' AND deleted = 0
  SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM comment WHERE id = ${my_comment_id} AND deleted = 0)
  SELECT 1 FROM article_tag WHERE article_id = ${flow_article_id} HAVING COUNT(*) = 1
"""
import re
import logging
import allure
from utils.db_snapshot import db_connect

logger = logging.getLogger("api_test")

# ============================================================
#  断言结果
# ============================================================

class DbAssertResult:
    """数据库断言结果"""

    def __init__(self, passed: bool, message: str):
        self.passed = passed
        self.message = message

    def __bool__(self):
        return self.passed


# ============================================================
#  SQL 安全校验
# ============================================================

# 只允许 SELECT 语句（含 WITH、SELECT、HAVING、WHERE 等子句）
_SELECT_RE = re.compile(r"^\s*SELECT\s", re.IGNORECASE)

# 禁止的多语句/注入关键词
_BANNED_KEYWORDS = re.compile(
    r"\b(DROP|ALTER|TRUNCATE|INSERT|UPDATE|DELETE|CREATE|REPLACE|GRANT|REVOKE|"
    r"LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE|SLEEP|BENCHMARK)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> str:
    """校验 SQL 安全性

    Args:
        sql: 待校验的 SQL 语句

    Returns:
        str: 校验通过返回原 SQL

    Raises:
        ValueError: 校验失败时抛出
    """
    stripped = sql.strip()
    if not stripped:
        raise ValueError("SQL 断言表达式为空")

    if not _SELECT_RE.match(stripped):
        raise ValueError(f"只允许 SELECT 语句: {stripped[:80]}")

    if _BANNED_KEYWORDS.search(stripped):
        raise ValueError(f"SQL 包含禁止的关键字: {stripped[:80]}")

    return stripped


# ============================================================
#  SqlDbAssertor 主类
# ============================================================

class SqlDbAssertor:
    """SQL 形式的数据库断言引擎

    使用方式：
        db_assertor = SqlDbAssertor()
        results = db_assertor.assert_db(
            "SELECT 1 FROM article WHERE id = 1 AND deleted = 1",
        )
        db_assertor.close()

    每次 assert_db 执行后可通过 last_* 属性获取查询详情：
        db_assertor.last_sql      — 最后一条 SQL
        db_assertor.last_rows     — 最后一条 SQL 的查询结果行
        db_assertor.last_columns  — 列名
        db_assertor.last_row_dict — 首行数据 dict（方便查看）
    """

    def __init__(self):
        self._conn = None
        self.last_sql = ""
        self.last_rows = []
        self.last_columns = []
        self.last_row_dict = {}

    def _get_conn(self):
        """惰性获取连接，每次先 commit 保证读到最新已提交数据"""
        if self._conn is None:
            self._conn = db_connect()
            logger.info("[DB断言] 已建立数据库连接")
        self._conn.commit()
        return self._conn

    def close(self):
        """关闭数据库连接，清除上次查询缓存"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("[DB断言] 已关闭数据库连接")
        self.last_sql = ""
        self.last_rows = []
        self.last_columns = []
        self.last_row_dict = {}

    def assert_db(self, sql_expr: str, vm=None) -> list:
        """执行 SQL 断言表达式

        Args:
            sql_expr: SQL 表达式（多条用 ; 分隔）
            vm:       VariableManager 实例（可选，用于 ${var} 替换）

        Returns:
            list[DbAssertResult]
        """
        if not sql_expr or not sql_expr.strip():
            return [DbAssertResult(False, "[DB断言] SQL 断言表达式为空")]

        # 1. 替换变量（${var} → 实际值）
        resolved = vm.replace(sql_expr) if vm else sql_expr

        # 2. 按 ; 分割多条 SQL
        statements = [s.strip() for s in resolved.split(";") if s.strip()]
        if not statements:
            return [DbAssertResult(False, "[DB断言] 分割后无有效 SQL 语句")]

        # 3. 逐条校验并执行
        conn = self._get_conn()
        results = []

        for stmt in statements:
            # 3a. 安全校验
            try:
                _validate_sql(stmt)
            except ValueError as e:
                results.append(DbAssertResult(False, f"[DB断言] 安全校验失败: {e}"))
                continue

            # 3b. 执行查询
            try:
                cur = conn.cursor()
                cur.execute(stmt)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description] if cur.description else []
                cur.close()
            except Exception as e:
                self.last_sql = stmt
                self.last_rows = []
                self.last_columns = []
                self.last_row_dict = {}
                results.append(DbAssertResult(
                    False,
                    f"[DB断言] SQL 执行失败: {e}\nSQL: {stmt}",
                ))
                continue

            # 存储查询详情（最后一条覆盖）
            self.last_sql = stmt
            self.last_rows = rows
            self.last_columns = columns
            self.last_row_dict = dict(zip(columns, rows[0])) if rows else {}

            logger.debug(f"[DB断言] SQL: {stmt} | 返回行数: {len(rows)}")

            # 3c. 断言：有行则通过
            passed = len(rows) > 0
            row_info = f"（{len(rows)} 行）" if rows else "（无数据）"
            results.append(DbAssertResult(
                passed,
                f"[DB断言] SQL 返回 {len(rows)} 行: {'通过' if passed else '失败'}{row_info}\n  SQL: {stmt}",
            ))

        return results


# ============================================================
#  便捷函数：执行并返回失败列表
# ============================================================

def verify_db(db_assertor, expr: str, vm=None) -> tuple:
    """执行 DB 断言，返回全部结果和失败列表

    Args:
        db_assertor: SqlDbAssertor 实例
        expr: SQL 断言表达式
        vm:   VariableManager 实例（可选）

    Returns:
        (all_results, failures)
        all_results — list[DbAssertResult] 全部断言结果
        failures    — list[DbAssertResult] 仅失败项
    """
    if not expr or not expr.strip():
        return [], []

    results = db_assertor.assert_db(expr, vm)

    for r in results:
        if r.passed:
            logger.info(f"  DB断言: {r.message}")
        else:
            logger.error(f"  DB断言失败: {r.message}")

    return results, [r for r in results if not r.passed]