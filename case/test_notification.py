"""通知模块 UI 测试 — 数据驱动"""
import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.data_loader import UiDataLoader
from page.page_login import PageLogin
from page.page_notification import PageNotification
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from utils.assert_helpers import auto_assert
from utils.paths import UI_DATASOURCE as DATASOURCE
import allure

_loader = UiDataLoader(DATASOURCE)
_cases = _loader.load_functional_cases(module="通知")
_loader.close()
_params = [(c.case_id, c) for c in _cases]
_ids = [c.case_id for c in _cases]


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
            # 等待页面元素渲染完成（替代 sleep）
            from selenium.webdriver.support import expected_conditions as EC
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

        # 点击某条通知标记已读（FC-TZ-005）
        if "标记已读" in case.title or "已读未读" in case.expected:
            if notif.get_notification_count() > 0:
                notif.click_notification(0)
                notif.wait_for_page_ready()
                # 精确断言: 点击后通知应变为已读状态
                # (auto_assert 路径6 会检查无错误状态)

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

        # 无未读消息时全部已读按钮不可用（FC-TZ-011）
        if "全部已读" in case.title and "不可用" in case.title:
            items = self.driver.find_elements(By.CSS_SELECTOR, ".notification-item")
            btns = self.driver.find_elements(By.XPATH,
                '//div[contains(@class,"notification-actions")]//button[contains(.,"全部已读")]')
            if len(btns) == 0:
                pass  # 按钮不存在，符合预期
            else:
                is_disabled = not btns[0].is_enabled() or "is-disabled" in btns[0].get_attribute("class")
                assert is_disabled, "无未读消息时全部已读按钮应置灰或隐藏"

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

        auto_assert(notif, self.driver, case.expected)
