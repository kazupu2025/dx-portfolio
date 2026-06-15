"""
B-14 分析レポート生成
入力: cleaned_rental_202401.csv
出力: analysis_report.md
"""
import pandas as pd
import yaml
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT = Path(__file__).parent
CSV = OUT / "cleaned_rental_202401.csv"
REPORT = OUT / "analysis_report.md"

def load_cfg():
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    cfg = load_cfg()
    df = pd.read_csv(CSV, encoding="utf-8-sig")

    # numeric coerce
    for col in ["rent", "management_fee", "management_cost", "repair_cost", "monthly_revenue", "total_cost", "net_income"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["is_vacant"] = pd.to_numeric(df["is_vacant"], errors="coerce").fillna(0)

    # 1. エリア別空室率サマリー
    area_grp = df.groupby("area").agg(
        total=("property_id", "count"),
        vacant=("is_vacant", "sum"),
        avg_rent=("rent", "mean"),
        total_revenue=("monthly_revenue", "sum"),
    ).reset_index()
    area_grp["vacancy_rate"] = area_grp["vacant"] / area_grp["total"]
    area_grp["vacancy_rate_pct"] = (area_grp["vacancy_rate"] * 100).round(1)
    area_grp["avg_rent"] = area_grp["avg_rent"].round(0).astype(int)
    area_grp["total_revenue"] = area_grp["total_revenue"].astype(int)

    # 2. 物件タイプ別収益分析
    type_grp = df.groupby("property_type").agg(
        total=("property_id", "count"),
        vacant=("is_vacant", "sum"),
        avg_rent=("rent", "mean"),
        avg_net_income=("net_income", "mean"),
    ).reset_index()
    type_grp["vacancy_rate_pct"] = (type_grp["vacant"] / type_grp["total"] * 100).round(1)
    type_grp["avg_rent"] = type_grp["avg_rent"].round(0).astype(int)
    type_grp["avg_net_income"] = type_grp["avg_net_income"].round(0).astype(int)

    # 3. 修繕費アラート物件
    alert_threshold = cfg.get("high_repair_threshold", 100000)
    alert_df = df[df["repair_cost"] > alert_threshold][
        ["property_id", "property_name", "area", "property_type", "repair_cost", "occupancy_status"]
    ].sort_values("repair_cost", ascending=False)

    # 4. 全体KPI
    total_props = len(df)
    overall_vacancy_rate = df["is_vacant"].mean()
    total_monthly_revenue = df["monthly_revenue"].sum()
    total_monthly_cost = df["total_cost"].sum()
    total_net_income = df["net_income"].sum()

    # 5. ビジネスインサイト
    vacancy_threshold = cfg.get("vacancy_alert_threshold", 0.20)
    alert_areas = area_grp[area_grp["vacancy_rate"] > vacancy_threshold]["area"].tolist()

    lines = []
    lines.append("# B-14 賃貸物件管理・空室率レポート")
    lines.append("")
    lines.append(f"生成日時: 2026-06-15")
    lines.append("")

    # KPIセクション
    lines.append("## KPI サマリー（全体）")
    lines.append("")
    lines.append(f"| 指標 | 値 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 総物件数 | {total_props} 件 |")
    lines.append(f"| 全体空室率 | {overall_vacancy_rate*100:.1f}% |")
    lines.append(f"| 月次総収益 | ¥{total_monthly_revenue:,.0f} |")
    lines.append(f"| 月次総コスト | ¥{total_monthly_cost:,.0f} |")
    lines.append(f"| 月次純収益 | ¥{total_net_income:,.0f} |")
    lines.append("")

    # エリア別空室率サマリー
    lines.append("## エリア別空室率サマリー")
    lines.append("")
    lines.append("| エリア | 物件数 | 空室数 | 空室率(%) | 平均賃料(円) | 月次収益合計(円) |")
    lines.append("|--------|--------|--------|-----------|------------|----------------|")
    for _, row in area_grp.sort_values("vacancy_rate_pct", ascending=False).iterrows():
        alert_mark = " ⚠" if row["vacancy_rate"] > vacancy_threshold else ""
        lines.append(f"| {row['area']}{alert_mark} | {row['total']} | {int(row['vacant'])} | {row['vacancy_rate_pct']}% | ¥{row['avg_rent']:,} | ¥{row['total_revenue']:,} |")
    lines.append("")

    # タイプ別収益分析
    lines.append("## 物件タイプ別収益分析")
    lines.append("")
    lines.append("| 物件タイプ | 物件数 | 平均賃料(円) | 平均純収益(円) | 空室率(%) |")
    lines.append("|-----------|--------|------------|--------------|-----------|")
    for _, row in type_grp.sort_values("avg_net_income", ascending=False).iterrows():
        lines.append(f"| {row['property_type']} | {row['total']} | ¥{row['avg_rent']:,} | ¥{row['avg_net_income']:,} | {row['vacancy_rate_pct']}% |")
    lines.append("")

    # 修繕費アラート
    lines.append(f"## 修繕費アラート物件（修繕費 > ¥{alert_threshold:,}）")
    lines.append("")
    if len(alert_df) > 0:
        lines.append("| 物件ID | 物件名 | エリア | タイプ | 修繕費(円) | 入居状況 |")
        lines.append("|--------|--------|--------|--------|-----------|---------|")
        for _, row in alert_df.iterrows():
            lines.append(f"| {row['property_id']} | {row['property_name']} | {row['area']} | {row['property_type']} | ¥{row['repair_cost']:,.0f} | {row['occupancy_status']} |")
        lines.append(f"\n要対応: {len(alert_df)}件の物件で高額修繕費が発生しています。")
    else:
        lines.append("修繕費アラート対象物件なし。")
    lines.append("")

    # ビジネスインサイト
    lines.append("## ビジネスインサイト")
    lines.append("")
    if alert_areas:
        lines.append(f"### 空室率要改善エリア（{vacancy_threshold*100:.0f}%超）")
        lines.append("")
        for area in alert_areas:
            area_data = area_grp[area_grp["area"] == area].iloc[0]
            lines.append(f"**{area}** — 空室率 {area_data['vacancy_rate_pct']}%")
            lines.append(f"- 対策: 賃料見直し（平均 ¥{area_data['avg_rent']:,} → 5〜10%引き下げ検討）")
            lines.append(f"- 対策: リノベーション・設備更新による付加価値向上")
            lines.append(f"- 対策: 不動産仲介会社への積極的な情報提供強化")
            lines.append("")
    else:
        lines.append(f"全エリアの空室率が{vacancy_threshold*100:.0f}%以下に収まっており、良好な状態です。")
        lines.append("")

    lines.append("### 収益最大化のポイント")
    lines.append("")
    best_type = type_grp.loc[type_grp["avg_net_income"].idxmax(), "property_type"]
    best_net = type_grp.loc[type_grp["avg_net_income"].idxmax(), "avg_net_income"]
    lines.append(f"- 収益性が最も高い物件タイプ: **{best_type}**（平均純収益 ¥{best_net:,.0f}）")

    best_area = area_grp.loc[area_grp["total_revenue"].idxmax(), "area"]
    lines.append(f"- 月次収益合計が最も高いエリア: **{best_area}**")
    lines.append(f"- 修繕費が高い物件の計画的修繕スケジュール策定を推奨")
    lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report saved: {REPORT}")
    print(f"Total properties: {total_props}, Vacancy rate: {overall_vacancy_rate*100:.1f}%")

if __name__ == "__main__":
    main()
