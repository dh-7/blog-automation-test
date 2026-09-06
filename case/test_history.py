"""阅读历史模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.excel_loader import load_ui_cases
from page.page_home import PageHome
from page.page_login import PageLogin
from page.page_history import PageHistory
from page.page_article_detail import PageArticleDetail
from utils import db_query
from utils.assert_helpers import auto_assert, assert_url
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_params, _ids = load_ui_cases(module="阅读历史")


@allure.epic("UI自动化测试")
@allure.feature("阅读历史")
class TestHistory:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    @pytest.mark.parametrize("case_id,case", _params, ids=_ids)
    def test_history(self, case_id, case):

        # 未登录访问（FC-YDLS-007）— 根据标题判断，而非 login_required 字段
        if "未登录" in case.title:
            history = PageHistory(self.driver)
            history.open_url(case.resolved_path())
            history.wait_for_page_ready()
            auto_assert(history, self.driver, case.expected)
            return

        user = case.login_user or "zhangsan"
        pwd = case.login_password or "123456"
        login_page = PageLogin(self.driver)
        login_page.login(user, pwd)

        # 先浏览一篇文章产生历史（FC-YDLS-004 用数据源「文章ID」指定目标文章）
        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        article_id = case.field('文章ID')
        if article_id:
            # 浏览数据源指定文章，确保它进入当前用户历史
            detail = PageArticleDetail(self.driver)
            detail.open_url(f'/article/{article_id}')
            target_title = detail.get_title()
        else:
            if home.get_article_count() > 0:
                home.click_article_by_index(0)
                home.wait_for_page_ready()
            target_title = None

        # 进入阅读历史页
        history = PageHistory(self.driver)
        history.open_url(case.resolved_path())
        history.wait_for_page_ready()

        # 删除单条（FC-YDLS-004）— 数据源「文章ID」指定删除目标
        if "删除单条" in case.title and history.get_history_count() > 0:
            titles_before = history.get_article_titles()
            count_before = len(titles_before)
            if target_title:
                assert target_title in titles_before, \
                    f"目标文章'{target_title}'未出现在历史列表中"
                history.click_delete_by_title(target_title)
            else:
                history.click_delete(0)
            # 处理确认弹框（click_delete 内部已确认，此处兜底）
            try:
                history.wait_for_confirm_dialog(timeout=3)
                history.confirm_dialog()
            except Exception:
                pass
            history.wait_for_page_ready()
            count_after = history.get_history_count()
            titles_after = history.get_article_titles()
            assert count_after < count_before, \
                f"删除后历史应减少: 删除前{count_before}, 删除后{count_after}"
            if target_title:
                assert target_title not in titles_after, \
                    f"被删除的记录'{target_title}'应从列表中消失"
            history.wait_for_page_ready()
            return  # FC-YDLS-004 删除单条已精确断言，跳过末尾通用 auto_assert

        # 清空全部（FC-YDLS-005）
        if "清空" in case.title and case_id != 'FC-YDLS-006':
            history.click_clear_all()
            auto_assert(history, self.driver, case.expected)
            history.wait_for_page_ready()

        # FC-YDLS-006: 清空只清自己的不影响其他用户
        if case_id == 'FC-YDLS-006':
            # 隔离验证：lisi 先产生历史 → zhangsan 清空自己的 → lisi 的历史仍在
            from case.conftest import login as _login
            home0 = PageHome(self.driver)
            _login(self.driver, 'lisi', '123456')
            home0.open_url()
            home0.wait_for_page_ready()
            assert home0.get_article_count() > 0, "首页应有文章供 lisi 浏览"
            home0.click_article_by_index(0)
            home0.wait_for_page_ready()
            import re as _re
            m = _re.search(r"/article/(\d+)", self.driver.current_url)
            assert m, "应成功打开文章详情页"
            lisi_article_id = int(m.group(1))
            # zhangsan 清空自己的阅读历史（重新登录后需重新打开历史页）
            _login(self.driver, user, pwd)
            history.open_url(case.resolved_path())
            history.wait_for_page_ready()
            history.click_clear_all()
            try:
                history.wait_for_confirm_dialog(timeout=3)
                history.confirm_dialog()
                history.wait_for_page_ready()
            except Exception:
                pass
            # 切回 lisi：其阅读历史应不受影响，仍包含刚才浏览的文章
            _login(self.driver, 'lisi', '123456')
            home0.open_url()
            home0.wait_for_page_ready()
            history.open_url(case.resolved_path())
            history.wait_for_page_ready()
            titles_after = history.get_article_titles()
            assert history.get_history_count() > 0, \
                "zhangsan 清空自己的历史后，lisi 的历史不应被清空"
            detail0 = PageArticleDetail(self.driver)
            detail0.open_url(f'/article/{lisi_article_id}')
            detail0.wait_for_page_ready()
            lisi_title = detail0.get_title()
            assert any(lisi_title in t for t in titles_after), \
                f"lisi 的历史应包含其浏览的文章'{lisi_title}'，实际={titles_after[:3]}"
            return

        # FC-YDLS-003: 再次浏览同一篇文章阅读时间更新
        if case_id == 'FC-YDLS-003':
            # 第一次浏览已发生（上方通用流程），取 article_id 做 DB 前后对比
            import re as _re
            m = _re.search(r"/article/(\d+)", self.driver.current_url)
            if not m:
                # 通用流程走的是首页第一篇，重新以详情页 URL 定位
                home0 = PageHome(self.driver)
                home0.open_url()
                home0.wait_for_page_ready()
                home0.click_article_by_index(0)
                home0.wait_for_page_ready()
                m = _re.search(r"/article/(\d+)", self.driver.current_url)
            assert m, "应能定位到被浏览的文章ID"
            article_id = int(m.group(1))
            t1 = db_query.read_time(user, article_id)
            assert t1 is not None, "第一次浏览后 read_history 应有记录"
            # 第二次浏览同一篇
            detail0 = PageArticleDetail(self.driver)
            import time as _time
            from datetime import datetime
            _time.sleep(1.1)  # 保证时间戳可区分（秒级精度）
            _mark = datetime.now()
            detail0.open_url(f'/article/{article_id}')
            detail0.wait_for_page_ready()
            t2 = db_query.read_time(user, article_id)
            assert t2 is not None and t2 > t1, \
                f"再次浏览后阅读时间应更新: 更新前={t1}, 更新后={t2}（第二次浏览开始于{_mark}）"
            return

        # FC-YDLS-002: 浏览文章详情自动记录到阅读历史
        if case_id == 'FC-YDLS-002':
            assert target_title, "浏览详情页时应能取到文章标题"
            # 历史列表中应能看到刚浏览的文章
            titles = history.get_article_titles()
            assert titles, "阅读历史列表不应为空"
            assert any(target_title in t for t in titles), \
                f"刚浏览的文章'{target_title}'应出现在阅读历史中，实际={titles[:3]}"
            return

        auto_assert(history, self.driver, case.expected)
