import pandas as pd
import re
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "Date": "date", "勤務日": "date",
    "社員ID": "employee_id", "EmployeeID": "employee_id", "社員番号": "employee_id",
    "氏名": "employee_name", "Name": "employee_name", "社員名": "employee_name",
    "部門": "department", "Department": "department", "所属部門": "department",
    "出勤時刻": "clock_in", "ClockIn": "clock_in", "出勤": "clock_in",
    "退勤時刻": "clock_out", "ClockOut": "clock_out", "退勤": "clock_out",
    "休憩(分)": "break_minutes", "BreakMinutes": "break_minutes", "休憩時間": "break_minutes",
    "有給フラグ": "paid_leave", "PaidLeave": "paid_leave", "有給": "paid_leave",
}

KEEP_COLS = {
    "date", "employee_id", "employee_name", "department",
    "clock_in", "clock_out", "break_minutes", "paid_leave",
    "actual_work_hours", "overtime_hours", "clock_imputed", "source_file",
}

log_lines = ["# クレンジングログ\n"]


def extract_department(filename: str) -> str:
    m = re.search(r'[ぁ-鿿々ー]+部', filename)
    if m:
        return m.group(0)
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
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日", "%m/%d/%Y"]:
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
    if s in ("", "NULL", "N/A"):
        return None
    m = re.match(r'^(\d{1,2}):(\d{2})$', s)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mn <= 59:
            return f"{h:02d}:{mn:02d}"
    return None


def calc_work_hours(row):
    try:
        ci = datetime.strptime(str(row["clock_in"]), "%H:%M")
        co = datetime.strptime(str(row["clock_out"]), "%H:%M")
        break_min = float(row.get("break_minutes", 60) or 60)
        diff_min = (co - ci).total_seconds() / 60
        if diff_min < 0:
            diff_min += 24 * 60
        actual_min = diff_min - break_min
        if actual_min < 0:
            actual_min = 0
        return round(actual_min / 60, 2)
    except Exception:
        return None


all_frames = []
files = sorted(Path(".").glob("*.csv"))

for f in files:
    if "output" in str(f).lower():
        continue
    dept = extract_department(f.name)
    log_lines.append(f"\n## {f.name} → 部門名: {dept}")

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

    has_clock = "clock_in" in df.columns and "clock_out" in df.columns
    df["clock_imputed"] = False
    if has_clock:
        df["clock_in"] = df["clock_in"].apply(normalize_time)
        df["clock_out"] = df["clock_out"].apply(normalize_time)
        missing_mask = df["clock_in"].isna() | df["clock_out"].isna()
        df.loc[missing_mask, "clock_imputed"] = True
        df["clock_in"] = df["clock_in"].fillna("09:00")
        df["clock_out"] = df["clock_out"].fillna("17:30")

    if "break_minutes" in df.columns:
        df["break_minutes"] = pd.to_numeric(df["break_minutes"], errors="coerce").fillna(60)
    else:
        df["break_minutes"] = 60

    if "paid_leave" in df.columns:
        df["paid_leave"] = pd.to_numeric(df["paid_leave"], errors="coerce").fillna(0).astype(int)
    else:
        df["paid_leave"] = 0

    df["actual_work_hours"] = df.apply(calc_work_hours, axis=1)
    df["overtime_hours"] = (df["actual_work_hours"] - 8.0).clip(lower=0)

    df["department"] = dept
    df["source_file"] = f.name

    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "date", "employee_id", "employee_name", "department",
        "clock_in", "clock_out", "break_minutes", "paid_leave",
        "actual_work_hours", "overtime_hours", "clock_imputed", "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    result.to_csv(OUTPUT_DIR / "cleaned_attendance_202401.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "cleansing_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    print(f"完了: {len(result)} 行, {result['department'].nunique()} 部門")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")
