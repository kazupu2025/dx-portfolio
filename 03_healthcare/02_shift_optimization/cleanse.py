"""
cleanse.py
data/ 以下の全CSVを読み込み、列名を統一してクレンジングし
output/cleaned_shift_202401.csv に出力する。
"""

import os
import glob
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cleaned_shift_202401.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── COLUMN_MAP ──────────────────────────────────────────────────────────
COLUMN_MAP = {
    # staff_id
    "スタッフID": "staff_id",
    "staff_id": "staff_id",
    "社員番号": "staff_id",
    # name
    "氏名": "name",
    "name": "name",
    "スタッフ名": "name",
    # role
    "役職": "role",
    "role": "role",
    "職種": "role",
    # date
    "日付": "date",
    "date": "date",
    "勤務日": "date",
    # preferred_shift
    "希望シフト": "preferred_shift",
    "preferred_shift": "preferred_shift",
    "シフト希望": "preferred_shift",
    # skill_level
    "スキルレベル": "skill_level",
    "skill_level": "skill_level",
    "技能区分": "skill_level",
    # employment_type
    "雇用形態": "employment_type",
    "employment_type": "employment_type",
    "雇用区分": "employment_type",
}

# ── シフト正規化マップ ──────────────────────────────────────────────────
SHIFT_NORM = {
    "早番": "早番", "Early": "早番", "早": "早番",
    "日勤": "日勤", "Day": "日勤", "日": "日勤",
    "遅番": "遅番", "Late": "遅番", "遅": "遅番",
    "夜勤": "夜勤", "Night": "夜勤", "夜": "夜勤",
    "休み": "休み", "Off": "休み", "休": "休み",
}

# ── 役職正規化マップ ────────────────────────────────────────────────────
ROLE_NORM = {
    "看護師": "看護師",
    "介護士": "介護士",
    "看護補助": "看護補助",
    "リハビリ師": "リハビリ師",
    # 表記揺れ対応
    "ナース": "看護師",
    "介護": "介護士",
    "看護助手": "看護補助",
    "リハビリ": "リハビリ師",
    "PT": "リハビリ師",
    "OT": "リハビリ師",
}


def load_all_csvs() -> pd.DataFrame:
    """data/ 以下の全CSVを読み込み、列名を統一して結合する"""
    csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"data/ にCSVが見つかりません: {DATA_DIR}")

    dfs = []
    for path in csv_files:
        df = pd.read_csv(path, encoding="utf-8-sig")
        # 列名をマッピング（不明な列はそのまま）
        df = df.rename(columns={c: COLUMN_MAP.get(c, c) for c in df.columns})
        df["source_file"] = os.path.basename(path)
        dfs.append(df)
        print(f"[読込] {os.path.basename(path)}  {len(df)}行")

    combined = pd.concat(dfs, ignore_index=True)
    print(f"[結合] 合計 {len(combined)} 行")
    return combined


def normalize_date(series: pd.Series) -> pd.Series:
    """日付を YYYY-MM-DD 形式に正規化"""
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d")


def normalize_shift(series: pd.Series) -> pd.Series:
    """希望シフトを正規化"""
    return series.map(lambda v: SHIFT_NORM.get(str(v).strip(), v) if pd.notna(v) else v)


def normalize_role(series: pd.Series) -> pd.Series:
    """役職を正規化"""
    return series.map(lambda v: ROLE_NORM.get(str(v).strip(), v) if pd.notna(v) else v)


def cleanse(df: pd.DataFrame) -> pd.DataFrame:
    """クレンジング処理のメイン"""
    # 日付正規化
    df["date"] = normalize_date(df["date"])

    # シフト正規化
    df["preferred_shift"] = normalize_shift(df["preferred_shift"])

    # 役職正規化
    df["role"] = normalize_role(df["role"])

    # 欠損補完
    df["preferred_shift"] = df["preferred_shift"].fillna("日勤")
    df["skill_level"] = df["skill_level"].fillna("中級")

    # is_night / is_off フラグ
    df["is_night"] = df["preferred_shift"] == "夜勤"
    df["is_off"] = df["preferred_shift"] == "休み"

    # 必須列の順序を整理
    required_cols = [
        "staff_id", "name", "role", "date", "preferred_shift",
        "skill_level", "employment_type", "is_night", "is_off", "source_file"
    ]
    extra_cols = [c for c in df.columns if c not in required_cols]
    df = df[required_cols + extra_cols]

    return df


def main():
    df = load_all_csvs()
    df = cleanse(df)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n[出力] {OUTPUT_FILE}  ({len(df)}行)")
    return df


if __name__ == "__main__":
    main()
