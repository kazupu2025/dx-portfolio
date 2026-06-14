import pandas as pd
import re
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
BASE_DIR = OUTPUT_DIR.parent

COLUMN_MAP = {
    "日付": "date", "Date": "date", "来院日": "date",
    "曜日": "weekday", "Weekday": "weekday", "曜日区分": "weekday",
    "患者ID": "patient_id", "PatientID": "patient_id", "受診番号": "patient_id",
    "診療科": "department", "Department": "department", "科": "department",
    "受付時刻": "reception_time", "ReceptionTime": "reception_time", "チェックイン": "reception_time",
    "待ち時間(分)": "wait_minutes", "WaitMinutes": "wait_minutes", "待ち(分)": "wait_minutes",
    "来院経路": "visit_route", "VisitRoute": "visit_route", "経路": "visit_route",
}

KEEP_COLS = {
    "date", "weekday", "patient_id", "department",
    "reception_time", "hour_slot", "wait_minutes",
    "visit_route", "is_long_wait", "time_imputed", "source_file",
}

log_lines = ["# クレンジングログ\n"]


def extract_department(filename: str) -> str:
    # 診療科名のパターン（〜科）
    m = re.search(r'[ぁ-鿿々ー]+(科|内科|外科)', filename)
    if m:
        return m.group(0)
    # 2文字以上の日本語
    parts = re.split(r'[_\-\s]', Path(filename).stem)
    for part in parts:
        if re.search(r'[ぁ-鿿々ー]{2,}', part):
            return part
    return Path(filename).stem


def read_file(f: Path) -> pd.DataFrame:
    raw_bytes = f.read_bytes()
    enc = "utf-8-sig"
    for candidate in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            raw_bytes.decode(candidate)
            enc = candidate
            break
        except Exception:
            continue
    return pd.read_csv(f, encoding=enc)


def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("", "NULL", "N/A"):
        return None
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"]:
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_time(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    m = re.match(r'^(\d{1,2}):(\d{2})$', s)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if 8 <= h <= 18 and 0 <= mn <= 59:
            return f"{h:02d}:{mn:02d}"
    return None


def extract_hour(time_str):
    if pd.isna(time_str) or str(time_str).strip() == "":
        return None
    m = re.match(r'^(\d{1,2}):', str(time_str))
    if m:
        return int(m.group(1))
    return None


all_frames = []
files = sorted(BASE_DIR.glob("*.csv"))

for f in files:
    if "output" in str(f).lower():
        continue
    dept = extract_department(f.name)
    log_lines.append(f"\n## {f.name} → 診療科: {dept}")

    try:
        df = read_file(f)
    except Exception as e:
        log_lines.append(f"- 読み込みエラー: {e}")
        continue

    renamed = {}
    for col in df.columns:
        col_str = str(col).strip()
        if col_str in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col_str]
        elif str(col).startswith("Unnamed"):
            renamed[col] = f"_drop_{col}"
    df = df.rename(columns=renamed)

    drop_cols = [c for c in df.columns if str(c).startswith("_drop_")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    df = df.dropna(how="all")

    if "date" in df.columns:
        df["date"] = df["date"].apply(normalize_date)
        df = df.dropna(subset=["date"])

    df["time_imputed"] = False
    if "reception_time" in df.columns:
        df["reception_time"] = df["reception_time"].apply(normalize_time)
        missing = df["reception_time"].isna()
        df.loc[missing, "time_imputed"] = True
        df.loc[missing, "reception_time"] = "09:00"

    df["hour_slot"] = df["reception_time"].apply(extract_hour)

    if "wait_minutes" in df.columns:
        df["wait_minutes"] = pd.to_numeric(df["wait_minutes"], errors="coerce")
        df["wait_minutes"] = df["wait_minutes"].clip(lower=0).fillna(30)
    else:
        df["wait_minutes"] = 30

    wait_alert = 60
    df["is_long_wait"] = df["wait_minutes"] > wait_alert

    if "weekday" not in df.columns:
        df["weekday"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%a").map(
            {"Mon": "月", "Tue": "火", "Wed": "水", "Thu": "木",
             "Fri": "金", "Sat": "土", "Sun": "日"}
        )

    df["department"] = dept
    df["source_file"] = f.name

    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行, 長時間待ち: {df['is_long_wait'].sum()} 件")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "date", "weekday", "patient_id", "department",
        "reception_time", "hour_slot", "wait_minutes",
        "visit_route", "is_long_wait", "time_imputed", "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    result.to_csv(OUTPUT_DIR / "cleaned_visit_202401.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "cleansing_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    long_wait = result["is_long_wait"].sum()
    print(f"完了: {len(result)} 行, 5診療科, 長時間待ち: {long_wait} 件")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")
