# -*- coding: utf-8 -*-
import os
import glob
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cleaned_contracts_202401.csv")

CANONICAL_COLS = [
    "contract_date", "contract_id", "plan", "industry",
    "monthly_fee", "usage_months", "login_count", "support_count",
    "status", "churn_reason", "ltv", "is_churned",
    "churn_risk", "arpu_grade", "source_file"
]

# ---- column maps for each style ----
COLUMN_MAP_A = {
    "契約開始日": "contract_date",
    "契約ID": "contract_id",
    "プラン": "plan",
    "業種": "industry",
    "月額料金": "monthly_fee",
    "利用月数": "usage_months",
    "月間ログイン数": "login_count",
    "サポート問い合わせ数": "support_count",
    "ステータス": "status",
    "解約理由": "churn_reason",
}

COLUMN_MAP_B = {
    "ContractDate": "contract_date",
    "ContractID": "contract_id",
    "Plan": "plan",
    "Industry": "industry",
    "MonthlyFee": "monthly_fee",
    "UsageMonths": "usage_months",
    "LoginCount": "login_count",
    "SupportCount": "support_count",
    "Status": "status",
    "ChurnReason": "churn_reason",
}

COLUMN_MAP_C = {
    "開始日": "contract_date",
    "顧客ID": "contract_id",
    "料金プラン": "plan",
    "業界": "industry",
    "月額": "monthly_fee",
    "契約月数": "usage_months",
    "ログイン回数": "login_count",
    "問い合わせ回数": "support_count",
    "契約状態": "status",
    "退会理由": "churn_reason",
}

# StyleB uses English values — need reverse mapping to Japanese
PLAN_MAP_B = {
    "Starter": "スタータープラン",
    "Standard": "スタンダードプラン",
    "Enterprise": "エンタープライズプラン",
}
INDUSTRY_MAP_B = {
    "Retail": "小売",
    "Manufacturing": "製造",
    "Healthcare": "医療",
    "IT": "IT",
    "Service": "サービス",
}
STATUS_MAP_B = {"Active": "継続", "Churned": "解約"}
REASON_MAP_B = {
    "Too expensive": "価格が高い",
    "Lack of features": "機能不足",
    "Switched to competitor": "競合他社に移行",
    "Business closed": "業務終了",
    "Hard to use": "使いにくい",
    "": "",
}

COLUMN_MAPS = {
    "contracts_styleA.csv": (COLUMN_MAP_A, None),
    "contracts_styleB.csv": (COLUMN_MAP_B, "B"),
    "contracts_styleC.csv": (COLUMN_MAP_C, None),
}


def normalize_date(series):
    """Normalize date strings to YYYY-MM-DD format."""
    return pd.to_datetime(
        series.astype(str).str.replace("/", "-", regex=False),
        format="%Y-%m-%d",
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")


def calc_churn_risk(row):
    if row["login_count"] < 5 and row["usage_months"] < 6:
        return "高リスク"
    elif row["login_count"] < 15:
        return "中リスク"
    else:
        return "低リスク"


def process_file(filepath, col_map, style=None):
    fname = os.path.basename(filepath)
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df = df.rename(columns=col_map)

    if style == "B":
        df["plan"] = df["plan"].map(PLAN_MAP_B).fillna(df["plan"])
        df["industry"] = df["industry"].map(INDUSTRY_MAP_B).fillna(df["industry"])
        df["status"] = df["status"].map(STATUS_MAP_B).fillna(df["status"])
        df["churn_reason"] = df["churn_reason"].map(REASON_MAP_B).fillna(df["churn_reason"])

    # Date normalization
    df["contract_date"] = normalize_date(df["contract_date"])

    # Numeric conversion
    for col in ["monthly_fee", "usage_months", "login_count", "support_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill missing churn_reason
    df["churn_reason"] = df["churn_reason"].fillna("")

    # Derived columns
    df["ltv"] = df["monthly_fee"] * df["usage_months"]
    df["is_churned"] = df["status"].apply(lambda s: 1 if s == "解約" else 0)
    df["churn_risk"] = df.apply(calc_churn_risk, axis=1)
    df["arpu_grade"] = df["monthly_fee"].apply(
        lambda x: "高ARPU" if x >= 8000 else "低ARPU"
    )
    df["source_file"] = fname

    return df[CANONICAL_COLS]


def main():
    all_dfs = []
    for fname, (col_map, style) in COLUMN_MAPS.items():
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            print(f"[NG] File not found: {path}")
            continue
        df = process_file(path, col_map, style)
        all_dfs.append(df)
        print(f"[OK] Processed {fname}: {len(df)} rows")

    if not all_dfs:
        print("[NG] No files processed.")
        return

    combined = pd.concat(all_dfs, ignore_index=True)
    combined.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"[OK] Output saved: {OUTPUT_FILE}")
    print(f"[OK] Total rows: {len(combined)}")


if __name__ == "__main__":
    main()
