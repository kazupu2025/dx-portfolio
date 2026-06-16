import pandas as pd
import json
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_material_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_PATH = OUTPUT_DIR / "material_summary_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["quantity", "unit_price", "prev_month_price", "price_change_rate", "total_cost"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
if "purchase_date" in df.columns:
    df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")

lines = ["# 原材料コスト変動レポート（2024年1月）\n"]

# 1. カテゴリ別コスト合計・前月比変動率
lines.append("## 1. カテゴリ別コスト合計と変動率\n")
cat_summary = df.groupby("category").agg(
    仕入コスト合計=("total_cost", "sum"),
    平均単価=("unit_price", "mean"),
    平均前月単価=("prev_month_price", "mean"),
    取引件数=("total_cost", "count"),
).copy()
cat_summary["平均変動率(%)"] = (
    (cat_summary["平均単価"] - cat_summary["平均前月単価"]) /
    cat_summary["平均前月単価"].replace(0, float("nan")) * 100
).round(2)
cat_summary = cat_summary.sort_values("仕入コスト合計", ascending=False)
fmt1 = cat_summary.copy()
fmt1["仕入コスト合計"] = fmt1["仕入コスト合計"].map("{:,.0f}".format)
fmt1["平均単価"] = fmt1["平均単価"].map("{:,.0f}".format)
fmt1["平均前月単価"] = fmt1["平均前月単価"].map("{:,.0f}".format)
lines.append(fmt1.to_markdown())
lines.append("")

# 2. 原材料別単価変動ランキング（急騰上位5件・急落上位5件）
lines.append("## 2. 原材料別単価変動ランキング\n")

if "price_change_flag" in df.columns:
    soar_df = df[df["price_change_flag"] == "急騰"]
    drop_df = df[df["price_change_flag"] == "急落"]

    lines.append("### 急騰上位5件\n")
    if len(soar_df) > 0:
        soar_top = (soar_df.groupby(["material_code", "material_name", "category"])
                    .agg(平均変動率=("price_change_rate", "mean"),
                         件数=("price_change_rate", "count"))
                    .sort_values("平均変動率", ascending=False)
                    .head(5))
        soar_top["平均変動率(%)"] = (soar_top["平均変動率"] * 100).round(2)
        soar_top = soar_top.drop(columns="平均変動率")
        lines.append(soar_top.to_markdown())
    else:
        lines.append("- 急騰データなし")
    lines.append("")

    lines.append("### 急落上位5件\n")
    if len(drop_df) > 0:
        drop_top = (drop_df.groupby(["material_code", "material_name", "category"])
                    .agg(平均変動率=("price_change_rate", "mean"),
                         件数=("price_change_rate", "count"))
                    .sort_values("平均変動率", ascending=True)
                    .head(5))
        drop_top["平均変動率(%)"] = (drop_top["平均変動率"] * 100).round(2)
        drop_top = drop_top.drop(columns="平均変動率")
        lines.append(drop_top.to_markdown())
    else:
        lines.append("- 急落データなし")
    lines.append("")
else:
    lines.append("- price_change_flag 列なし\n")

# 3. 仕入先別コスト構成
lines.append("## 3. 仕入先別コスト構成\n")
sup_summary = df.groupby("supplier").agg(
    仕入コスト合計=("total_cost", "sum"),
    取引件数=("total_cost", "count"),
    取扱原材料数=("material_code", "nunique"),
).copy()
total_cost_all = sup_summary["仕入コスト合計"].sum()
sup_summary["コスト構成比(%)"] = (
    sup_summary["仕入コスト合計"] / total_cost_all * 100
).round(2)
sup_summary = sup_summary.sort_values("仕入コスト合計", ascending=False)
fmt3 = sup_summary.copy()
fmt3["仕入コスト合計"] = fmt3["仕入コスト合計"].map("{:,.0f}".format)
lines.append(fmt3.to_markdown())
lines.append("")

