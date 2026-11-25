import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    # スタイルA（標準日本語列名）
    "受講日":       "enroll_date",
    "受講番号":     "enroll_no",
    "講座名":       "course_name",
    "受講者タイプ": "learner_type",
    "受講時間":     "study_hours",
    "テストスコア": "test_score",
    "ステータス":   "status",
    "満足度":       "satisfaction",
    # スタイルB（英語列名）
    "EnrollDate":   "enroll_date",
    "EnrollNo":     "enroll_no",
    "CourseName":   "course_name",
    "LearnerType":  "learner_type",
    "StudyHours":   "study_hours",
    "TestScore":    "test_score",
    "Status":       "status",
    "Satisfaction": "satisfaction",
    # スタイルC（バリアント日本語）
    "日付":     "enroll_date",
    "管理番号": "enroll_no",
    "講座":     "course_name",
    "受講区分": "learner_type",
    "学習時間": "study_hours",
    "スコア":   "test_score",
    "状況":     "status",
    "評価":     "satisfaction",
}

REQUIRED_COLS = [
    "enroll_date", "enroll_no", "course_name", "learner_type",
    "study_hours", "test_score", "status", "satisfaction",
]


def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip().replace("/", "-")
    try:
        return pd.to_datetime(s, format="%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_numeric(val):
    if pd.isna(val):
        return None
    s = str(val).strip().replace(",", "").replace(",", "")
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
    if "enroll_date" in df.columns:
        df["enroll_date"] = df["enroll_date"].apply(normalize_date)
        df = df.dropna(subset=["enroll_date"])

    # 数値列の正規化・欠損補完
    for col in ["study_hours", "test_score", "satisfaction"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            if df[col].isna().any():
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val if median_val is not None else 0)
        else:
            df[col] = 0.0

    # source_file 追加
    df["source_file"] = f.name

    # 計算列の追加
    # is_completed: 修了=1, それ以外=0
    df["is_completed"] = df["status"].apply(
        lambda x: 1 if str(x).strip() == "修了" else 0
    )

    # score_grade: テストスコアに基づくグレード
    df["score_grade"] = df["test_score"].apply(
        lambda x: "優秀" if x >= 80 else ("合格" if x >= 60 else "不合格")
    )

    # dropout_risk: 受講中かつ学習時間が中央値未満 → "高"
    study_hours_median = df["study_hours"].median()
    df["dropout_risk"] = df.apply(
        lambda row: "高"
        if (str(row["status"]).strip() == "受講中" and row["study_hours"] < study_hours_median)
        else "低",
        axis=1,
    )

    # 必要な列のみ保持
    keep_cols = REQUIRED_COLS + [
        "source_file", "is_completed", "score_grade", "dropout_risk"
    ]
    keep = [c for c in keep_cols if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    print(f"[OK] {f.name}: {len(df)} 行")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates(subset=["enroll_no"]) if "enroll_no" in result.columns else result

    col_order = [
        "enroll_date", "enroll_no", "course_name", "learner_type",
        "study_hours", "test_score", "status", "satisfaction",
        "source_file", "is_completed", "score_grade", "dropout_risk",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    out_path = OUTPUT_DIR / "cleaned_enrollment_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nクレンジング完了: {len(result)} 行 -> {out_path}")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")
