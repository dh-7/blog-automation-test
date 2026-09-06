import pytest
from utils.excel_loader import load_ui_cases
from page.page_article_detail import PageArticleDetail
from page.page_login import PageLogin
from utils.assert_helpers import auto_assert, assert_url, assert_toast
from utils.config import Config
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure


_params, _ids = load_ui_cases(module='文章详情')


@allure.epic("UI自动化测试")
@allure.feature("文章详情")
class TestArticleDetail:
    """文章详情 — 数据驱动测试"""

    @pytest.mark.parametrize('case_id,case', _params, ids=_ids)
    def test_article_detail(self, driver, case_id, case):
        page = PageArticleDetail(driver)

        # 处理需要登录的用例
        if case.login_required:
            u = case.login_user or 'zhangsan'
            p = case.login_password or '123456'
            login_page = PageLogin(driver)
            login_page.login(u, p)

        # FC-WZXQ-007: 访问已删除的文章提示不存在（特殊处理，不走常规open）
        if case_id == 'FC-WZXQ-007':
            case.fields['文章ID'] = case.field('已删除文章的ID', '999')
            page.open_url(case.resolved_path())
            page.wait_for_page_ready()
            auto_assert(page, driver, case.expected)
            return

        # FC-WZXQ-004: 进入详情页浏览量增加1
        # 通过数据库直查获取浏览量（避免API调用触发自增副作用）
        if case_id == 'FC-WZXQ-004':
            import pymysql
            article_id = case.field('文章ID', '1')
            conn = pymysql.connect(
                host=Config.get("mysql", "host", default="localhost"),
                port=Config.get("mysql", "port", default=3306),
                user=Config.get("mysql", "user", default="root"),
                password=Config.get("mysql", "password", default=""),
                database=Config.get("mysql", "database", default="blog_db"),
                charset="utf8mb4",
                autocommit=True,
            )
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT view_count FROM article WHERE id=%s", (article_id,))
                    v1 = cur.fetchone()[0]
                page.open_url(case.resolved_path())
                page.wait_for_page_ready()
                with conn.cursor() as cur:
                    cur.execute("SELECT view_count FROM article WHERE id=%s", (article_id,))
                    v2 = cur.fetchone()[0]
                assert v2 == v1 + 1, f"浏览量应增加1，访问前={v1}，访问后={v2}"
            finally:
                conn.close()
            return

        # FC-WZXQ-005: 再次进入同一篇文章浏览量继续增加
        if case_id == 'FC-WZXQ-005':
            import pymysql
            article_id = case.field('文章ID', '1')
            conn = pymysql.connect(
                host=Config.get("mysql", "host", default="localhost"),
                port=Config.get("mysql", "port", default=3306),
                user=Config.get("mysql", "user", default="root"),
                password=Config.get("mysql", "password", default=""),
                database=Config.get("mysql", "database", default="blog_db"),
                charset="utf8mb4",
                autocommit=True,
            )
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT view_count FROM article WHERE id=%s", (article_id,))
                    v1 = cur.fetchone()[0]
                page.open_url(case.resolved_path())
                page.wait_for_page_ready()
                with conn.cursor() as cur:
                    cur.execute("SELECT view_count FROM article WHERE id=%s", (article_id,))
                    v2 = cur.fetchone()[0]
                assert v2 == v1 + 1, f"浏览量应继续增加1，访问前={v1}，访问后={v2}"
            finally:
                conn.close()
            return

        page.open_url(case.resolved_path())
        page.wait_for_page_ready()

        # FC-WZXQ-001: 详情页显示完整文章信息（标题、正文、作者、分类、标签、发布时间、浏览量、收藏数）
        if case_id == 'FC-WZXQ-001':
            page.assert_article_info_complete()
            auto_assert(page, driver, case.expected)
            return

        # FC-WZXQ-002: 页面底部显示相关文章推荐区域
        if case_id == 'FC-WZXQ-002':
            related = page.get_related_articles()
            # 相关文章推荐区域存在即可（可以为空列表，但元素应存在）
            auto_assert(page, driver, case.expected)
            return

        # FC-WZXQ-003: 页面底部显示评论区域（评论输入框和已有评论列表）
        if case_id == 'FC-WZXQ-003':
            assert page.is_comment_section_visible(), "评论区域应可见"
            auto_assert(page, driver, case.expected)
            return

        # FC-WZXQ-006: 相关文章不包含当前文章自身
        if case_id == 'FC-WZXQ-006':
            current_title = page.get_title()
            related = page.get_related_articles()
            # 精确断言: 相关文章中每项都不应包含当前标题
            for r in related:
                assert current_title not in r, \
                    f"相关文章'{r}'不应包含当前文章'{current_title}'"
            auto_assert(page, driver, case.expected)
            return

        # 兜底
        auto_assert(page, driver, case.expected)