# 4. 日別仕入コストトレンド
lines.append("## 4. 日別仕入コストトレンド\n")
if "purchase_date" in df.columns and df["purchase_date"].notna().any():
    daily = df.groupby("purchase_date").agg(
        仕入コスト=("total_cost", "sum"),
        件数=("total_cost", "count"),
    ).copy()
    peak_date = daily["仕入コスト"].idxmax()
    avg_daily = daily["仕入コスト"].mean()
    min_date = daily.index.min()
    max_date = daily.index.max()
    lines.append(f"- 集計期間: {str(min_date)[:10]} - {str(max_date)[:10]}")
    lines.append(f"- 日次平均仕入コスト: **{avg_daily:,.0f}**")
    lines.append(f"- 最大仕入日: {str(peak_date)[:10]} ({daily.loc[peak_date, '仕入コスト']:,.0f})")
    lines.append(f"- 営業日数: {len(daily)} 日")
else:
    lines.append("- 日付データなし")
lines.append("")

# 5. ビジネスインサイト・まとめ
lines.append("## 5. ビジネスインサイトとまとめ\n")
total_cost = df["total_cost"].sum()
n_soar = (df["price_change_flag"] == "急騰").sum() if "price_change_flag" in df.columns else 0
n_drop = (df["price_change_flag"] == "急落").sum() if "price_change_flag" in df.columns else 0
n_stable = (df["price_change_flag"] == "安定").sum() if "price_change_flag" in df.columns else 0
avg_change = df["price_change_rate"].mean() * 100 if "price_change_rate" in df.columns else 0
worst_cat = cat_summary["平均変動率(%)"].idxmax() if not cat_summary.empty else "不明"
best_cat = cat_summary["平均変動率(%)"].idxmin() if not cat_summary.empty else "不明"
top_sup = sup_summary.index[0] if not sup_summary.empty else "不明"
top_sup_share = sup_summary["コスト構成比(%)"].iloc[0] if not sup_summary.empty else 0

lines.append(f"- 月次総仕入コスト: **{total_cost:,.0f}**")
lines.append(f"- 平均変動率: **{avg_change:+.2f}%**")
lines.append(f"- 急騰件数: {n_soar} 件 / 急落件数: {n_drop} 件 / 安定: {n_stable} 件")
lines.append(f"- 変動率最大カテゴリ: **{worst_cat}** — コスト上昇リスクが高く、代替調達先の検討を推奨")
lines.append(f"- 変動率最小カテゴリ: **{best_cat}** — 相対的に安定。長期契約への切替が有効")
lines.append(f"- 最大仕入先: **{top_sup}**（コスト構成比 {top_sup_share:.1f}%）— 依存度が高い場合は複数調達でリスク分散を検討")
if n_soar > 0:
    lines.append(f"- **急騰品目 {n_soar} 件を検出。緊急対応として代替素材・緊急在庫確保を検討すること**")
if n_drop > 0:
    lines.append(f"- **急落品目 {n_drop} 件を検出。スポット購入による追加コスト削減機会がある**")
lines.append("")

report_text = "\n".join(lines)
REPORT_PATH.write_text(report_text, encoding="utf-8")

# 原材料別サマリーCSV出力
mat_summary = df.groupby(["material_code", "material_name", "category"]).agg(
    仕入コスト合計=("total_cost", "sum"),
    平均単価=("unit_price", "mean"),
    平均前月単価=("prev_month_price", "mean"),
    平均変動率=("price_change_rate", "mean"),
    取引件数=("total_cost", "count"),
    急騰件数=("price_change_flag", lambda x: (x == "急騰").sum()),
    急落件数=("price_change_flag", lambda x: (x == "急落").sum()),
).copy()
mat_summary["平均変動率(%)"] = (mat_summary["平均変動率"] * 100).round(2)
mat_summary = mat_summary.drop(columns="平均変動率")
mat_summary = mat_summary.sort_values("仕入コスト合計", ascending=False)
mat_summary.to_csv(SUMMARY_PATH, encoding="utf-8-sig")

print(f"Analysis complete: total cost={total_cost:,.0f}, soar={n_soar}, drop={n_drop}")
print(f"Report: {REPORT_PATH}")
print(f"Summary CSV: {SUMMARY_PATH}")
