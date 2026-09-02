"""统一的 Excel 数据源加载器

将 api/DataLoader 和 base/UiDataLoader 合并到同一模块，
提取公共的 openpyxl 打开/关闭逻辑为 BaseExcelLoader。

子类:
    ApiCaseLoader  — 读取接口用例 Sheet + 全局配置 Sheet
    UiCaseLoader   — 读取 UI数据源 Sheet，返回 UiCase 结构体
    UiCase         — UI 用例的数据结构
"""
import os
import re
import openpyxl


# ============================================================
#  公共基类
# ============================================================

class BaseExcelLoader:
    """Excel 加载器基类 —— 封装 openpyxl 打开/关闭"""

    def __init__(self, filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"数据源文件不存在: {filepath}")
        self.filepath = filepath
        self._wb = openpyxl.load_workbook(filepath, read_only=True)

    def close(self):
        """关闭工作簿"""
        self._wb.close()


# ============================================================
#  接口测试数据加载器
# ============================================================

class ApiCaseLoader(BaseExcelLoader):
    """读取接口自动化数据源 Excel

    Sheet「全局配置」→ load_config() → dict
    Sheet「接口用例」→ load_cases()  → list[dict]
    """

    def load_config(self) -> dict:
        """读取全局配置 Sheet → dict"""
        ws = self._wb["全局配置"]
        config = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1] is not None:
                config[str(row[0]).strip()] = str(row[1]).strip()
        return config

    def load_cases(self, module: str = None, priority: str = None,
                   executable_only: bool = True) -> list:
        """读取接口用例 Sheet → list[dict]

        Args:
            module: 按模块筛选（可选）
            priority: 按优先级筛选（可选）
            executable_only: 是否只返回"是否执行=Y"的用例
        """
        ws = self._wb["接口用例"]
        headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        cases = []

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue

            case = dict(zip(headers, row))

            # 过滤：是否执行
            if executable_only and str(case.get("是否执行", "")).upper() != "Y":
                continue

            # 过滤：模块
            if module and case.get("所属模块") != module:
                continue

            # 过滤：优先级
            if priority and case.get("优先级") != priority:
                continue

            cases.append(case)

        return cases


# ============================================================
#  UI 测试数据结构 + 加载器
# ============================================================

# 不作为业务字段的列（核心字段 + 认证字段 + 预期结果 + 页面路径/方法）
_EXCLUDE_HEADERS = {
    "编号", "来源", "所属模块", "用例标题", "优先级",
    "页面路径", "请求方法",
    "是否需要登录", "登录用户", "登录密码", "用户角色",
    "预期结果",
}


class UiCase:
    """单条 UI 测试用例的结构化封装"""

    __slots__ = (
        "case_id", "source", "module", "title", "priority",
        "login_required", "login_user", "login_password", "role",
        "page_path", "fields", "expected",
    )

    def __init__(self, case_id, source, module, title, priority,
                 login_required, login_user, login_password, role,
                 page_path, fields, expected):
        self.case_id = case_id
        self.source = source
        self.module = module
        self.title = title
        self.priority = priority
        self.login_required = login_required
        self.login_user = login_user
        self.login_password = login_password
        self.role = role
        self.page_path = page_path    # 页面路径模板，如 /article/${article_id}
        self.fields = fields          # dict: 字段名 -> 值（已过滤空值）
        self.expected = expected      # 预期结果原文

    def __repr__(self):
        return f"<UiCase {self.case_id} [{self.module}] {self.title}>"

    def field(self, name, default=""):
        """安全取业务字段值，不存在返回 default"""
        return self.fields.get(name, default)

    def resolved_path(self):
        """将 page_path 模板中的 ${var} 替换为 fields 中的实际值（仅返回路径，不拼 base_url）。
        自动清理字段值中的中文括号注释（如 '1（或任意已发布文章ID）' -> '1'）。"""
        path = self.page_path or "/"
        def _replace(m):
            var_name = m.group(1)
            raw = self.fields.get(var_name, m.group(0))
            cleaned = re.split(r'[（(]', str(raw))[0].strip()
            return cleaned if cleaned else raw
        return re.sub(r'\$\{(\w+)\}', _replace, path)


