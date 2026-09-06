"""通知模块 UI 测试 — 数据驱动"""
import os, sys, pytest
from base.data_loader import UiDataLoader
from page.page_login import PageLogin
from page.page_notification import PageNotification
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from utils import db_query
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="通知")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


def _db_unread(username):
    """当前用户未读通知数（DB 口径）"""
    return db_query.unread_notification_count(username)


def _badge_int(text):
    import re
    m = re.search(r"\d+", str(text))
    return int(m.group()) if m else 0


@allure.epic("UI自动化测试")
@allure.feature("通知功能")
class TestNotification:

    @pytest.fixture(autouse=True)
    def _setup(self, driver):
        self.driver = driver

    @pytest.mark.parametrize("case_id,case", _params, ids=_ids)
    def test_notification(self, case_id, case):
        user = case.login_user
        pwd = case.login_password
        notif = PageNotification(self.driver)

        # FC-TZ-009: 未登录用户不显示通知图标（数据源登录用户为 None，不执行登录）
        if case_id == 'FC-TZ-009':
            from page.page_home import PageHome
            home = PageHome(self.driver)
            home.open_url()
            home.wait_for_page_ready()
            # 等待通知铃铛出现（正向），或等待登录按钮出现确认未登录（负向）。
            # 注意：不能用 contains(text(),"登录")——text() 节点集在 contains() 中匹配不到，
            # 实际验证过必须用 href 定位器或 contains(.,"登录")。
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, '.notification-bell')
                   or d.find_elements(By.XPATH, '//header//a[contains(@href,"/login")]')
            )
            # 导航栏不应显示通知铃铛图标（Layout.vue中v-if="userStore.isLoggedIn"）
            # 检查通知铃铛的可见性而非存在性（v-if会从DOM移除）
            bell = self.driver.find_elements(By.CSS_SELECTOR, '.notification-bell')
            # v-if会完全移除DOM元素，所以bell应该为空
            # 如果bell不为空，检查是否是因为用户仍处于登录状态
            if len(bell) > 0:
                # 验证确实未登录（应显示登录/注册按钮）
                login_btns = self.driver.find_elements(By.XPATH,
                    '//header//a[contains(@href,"/login")]')
                assert len(login_btns) > 0, "页面应显示登录按钮（未登录状态），但未找到"
            auto_assert(notif, self.driver, case.expected)
            return

        # 其余用例需登录（FC-TZ-009 之外数据源均提供登录用户）
        login_page = PageLogin(self.driver)
        login_page.open_url()
        login_page.input_username(user or "zhangsan")
        login_page.input_password(pwd or "123456")
        login_page.click_login_button()
        # 等待登录成功（URL 离开 /login）；登录失败立即暴露，而非静默导致后续铃铛找不到
        login_page.wait_for_login_success()

        notif.open_url(case.resolved_path())
        notif.wait_for_page_ready()

        # FC-TZ-001: 通知列表显示完整通知信息（内容/时间/头像逐项结构校验）
        if case_id == 'FC-TZ-001':
            items = self.driver.find_elements(By.CSS_SELECTOR, ".notification-item")
            assert len(items) > 0, \
                "通知列表应有通知（前置数据：FC-PL-007/YW-PLHD-004 已产生通知）"
            for i, item in enumerate(items[:5]):
                content = item.find_elements(By.CSS_SELECTOR, ".notification-content")
                assert content and content[0].text.strip(), f"通知{i}缺内容"
                assert item.find_elements(By.CSS_SELECTOR, ".notification-time"), \
                    f"通知{i}缺时间"
                assert item.find_elements(By.CSS_SELECTOR, "img, .el-avatar"), \
                    f"通知{i}缺发送人头像"
            return

        # FC-TZ-002: 导航栏显示未读通知数量角标
        if case_id == 'FC-TZ-002':
            db_unread = _db_unread(user)
            assert db_unread > 0, \
                f"前置数据缺失：{user} 应有未读通知（DB未读数={db_unread}）"
            badges = self.driver.find_elements(
                By.CSS_SELECTOR, '.notification-bell .el-badge__content')
            assert badges, "有未读通知时导航栏应显示未读角标"
            assert _badge_int(badges[0].text) == db_unread, \
                f"角标数字({badges[0].text})应等于DB未读数({db_unread})"
            return

        # FC-TZ-003: 有新通知时未读数角标显示正确的数字
        if case_id == 'FC-TZ-003':
            db_unread = _db_unread(user)
            assert db_unread > 0, \
                f"前置数据缺失：{user} 应有未读通知（DB未读数={db_unread}）"
            badges = self.driver.find_elements(
                By.CSS_SELECTOR, '.notification-bell .el-badge__content')
            assert badges, "有未读通知时应显示角标"
            assert _badge_int(badges[0].text) == db_unread, \
                f"角标数字({badges[0].text})与实际未读数({db_unread})不一致"
            return

        # FC-TZ-004: 通知列表按时间从新到旧排列（UI 顺序与 DB 时间倒序一致）
        if case_id == 'FC-TZ-004':
            items = self.driver.find_elements(By.CSS_SELECTOR, ".notification-item")
            n = min(5, len(items))
            assert n >= 2, "至少需要2条通知才能验证排序"
            expected = db_query.notifications_ordered_desc(user, n)
            for i in range(n):
                ui_text = items[i].text
                db_content = expected[i][1]
                assert db_content in ui_text, \
                    f"通知第{i+1}条应是最新的'{db_content}'，实际UI显示: '{ui_text[:50]}'"
            return

        # 点击某条通知标记已读（FC-TZ-005）— 精确验证未读数-1
        if case_id == 'FC-TZ-005':
            unread_before = _db_unread(user)
            assert unread_before > 0, \
                f"前置数据缺失：{user} 应有未读通知（DB未读数={unread_before}）"
            assert notif.click_first_unread(), "通知列表中应存在带未读蓝点的通知"
            notif.wait_for_page_ready()

            def _unread_changed(d):
                return _db_unread(user) == unread_before - 1
            assert WebDriverWait(self.driver, 5).until(_unread_changed), \
                f"点击通知后未读数应-1（{unread_before}→{unread_before-1}）"
            return

        # 全部已读（FC-TZ-006）
        if "全部已读" in case.title and "不可用" not in case.title:
            notif.click_mark_all_read()
            notif.wait_for_page_ready()
            # 精确断言: 所有通知应变为已读，未读数归0
            # （后端异步更新角标，轮询等待其归0/隐藏，而非点击后立即断言）
            def _unread_zero(d):
                badges = d.find_elements(By.CSS_SELECTOR, '.el-badge__content, .unread-count')
                return all(
                    not (b.text.strip().isdigit() and int(b.text.strip()) != 0)
                    for b in badges
                )
            assert WebDriverWait(self.driver, 5).until(lambda d: _unread_zero(d)), \
                "全部已读后未读数应归0"
            # 精确回查：DB 中该用户全部通知均已读
            assert _db_unread(user) == 0, "全部已读后 DB 中不应再有未读通知"
            return

        # 无未读消息时全部已读按钮不可用（FC-TZ-011）
        if "全部已读" in case.title and "不可用" in case.title:
            # 自给自足：若仍有未读，先全部已读，再验证按钮不可用
            if _db_unread(user) > 0:
                notif.click_mark_all_read()
                notif.wait_for_page_ready()
            assert _db_unread(user) == 0, (
                f"前置数据缺失：本用例要求无未读消息（DB未读数={_db_unread(user)}）")
            btns = self.driver.find_elements(By.XPATH,
                '//div[contains(@class,"notification-actions")]//button[contains(.,"全部已读")]')
            if len(btns) == 0:
                pass  # 按钮不存在，符合预期
            else:
                is_disabled = not btns[0].is_enabled() or "is-disabled" in btns[0].get_attribute("class")
                assert is_disabled, "无未读消息时全部已读按钮应置灰或隐藏"
            return

        # 删除单条（FC-TZ-007）
        if "删除单条" in case.title and notif.get_notification_count() > 0:
            count_before = notif.get_notification_count()
            notif.click_delete(0)
            notif.wait_for_page_ready()
            # 面板可能关闭，重新打开
            notif.open_url()
            notif.wait_for_page_ready()
            count_after = notif.get_notification_count()
            assert count_after < count_before, \
                f"删除后通知应减少: 删除前{count_before}, 删除后{count_after}"
            # 通知面板为悬浮 popover，通用 auto_assert 的"消失"分支会误检首页文章卡片；
            # 已用 count_after < count_before 精确验证"该通知从列表中消失"，此处直接返回
            return

        # 清空所有（FC-TZ-008）
        if "清空" in case.title:
            # 前端"清空"按钮仅在有通知时渲染（Layout.vue v-if），且清空无二次确认弹窗；
            # 无通知时按钮不存在，click_clear_all() 返回 False，此时数量已为 0
            notif.click_clear_all()
            notif.wait_for_page_ready()
            # 面板可能关闭，重新打开验证
            notif.open_url()
            notif.wait_for_page_ready()
            # 后端删除为异步，轮询等待通知列表变为空
            assert notif.wait_for_count(0, timeout=5), "清空后通知数应为0"
            # 通知为空时面板渲染 .notification-empty 空态（等待其出现）。
            # 注意：通知面板是悬浮在首页的 popover，页面其余区域（如首页文章卡片）
            # 与通知无关，故此处限定在 .notification-panel 内断言，而非通用 auto_assert。
            WebDriverWait(self.driver, 3).until(
                lambda d: d.find_elements(
                    By.CSS_SELECTOR, ".notification-panel .notification-empty")
            )
            assert not self.driver.find_elements(
                By.CSS_SELECTOR, ".notification-panel .notification-item"), \
                "清空后通知面板不应再有任何通知项"
            return

        # FC-TZ-010: 通知类型包括评论通知和回复通知（自造两类通知后验证）
        if case_id == 'FC-TZ-010':
            # 本模块 TZ-008 已清空通知，这里自造两类通知（接收人=zhangsan）
            from page.page_article_detail import PageArticleDetail
            from page.page_comment import PageComment
            from case.conftest import login as _login
            _login(self.driver, 'lisi', '123456')
            detail0 = PageArticleDetail(self.driver)
            # ① 评论 zhangsan 的文章3 -> comment 通知
            detail0.open_url('/article/3')
            detail0.wait_for_page_ready()
            c0 = PageComment(self.driver)
            c0.input_comment('自动化-TZ010验证-评论类型')
            c0.click_submit()
            c0.wait_for_page_ready()
            # ② 回复 zhangsan 在文章1的评论 -> reply 通知
            #    （评论列表按最新在前排序，必须定位到 zhangsan 的评论，不能盲取第0条）
            detail0.open_url('/article/1')
            detail0.wait_for_page_ready()
            c0 = PageComment(self.driver)
            zs_nick = db_query.scalar(
                "SELECT nickname FROM user WHERE username='zhangsan'")
            authors = c0.get_comment_authors()
            assert zs_nick in authors, "文章1应有 zhangsan 的评论可回复"
            reply_idx = authors.index(zs_nick)
            c0.click_reply(reply_idx)
            c0.input_reply('自动化-TZ010验证-回复类型')
            c0.submit_reply()
            c0.wait_for_page_ready()
            # ③ 切回 zhangsan 验证两类通知（断言失败也要恢复无未读，供 TZ-011 使用）
            _login(self.driver, 'zhangsan', '123456')
            notif.open_url(case.resolved_path())
            notif.wait_for_page_ready()
            try:
                assert db_query.has_notification_type('zhangsan', 'comment'), (
                    "zhangsan 的通知中应存在 comment（评论）类型通知")
                assert db_query.has_notification_type('zhangsan', 'reply'), (
                    "zhangsan 的通知中应存在 reply（回复）类型通知")
                items = self.driver.find_elements(By.CSS_SELECTOR, ".notification-item")
                texts = [it.text for it in items]
                assert any("回复" in t for t in texts), "通知列表中应能区分出回复类通知"
                assert any("评论" in t for t in texts), "通知列表中应能区分出评论类通知"
            finally:
                # ④ 恢复无未读状态（后续 TZ-011 依赖）
                notif.click_mark_all_read()
                notif.wait_for_page_ready()
            return

        auto_assert(notif, self.driver, case.expected)
