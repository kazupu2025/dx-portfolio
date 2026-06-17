# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CANONICAL_COLS = [
    "claim_date", "claim_id", "dept", "insurance_type",
    "patient_count", "total_points", "claim_amount", "reduction_amount",
    "payment_status", "net_amount", "reduction_rate",
    "is_returned", "collection_flag", "source_file"
]

COLUMN_MAP = {
    "styleA": {
        "請求日": "claim_date",
        "請求ID": "claim_id",
        "診療科": "dept",
        "保険区分": "insurance_type",
        "患者数": "patient_count",
        "診療報酷点数": "total_points",
        "請求金額": "claim_amount",
        "査定減額": "reduction_amount",
        "支払状況": "payment_status",
    },
    "styleB": {
        "ClaimDate": "claim_date",
        "ClaimID": "claim_id",
        "Department": "dept",
        "InsuranceType": "insurance_type",
        "PatientCount": "patient_count",
        "TotalPoints": "total_points",
        "ClaimAmount": "claim_amount",
        "ReductionAmount": "reduction_amount",
        "PaymentStatus": "payment_status",
    },
    "styleC": {
        "算定日": "claim_date",
        "明細番号": "claim_id",
        "科名": "dept",
        "保険種別": "insurance_type",
        "受診者数": "patient_count",
        "点数合計": "total_points",
        "請求額": "claim_amount",
        "減額査定": "reduction_amount",
        "決済状況": "payment_status",
    },
}

PAYMENT_EN_TO_JP = {
    "Paid": "支払済み",
    "UnderReview": "審査中",
    "Returned": "返戈",
}

FILES = [
    ("claims_styleA_202401.csv", "styleA"),
    ("claims_styleB_202401.csv", "styleB"),
    ("claims_styleC_202401.csv", "styleC"),
]


def normalize_date(s):
    s = s.astype(str).str.replace("/", "-", regex=False)
    return pd.to_datetime(s, format="%Y-%m-%d", errors="coerce").dt.strftime("%Y-%m-%d")


def cleanse_file(filename, style):
    fpath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(fpath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP[style])
    df["claim_date"] = normalize_date(df["claim_date"])
    for col in ["patient_count", "total_points", "claim_amount", "reduction_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "payment_status" in df.columns:
        df["payment_status"] = df["payment_status"].replace(PAYMENT_EN_TO_JP)
    df["net_amount"] = df["claim_amount"] - df["reduction_amount"]
    df["reduction_rate"] = df.apply(
        lambda r: r["reduction_amount"] / r["claim_amount"]
        if pd.notna(r["claim_amount"]) and r["claim_amount"] > 0 else 0.0,
        axis=1
    )
    df["is_returned"] = (df["payment_status"] == "返戈").astype(int)
    df["collection_flag"] = df["payment_status"].apply(
        lambda s: "回収済み" if s == "支払済み" else "未回収"
    )
    df["source_file"] = filename
    df = df[CANONICAL_COLS]
    return df


dfs = []
for fname, style in FILES:
    df = cleanse_file(fname, style)
    dfs.append(df)
    print("[OK] {} => {} rows".format(fname, len(df)))

result = pd.concat(dfs, ignore_index=True)
out_path = os.path.join(OUTPUT_DIR, "cleaned_claims_202401.csv")
result.to_csv(out_path, index=False, encoding="utf-8-sig")
print("[OK] Output: {} rows => {}".format(len(result), out_path))