class UiCaseLoader(BaseExcelLoader):
    """读取 UI 自动化数据源 Excel（Sheet「UI数据源」）

    load_cases()            -> list[UiCase]  (支持多维筛选)
    load_functional_cases() -> list[UiCase]  (仅功能测试用例)
    load_flow_cases()       -> list[UiCase]  (仅业务流程用例)
    get_modules()           -> list[str]
    """

    def __init__(self, filepath):
        super().__init__(filepath)
        self._ws = self._wb["UI数据源"]
        # 读取表头，建立 name -> index 映射
        self._headers = [
            str(cell.value) if cell.value else ""
            for cell in next(self._ws.iter_rows(min_row=1, max_row=1))
        ]
        self._header_idx = {h: i for i, h in enumerate(self._headers)}
        # 预期结果列索引
        self._expected_idx = self._header_idx.get("预期结果", 60)

    # ── 公开接口 ──

    def load_cases(self, module=None, priority=None, source=None,
                   login_required=None):
        """加载用例列表，支持按条件筛选

        Args:
            module:         按模块筛选
            priority:       按优先级筛选（高/中/低）
            source:         按来源筛选（功能测试用例/业务流程测试用例）
            login_required: True=只要需登录, False=只要不需登录, None=全部
        """
        cases = []
        for row in self._ws.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            case = self._parse_case(row)
            if module and case.module != module:
                continue
            if priority and case.priority != priority:
                continue
            if source and case.source != source:
                continue
            if login_required is not None and case.login_required != login_required:
                continue
            cases.append(case)
        return cases

    def load_functional_cases(self, module=None, priority=None):
        """只加载功能测试用例（排除 YW_ 业务流程）"""
        cases = self.load_cases(module=module, priority=priority,
                                source="功能测试用例")
        # 额外排除 YW_ 开头的编号
        return [c for c in cases if not c.case_id.startswith("YW_")]

    def load_flow_cases(self, module=None):
        """只加载业务流程测试用例（YW_ 开头）"""
        return self.load_cases(module=module, source="业务流程测试用例")

    def get_modules(self):
        """返回所有模块名称列表"""
        modules = []
        seen = set()
        for row in self._ws.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            mod = str(row[2]).strip() if row[2] else ""
            if mod and mod not in seen:
                seen.add(mod)
                modules.append(mod)
        return modules

    # ── 内部方法 ──

    def _parse_case(self, row):
        """将一行 Excel 数据解析为 UiCase 对象"""
        case_id = self._cell(row, "编号")
        source = self._cell(row, "来源")
        module = self._cell(row, "所属模块")
        title = self._cell(row, "用例标题")
        priority = self._cell(row, "优先级")

        page_path = self._cell(row, "页面路径")

        login_flag = self._cell(row, "是否需要登录")
        login_user = self._cell(row, "登录用户")
        login_pwd = self._cell(row, "登录密码")
        role = self._cell(row, "用户角色")

        # 解析业务字段：只保留非空、非排除列的字段；
        # "（空）" 为"显式空值"哨兵：保留 key、值为 ""，供测试区分"故意为空"与"字段缺失"
        fields = {}
        for header in self._headers:
            if header in _EXCLUDE_HEADERS:
                continue
            idx = self._header_idx[header]
            if idx < len(row) and row[idx] is not None:
                val = str(row[idx]).strip()
                if val == "（空）":
                    fields[header] = ""
                elif val and val not in ("", "None"):
                    fields[header] = val

        expected = ""
        if self._expected_idx < len(row) and row[self._expected_idx]:
            expected = str(row[self._expected_idx]).strip()

        return UiCase(
            case_id=case_id,
            source=source,
            module=module,
            title=title,
            priority=priority,
            login_required=(login_flag == "是"),
            login_user=login_user,
            login_password=login_pwd,
            role=role,
            page_path=page_path,
            fields=fields,
            expected=expected,
        )

    def _cell(self, row, header_name):
        """安全读取一行中指定列的值，返回空字符串兜底"""
        idx = self._header_idx.get(header_name)
        if idx is None or idx >= len(row):
            return ""
        val = row[idx]
        return str(val).strip() if val is not None else ""
