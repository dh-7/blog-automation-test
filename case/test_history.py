"""阅读历史模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_home import PageHome
from page.page_login import PageLogin
from page.page_history import PageHistory
from page.page_article_detail import PageArticleDetail
from utils.assert_helpers import auto_assert, assert_url
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="阅读历史")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


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
            # 清空当前用户(zhangsan)的阅读历史
            history.click_clear_all()
            history.wait_for_page_ready()
            # 处理确认弹框
            try:
                history.wait_for_confirm_dialog(timeout=3)
                history.confirm_dialog()
                history.wait_for_page_ready()
            except Exception:
                pass
            # 登录另一个用户(lisi)验证历史不受影响
            login_page = PageLogin(self.driver)
            login_page.login('lisi', '123456')
            # 先让lisi浏览一篇文章产生历史
            home = PageHome(self.driver)
            home.open_url()
            home.wait_for_page_ready()
            if home.get_article_count() > 0:
                home.click_article_by_index(0)
                home.wait_for_page_ready()
            history.open_url(case.resolved_path())
            history.wait_for_page_ready()
            auto_assert(history, self.driver, case.expected)
            return

        auto_assert(history, self.driver, case.expected)
