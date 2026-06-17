# -*- coding: utf-8 -*-
"""
C-34 返品・クレームデータ集計レポートパイプライン
分析スクリプト

cleaned_claims_202401.csv を読み込み、多角的な分析を行い
analysis_report.md と store_summary_202401.csv を出力する。
"""

import json
import pandas as pd
from pathlib import Path


def load_data(base_dir: Path) -> pd.DataFrame:
    csv_path = base_dir / "output" / "cleaned_claims_202401.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"[ERROR] {csv_path} が見つかりません。cleanse.py を先に実行してください。")
    return pd.read_csv(csv_path, encoding="utf-8-sig")


def analyze_store(df: pd.DataFrame) -> pd.DataFrame:
    """店舗別: クレーム件数・解決率・平均返品金額"""
    grp = df.groupby("store_name", sort=True)
    summary = pd.DataFrame({
        "クレーム件数": grp["case_no"].count(),
        "解決件数": grp["is_resolved"].sum(),
        "解決率": grp["is_resolved"].mean().round(4),
        "平均返品金額": grp["return_amount"].mean().round(0).astype(int),
        "合計返品金額": grp["return_amount"].sum().astype(int),
        "平均対応日数": grp["response_days"].mean().round(1),
    }).reset_index()
    summary.rename(columns={"store_name": "店舗名"}, inplace=True)
    return summary


def analyze_claim_type(df: pd.DataFrame) -> pd.DataFrame:
    """クレーム区分別発生件数ランキング"""
    grp = df.groupby("claim_type", sort=False)["case_no"].count().reset_index()
    grp.columns = ["クレーム区分", "件数"]
    grp = grp.sort_values("件数", ascending=False).reset_index(drop=True)
    grp["順位"] = grp.index + 1
    return grp[["順位", "クレーム区分", "件数"]]


def analyze_category_amount(df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ別返品金額合計"""
    grp = df.groupby("category", sort=False)["return_amount"].sum().reset_index()
    grp.columns = ["商品カテゴリ", "返品金額合計"]
    grp = grp.sort_values("返品金額合計", ascending=False).reset_index(drop=True)
    return grp


def analyze_response_level(df: pd.DataFrame) -> pd.DataFrame:
    """対応スピード分布"""
    grp = df.groupby("response_level", sort=False)["case_no"].count().reset_index()
    grp.columns = ["対応スピード", "件数"]
    order = ["迅速", "標準", "遅延"]
    grp["_order"] = grp["対応スピード"].map({v: i for i, v in enumerate(order)})
    grp = grp.sort_values("_order").drop(columns="_order").reset_index(drop=True)
    total = grp["件数"].sum()
    grp["割合"] = (grp["件数"] / total * 100).round(1).astype(str) + "%"
    return grp


def build_report(
    df: pd.DataFrame,
    store_df: pd.DataFrame,
    claim_type_df: pd.DataFrame,
    category_df: pd.DataFrame,
    response_df: pd.DataFrame,
) -> str:
    """Markdown レポートを生成して返す。"""
    total_claims = len(df)
    total_resolved = int(df["is_resolved"].sum())
    resolve_rate = df["is_resolved"].mean() * 100
    avg_response = df["response_days"].mean()
    total_amount = int(df["return_amount"].sum())
    unresolved = total_claims - total_resolved

    worst_store = store_df.sort_values("クレーム件数", ascending=False).iloc[0]["店舗名"]
    best_resolve_store = store_df.sort_values("解決率", ascending=False).iloc[0]["店舗名"]
    top_claim = claim_type_df.iloc[0]["クレーム区分"]
    delayed_count = int(response_df.loc[response_df["対応スピード"] == "遅延", "件数"].values[0]) if "遅延" in response_df["対応スピード"].values else 0

    lines = [
        "# 返品・クレームデータ集計レポート (2024年1月)",
        "",
        "## 1. エグゼクティブサマリー",
        "",
        f"- 総クレーム件数: **{total_claims} 件**",
        f"- 解決件数: {total_resolved} 件 / 未解決件数: {unresolved} 件",
        f"- 解決率: **{resolve_rate:.1f}%**",
        f"- 平均対応日数: **{avg_response:.1f} 日**",
        f"- 総返品金額: **{total_amount:,} 円**",
        "",
        "## 2. 店舗別サマリー",
        "",
        store_df.to_markdown(index=False),
        "",
        "## 3. クレーム区分別発生件数ランキング",
        "",
        claim_type_df.to_markdown(index=False),
        "",
        "## 4. カテゴリ別返品金額合計",
        "",
        category_df.to_markdown(index=False),
        "",
        "## 5. 対応スピード分布",
        "",
        response_df.to_markdown(index=False),
        "",
        "## 6. インサイト・改善示唆",
        "",
        f"### 6-1. 最多クレーム店舗: {worst_store}",
        f"- {worst_store} はクレーム件数が最も多い。店舗オペレーション・品質管理の重点的な見直しを推奨する。",
        "",
        f"### 6-2. 解決率トップ店舗: {best_resolve_store}",
        f"- {best_resolve_store} の解決率が最も高く、対応フローをベストプラクティスとして横展開することが効果的である。",
        "",
        f"### 6-3. 最多クレーム区分: {top_claim}",
        f"- 「{top_claim}」が全体の最多区分であり、商品検品プロセスや包装基準の強化が優先課題となる。",
        "",
        f"### 6-4. 遅延対応の削減",
        f"- 遅延対応件数は {delayed_count} 件であり、対応フローの標準化とエスカレーションルールの明確化によって削減が見込める。",
        "",
        "---",
        "",
        "*本レポートは自動生成されました。*",
    ]
    return "\n".join(lines)


def main() -> None:
    base_dir = Path(__file__).parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    df = load_data(base_dir)
    print(f"[LOAD] {len(df)} rows loaded")

    store_df = analyze_store(df)
    claim_type_df = analyze_claim_type(df)
    category_df = analyze_category_amount(df)
    response_df = analyze_response_level(df)

    # --- 店舗別サマリー CSV ---
    store_csv = output_dir / "store_summary_202401.csv"
    store_df.to_csv(store_csv, index=False, encoding="utf-8-sig")
    print(f"[DONE] {store_csv}")

    # --- Markdown レポート ---
    report_md = output_dir / "analysis_report.md"
    report_text = build_report(df, store_df, claim_type_df, category_df, response_df)
    report_md.write_text(report_text, encoding="utf-8")
    print(f"[DONE] {report_md}")

    # --- JSON サマリー（任意出力、ダッシュボード連携用）---
    result_json = {
        "total_claims": len(df),
        "resolved_count": int(df["is_resolved"].sum()),
        "resolve_rate": round(df["is_resolved"].mean() * 100, 2),
        "avg_response_days": round(df["response_days"].mean(), 2),
        "total_return_amount": int(df["return_amount"].sum()),
        "store_summary": store_df.to_dict(orient="records"),
        "claim_type_ranking": claim_type_df.to_dict(orient="records"),
        "category_amount": category_df.to_dict(orient="records"),
        "response_level_dist": response_df.to_dict(orient="records"),
    }
    json_path = output_dir / "result_analysis.json"
    json_path.write_text(json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] {json_path}")


if __name__ == "__main__":
    main()
