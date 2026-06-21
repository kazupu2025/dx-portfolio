"""5協力会社（A社〜E社）× 6ヶ月（2024-01〜2024-06）受入不良率デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    rows = []
    # A社: 不良率 ≈ 0.8%（優良）
    for month, qty, defects in [
        ("2024-01", 500, 4), ("2024-02", 520, 4), ("2024-03", 510, 5),
        ("2024-04", 530, 4), ("2024-05", 500, 4), ("2024-06", 515, 4),
    ]:
        rows.append({"supplier": "A社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # B社: 不良率 ≈ 4.5%（要改善）
    for month, qty, defects in [
        ("2024-01", 300, 14), ("2024-02", 280, 13), ("2024-03", 310, 14),
        ("2024-04", 290, 13), ("2024-05", 300, 13), ("2024-06", 305, 14),
    ]:
        rows.append({"supplier": "B社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # C社: 不良率 ≈ 2.5%（要注意）
    for month, qty, defects in [
        ("2024-01", 800, 20), ("2024-02", 820, 21), ("2024-03", 810, 20),
        ("2024-04", 830, 21), ("2024-05", 800, 20), ("2024-06", 815, 20),
    ]:
        rows.append({"supplier": "C社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # D社: 不良率 ≈ 0.5%（最優良）
    for month, qty, defects in [
        ("2024-01", 600, 3), ("2024-02", 610, 3), ("2024-03", 605, 3),
        ("2024-04", 620, 3), ("2024-05", 600, 3), ("2024-06", 610, 3),
    ]:
        rows.append({"supplier": "D社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # E社: 不良率 ≈ 2.8%（要注意）
    for month, qty, defects in [
        ("2024-01", 400, 11), ("2024-02", 410, 12), ("2024-03", 400, 11),
        ("2024-04", 420, 12), ("2024-05", 400, 11), ("2024-06", 410, 11),
    ]:
        rows.append({"supplier": "E社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # 期待 avg ≈ 2.0% → verdict = "warning" / worst: B社 / best: D社
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_supplier_defect_rate.csv", index=False)
    print(df.to_string())
