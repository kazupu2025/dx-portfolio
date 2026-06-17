"""
C-39: 入居者対応履歴・クレーム集計パイプライン
分析スクリプト
- 物件別クレーム件数・解決率・平均対応日数
- クレーム区分別発生件数ランキング
- 緊急対応が必要な案件リスト
- 月別トレンド・工数合計
出力: output/analysis_report.md, output/property_summary_202401.csv
"""

import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
CLEANED_CSV = OUTPUT_DIR / "cleaned_claims_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
    df["receipt_date"] = pd.to_datetime(df["receipt_date"], format="%Y-%m-%d", errors="coerce")
    df["response_days"] = pd.to_numeric(df["response_days"], errors="coerce")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    df["cost_estimate"] = pd.to_numeric(df["cost_estimate"], errors="coerce")
    df["is_resolved"] = pd.to_numeric(df["is_resolved"], errors="coerce")
    return df


def analyze_by_property(df: pd.DataFrame) -> pd.DataFrame:
    """物件別クレーム件数・解決率・平均対応日数"""
    grp = df.groupby("property_name").agg(
        claim_count=("case_no", "count"),
        resolved_count=("is_resolved", "sum"),
        avg_response_days=("response_days", "mean"),
        total_work_hours=("work_hours", "sum"),
        total_cost_estimate=("cost_estimate", "sum"),
    ).reset_index()
    grp["resolution_rate_pct"] = (grp["resolved_count"] / grp["claim_count"] * 100).round(1)
    grp["avg_response_days"] = grp["avg_response_days"].round(1)
    grp["total_work_hours"] = grp["total_work_hours"].round(1)
    grp["total_cost_estimate"] = grp["total_cost_estimate"].astype(int)
    return grp.sort_values("claim_count", ascending=False)


def analyze_by_claim_type(df: pd.DataFrame) -> pd.DataFrame:
    """クレーム区分別発生件数ランキング"""
    grp = df.groupby("claim_type").agg(
        count=("case_no", "count"),
        avg_days=("response_days", "mean"),
        unresolved=("status", lambda x: (x == "未対応").sum()),
    ).reset_index()
    grp["avg_days"] = grp["avg_days"].round(1)
    return grp.sort_values("count", ascending=False)


def get_urgent_cases(df: pd.DataFrame) -> pd.DataFrame:
    """緊急対応が必要な案件リスト"""
    urgent = df[df["urgency"] == "緊急"].copy()
    urgent = urgent.sort_values("response_days", ascending=False)
    cols = ["case_no", "property_name", "room_no", "claim_type", "status", "response_days", "receipt_date"]
    return urgent[cols].head(20)


def analyze_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """月別トレンド・工数合計"""
    df["year_month"] = df["receipt_date"].dt.to_period("M").astype(str)
    grp = df.groupby("year_month").agg(
        claim_count=("case_no", "count"),
        resolved_count=("is_resolved", "sum"),
        total_work_hours=("work_hours", "sum"),
        total_cost_estimate=("cost_estimate", "sum"),
    ).reset_index()
    grp["resolution_rate_pct"] = (grp["resolved_count"] / grp["claim_count"] * 100).round(1)
    grp["total_work_hours"] = grp["total_work_hours"].round(1)
    grp["total_cost_estimate"] = grp["total_cost_estimate"].astype(int)
    return grp.sort_values("year_month")


def format_property_table(df: pd.DataFrame) -> str:
    lines = ["| 物件名 | 件数 | 解決率(%) | 平均対応日数 | 工数合計(h) | 概算コスト(円) |",
             "|--------|------|-----------|------------|------------|--------------|"]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['property_name']} | {row['claim_count']} | "
            f"{row['resolution_rate_pct']} | {row['avg_response_days']} | "
            f"{row['total_work_hours']} | {row['total_cost_estimate']:,} |"
        )
    return "\n".join(lines)


def format_claim_type_table(df: pd.DataFrame) -> str:
    lines = ["| クレーム区分 | 件数 | 平均対応日数 | 未対応件数 |",
             "|------------|------|------------|---------|"]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['claim_type']} | {row['count']} | {row['avg_days']} | {row['unresolved']} |"
        )
    return "\n".join(lines)


def format_urgent_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "現在、緊急対応案件はありません。"
    lines = ["| 案件番号 | 物件名 | 部屋番号 | クレーム区分 | 対応状況 | 対応日数 |",
             "|---------|--------|---------|------------|---------|---------|"]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['case_no']} | {row['property_name']} | {row['room_no']} | "
            f"{row['claim_type']} | {row['status']} | {row['response_days']:.0f} |"
        )
    return "\n".join(lines)


