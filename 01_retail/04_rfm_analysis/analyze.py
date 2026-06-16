# -*- coding: utf-8 -*-
"""
analyze.py
RFM分析を実施し、顧客別RFMスコア・セグメントCSVと分析レポートMDを出力する。
print文に円記号を使わない。
"""

import pandas as pd
from pathlib import Path
import datetime

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "cleaned_purchases_202401.csv"
OUTPUT_CSV = OUTPUT_DIR / "customer_rfm_202401.csv"
OUTPUT_REPORT = OUTPUT_DIR / "analysis_report.md"

REFERENCE_DATE = datetime.date(2024, 2, 1)

SEGMENT_LABELS = {
    "優良顧客": "優良顧客（合計スコア >= 12）",
    "成長顧客": "成長顧客（合計スコア 9 ~ 11）",
    "離反リスク": "離反リスク（合計スコア 6 ~ 8）",
    "休眠顧客": "休眠顧客（合計スコア <= 5）",
}


def classify_segment(total_score: int) -> str:
    if total_score >= 12:
        return "優良顧客"
    elif total_score >= 9:
        return "成長顧客"
    elif total_score >= 6:
        return "離反リスク"
    else:
        return "休眠顧客"


def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    ref = pd.Timestamp(REFERENCE_DATE)

    rfm = df.groupby("customer_code").agg(
        last_order_date=("order_date", "max"),
        frequency=("order_date", "count"),
        monetary=("amount", "sum"),
    ).reset_index()

    rfm["recency"] = (ref - rfm["last_order_date"]).dt.days

    # 1~5スコアリング（qcut）
    # Recency: 低いほど良い -> 逆順でスコア付け
    rfm["r_score"] = pd.qcut(rfm["recency"], q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_total"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
    rfm["segment"] = rfm["rfm_total"].apply(classify_segment)

    return rfm


def generate_report(rfm: pd.DataFrame, df_raw: pd.DataFrame) -> str:
    seg_counts = rfm["segment"].value_counts()
    total_customers = len(rfm)
    avg_frequency = rfm["frequency"].mean()
    avg_monetary = rfm["monetary"].mean()

    seg_order = ["優良顧客", "成長顧客", "離反リスク", "休眠顧客"]

    # カテゴリ別売上
    cat_sales = df_raw.groupby("category")["amount"].sum().sort_values(ascending=False)
    top_cat = cat_sales.index[0]
    top_cat_amount = cat_sales.iloc[0]

    # 店舗別売上
    store_sales = df_raw.groupby("store_name")["amount"].sum().sort_values(ascending=False)
    top_store = store_sales.index[0]

    lines = [
        "# 顧客購買履歴 RFM 分析レポート",
        "",
        f"基準日: {REFERENCE_DATE}  分析対象顧客数: {total_customers}名",
        "",
        "---",
        "",
        "## 1. RFM 分析概要",
        "",
        "RFM 分析とは顧客を Recency（最終購買日）、Frequency（購買頻度）、Monetary（累計購買金額）の",
        "3軸でスコアリングし、顧客価値を可視化する手法です。",
        "",
        "### Recency（直近性）",
        f"- 基準日 {REFERENCE_DATE} からの経過日数で評価します。",
        "- 経過日数が短いほど高スコア（1〜5点）を付与します。",
        "",
        "### Frequency（頻度）",
        f"- 全期間の購買回数で評価します。平均購買回数: {avg_frequency:.1f}回",
        "- 購買回数が多いほど高スコア（1〜5点）を付与します。",
        "",
        "### Monetary（金額）",
        f"- 全期間の累計購買金額で評価します。平均累計購買金額: {avg_monetary:,.0f}円",
        "- 累計金額が大きいほど高スコア（1〜5点）を付与します。",
        "",
        "---",
        "",
        "## 2. セグメント分析",
        "",
        "| セグメント | 顧客数 | 割合 |",
        "|-----------|--------|------|",
    ]

    for seg in seg_order:
        count = seg_counts.get(seg, 0)
        pct = count / total_customers * 100
        lines.append(f"| {seg} | {count}名 | {pct:.1f}% |")

    lines += [
        "",
        "---",
        "",
        "## 3. インサイト・まとめ",
        "",
        f"- 優良顧客（RFMスコア合計 >= 12）は {seg_counts.get('優良顧客', 0)}名（{seg_counts.get('優良顧客', 0)/total_customers*100:.1f}%）存在します。",
        f"- 成長顧客は {seg_counts.get('成長顧客', 0)}名おり、適切なアプローチで優良顧客へ移行できる可能性があります。",
        f"- 離反リスク顧客は {seg_counts.get('離反リスク', 0)}名で、リテンション施策が急務です。",
        f"- 休眠顧客は {seg_counts.get('休眠顧客', 0)}名おり、再活性化キャンペーンの対象として検討が必要です。",
        f"- カテゴリ別売上トップは「{top_cat}」で累計 {top_cat_amount:,}円です。",
        f"- 店舗別売上トップは「{top_store}」です。",
        "",
        "---",
        "",
        "## 4. 改善示唆",
        "",
        "1. **優良顧客向け**: ロイヤルティプログラムや限定オファーで維持・強化を図る。",
        "2. **成長顧客向け**: パーソナライズされたレコメンデーションでアップセルを促進する。",
        "3. **離反リスク顧客向け**: 購買から一定期間経過時にクーポン配信など再購買を促す施策を実施する。",
        "4. **休眠顧客向け**: 「お久しぶりキャンペーン」でブランド想起を促し、再活性化を図る。",
        f"5. **カテゴリ戦略**: 売上トップの「{top_cat}」をさらに強化しつつ、下位カテゴリの改善策を検討する。",
        "",
        "---",
        "",
        f"*本レポートは analyze.py により自動生成されました（基準日: {REFERENCE_DATE}）*",
    ]

    return "\n".join(lines)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"[FAIL] 入力ファイルが見つかりません: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    print(f"[OK] 入力データ読み込み: {len(df)}行")

    rfm = compute_rfm(df)
    print(f"[OK] RFM計算完了: {len(rfm)}顧客")

    # セグメント内訳表示
    for seg, count in rfm["segment"].value_counts().items():
        print(f"  {seg}: {count}名")

    # CSV出力
    rfm.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"[OK] 顧客RFMスコアCSV出力: {OUTPUT_CSV}")

    # レポート出力
    report_text = generate_report(rfm, df)
    OUTPUT_REPORT.write_text(report_text, encoding="utf-8")
    print(f"[OK] 分析レポート出力: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
