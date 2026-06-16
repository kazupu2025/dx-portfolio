"""
validate_report.py
analysis_report.md と shift_summary_202401.csv の品質を7項目チェックする。
"""

import os
import sys
import re
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
SUMMARY_FILE = os.path.join(BASE_DIR, "output", "shift_summary_202401.csv")
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_shift_202401.csv")


def run_checks():
    results = []

    def chk(name: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        msg = f"[{status}] {name}"
        if detail:
            msg += f"  ({detail})"
        print(msg)
        results.append((name, passed))

    # ── 1. analysis_report.md の存在 ────────────────────────────────
    chk("analysis_report.md が存在する", os.path.isfile(REPORT_FILE))

    # ── 2. shift_summary_202401.csv の存在 ──────────────────────────
    chk("shift_summary_202401.csv が存在する", os.path.isfile(SUMMARY_FILE))

    # ── レポート内容チェック ────────────────────────────────────────
    report_text = ""
    if os.path.isfile(REPORT_FILE):
        with open(REPORT_FILE, encoding="utf-8") as f:
            report_text = f.read()

    # ── 3. レポートに「夜勤」が含まれる ────────────────────────────
    chk("レポートに「夜勤」が含まれる", "夜勤" in report_text)

    # ── 4. レポートに「役職」または「スタッフ」が含まれる ──────────
    chk(
        "レポートに「役職」または「スタッフ」が含まれる",
        "役職" in report_text or "スタッフ" in report_text,
    )

    # ── 5. レポートにインサイト・提案が含まれる ─────────────────────
    insight_keywords = ["提案", "推奨", "インサイト", "改善", "リスク"]
    has_insight = any(kw in report_text for kw in insight_keywords)
    chk("レポートにインサイト・提案が含まれる", has_insight, str(insight_keywords))

    # ── 6. レポートに数値が含まれる ────────────────────────────────
    has_numbers = bool(re.search(r"\d+", report_text))
    chk("レポートに数値が含まれる", has_numbers)

    # ── 7. shift_summary_202401.csv の行数（スタッフ数以上） ────────
    if os.path.isfile(SUMMARY_FILE) and os.path.isfile(CLEANED_FILE):
        summary = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
        cleaned = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
        n_staff = cleaned["staff_id"].nunique()
        chk(
            f"shift_summary の行数がスタッフ数（{n_staff}名）以上",
            len(summary) >= n_staff,
            f"サマリー: {len(summary)}行",
        )
    elif os.path.isfile(SUMMARY_FILE):
        summary = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
        chk("shift_summary の行数が1以上", len(summary) >= 1, f"{len(summary)}行")

    # ── 8. shift_summary に必須列が存在する ─────────────────────────
    if os.path.isfile(SUMMARY_FILE):
        summary = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
        required_cols = ["staff_id", "name", "role", "total_days", "night_count", "off_count", "night_ratio"]
        missing = [c for c in required_cols if c not in summary.columns]
        chk(
            "shift_summary に必須列が存在する",
            len(missing) == 0,
            f"欠けている列: {missing}" if missing else "全列OK",
        )

    return results


def main():
    print("=" * 50)
    print("validate_report.py - 分析出力品質チェック")
    print("=" * 50)

    results = run_checks()

    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    total = len(results)

    print()
    print(f"結果: {passed}/{total} PASS  /  {failed} FAIL")

    if failed > 0:
        print("\n[NG] FAILがあります。analyze.py を修正して再実行してください。")
        sys.exit(1)
    else:
        print("\n[OK] 全チェック PASS")


if __name__ == "__main__":
    main()
