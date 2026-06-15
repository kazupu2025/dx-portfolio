"""
B-09 分析レポートバリデーション (7チェック)
Usage: cd 02_manufacturing/02_equipment_log && python output/validate_report.py
"""
import sys
import re
from pathlib import Path

OUT = Path(__file__).parent


def run():
    results = []

    report_path = OUT / "analysis_report.md"
    anomaly_path = OUT / "anomaly_sensor_202401.csv"

    # 1. report_exists
    ok = report_path.exists()
    results.append(("1", "report_exists", ok, "" if ok else f"{report_path} が存在しない"))

    # 2. anomaly_csv_exists
    ok = anomaly_path.exists()
    results.append(("2", "anomaly_csv_exists", ok, "" if ok else f"{anomaly_path} が存在しない"))

    content = ""
    if report_path.exists():
        with open(report_path, encoding="utf-8") as f:
            content = f.read()

    # 3. all_sections
    sections = ["設備別", "予兆", "センサー", "時系列", "インサイト"]
    missing = [s for s in sections if s not in content]
    ok = len(missing) == 0
    results.append(("3", "all_sections", ok, "" if ok else f"欠損セクション: {missing}"))

    # 4. all_equipment_in_report
    eqs = ["E-001", "E-002", "E-003", "E-004", "E-005"]
    missing_eq = [e for e in eqs if e not in content]
    ok = len(missing_eq) == 0
    results.append(("4", "all_equipment_in_report", ok, "" if ok else f"欠損設備: {missing_eq}"))

    # 5. alert_keywords
    ok = any(kw in content for kw in ["CRITICAL", "WARNING", "アラート"])
    results.append(("5", "alert_keywords", ok, "" if ok else "アラートキーワードなし"))

    # 6. numeric_present
    ok = bool(re.search(r"\d+\.\d+|\d{3,}", content))
    results.append(("6", "numeric_present", ok, "" if ok else "数値が見つからない"))

    # 7. maintenance_insight
    ok = any(kw in content for kw in ["メンテナンス", "点検", "整備"])
    results.append(("7", "maintenance_insight", ok, "" if ok else "メンテナンス関連キーワードなし"))

    passed = sum(1 for _, _, ok, _ in results if ok)
    total  = len(results)
    print(f"\n=== レポートバリデーション: {passed}/{total} PASS ===")
    for no, name, ok, msg in results:
        status = "PASS" if ok else "FAIL"
        detail = f" ({msg})" if msg else ""
        print(f"  [{status}] {no}. {name}{detail}")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    run()
