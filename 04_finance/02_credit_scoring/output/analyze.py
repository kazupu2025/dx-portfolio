"""
B-11: 与信スコアリング 分析レポート生成
クレンジング済みデータから多角的な与信分析レポートを出力する。
出力: output/credit_report_202401.txt
"""
import sys
from pathlib import Path
import pandas as pd
import yaml

BASE = Path(__file__).parent.parent
OUT = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

CSV_PATH = OUT / "cleaned_credit_202401.csv"
REPORT_PATH = OUT / "credit_report_202401.txt"


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} が見つかりません。cleanse.py を先に実行してください。")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    lines = []

    def section(title: str):
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"  {title}")
        lines.append("=" * 60)

    lines.append("B-11 与信スコアリング 分析レポート（2024年1月）")
    lines.append(f"総申込件数: {len(df):,} 件")
    lines.append(f"平均スコア: {df['credit_score'].mean():.1f} 点")
    lines.append(f"スコア標準偏差: {df['credit_score'].std():.1f}")

    # =====================================================
    # 1. リスク分類別サマリー
    # =====================================================
    section("1. リスク分類別サマリー")
    risk_order = ["低リスク", "中リスク", "高リスク"]
    risk_df = (
        df.groupby("risk_category")
        .agg(
            申込件数=("application_id", "count"),
            平均スコア=("credit_score", "mean"),
            平均年収=("annual_income", "mean"),
        )
        .reindex([r for r in risk_order if r in df["risk_category"].unique()])
    )
    total = len(df)
    for cat, row in risk_df.iterrows():
        pct = row["申込件数"] / total * 100
        lines.append(
            f"  {cat}: {int(row['申込件数'])}件 ({pct:.1f}%) "
            f"| 平均スコア {row['平均スコア']:.1f}点 "
            f"| 平均年収 {row['平均年収']:.0f}万円"
        )

    # =====================================================
    # 2. 職業別与信スコア分析
    # =====================================================
    section("2. 職業別与信スコア分析")
    high_risk_threshold = config["high_risk_threshold"]
    occ_df = (
        df.groupby("occupation")
        .agg(
            件数=("application_id", "count"),
            平均スコア=("credit_score", "mean"),
            高リスク率=("risk_category", lambda x: (x == "高リスク").mean() * 100),
            平均年収=("annual_income", "mean"),
        )
        .sort_values("平均スコア", ascending=False)
    )
    for occ, row in occ_df.iterrows():
        lines.append(
            f"  {occ}: {int(row['件数'])}件 "
            f"| 平均スコア {row['平均スコア']:.1f}点 "
            f"| 高リスク率 {row['高リスク率']:.1f}% "
            f"| 平均年収 {row['平均年収']:.0f}万円"
        )

    # =====================================================
    # 3. 申込用途別分析
    # =====================================================
    section("3. 申込用途別分析")
    purpose_df = (
        df.groupby("loan_purpose")
        .agg(
            件数=("application_id", "count"),
            平均スコア=("credit_score", "mean"),
            高リスク率=("risk_category", lambda x: (x == "高リスク").mean() * 100),
        )
        .sort_values("件数", ascending=False)
    )
    for purpose, row in purpose_df.iterrows():
        lines.append(
            f"  {purpose}: {int(row['件数'])}件 "
            f"| 平均スコア {row['平均スコア']:.1f}点 "
            f"| 高リスク率 {row['高リスク率']:.1f}%"
        )

    # =====================================================
    # 4. 負債比率アラート
    # =====================================================
    section("4. 負債比率アラート（高リスク・要注意）")
    alert_ratio = config["debt_income_alert_ratio"]
    alert_df = df[df["debt_income_ratio"] > alert_ratio]
    n_alert = len(alert_df)
    pct_alert = n_alert / total * 100
    lines.append(f"  負債/年収比率 > {alert_ratio:.0%} の申込者: {n_alert}件 ({pct_alert:.1f}%)")
    lines.append(f"  このうち高リスク: {(alert_df['risk_category'] == '高リスク').sum()}件")
    lines.append(f"  平均スコア（要注意群）: {alert_df['credit_score'].mean():.1f}点")
    lines.append(f"  ※ 負債比率が高い申込者は追加審査を推奨")

    # =====================================================
    # 5. スコア分布サマリー
    # =====================================================
    section("5. スコア分布サマリー")
    bands = [(0, 39, "高リスクゾーン"), (40, 59, "中リスクゾーン"), (60, 79, "低リスクゾーン"), (80, 100, "優良ゾーン")]
    for lo, hi, label in bands:
        n_band = df["credit_score"].between(lo, hi).sum()
        pct_band = n_band / total * 100
        lines.append(f"  スコア {lo:3d}〜{hi:3d}点 ({label}): {n_band}件 ({pct_band:.1f}%)")

    # =====================================================
    # 6. ビジネスインサイト
    # =====================================================
    section("6. ビジネスインサイト・推奨アクション")

    # 高リスク率が最も高い職業
    highest_risk_occ = occ_df["高リスク率"].idxmax()
    highest_risk_rate = occ_df.loc[highest_risk_occ, "高リスク率"]

    # 高リスク率が最も高い用途
    highest_risk_purpose = purpose_df["高リスク率"].idxmax()
    highest_risk_purpose_rate = purpose_df.loc[highest_risk_purpose, "高リスク率"]

    overall_high_risk_rate = (df["risk_category"] == "高リスク").mean() * 100
    low_risk_count = (df["risk_category"] == "低リスク").sum()

    lines.append(f"  【全体高リスク率】 {overall_high_risk_rate:.1f}%")
    lines.append(f"  【承認推奨件数（低リスク）】 {low_risk_count}件 ({low_risk_count/total*100:.1f}%)")
    lines.append("")
    lines.append(f"  ■ 高リスク率が高い職業: {highest_risk_occ} ({highest_risk_rate:.1f}%)")
    lines.append(f"    → 年収・勤続年数の追加確認が有効")
    lines.append(f"  ■ 高リスク率が高い申込用途: {highest_risk_purpose} ({highest_risk_purpose_rate:.1f}%)")
    lines.append(f"    → 返済計画書の提出を必須化を検討")
    lines.append(f"  ■ 負債比率アラート（>{alert_ratio:.0%}）: {n_alert}件 ({pct_alert:.1f}%)")
    lines.append(f"    → 既存債務の詳細確認と返済能力審査を強化")
    lines.append("")
    lines.append(f"  ■ スコア 60点以上（低リスク）の申込者 {low_risk_count}件は優先承認を推奨")
    lines.append(f"  ■ スコア 40点未満（高リスク）の申込者は個別審査フローへ移行を推奨")

    report_text = "\n".join(lines)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    print(report_text)
    print(f"\n分析レポート出力完了: {REPORT_PATH}")


if __name__ == "__main__":
    main()
