import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "講師ID": "instructor_id", "instructor_id": "instructor_id", "社員番号": "instructor_id",
    "氏名": "name", "name": "name", "講師名": "name",
    "専門分野": "specialty", "specialty": "specialty", "担当分野": "specialty",
    "雇用区分": "employment_type", "employment_type": "employment_type", "雇用形態": "employment_type",
    "実施日": "session_date", "session_date": "session_date", "開催日": "session_date",
    "コース名": "course_name", "course_name": "course_name", "研修名": "course_name",
    "コマ数": "lesson_count", "lesson_count": "lesson_count", "担当コマ": "lesson_count",
    "受講者数": "attendee_count", "attendee_count": "attendee_count", "参加人数": "attendee_count",
    "会場": "venue", "venue": "venue", "開催場所": "venue",
    "時給単価": "hourly_rate", "hourly_rate": "hourly_rate", "単価": "hourly_rate",
}

REQUIRED_COLS = [
    "instructor_id", "name", "specialty", "employment_type",
    "session_date", "course_name", "lesson_count", "attendee_count",
    "venue", "hourly_rate",
]


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


def normalize_numeric(val):
    if pd.isna(val):
        return None
    s = str(val).strip().replace(",", "").replace("，", "")
    s = s.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        return float(s)
    except ValueError:
        return None


def read_csv_auto(f: Path) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            return pd.read_csv(f, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(f)


all_frames = []
csv_files = sorted(DATA_DIR.glob("*.csv"))

for f in csv_files:
    try:
        df = read_csv_auto(f)
    except Exception as e:
        print(f"[SKIP] {f.name}: {e}")
        continue

    # カラム名を統一
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

    # 日付正規化
    if "session_date" in df.columns:
        df["session_date"] = df["session_date"].apply(normalize_date)
        df = df.dropna(subset=["session_date"])

    # 数値列の正規化・欠損補完
    for col in ["lesson_count", "attendee_count", "hourly_rate"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            if df[col].isna().any():
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val if median_val is not None else 0)
            df[col] = df[col].clip(lower=0)
        else:
            df[col] = 0.0

    # source_file 追加
    df["source_file"] = f.name

    # 計算列
    # 1コマ = 90分 = 1.5時間
    df["lesson_hours"] = (df["lesson_count"] * 1.5).round(2)
    df["lesson_cost"] = (df["lesson_hours"] * df["hourly_rate"]).round(0)
    df["cost_per_attendee"] = (
        df["lesson_cost"] / df["attendee_count"].replace(0, float("nan"))
    ).round(2)

    # workload_flag: 行レベルで lesson_count > 3 なら "高負荷"
    df["workload_flag"] = df["lesson_count"].apply(
        lambda x: "高負荷" if x > 3 else "通常"
    )

    # 必要な列のみ保持
    keep = [c for c in REQUIRED_COLS + ["source_file", "lesson_hours", "lesson_cost", "cost_per_attendee", "workload_flag"] if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    print(f"[OK] {f.name}: {len(df)} 行")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "instructor_id", "name", "specialty", "employment_type",
        "session_date", "course_name", "lesson_count", "attendee_count",
        "venue", "hourly_rate", "source_file",
        "lesson_hours", "lesson_cost", "cost_per_attendee", "workload_flag",
    ]
    result = result[[c for c in col_order if c in result.columns]]
    out_path = OUTPUT_DIR / "cleaned_instructor_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nクレンジング完了: {len(result)} 行 -> {out_path}")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")
