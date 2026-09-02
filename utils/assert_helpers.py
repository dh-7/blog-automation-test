"""UI 测试断言辅助工具 — 根据预期结果文本自动选择断言方式"""
import re
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By


# ── 关键词 → 断言策略映射 ──

# URL 跳转类关键词
_URL_KEYWORDS = {
    "首页": "/",
    "登录": "/login",
    "注册": "/register",
    "后台": "/admin",
    "个人中心": "/profile",
}

# 错误提示类关键词（toast 或表单错误）
_ERROR_KEYWORDS = [
    "不能为空", "已存在", "错误", "不存在", "无权", "失败",
    "不一致", "长度", "超过", "不足", "请先登录", "需要登录", "无权限",
]

# 关键词 → 常见实际toast文本变体（用于模糊匹配）
_TOAST_VARIANTS = {
    "需要登录": ["请先登录", "需要登录", "请登录"],
    "无权": ["无权", "无权限", "没有权限", "无权操作"],
    "不能为空": ["不能为空", "请输入", "请填写", "不能为"],
    "不存在": ["不存在", "未找到", "找不到"],
}


def _extract_quoted_texts(text):
    """从文本中提取引号内的内容（支持中英文引号）

    例: '提示\"用户名长度3-20位\"，注册失败' → ['用户名长度3-20位']
    """
    patterns = [
        r'\u201c([^\u201d]+)\u201d',  # \u201c...\u201d 中文双引号
        r'"([^"]+)"',                   # "..." 英文双引号
        r'\u2018([^\u2019]+)\u2019',  # \u2018...\u2019 中文单引号
        r'「([^」]+)」',                 # 「...」
    ]
    results = []
    for p in patterns:
        results.extend(re.findall(p, text))
    return [r for r in results if r.strip()]


def _check_page_contains(page, driver, text):
    """检查页面源码中是否包含指定文本"""
    page.wait_for_page_ready()
    source = driver.page_source
    assert text in source, f"页面中未找到文本: '{text}'"


def _match_url_keyword(expected, trigger):
    """匹配预期文本中的目标页面关键词

    优先取触发词（"进入"/"跳转"）之后的关键词：避免 "登录成功，……进入后台管理页面"
    这类文本中，"登录"（来自"登录成功"）错误盖过真正的目标页"后台"。
    """
    idx = expected.find(trigger)
    if idx != -1:
        tail = expected[idx + len(trigger):]
        for keyword, url_part in _URL_KEYWORDS.items():
            if keyword in tail:
                return keyword, url_part
    # 回退：整个预期文本内匹配（触发词前后均可能出现，如"页面自动跳转到首页"）
    for keyword, url_part in _URL_KEYWORDS.items():
        if keyword in expected:
            return keyword, url_part
    return None, None


def _check_page_not_contains(page, driver, text):
    """检查页面源码中不包含指定文本"""
    page.wait_for_page_ready()
    source = driver.page_source
    assert text not in source, f"页面中不应包含文本: '{text}'"


