# -*- coding: utf-8 -*-
"""
C-38: 予約キャンセル集計・傾向分析パイプライン
分析スクリプト
- 店舗別キャンセル率・ロス金額
- キャンセル理由別件数ランキング
- 曜日別予約・キャンセル件数
- コース別キャンセル率
"""

import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "cleaned_reservations_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig", dtype=str)
    df["guest_count"] = pd.to_numeric(df["guest_count"], errors="coerce").fillna(0).astype(int)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0).astype(int)
    df["is_cancel"] = pd.to_numeric(df["is_cancel"], errors="coerce").fillna(0).astype(int)
    df["loss_amount"] = pd.to_numeric(df["loss_amount"], errors="coerce").fillna(0).astype(int)
    df["reserv_date"] = pd.to_datetime(df["reserv_date"], format="%Y-%m-%d")
    return df


def analyze_store(df: pd.DataFrame) -> pd.DataFrame:
    """店舗別: 総予約数、キャンセル数、キャンセル率、ロス金額合計"""
    grp = df.groupby("store_name").agg(
        total_reserv=("reserv_no", "count"),
        cancel_count=("is_cancel", "sum"),
        loss_amount_total=("loss_amount", "sum"),
        revenue_total=("amount", "sum"),
    ).reset_index()
    grp["cancel_rate"] = (grp["cancel_count"] / grp["total_reserv"] * 100).round(2)
    return grp.sort_values("cancel_rate", ascending=False)


def analyze_cancel_reason(df: pd.DataFrame) -> pd.DataFrame:
    """キャンセル理由別件数ランキング"""
    cancel_df = df[df["is_cancel"] == 1].copy()
    reason_counts = cancel_df["cancel_reason"].value_counts().reset_index()
    reason_counts.columns = ["cancel_reason", "count"]
    reason_counts["ratio"] = (reason_counts["count"] / reason_counts["count"].sum() * 100).round(2)
    return reason_counts


def analyze_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """曜日別予約・キャンセル件数"""
    weekday_order = ["月", "火", "水", "木", "金", "土", "日"]
    grp = df.groupby("day_of_week").agg(
        total_reserv=("reserv_no", "count"),
        cancel_count=("is_cancel", "sum"),
    ).reset_index()
    grp["cancel_rate"] = (grp["cancel_count"] / grp["total_reserv"] * 100).round(2)
    # 曜日順にソート
    grp["day_order"] = grp["day_of_week"].map({d: i for i, d in enumerate(weekday_order)})
    grp = grp.sort_values("day_order").drop(columns=["day_order"])
    return grp


def analyze_course(df: pd.DataFrame) -> pd.DataFrame:
    """コース別キャンセル率"""
    grp = df.groupby("course").agg(
        total_reserv=("reserv_no", "count"),
        cancel_count=("is_cancel", "sum"),
        loss_amount_total=("loss_amount", "sum"),
    ).reset_index()
    grp["cancel_rate"] = (grp["cancel_count"] / grp["total_reserv"] * 100).round(2)
    return grp.sort_values("cancel_rate", ascending=False)


def generate_insights(df, store_df, reason_df, weekday_df, course_df) -> str:
    """分析インサイトを文字列で返す"""
    total = len(df)
    cancel_total = df["is_cancel"].sum()
    cancel_rate_overall = cancel_total / total * 100 if total > 0 else 0
    loss_total = df["loss_amount"].sum()

    top_store = store_df.iloc[0]["store_name"] if len(store_df) > 0 else "-"
    top_store_rate = store_df.iloc[0]["cancel_rate"] if len(store_df) > 0 else 0

    top_reason = reason_df.iloc[0]["cancel_reason"] if len(reason_df) > 0 else "-"
    top_reason_count = reason_df.iloc[0]["count"] if len(reason_df) > 0 else 0

    high_cancel_day = weekday_df.sort_values("cancel_count", ascending=False).iloc[0]
    top_course = course_df.iloc[0]["course"] if len(course_df) > 0 else "-"
    top_course_rate = course_df.iloc[0]["cancel_rate"] if len(course_df) > 0 else 0

    lines = [
        "## インサイトサマリー",
        "",
        f"- 全体のキャンセル率は {cancel_rate_overall:.1f}% (総予約数: {total}件, キャンセル数: {cancel_total}件)",
        f"- 機会損失金額の合計: {loss_total:,}円",
        f"- 最もキャンセル率が高い店舗: {top_store} ({top_store_rate:.1f}%)",
        f"- 最多キャンセル理由: {top_reason} ({top_reason_count}件)",
        f"- キャンセルが最多の曜日: {high_cancel_day['day_of_week']}曜日 ({int(high_cancel_day['cancel_count'])}件)",
        f"- キャンセル率が最も高いコース: {top_course} ({top_course_rate:.1f}%)",
        "",
        "## 改善示唆",
        "",
        "1. **事前リマインド強化**: キャンセル理由「忘れ」が多い場合、予約前日のSMS/メールリマインドが有効",
        "2. **天候対応ポリシー**: 「天候」によるキャンセルが多い場合、悪天候時の特別対応(振替・クーポン)を検討",
        "3. **個室コース対策**: 高単価コースのキャンセルは機会損失が大きいため、キャンセル保証金制度の導入を推奨",
        "4. **曜日別人員配置**: キャンセルが多い曜日はキャンセル待ち対応スタッフを増員し、席の空き対応を迅速化",
        "5. **店舗別施策**: キャンセル率が最高の店舗には重点的なフォローアップコール体制を整備",
    ]
    return "\n".join(lines)


