# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
分析スクリプト: クレンジング済みCSVを読み込み、分析結果を output/ に出力する
print文に記号類は使わない
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_medicine_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV_PATH = OUTPUT_DIR / "medicine_summary_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def analyze_alert_summary(df: pd.DataFrame) -> pd.DataFrame:
    """アラートレベル別件数・在庫金額サマリー"""
    summary = df.groupby("alert_level").agg(
        件数=("med_code", "count"),
        総在庫金額=("stock_value", "sum"),
        平均在庫金額=("stock_value", "mean"),
    ).round(0).reset_index()
    return summary


def analyze_ward_alert(df: pd.DataFrame) -> pd.DataFrame:
    """病棟別欠品・警告品目数"""
    alert_df = df[df["alert_level"].isin(["欠品", "警告"])].copy()
    ward_alert = alert_df.groupby(["ward", "alert_level"]).size().unstack(fill_value=0).reset_index()
    # 列を揃える
    for col in ["欠品", "警告"]:
        if col not in ward_alert.columns:
            ward_alert[col] = 0
    ward_alert["合計"] = ward_alert["欠品"] + ward_alert["警告"]
    return ward_alert


def analyze_category_value(df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ別在庫金額構成"""
    cat_val = df.groupby("category").agg(
        総在庫金額=("stock_value", "sum"),
        品目数=("med_code", "nunique"),
    ).sort_values("総在庫金額", ascending=False).reset_index()
    total = cat_val["総在庫金額"].sum()
    cat_val["構成比率(%)"] = (cat_val["総在庫金額"] / total * 100).round(1)
    return cat_val


def analyze_stockout_risk(df: pd.DataFrame) -> pd.DataFrame:
    """欠品リスク上位10品目（days_until_stockout 昇順）"""
    risk_df = df[df["days_until_stockout"].notna()].copy()
    risk_top10 = (
        risk_df.sort_values("days_until_stockout")
        .drop_duplicates("med_code")
        .head(10)[["med_code", "med_name", "category", "ward",
                   "stock_qty", "min_stock", "daily_usage",
                   "days_until_stockout", "alert_level"]]
    )
    return risk_top10


def build_medicine_summary(df: pd.DataFrame) -> pd.DataFrame:
    """薬品別サマリー"""
    summary = df.groupby(["med_code", "med_name", "category"]).agg(
        レコード数=("date", "count"),
        平均在庫数=("stock_qty", "mean"),
        最小在庫数=("stock_qty", "min"),
        最大在庫数=("stock_qty", "max"),
        欠品件数=("alert_level", lambda x: (x == "欠品").sum()),
        警告件数=("alert_level", lambda x: (x == "警告").sum()),
        総在庫金額=("stock_value", "sum"),
        平均days_until_stockout=("days_until_stockout", "mean"),
    ).round(1).reset_index()
    return summary


def build_report(
    alert_summary: pd.DataFrame,
    ward_alert: pd.DataFrame,
    cat_val: pd.DataFrame,
    risk_top10: pd.DataFrame,
    df: pd.DataFrame,
) -> str:
    total_meds = df["med_code"].nunique()
    total_records = len(df)
    shortage_count = (df["alert_level"] == "欠品").sum()
    warning_count = (df["alert_level"] == "警告").sum()
    total_value = df["stock_value"].sum()

    lines = []
    lines.append("# 薬品在庫管理 分析レポート")
    lines.append("")
    lines.append("## 概要")
    lines.append("")
    lines.append(f"- 分析対象レコード数: {total_records} 件")
    lines.append(f"- 管理薬品数: {total_meds} 品目")
    lines.append(f"- 欠品件数: {shortage_count} 件")
    lines.append(f"- 警告件数: {warning_count} 件")
    lines.append(f"- 総在庫金額: {total_value:,.0f} 円")
    lines.append("")

    lines.append("## アラートレベル別サマリー")
    lines.append("")
    lines.append(alert_summary.to_markdown(index=False))
    lines.append("")

    lines.append("## 病棟別 欠品・警告品目数")
    lines.append("")
    lines.append(ward_alert.to_markdown(index=False))
    lines.append("")

    lines.append("## カテゴリ別在庫金額構成")
    lines.append("")
    lines.append(cat_val.to_markdown(index=False))
    lines.append("")

    lines.append("## 欠品リスク上位10品目")
    lines.append("")
    lines.append(risk_top10.to_markdown(index=False))
    lines.append("")

    lines.append("## インサイト・改善示唆")
    lines.append("")

    # 自動インサイト生成
    top_ward = ward_alert.sort_values("合計", ascending=False).iloc[0] if len(ward_alert) > 0 else None
    top_cat = cat_val.iloc[0] if len(cat_val) > 0 else None
    riskiest = risk_top10.iloc[0] if len(risk_top10) > 0 else None

    if top_ward is not None:
        lines.append(f"1. **病棟別リスク**: {top_ward['ward']} が最多アラート "
                     f"（欠品 {int(top_ward.get('欠品', 0))} 件、警告 {int(top_ward.get('警告', 0))} 件）。"
                     f"発注頻度の見直しを推奨する。")
    if top_cat is not None:
        lines.append(f"2. **在庫金額集中**: {top_cat['category']} が在庫金額の "
                     f"{top_cat['構成比率(%)']:.1f}% を占める。"
                     f"ABC分析を適用してA品目の在庫管理精度を高めることを推奨する。")
    if riskiest is not None:
        days = riskiest["days_until_stockout"]
        lines.append(f"3. **最高リスク品目**: {riskiest['med_name']}（{riskiest['med_code']}）は "
                     f"あと {days:.1f} 日で欠品見込み。即時発注が必要。")

    shortage_rate = shortage_count / total_records * 100 if total_records > 0 else 0
    lines.append(f"4. **欠品率**: 全体の {shortage_rate:.1f}% が欠品状態。"
                 f"定期発注ルールの見直しにより欠品率 5% 未満を目標とする。")

    lines.append("")
    lines.append("## まとめ")
    lines.append("")
    lines.append(
        f"本分析では {total_meds} 品目、{total_records} 件の在庫データを対象とした。"
        f"欠品 {shortage_count} 件・警告 {warning_count} 件が検出され、"
        f"特に在庫金額上位カテゴリの管理強化と高リスク品目への迅速な発注対応が求められる。"
        f"病棟別データを活用した発注トリガー設定および自動アラートシステムの導入が効果的である。"
    )
    lines.append("")

    return "\n".join(lines)


def main():
    print("[INFO] 分析開始...")

    df = load_data()
    print(f"[INFO] データ読み込み: {len(df)} 件")

    alert_summary = analyze_alert_summary(df)
    ward_alert = analyze_ward_alert(df)
    cat_val = analyze_category_value(df)
    risk_top10 = analyze_stockout_risk(df)
    med_summary = build_medicine_summary(df)

    # レポート出力
    report_text = build_report(alert_summary, ward_alert, cat_val, risk_top10, df)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    print(f"[OK] レポート出力: {REPORT_PATH}")

    # 薬品別サマリーCSV出力
    med_summary.to_csv(SUMMARY_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] 薬品別サマリーCSV出力: {SUMMARY_CSV_PATH} ({len(med_summary)} 件)")


if __name__ == "__main__":
    main()