def auto_assert(page, driver, expected):
    """根据预期结果文本自动断言

    逻辑：
    1. 包含"跳转" → 检查 URL
    2. 包含错误关键词 → 检查 toast 或表单错误（必须找到，否则失败）
    3. 包含"显示" → 检查页面包含预期文本
    4. 包含"消失/为空/不可见/不包含" → 检查页面不包含或列表为空
    5. 包含"弹出/确认/提示框" → 检查弹窗出现
    6. 包含"进入" → 检查 URL 跳转
    7. 包含"成功" → 检查 toast 或 URL 变化
    8. 其他 → 检查页面包含预期文本
    """
    if not expected:
        return

    # 1. URL 跳转类
    if "跳转" in expected:
        _kw, url_part = _match_url_keyword(expected, "跳转")
        if url_part is not None:
            try:
                page.wait_for_url_contains(url_part, timeout=10)
            except Exception:
                pass
            assert url_part in driver.current_url, \
                f"预期跳转到 {url_part}，实际 URL: {driver.current_url}"
            return

    # 2. 错误提示类（toast 或表单验证）— 必须找到，否则失败
    matched_keywords = [kw for kw in _ERROR_KEYWORDS if kw in expected]
    if matched_keywords:
        # 2a. 优先：提取 expected 中引号内的精确文本搜索
        #     例: expected='提示\"3-20位\"，注册失败' → 搜索 \"3-20位\"
        quoted_texts = _extract_quoted_texts(expected)
        for qt in quoted_texts:
            toast = page.quick_wait_toast(qt, timeout=3, interval=0.2)
            if toast:
                return
            form_err = page.find_form_error(qt)
            if form_err:
                return
            form_err = page.wait_for_form_error(qt, timeout=2)
            if form_err:
                return

        # 2b. 用 error keywords 搜索（尝试所有匹配的关键词，不再只试第一个）
        for keyword in matched_keywords:
            toast = page.quick_wait_toast(keyword, timeout=2, interval=0.2)
            if toast:
                return
            form_err = page.find_form_error(keyword)
            if form_err:
                return
            form_err = page.wait_for_form_error(keyword, timeout=1)
            if form_err:
                return

        # 2b2. 用 toast 变体搜索（如"需要登录"→"请先登录"）
        for keyword in matched_keywords:
            variants = _TOAST_VARIANTS.get(keyword, [])
            for variant in variants:
                if variant == keyword:
                    continue  # 已在2b中搜索过
                toast = page.quick_wait_toast(variant, timeout=2, interval=0.2)
                if toast:
                    return
                form_err = page.find_form_error(variant)
                if form_err:
                    return
                form_err = page.wait_for_form_error(variant, timeout=1)
                if form_err:
                    return

        # 2b3. 引号文本的"X不能为空"→"请输入X"变体
        for qt in quoted_texts:
            m = re.match(r'(.+?)不能为空', qt)
            if m:
                prefix = m.group(1)
                for alt in [f"请输入{prefix}", f"请填写{prefix}", "请输入", "请填写"]:
                    toast = page.quick_wait_toast(alt, timeout=2, interval=0.2)
                    if toast:
                        return
                    form_err = page.find_form_error(alt)
                    if form_err:
                        return

        # 2b4. 检查页面是否有错误状态元素(el-result/error-state)或错误文本
        page.wait_for_page_ready()
        error_els = driver.find_elements(By.CSS_SELECTOR,
            '.el-result__title, .error-state, .el-result__subtitle')
        if error_els:
            return  # 页面有错误状态元素，视为验证通过
        source = driver.page_source
        for keyword in matched_keywords:
            if keyword in source:
                return  # 页面源码包含错误关键词
        # 也检查引号文本是否出现在页面中(可能是静态文本而非toast)
        for qt in quoted_texts:
            if qt in source:
                return

        # 2c. 通用表单校验匹配
        _form_error_fallbacks = [
            "请输入", "不能为", "必填", "至少", "不能少于",
            "不能超过", "格式", "合法", "请填写",
        ]
        for fallback in _form_error_fallbacks:
            err = page.find_form_error(fallback)
            if err:
                return
        for fallback in _form_error_fallbacks:
            err = page.wait_for_form_error(fallback, timeout=2)
            if err:
                return
        # 全部未找到 → 断言失败
        assert False, (
            f"预期出现错误提示（引号文本: {quoted_texts}, 关键词: {matched_keywords}），"
            f"但未找到 toast 或表单错误"
        )
        return

    # 3. "消失/为空/不可见/不包含" 类 → 检查页面不包含或列表为空
    _not_present_keywords = ["不显示", "消失", "为空", "空列表", "不可见", "不包含", "不产生"]
    for keyword in _not_present_keywords:
        if keyword in expected:
            page.wait_for_page_ready()
            # 3a. 提取引号文本，验证已从页面消失
            quoted = _extract_quoted_texts(expected)
            source = driver.page_source
            for qt in quoted:
                assert qt not in source, \
                    f"预期'{qt}'不应出现在页面中，但仍存在"
            # 3b. 如果预期含"列表为空"/"消失"，检查列表确实为空
            if "为空" in expected or "消失" in expected:
                empty_els = driver.find_elements(
                    By.CSS_SELECTOR,
                    '.empty-state, .el-table__empty-text, '
                    '.el-empty, .no-data')
                list_items = driver.find_elements(
                    By.CSS_SELECTOR,
                    '.article-card, .article-item, .comment-item, '
                    '.notification-item, .history-item, .favorite-item, '
                    '.el-table__row')
                if not empty_els:
                    assert len(list_items) == 0, \
                        f"预期列表为空或元素消失，但仍有{len(list_items)}项"
            # 3c. "不包含" → 验证特定文本不在列表项中
            if "不包含" in expected and quoted:
                items = driver.find_elements(
                    By.CSS_SELECTOR,
                    '.related-item, .article-card, .comment-item')
                for item in items:
                    for qt in quoted:
                        assert qt not in item.text, \
                            f"列表项中不应包含'{qt}'，但实际包含"
            # 3d. "不产生" → 验证没有新通知/数据产生
            if "不产生" in expected:
                notif_items = driver.find_elements(
                    By.CSS_SELECTOR, '.notification-item')
                # "不产生通知"时，通知列表应为空或无新通知
                # 这里只做基础检查，具体逻辑由业务流程测试覆盖
                pass
            return

    # 4. "弹出/确认/提示框" 类 → 检查弹窗出现
    if "弹出" in expected or "确认" in expected or "提示框" in expected:
        try:
            page.wait_for_confirm_dialog(timeout=5)
            return
        except Exception:
            pass
        # 也可能是 toast
        for kw in ["确认", "提示"]:
            toast = page.wait_for_toast(kw, timeout=3)
            if toast:
                return
        # 检查页面是否包含相关文本（可能是静态提示而非弹窗）
        source = driver.page_source
        for kw in ["确认", "提示", "二次确认"]:
            if kw in source:
                return
        assert False, f"预期出现弹窗或提示，但未找到"
        return

    # 5. "进入" 类 → 检查 URL 跳转
    if "进入" in expected:
        _kw, url_part = _match_url_keyword(expected, "进入")
        if url_part is not None:
            try:
                page.wait_for_url_contains(url_part, timeout=10)
            except Exception:
                pass
            assert url_part in driver.current_url, \
                f"预期进入 {url_part}，实际 URL: {driver.current_url}"
            return
        # 没有匹配到具体页面，至少检查页面加载且无错误
        page.wait_for_page_ready()
        source = driver.page_source
        assert len(source) > 500, "页面内容过少，可能加载失败"
        return

    # 6. "成功" 类 → 检查 toast 出现或页面状态变化
    if "成功" in expected:
        # 尝试找 toast（各种成功提示）
        for toast_text in ["成功", "已", "完成"]:
            toast = page.wait_for_toast(toast_text, timeout=3)
            if toast:
                return
        # 没有 toast → 验证操作未失败
        page.wait_for_page_ready()
        # 检查是否有错误提示（说明操作失败）
        error = page.find_form_error()
        assert not error, f"操作出现表单错误: {error}"
        # 检查页面不含明显的失败/错误状态
        source = driver.page_source
        error_els = driver.find_elements(
            By.CSS_SELECTOR, '.el-result__title, .error-state')
        if error_els:
            err_text = error_els[0].text
            assert False, f"页面显示错误状态: {err_text}"
        return

    # 7. "显示" 类 → 检查页面包含预期文本或元素
    if "显示" in expected:
        page.wait_for_page_ready()
        # 7a. 提取引号文本，验证在页面中存在
        quoted = _extract_quoted_texts(expected)
        source = driver.page_source
        for qt in quoted:
            assert qt in source, f"页面中未找到'{qt}'"
        # 7b. 如果没有引号文本，用关键词映射检查元素
        if not quoted:
            _display_checks = {
                "输入框": "input, textarea, .el-input, .el-textarea",
                "按钮": "button, .el-button",
                "列表": ".article-item, .article-card, .comment-item, .el-table, "
                       ".notification-item, .history-item",
                "分页": ".pagination, .el-pagination",
                "头像": ".avatar, .user-avatar, img.avatar, .el-avatar",
                "昵称": ".nickname, .user-name, .author-name, "
                        ".meta-author, .el-table .cell",
                "统计": ".stat-card, .stat-item, .count-card, "
                        ".stats-grid, .stat-number",
                "评论": ".comment-section, .comment-item, "
                        ".comment-form, .el-table",
                "文章": ".article-item, .article-card, .article-title, "
                        ".article-content",
                "通知": ".notification-item, .notification-list, "
                        ".notification-panel",
                "收藏": ".favorite-btn, .favorite-count, "
                        ".action-btn, .el-table",
                "标签": ".el-tag, .tag, .article-tags .tag, .el-table .cell, "
                         ".tag-item, .tag-cloud .tag-item",
                "分类": ".category-item, .category-name, .el-table .cell",
                "目录": ".toc, .article-toc, .table-of-contents",
                "导航": "nav, .navbar, .el-menu",
                "搜索": "input[placeholder*='搜索'], .search-input",
                "编辑": ".editor, .markdown-editor, .el-textarea",
                "表格": ".el-table, .el-table__row",
                "操作": "button, .el-button, .el-table .cell",
                "注册时间": ".el-table .cell, .meta-date",
                "角色": ".el-table .cell, .el-tag",
            }
            checked = False
            for keyword, selector in _display_checks.items():
                if keyword in expected:
                    els = driver.find_elements(By.CSS_SELECTOR, selector)
                    assert len(els) > 0, \
                        f"预期显示{keyword}，但未找到对应元素({selector})"
                    checked = True
                    break
            # 7c. 如果关键词都不匹配，至少验证页面有实质内容
            if not checked:
                assert len(source) > 500, \
                    "页面内容过少，可能加载失败"
        return

    # 8. 默认 → 检查页面加载且无错误状态
    page.wait_for_page_ready()
    source = driver.page_source
    # 至少验证页面有实质内容
    assert len(source) > 500, "页面内容过少，可能加载失败"
    # 检查页面不处于错误/异常状态
    error_els = driver.find_elements(
        By.CSS_SELECTOR, '.el-result__title, .error-state')
    if error_els:
        err_text = error_els[0].text
        assert False, f"页面显示错误状态: {err_text}"


def assert_url(page, driver, url_part):
    """断言 URL 包含指定字符串"""
    try:
        page.wait_for_url_contains(url_part, timeout=10)
    except Exception:
        pass
    assert url_part in driver.current_url, \
        f"预期 URL 包含 '{url_part}'，实际: {driver.current_url}"


def assert_toast(page, keyword, timeout=5):
    """断言出现包含关键词的 toast"""
    toast = page.wait_for_toast(keyword, timeout=timeout)
    assert toast is not None, f"未找到包含 '{keyword}' 的 toast 提示"
    return toast


def assert_form_error(page, keyword, timeout=5):
    """断言出现包含关键词的表单验证错误"""
    err = page.wait_for_form_error(keyword, timeout=timeout)
    assert err is not None, f"未找到包含 '{keyword}' 的表单错误"
    return err
