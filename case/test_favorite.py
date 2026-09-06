"""收藏模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_home import PageHome
from page.page_login import PageLogin
from page.page_article_detail import PageArticleDetail
from page.page_favorite import PageFavorite
from utils import db_query
from utils.assert_helpers import auto_assert, assert_toast
from utils.config import Config
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="收藏")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


def _article_id_from_url(driver):
    """从详情页 URL 提取文章ID，如 /article/3 -> 3"""
    import re
    m = re.search(r"/article/(\d+)", driver.current_url)
    return int(m.group(1)) if m else None


def _int_in(text):
    """从按钮文本（如'收藏 3'）中提取数字，无数字返回 0"""
    import re
    m = re.search(r"\d+", str(text))
    return int(m.group()) if m else 0


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
            import time
            aid0 = _article_id_from_url(self.driver)
            # 确保起始为"未收藏"：若已收藏先取消
            if db_query.favorite_row(user, aid0):
                detail.click_favorite()
                for _ in range(10):
                    if not db_query.favorite_row(user, aid0):
                        break
                    time.sleep(0.5)
            db_before = db_query.favorite_row(user, aid0)
            assert not db_before, "前置状态应为未收藏"
            count_before = detail.get_favorite_count()
            detail.click_favorite()
            db_after = None
            for _ in range(10):
                db_after = db_query.favorite_row(user, aid0)
                if db_after:
                    break
                time.sleep(0.5)
            detail.wait_for_page_ready()
            count_after = detail.get_favorite_count()
            assert db_after, "收藏后 DB 应存在收藏记录"
            assert _int_in(count_after) == _int_in(count_before) + 1, (
                f"收藏数应+1: 操作前={count_before}, 操作后={count_after}")
            return

        # FC-SC-005: 取消收藏成功收藏数-1
        if case_id == 'FC-SC-005':
            import time
            aid0 = _article_id_from_url(self.driver)
            # 确保起始为"已收藏"：若未收藏先收藏
            if not db_query.favorite_row(user, aid0):
                detail.click_favorite()
                for _ in range(10):
                    if db_query.favorite_row(user, aid0):
                        break
                    time.sleep(0.5)
            db_before = db_query.favorite_row(user, aid0)
            assert db_before, "前置状态应为已收藏"
            count_before = detail.get_favorite_count()
            # 取消收藏（轮询等待删除完成）
            detail.click_favorite()
            db_after = db_before
            for _ in range(10):
                db_after = db_query.favorite_row(user, aid0)
                if not db_after:
                    break
                time.sleep(0.5)
            detail.wait_for_page_ready()
            count_after = detail.get_favorite_count()
            assert not db_after, (
                f"取消收藏后 DB 收藏记录应消失（操作前={db_before}, 操作后={db_after}）")
            assert _int_in(count_after) == _int_in(count_before) - 1, (
                f"收藏数应-1: 操作前={count_before}, 操作后={count_after}")
            return

        # FC-SC-006: 从我的收藏列表取消收藏（该文章从列表消失；列表可有其他收藏）
        if case_id == 'FC-SC-006':
            # 先收藏文章（轮询等待写库完成，再进收藏列表）
            import time as _t
            aid0 = _article_id_from_url(self.driver)
            detail.click_favorite()
            for _ in range(10):
                if db_query.favorite_row(user, aid0):
                    break
                _t.sleep(0.5)
            detail.wait_for_page_ready()
            target_title = detail.get_title()
            # 进入收藏列表页面验证
            fav_page = PageFavorite(self.driver)
            fav_page.open_url()
            fav_page.wait_for_page_ready()
            titles_before = fav_page.get_article_titles()
            if not any(target_title in t for t in titles_before):
                # 列表可能取到缓存旧数据，刷新一次再确认
                fav_page.open_url()
                fav_page.wait_for_page_ready()
                titles_before = fav_page.get_article_titles()
            assert any(target_title in t for t in titles_before),                 f"收藏列表应包含'{target_title}'，实际={titles_before}"
            # 取消收藏第一篇（即刚收藏的文章）
            fav_page.click_unfavorite(0)
            fav_page.wait_for_page_ready()
            # 处理确认弹框（如有）
            try:
                fav_page.wait_for_confirm_dialog(timeout=3)
                fav_page.confirm_dialog()
                fav_page.wait_for_page_ready()
            except Exception:
                pass
            titles_after = fav_page.get_article_titles()
            assert not any(target_title in t for t in titles_after),                 f"取消收藏后'{target_title}'应从收藏列表消失，实际={titles_after}"
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
            # 检查收藏按钮存在且文本明确表达状态（收藏/已收藏）
            btn_text = detail.get_text(detail.favorite_btn)
            assert btn_text and ("收藏" in btn_text), \
                f"收藏按钮应显示'收藏/已收藏'状态文本，实际='{btn_text}'"
            return

        # FC-SC-002: 文章详情页显示收藏数量
        if case_id == 'FC-SC-002':
            count_text = detail.get_favorite_count()
            assert count_text is not None, "详情页应显示收藏数量"
            assert _int_in(count_text) >= 0 and any(ch.isdigit() for ch in str(count_text)), \
                f"收藏数量应为数字，实际='{count_text}'"
            return

        detail.click_favorite()
        auto_assert(detail, self.driver, case.expected)
        detail.wait_for_page_ready()
