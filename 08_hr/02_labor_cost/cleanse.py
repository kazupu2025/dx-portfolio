"""
C-30: クレンジングスクリプト
data/ 以下の3スタイルCSVを統一フォーマットに変換し
output/cleaned_labor_cost_202401.csv へ出力
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    # スタイルA (標準日本語)
    "対象年月":   "year_month",
    "部門":       "department",
    "雇用区分":   "employment_type",
    "社員数":     "head_count",
    "予算人件費": "budget_cost",
    "実績人件費": "actual_cost",
    "残業代":     "overtime_cost",
    # スタイルB (英語)
    "YearMonth":       "year_month",
    "Department":      "department",
    "EmploymentType":  "employment_type",
    "HeadCount":       "head_count",
    "BudgetLaborCost": "budget_cost",
    "ActualLaborCost": "actual_cost",
    "OvertimeCost":    "overtime_cost",
    # スタイルC (バリアント日本語)
    "集計月":     "year_month",
    "所属部門":   "department",
    "雇用形態":   "employment_type",
    "人員数":     "head_count",
    "人件費予算": "budget_cost",
    "人件費実績": "actual_cost",
    "時間外手当": "overtime_cost",
}

REQUIRED_COLS = [
    "year_month", "department", "employment_type",
    "head_count", "budget_cost", "actual_cost", "overtime_cost",
]


def read_csv_auto(path: Path) -> pd.DataFrame:
    """エンコーディング自動検出してCSV読み込み"""
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            raw.decode(enc)
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


def normalize_year_month(val) -> str | None:
    """YYYY-MM 形式に正規化 (YYYY/MM または YYYY-MM を受け付ける)"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    # YYYY/MM
    if len(s) == 7 and s[4] == "/":
        return s[:4] + "-" + s[5:]
    # YYYY-MM
    if len(s) == 7 and s[4] == "-":
        return s
    # YYYY/MM/DD or YYYY-MM-DD など先頭7文字を使う
    if len(s) >= 7:
        candidate = s[:7].replace("/", "-")
        if len(candidate) == 7 and candidate[4] == "-":
            return candidate
    return None


def process_file(path: Path) -> pd.DataFrame:
    df = read_csv_auto(path)

    # 列名マッピング
    renamed = {col: COLUMN_MAP[str(col).strip()] for col in df.columns if str(col).strip() in COLUMN_MAP}
    df = df.rename(columns=renamed)

    # source_file 列追加
    df["source_file"] = path.name

    # 必要列だけ残す
    keep = [c for c in REQUIRED_COLS + ["source_file"] if c in df.columns]
    df = df[keep]

    # 全列 NaN 行削除
    df = df.dropna(how="all")

    # year_month 正規化
    if "year_month" in df.columns:
        df["year_month"] = df["year_month"].apply(normalize_year_month)
        df = df.dropna(subset=["year_month"])

    # 数値列を数値型に変換・非負にクリップ
    for col in ("head_count", "budget_cost", "actual_cost", "overtime_cost"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # head_count が 0 以下の行を除外
    if "head_count" in df.columns:
        df = df[df["head_count"] > 0]

    # 計算列を追加
    df["variance_amount"] = df["actual_cost"] - df["budget_cost"]
    df["variance_rate"] = df.apply(
        lambda r: r["variance_amount"] / r["budget_cost"] if r["budget_cost"] != 0 else float("nan"),
        axis=1,
    )
    df["cost_per_person"] = df.apply(
        lambda r: r["actual_cost"] / r["head_count"] if r["head_count"] > 0 else float("nan"),
        axis=1,
    )
    df["variance_flag"] = df["variance_rate"].apply(
        lambda r: "超過" if (not pd.isna(r) and r > 0.15)
        else ("節約" if (not pd.isna(r) and r < -0.15) else "正常")
    )

    return df


def main():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print(f"データファイルが見つかりません: {DATA_DIR}")
        return

    frames = []
    for path in csv_files:
        print(f"処理中: {path.name}")
        df = process_file(path)
        frames.append(df)
        print(f"  -> {len(df)} 行")

    result = pd.concat(frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "year_month", "department", "employment_type",
        "head_count", "budget_cost", "actual_cost", "overtime_cost",
        "variance_amount", "variance_rate", "cost_per_person", "variance_flag",
        "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    out_path = OUTPUT_DIR / "cleaned_labor_cost_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nクレンジング完了: {len(result)} 行")
    print(f"出力: {out_path}")
    print(f"列: {list(result.columns)}")


if __name__ == "__main__":
    main()