def write_report(df, store_df, reason_df, weekday_df, course_df):
    """analysis_report.md を出力"""
    total = len(df)
    cancel_total = int(df["is_cancel"].sum())
    loss_total = int(df["loss_amount"].sum())
    cancel_rate_overall = cancel_total / total * 100 if total > 0 else 0

    lines = [
        "# C-38 予約キャンセル集計・傾向分析レポート",
        "",
        "## 1. 全体サマリー",
        "",
        f"| 指標 | 値 |",
        f"|------|-----|",
        f"| 総予約件数 | {total:,} |",
        f"| キャンセル件数 | {cancel_total:,} |",
        f"| キャンセル率 | {cancel_rate_overall:.1f}% |",
        f"| 機会損失合計 | {loss_total:,}円 |",
        "",
        "## 2. 店舗別キャンセル分析",
        "",
        "| 店舗名 | 総予約 | キャンセル | キャンセル率 | 損失金額 |",
        "|--------|--------|-----------|------------|---------|",
    ]
    for _, row in store_df.iterrows():
        lines.append(
            f"| {row['store_name']} | {int(row['total_reserv'])} | "
            f"{int(row['cancel_count'])} | {row['cancel_rate']:.1f}% | "
            f"{int(row['loss_amount_total']):,}円 |"
        )

    lines += [
        "",
        "## 3. キャンセル理由別ランキング",
        "",
        "| 順位 | 理由 | 件数 | 割合 |",
        "|------|------|------|------|",
    ]
    for i, (_, row) in enumerate(reason_df.iterrows(), 1):
        lines.append(f"| {i} | {row['cancel_reason']} | {int(row['count'])} | {row['ratio']:.1f}% |")

    lines += [
        "",
        "## 4. 曜日別予約・キャンセル件数",
        "",
        "| 曜日 | 総予約 | キャンセル | キャンセル率 |",
        "|------|--------|-----------|------------|",
    ]
    for _, row in weekday_df.iterrows():
        lines.append(
            f"| {row['day_of_week']}曜日 | {int(row['total_reserv'])} | "
            f"{int(row['cancel_count'])} | {row['cancel_rate']:.1f}% |"
        )

    lines += [
        "",
        "## 5. コース別キャンセル率",
        "",
        "| コース | 総予約 | キャンセル | キャンセル率 | 損失金額 |",
        "|--------|--------|-----------|------------|---------|",
    ]
    for _, row in course_df.iterrows():
        lines.append(
            f"| {row['course']} | {int(row['total_reserv'])} | "
            f"{int(row['cancel_count'])} | {row['cancel_rate']:.1f}% | "
            f"{int(row['loss_amount_total']):,}円 |"
        )

    lines += ["", generate_insights(df, store_df, reason_df, weekday_df, course_df)]

    report_path = OUTPUT_DIR / "analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Report: {report_path}")


def write_store_summary(store_df: pd.DataFrame):
    """store_summary_202401.csv を出力"""
    out_path = OUTPUT_DIR / "store_summary_202401.csv"
    store_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Store summary: {out_path}")


def main():
    df = load_data()
    print(f"[OK] Loaded {len(df)} rows")

    store_df = analyze_store(df)
    reason_df = analyze_cancel_reason(df)
    weekday_df = analyze_weekday(df)
    course_df = analyze_course(df)

    write_report(df, store_df, reason_df, weekday_df, course_df)
    write_store_summary(store_df)

    # JSON形式でも保存（app.py から利用）
    summary = {
        "total_reserv": int(len(df)),
        "cancel_count": int(df["is_cancel"].sum()),
        "cancel_rate": round(df["is_cancel"].mean() * 100, 2),
        "loss_amount_total": int(df["loss_amount"].sum()),
    }
    with open(OUTPUT_DIR / "result_analysis.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON summary: {OUTPUT_DIR / 'result_analysis.json'}")

    return df, store_df, reason_df, weekday_df, course_df


if __name__ == "__main__":
    main()
