"""5顧客（A社〜E社）× 6ヶ月（2024-01〜2024-06）× 3原因分類 デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """5顧客（A社〜E社）× 6ヶ月 × 3原因分類 = 90行のサンプルデータを生成する。

    列: customer, month, category, count
    期待値: avg_monthly ≈ 27件 → verdict = "alert"
            top_category: 寸法不良 / worst_customer: C社
    """
    rows = []
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    categories = ["寸法不良", "外観不良", "機能不良"]

    # A社: 少ない（good水準、月計 ≈ 3件）
    data_a = {
        "寸法不良": [2, 1, 2, 1, 2, 1],
        "外観不良": [1, 1, 0, 1, 0, 1],
        "機能不良": [0, 1, 0, 0, 1, 0],
    }
    # B社: 中程度（月計 ≈ 6件）
    data_b = {
        "寸法不良": [3, 4, 3, 4, 3, 3],
        "外観不良": [2, 1, 2, 1, 2, 2],
        "機能不良": [1, 1, 1, 1, 0, 1],
    }
    # C社: 最多（worst_customer、月計 ≈ 11件）
    data_c = {
        "寸法不良": [6, 7, 6, 7, 6, 6],
        "外観不良": [3, 2, 3, 2, 3, 3],
        "機能不良": [2, 2, 1, 2, 1, 2],
    }
    # D社: 少ない（月計 ≈ 2件）
    data_d = {
        "寸法不良": [1, 1, 1, 1, 1, 1],
        "外観不良": [0, 1, 0, 1, 0, 0],
        "機能不良": [0, 0, 1, 0, 0, 0],
    }
    # E社: 中程度（月計 ≈ 5件）
    data_e = {
        "寸法不良": [2, 3, 2, 3, 2, 3],
        "外観不良": [2, 1, 2, 1, 2, 1],
        "機能不良": [1, 0, 1, 0, 1, 0],
    }

    for customer, data in [
        ("A社", data_a), ("B社", data_b), ("C社", data_c),
        ("D社", data_d), ("E社", data_e),
    ]:
        for cat in categories:
            for i, month in enumerate(months):
                rows.append({
                    "customer": customer,
                    "month":    month,
                    "category": cat,
                    "count":    data[cat][i],
                })

    # avg_monthly: 6ヶ月合計 / 6ヶ月
    # 月計: A≈3, B≈6, C≈11, D≈2, E≈5 → 全体月合計 ≈ 27件
    # verdict = "alert"（> 15件）
    # top_category: 寸法不良 / worst_customer: C社
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["count"].sum()
    avg = total / df["month"].nunique()
    print(f"total={total}, avg_monthly={avg:.1f}")
    df.to_csv("sample_customer_claim.csv", index=False)
