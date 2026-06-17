# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_reservations_202401.csv")

REQUIRED_COLS = [
    "checkin_date", "reserv_no", "room_type", "guest_count", "nights",
    "room_rate", "status", "cancel_reason", "total_revenue", "is_cancel",
    "loss_revenue", "revenue_per_guest", "source_file"
]

EXPECTED_ROOM_TYPES = {"シングル", "ツイン", "ダブル", "スイート"}
EXPECTED_STATUSES = {"宿泊済み", "キャンセル", "ノーショウ"}
EXPECTED_SOURCES = {"styleA", "styleB", "styleC"}

results = []


def check(name, passed, detail=""):
    status = "[PASS]" if passed else "[FAIL]"
    msg = "{} {}".format(status, name)
    if detail:
        msg += " | " + detail
    print(msg)
    results.append(passed)


# Load
if not os.path.exists(CSV_PATH):
    print("[FAIL] File exists: cleaned_reservations_202401.csv")
    print("Result: 0/18 checks passed")
    sys.exit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

check("File exists", True)
check("Row count >= 420", len(df) >= 420, "rows={}".format(len(df)))
check("Required columns present", all(c in df.columns for c in REQUIRED_COLS),
      "missing={}".format([c for c in REQUIRED_COLS if c not in df.columns]))

# Date format
try:
    parsed = pd.to_datetime(df["checkin_date"], format="%Y-%m-%d")
    check("checkin_date format YYYY-MM-DD", not parsed.isnull().any())
except Exception as e:
    check("checkin_date format YYYY-MM-DD", False, str(e))

check("reserv_no uniqueness", df["reserv_no"].is_unique,
      "duplicates={}".format(df["reserv_no"].duplicated().sum()))
check("room_type 4 types", set(df["room_type"].unique()) == EXPECTED_ROOM_TYPES,
      "found={}".format(set(df["room_type"].unique())))
check("status 3 types", set(df["status"].unique()) == EXPECTED_STATUSES,
      "found={}".format(set(df["status"].unique())))
check("guest_count >= 1", (df["guest_count"] >= 1).all(),
      "violations={}".format((df["guest_count"] < 1).sum()))
check("nights >= 1", (df["nights"] >= 1).all(),
      "violations={}".format((df["nights"] < 1).sum()))
check("room_rate > 0", (df["room_rate"] > 0).all(),
      "violations={}".format((df["room_rate"] <= 0).sum()))
check("total_revenue >= 0", (df["total_revenue"] >= 0).all(),
      "violations={}".format((df["total_revenue"] < 0).sum()))
check("is_cancel values 0 or 1", df["is_cancel"].isin([0, 1]).all(),
      "violations={}".format((~df["is_cancel"].isin([0, 1])).sum()))
check("loss_revenue >= 0", (df["loss_revenue"] >= 0).all(),
      "violations={}".format((df["loss_revenue"] < 0).sum()))

check_cols = [c for c in REQUIRED_COLS if c not in ("cancel_reason", "revenue_per_guest")]
null_rate = df[check_cols].isnull().mean().max()
check("Missing rate <= 15% (cancel_reason/revenue_per_guest除く)", null_rate <= 0.15, "max_null_rate={:.1%}".format(null_rate))
check("source_file 3 types", set(df["source_file"].unique()) == EXPECTED_SOURCES,
      "found={}".format(set(df["source_file"].unique())))

cancel_count = (df["status"] == "キャンセル").sum()
noshow_count = (df["status"] == "ノーショウ").sum()
stayed_count = (df["status"] == "宿泊済み").sum()
check("Cancel count >= 1", cancel_count >= 1, "count={}".format(cancel_count))
check("NoShow count >= 1", noshow_count >= 1, "count={}".format(noshow_count))
check("Stayed count >= 1", stayed_count >= 1, "count={}".format(stayed_count))

passed = sum(results)
total = len(results)
print("Result: {}/{} checks passed".format(passed, total))
if passed < total:
    sys.exit(1)
