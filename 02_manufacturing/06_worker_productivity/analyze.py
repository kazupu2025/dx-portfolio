"""作業員別生産性分析 -> analysis_report.md + worker_summary_202401.csv"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUTPUT_DIR / "cleaned_worker_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# ── 1. 作業員別集計 ──
worker_agg = df.groupby("worker_id").agg(
    avg_productivity=("productivity", "mean"),
    avg_defect_rate=("defect_rate", "mean"),
    total_production=("production_qty", "sum"),
    total_defect=("defect_qty", "sum"),
    total_work_hours=("work_hours", "sum"),
    total_overtime=("overtime_hours", "sum"),
    record_count=("work_date", "count"),
).reset_index()

worker_agg["avg_productivity"] = worker_agg["avg_productivity"].round(2)
worker_agg["avg_defect_rate"] = worker_agg["avg_defect_rate"].round(4)

# ── 2. 生産性ランキング ──
top10 = worker_agg.sort_values("avg_productivity", ascending=False).head(10)
bottom10 = worker_agg.sort_values("avg_productivity", ascending=True).head(10)

# ── 3. ライン別平均生産性・不良率 ──
line_agg = df.groupby("line").agg(
    avg_productivity=("productivity", "mean"),
    avg_defect_rate=("defect_rate", "mean"),
    total_production=("production_qty", "sum"),
    record_count=("work_date", "count"),
).reset_index().sort_values("avg_productivity", ascending=False)

# ── 4. 工程別平均生産性・不良率 ──
process_agg = df.groupby("process").agg(
    avg_productivity=("productivity", "mean"),
    avg_defect_rate=("defect_rate", "mean"),
    total_production=("production_qty", "sum"),
    record_count=("work_date", "count"),
).reset_index().sort_values("avg_productivity", ascending=False)

# ── 5. 残業時間と生産性の相関 ──
corr_overtime_prod = df[["overtime_hours", "productivity"]].dropna().corr().iloc[0, 1]

# ── 6. OJT優先候補（低生産性×高不良率） ──
prod_median = worker_agg["avg_productivity"].median()
defect_median = worker_agg["avg_defect_rate"].median()
ojt_candidates = worker_agg[
    (worker_agg["avg_productivity"] < prod_median) &
    (worker_agg["avg_defect_rate"] > defect_median)
].sort_values("avg_defect_rate", ascending=False)

# ── レポート出力 ──
lines_out = []
lines_out.append("# 作業員別生産性分析レポート（2024年1月）\n")
lines_out.append(f"分析対象レコード数: {len(df):,}件  |  作業員数: {df['worker_id'].nunique()}名\n")

lines_out.append("## 1. 生産性上位10名\n")
lines_out.append("| 順位 | 作業員ID | 平均生産性(個/時) | 平均不良率 |")
lines_out.append("|------|---------|-----------------|-----------|")
for i, (_, r) in enumerate(top10.iterrows(), 1):
    lines_out.append(
        f"| {i} | {r['worker_id']} | {r['avg_productivity']:.2f} | {r['avg_defect_rate']*100:.2f}% |"
    )
lines_out.append("")

lines_out.append("## 2. 生産性下位10名\n")
lines_out.append("| 順位 | 作業員ID | 平均生産性(個/時) | 平均不良率 |")
lines_out.append("|------|---------|-----------------|-----------|")
for i, (_, r) in enumerate(bottom10.iterrows(), 1):
    lines_out.append(
        f"| {i} | {r['worker_id']} | {r['avg_productivity']:.2f} | {r['avg_defect_rate']*100:.2f}% |"
    )
lines_out.append("")

lines_out.append("## 3. ライン別平均生産性・不良率\n")
lines_out.append("| ライン | 平均生産性(個/時) | 平均不良率 | 総生産数 | レコード数 |")
lines_out.append("|--------|-----------------|-----------|---------|-----------|")
for _, r in line_agg.iterrows():
    lines_out.append(
        f"| {r['line']} | {r['avg_productivity']:.2f} | {r['avg_defect_rate']*100:.2f}% "
        f"| {r['total_production']:,} | {r['record_count']:,} |"
    )
lines_out.append("")

lines_out.append("## 4. 工程別平均生産性・不良率\n")
lines_out.append("| 工程 | 平均生産性(個/時) | 平均不良率 | 総生産数 | レコード数 |")
lines_out.append("|------|-----------------|-----------|---------|-----------|")
for _, r in process_agg.iterrows():
    lines_out.append(
        f"| {r['process']} | {r['avg_productivity']:.2f} | {r['avg_defect_rate']*100:.2f}% "
        f"| {r['total_production']:,} | {r['record_count']:,} |"
    )
lines_out.append("")

lines_out.append("## 5. 残業時間と生産性の関係\n")
lines_out.append(f"残業時間と生産性の相関係数: **{corr_overtime_prod:.4f}**\n")
if corr_overtime_prod > 0.3:
    lines_out.append("解釈: 残業時間が長い作業員ほど生産性が高い傾向が見られる。\n")
elif corr_overtime_prod < -0.3:
    lines_out.append("解釈: 残業時間が長いほど生産性が低下する傾向が見られる（疲労の影響が疑われる）。\n")
else:
    lines_out.append("解釈: 残業時間と生産性の間に顕著な相関は見られない。\n")

lines_out.append("## 6. OJT優先候補（低生産性×高不良率）\n")
if len(ojt_candidates) > 0:
    lines_out.append("| 作業員ID | 平均生産性(個/時) | 平均不良率 | 総残業時間 |")
    lines_out.append("|---------|-----------------|-----------|-----------|")
    for _, r in ojt_candidates.iterrows():
        lines_out.append(
            f"| {r['worker_id']} | {r['avg_productivity']:.2f} | {r['avg_defect_rate']*100:.2f}% "
            f"| {r['total_overtime']:.1f}h |"
        )
    lines_out.append("")
else:
    lines_out.append("OJT優先候補なし\n")

lines_out.append("## 7. インサイトと改善示唆\n")
lines_out.append(
    f"- 生産性中央値 {prod_median:.2f}個/時 を下回り、かつ不良率が中央値 "
    f"{defect_median*100:.2f}% を超える作業員が {len(ojt_candidates)}名 存在する。"
    " 優先的にOJTや作業指導を実施することを推奨する。"
)
lines_out.append(
    "- ライン別の生産性差異を確認し、生産性の低いラインには設備点検・レイアウト改善を検討すること。"
)
lines_out.append(
    "- 工程別不良率が高い工程については、作業手順の標準化と検査強化が有効である。"
)
lines_out.append(
    "- 残業時間の長い作業員については、過負荷による品質低下リスクを監視し、シフト調整を検討すること。"
)
lines_out.append(
    "- 上位作業員のベストプラクティスを横展開することで、全体の生産性底上げが期待できる。\n"
)

report_path = OUTPUT_DIR / "analysis_report.md"
report_path.write_text("\n".join(lines_out), encoding="utf-8")
print(f"レポート出力完了: {report_path}")

# worker_summary_202401.csv
summary_path = OUTPUT_DIR / "worker_summary_202401.csv"
worker_agg.to_csv(summary_path, index=False, encoding="utf-8-sig")
print(f"サマリCSV出力完了: {summary_path} ({len(worker_agg)}行)")
