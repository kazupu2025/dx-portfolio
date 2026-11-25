# validate_report.py — 分析レポートのバリデーション（C-36 顧客満足度）
# encoding: utf-8

from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
SERVICE_SUMMARY_FILE = OUTPUT_DIR / "service_summary_202401.csv"


def _check(label: str, condition: bool, detail: str = "") -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return condition


def run() -> bool:
    results = []

    # 1. レポートファイルの存在確認
    report_exists = REPORT_FILE.exists()
    results.append(_check("1. analysis_report.md が存在する", report_exists, str(REPORT_FILE)))

    # 2. サービスサマリー CSV の存在確認
    csv_exists = SERVICE_SUMMARY_FILE.exists()
    results.append(_check("2. service_summary_202401.csv が存在する", csv_exists, str(SERVICE_SUMMARY_FILE)))

    if report_exists:
        content = REPORT_FILE.read_text(encoding="utf-8")

        # 3. タイトル行が含まれる
        has_title = "顧客満足度" in content
        results.append(_check("3. レポートにタイトル行が含まれる", has_title))

        # 4. NPS セクションが含まれる
        has_nps = "NPS" in content
        results.append(_check("4. NPS セクションが含まれる", has_nps))

        # 5. サービス区分別セクションが含まれる
        has_service = "サービス区分" in content
        results.append(_check("5. サービス区分別セクションが含まれる", has_service))

        # 6. 担当者別セクションが含まれる
        has_agent = "担当者" in content
        results.append(_check("6. 担当者別セクションが含まれる", has_agent))

        # 7. 月別トレンドセクションが含まれる
        has_trend = "月別" in content or "トレンド" in content
        results.append(_check("7. 月別トレンドセクションが含まれる", has_trend))

        # 8. インサイト・改善示唆セクションが含まれる
        has_insights = "インサイト" in content or "改善" in content
        results.append(_check("8. インサイト・改善示唆セクションが含まれる", has_insights))

        # 9. Markdown テーブルが存在する（最低1つ）
        has_table = "|" in content
        results.append(_check("9. Markdown テーブルが存在する", has_table))

        # 10. レポートが空でない（500文字以上）
        has_content = len(content) >= 500
        results.append(_check("10. レポートが十分な長さ(>=500字)", has_content,
                              f"length={len(content)}"))

    if csv_exists:
        import pandas as pd
        svc_df = pd.read_csv(SERVICE_SUMMARY_FILE, encoding="utf-8-sig")

        # 11. サービスサマリーに必要列が存在する
        required_cols = ["service_type", "response_count", "avg_csat", "nps_score"]
        missing = [c for c in required_cols if c not in svc_df.columns]
        results.append(_check("11. サービスサマリーに必要列が存在する",
                              len(missing) == 0,
                              f"missing={missing}" if missing else "all present"))

        # 12. サービスサマリーに5行ある（5サービス区分）
        results.append(_check("12. サービスサマリーが5行（5サービス区分）",
                              len(svc_df) == 5, f"actual={len(svc_df)}"))

    # サマリー
    passed = sum(results)
    total = len(results)
    print(f"\nResult: {passed}/{total} report checks passed")
    return all(results)


if __name__ == "__main__":
    ok = run()
    exit(0 if ok else 1)
