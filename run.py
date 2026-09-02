"""一键运行自动化测试 + 生成 Allure 报告

用法:
    python run.py                # 运行 UI 自动化
    python run.py api            # 运行接口自动化
    python run.py all            # 运行全部
    python run.py clean          # 清理报告后运行 UI 自动化
    python run.py noreport       # 仅运行测试，不生成报告
"""
import os
import sys
import shutil
import subprocess
import pytest

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(PROJECT_ROOT, "report")


def clean():
    """清理旧报告"""
    for d in ["allure-report-ui", "allure-report-api",
              "allure-results-ui", "allure-results-api"]:
        p = os.path.join(REPORT_DIR, d)
        if os.path.exists(p):
            shutil.rmtree(p)
            print(f"  已清理: {p}")


def generate_report(results_dir, report_dir):
    """生成 Allure 报告"""
    if not os.path.exists(results_dir):
        print(f"[跳过报告] 结果目录不存在: {results_dir}")
        return False
    try:
        subprocess.run(
            ["allure", "generate", results_dir, "-o", report_dir, "--clean"],
            check=True, capture_output=True, text=True, shell=True,
        )
        print(f"[报告] 已生成: {report_dir}")
        return True
    except FileNotFoundError:
        print("[跳过报告] 未安装 allure 命令行工具")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[报告生成失败] {e.stderr}")
        return False


if __name__ == "__main__":
    args = sys.argv[1:]

    # clean: 先清理报告再跑
    if "clean" in args:
        clean()
        args.remove("clean")

    # 是否生成报告
    no_report = "noreport" in args
    if no_report:
        args.remove("noreport")

    # 确定运行模式
    mode = args[0] if args else "ui"

    if mode == "api":
        # ── 接口自动化 ──
        pytest.main([
            "-v",
            "--tb=short",
            f"--alluredir={REPORT_DIR}/allure-results-api",
            "--clean-alluredir",
            os.path.join(PROJECT_ROOT, "api_case"),
        ])
        if not no_report:
            generate_report(
                f"{REPORT_DIR}/allure-results-api",
                f"{REPORT_DIR}/allure-report-api",
            )

    elif mode == "all":
        # ── UI + 接口全部 ──
        pytest.main([
            "-v", "--tb=short",
            f"--alluredir={REPORT_DIR}/allure-results-ui",
            "--clean-alluredir",
            os.path.join(PROJECT_ROOT, "case"),
        ])
        pytest.main([
            "-v", "--tb=short",
            f"--alluredir={REPORT_DIR}/allure-results-api",
            "--clean-alluredir",
            os.path.join(PROJECT_ROOT, "api_case"),
        ])
        if not no_report:
            generate_report(
                f"{REPORT_DIR}/allure-results-ui",
                f"{REPORT_DIR}/allure-report-ui",
            )
            generate_report(
                f"{REPORT_DIR}/allure-results-api",
                f"{REPORT_DIR}/allure-report-api",
            )

    else:
        # ── UI 自动化（默认） ──
        pytest.main([
            "-v",
            "--tb=short",
            f"--alluredir={REPORT_DIR}/allure-results-ui",
            "--clean-alluredir",
            os.path.join(PROJECT_ROOT, "case"),
        ])
        if not no_report:
            generate_report(
                f"{REPORT_DIR}/allure-results-ui",
                f"{REPORT_DIR}/allure-report-ui",
            )