def format_monthly_table(df: pd.DataFrame) -> str:
    lines = ["| 年月 | 件数 | 解決率(%) | 工数合計(h) | 概算コスト(円) |",
             "|------|------|-----------|------------|--------------|"]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['year_month']} | {row['claim_count']} | "
            f"{row['resolution_rate_pct']} | {row['total_work_hours']} | "
            f"{row['total_cost_estimate']:,} |"
        )
    return "\n".join(lines)


def generate_insights(df: pd.DataFrame, prop_df: pd.DataFrame, ct_df: pd.DataFrame) -> str:
    total = len(df)
    resolved = (df["status"] == "解決済").sum()
    unresolved = (df["status"] == "未対応").sum()
    urgent = (df["urgency"] == "緊急").sum()
    avg_days = df["response_days"].mean()
    top_prop = prop_df.iloc[0]["property_name"]
    top_ct = ct_df.iloc[0]["claim_type"]
    total_cost = int(df["cost_estimate"].sum())

    insights = f"""## 分析インサイト・改善示唆

### 全体概要
- 総クレーム件数: {total} 件
- 解決済: {resolved} 件 ({resolved/total*100:.1f}%)
- 未対応: {unresolved} 件 ({unresolved/total*100:.1f}%)
- 緊急案件: {urgent} 件
- 平均対応日数: {avg_days:.1f} 日
- 概算コスト合計: {total_cost:,} 円

### 主要課題
1. **クレーム集中物件**: {top_prop} が最多件数。優先的な設備点検・入居者コミュニケーション強化を推奨。
2. **頻発クレーム区分**: {top_ct} が最多。原因の根本分析と予防保全計画の策定が有効。
3. **緊急案件管理**: 緊急と分類された {urgent} 件（水漏れ・設備故障の未解決）は最優先で対処が必要。

### 改善示唆
- 対応日数が長い案件（30日超）は escalation ルールの設定を検討する
- 未対応案件が積み上がっている物件には専任担当者の配置を推奨する
- 工数が多いクレーム区分については外部業者との長期契約で単価削減が見込める
- 月次でクレームトレンドをモニタリングし、季節変動に備えた事前対応を実施する
"""
    return insights


def analyze():
    if not CLEANED_CSV.exists():
        raise FileNotFoundError(f"Cleaned CSV not found: {CLEANED_CSV}. Run cleanse.py first.")

    df = load_data()
    print(f"[OK] Data loaded: {len(df)} rows")

    prop_df = analyze_by_property(df)
    ct_df = analyze_by_claim_type(df)
    urgent_df = get_urgent_cases(df)
    monthly_df = analyze_monthly_trend(df)

    # property_summary_202401.csv の出力
    prop_df.to_csv(OUTPUT_DIR / "property_summary_202401.csv", index=False, encoding="utf-8-sig")
    print("[OK] property_summary_202401.csv saved")

    # analysis_report.md の生成
    insights = generate_insights(df, prop_df, ct_df)
    report = f"""# 入居者クレーム分析レポート

生成日時: 2024-03-31
対象データ: 2024年1月-3月

---

## 1. 物件別クレーム状況

{format_property_table(prop_df)}

---

## 2. クレーム区分別発生件数ランキング

{format_claim_type_table(ct_df)}

---

## 3. 緊急対応が必要な案件（水漏れ・設備故障の未解決）

{format_urgent_table(urgent_df)}

---

## 4. 月別トレンド

{format_monthly_table(monthly_df)}

---

{insights}
"""

    report_path = OUTPUT_DIR / "analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[OK] analysis_report.md saved: {report_path}")

    # JSON サマリー（app.py 用）
    summary = {
        "total_claims": int(len(df)),
        "resolved_count": int((df["status"] == "解決済").sum()),
        "unresolved_count": int((df["status"] == "未対応").sum()),
        "in_progress_count": int((df["status"] == "対応中").sum()),
        "urgent_count": int((df["urgency"] == "緊急").sum()),
        "avg_response_days": round(float(df["response_days"].mean()), 1),
        "total_cost_estimate": int(df["cost_estimate"].sum()),
    }
    with open(OUTPUT_DIR / "result_analysis.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("[OK] result_analysis.json saved")

    print(f"\n[DONE] Analysis complete")
    return df, prop_df, ct_df, urgent_df, monthly_df


if __name__ == "__main__":
    analyze()
