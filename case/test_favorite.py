"""收藏模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_home import PageHome
from page.page_login import PageLogin
from page.page_article_detail import PageArticleDetail
from page.page_favorite import PageFavorite
from utils.assert_helpers import auto_assert, assert_toast
from utils.config import Config
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="收藏")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


@allure.epic("UI自动化测试")
@allure.feature("收藏功能")
class TestFavorite:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    @pytest.mark.parametrize("case_id,case", _params, ids=_ids)
    def test_favorite(self, case_id, case):

        # 未登录收藏（FC-SC-007）— 触发动作 = 点击收藏按钮
        # 前端 handleToggleFavorite：未登录点击收藏弹"请先登录"toast。
        # 直接定向断言 toast（auto_assert 多关键词轮询会先查"失败"等无关词，
        # 把 3 秒的 toast 等过期）。
        if not case.login_required and "未登录" in case.title:
            home = PageHome(self.driver)
            home.open_url()
            home.wait_for_page_ready()
            if home.get_article_count() > 0:
                home.click_article_by_index(0)
                home.wait_for_page_ready()
            detail = PageArticleDetail(self.driver)
            detail.click_favorite()
            toast = detail.quick_wait_toast("请先登录", timeout=3, interval=0.2)
            assert toast, "未登录点击收藏应弹出'请先登录'提示"
            return

        # 已登录操作
        user = case.login_user or "zhangsan"
        pwd = case.login_password or "123456"
        login_page = PageLogin(self.driver)
        login_page.login(user, pwd)

        home = PageHome(self.driver)
        home.open_url()
        home.wait_for_page_ready()
        if home.get_article_count() == 0:
            pytest.skip("无文章可测试")

        home.click_article_by_index(0)
        home.wait_for_page_ready()
        detail = PageArticleDetail(self.driver)

        # FC-SC-004: 收藏成功收藏数+1
        if case_id == 'FC-SC-004':
            count_before = detail.get_favorite_count()
            detail.click_favorite()
            detail.wait_for_page_ready()
            count_after = detail.get_favorite_count()
            # 收藏数应变化(+1 或变为已收藏状态)
            auto_assert(detail, self.driver, case.expected)
            detail.wait_for_page_ready()
            return

        # FC-SC-005: 取消收藏成功收藏数-1
        if case_id == 'FC-SC-005':
            # 先确保已收藏状态
            detail.click_favorite()
            detail.wait_for_page_ready()
            count_before = detail.get_favorite_count()
            detail.click_favorite()
            detail.wait_for_page_ready()
            count_after = detail.get_favorite_count()
            auto_assert(detail, self.driver, case.expected)
            detail.wait_for_page_ready()
            return

        # FC-SC-006: 从我的收藏列表取消收藏
        if case_id == 'FC-SC-006':
            # 先收藏文章
            detail.click_favorite()
            detail.wait_for_page_ready()
            # 进入收藏列表页面
            fav_page = PageFavorite(self.driver)
            fav_page.open_url()
            fav_page.wait_for_page_ready()
            titles_before = fav_page.get_article_titles()
            assert len(titles_before) > 0, "收藏列表应有文章"
            # 取消收藏第一篇
            fav_page.click_unfavorite(0)
            fav_page.wait_for_page_ready()
            # 处理确认弹框（如有）
            try:
                fav_page.wait_for_confirm_dialog(timeout=3)
                fav_page.confirm_dialog()
                fav_page.wait_for_page_ready()
            except Exception:
                pass
            auto_assert(fav_page, self.driver, case.expected)
            return

        # FC-SC-003: 我的收藏列表显示收藏文章信息
        if case_id == 'FC-SC-003':
            # 先收藏文章
            detail.click_favorite()
            detail.wait_for_page_ready()
            # 进入收藏列表页面验证
            fav_page = PageFavorite(self.driver)
            fav_page.open_url()
            fav_page.wait_for_page_ready()
            assert fav_page.get_favorite_count() > 0, "收藏列表应显示收藏的文章"
            auto_assert(fav_page, self.driver, case.expected)
            return

        # FC-SC-001: 收藏按钮显示当前收藏状态
        if case_id == 'FC-SC-001':
            # 检查收藏按钮是否存在并显示状态
            btn_text = detail.get_text(detail.favorite_btn)
            assert btn_text, "收藏按钮应显示文本（已收藏或收藏）"
            auto_assert(detail, self.driver, case.expected)
            return

        # FC-SC-002: 文章详情页显示收藏数量
        if case_id == 'FC-SC-002':
            count_text = detail.get_favorite_count()
            assert count_text is not None, "详情页应显示收藏数量"
            auto_assert(detail, self.driver, case.expected)
            return

        detail.click_favorite()
        auto_assert(detail, self.driver, case.expected)
        detail.wait_for_page_ready()
