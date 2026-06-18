# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
データクレンジングスクリプト
3スタイルCSVを統一フォーマットに変換する
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# カノニカル列（出力列の定義）
CANONICAL_COLS = [
    "app_date",
    "app_id",
    "department",
    "selection_method",
    "region",
    "result",
    "score",
    "interview_flag",
    "decline_reason",
    "is_enrolled",
    "score_grade",
    "source_file",
]

# 各スタイルの列マッピング: 内部名 -> スタイル列名
COLUMN_MAP = {
    "styleA": {
        "app_date": "申込日",
        "app_id": "申込番号",
        "department": "学科",
        "selection_method": "選考方法",
        "region": "地域",
        "result": "合否",
        "score": "点数",
        "interview_flag": "面接フラグ",
        "decline_reason": "辞退理由",
    },
    "styleB": {
        "app_date": "ApplicationDate",
        "app_id": "AppID",
        "department": "Department",
        "selection_method": "SelectionMethod",
        "region": "Region",
        "result": "Result",
        "score": "Score",
        "interview_flag": "InterviewFlag",
        "decline_reason": "DeclineReason",
    },
    "styleC": {
        "app_date": "受付日",
        "app_id": "受付番号",
        "department": "専攻",
        "selection_method": "入試区分",
        "region": "出身地域",
        "result": "判定",
        "score": "得点",
        "interview_flag": "面接実施",
        "decline_reason": "不合格理由",
    },
}

# StyleB の result 変換マップ
RESULT_EN_MAP = {"Pass": "合格", "Fail": "不合格"}


def load_style(filename, style_key):
    """CSVを読み込み、内部列名に変換して返す"""
    filepath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    col_map = COLUMN_MAP[style_key]
    # 逆マッピング: スタイル列名 -> 内部名
    rename_map = {v: k for k, v in col_map.items()}
    df = df.rename(columns=rename_map)
    df["source_file"] = filename
    return df


def normalize_date(series):
    """YYYY/MM/DD または YYYY-MM-DD を YYYY-MM-DD に統一"""
    return pd.to_datetime(
        series.str.replace("/", "-"),
        format="%Y-%m-%d",
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")


def normalize_result(series):
    """合否を 合格/不合格 に統一（StyleBの Pass/Fail を変換）"""
    return series.map(lambda x: RESULT_EN_MAP.get(str(x).strip(), str(x).strip()) if pd.notna(x) else x)


def assign_score_grade(score):
    """点数区分を割り当て"""
    if score >= 80:
        return "高得点"
    elif score >= 65:
        return "中得点"
    else:
        return "低得点"


def cleanse():
    frames = []

    files = [
        ("applications_styleA.csv", "styleA"),
        ("applications_styleB.csv", "styleB"),
        ("applications_styleC.csv", "styleC"),
    ]

    for filename, style_key in files:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[NG] ファイルが見つかりません: {filepath}")
            continue
        df = load_style(filename, style_key)
        frames.append(df)
        print(f"[OK] {filename}: {len(df)} 行読み込み")

    if not frames:
        print("[FAIL] 読み込めるファイルがありません。")
        return

    df = pd.concat(frames, ignore_index=True)

    # 日付正規化
    df["app_date"] = normalize_date(df["app_date"])

    # result 正規化
    df["result"] = normalize_result(df["result"])

    # 数値変換
    df["score"] = pd.to_numeric(df["score"], errors="coerce").astype("Int64")
    df["interview_flag"] = pd.to_numeric(df["interview_flag"], errors="coerce").astype("Int64")

    # 派生列
    df["is_enrolled"] = df["result"].map(lambda x: 1 if x == "合格" else 0)
    df["score_grade"] = df["score"].apply(
        lambda x: assign_score_grade(int(x)) if pd.notna(x) else None
    )

    # decline_reason: 合格の場合は None に統一
    df["decline_reason"] = df.apply(
        lambda row: None if row["result"] == "合格" else (
            row["decline_reason"] if pd.notna(row["decline_reason"]) and str(row["decline_reason"]).strip() != "" else None
        ),
        axis=1
    )

    # CANONICAL_COLS のみ出力
    df = df[CANONICAL_COLS]

    output_path = os.path.join(OUTPUT_DIR, "cleaned_applications_202401.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[OK] クレンジング完了: {len(df)} 行 -> {output_path}")
    return df


if __name__ == "__main__":
    cleanse()
