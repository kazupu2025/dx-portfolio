"""
B-09 設備稼働ログ クレンジング
Usage: cd 02_manufacturing/02_equipment_log && python output/cleanse.py
"""
import sys
import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
OUT  = Path(__file__).parent
LOG  = []

COLUMN_MAP = {
    "日時":        "timestamp",
    "Timestamp":   "timestamp",
    "計測時刻":    "timestamp",
    "設備ID":      "equipment_id",
    "EquipmentID": "equipment_id",
    "機番":        "equipment_id",
    "設備名":      "equipment_name",
    "EquipmentName": "equipment_name",
    "機器名称":    "equipment_name",
    "温度(°C)":   "temperature",
    "Temperature": "temperature",
    "温度":        "temperature",
    "振動(mm/s)": "vibration",
    "Vibration":   "vibration",
    "振動値":      "vibration",
    "圧力(MPa)":  "pressure",
    "Pressure":    "pressure",
    "圧力値":      "pressure",
    "回転数(rpm)": "rpm",
    "RPM":         "rpm",
    "回転数":      "rpm",
    "稼働状態":    "op_status",
    "OperationStatus": "op_status",
    "稼働フラグ":  "op_status",
}

KEEP_COLS = {"timestamp", "equipment_id", "equipment_name",
             "temperature", "vibration", "pressure", "rpm",
             "op_status", "is_operating", "source_file"}

SENSOR_COLS = ["temperature", "vibration", "pressure", "rpm"]


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG.append(line)


def load_csv(path: Path) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            df.columns = [COLUMN_MAP.get(c, c) for c in df.columns]
            df["source_file"] = path.name
            log(f"  Loaded {path.name}: {len(df)} rows (enc={enc})")
            return df
        except Exception:
            continue
    raise RuntimeError(f"Failed to load {path}")


def normalize_timestamp(series: pd.Series) -> pd.Series:
    def parse(v):
        if pd.isna(v):
            return pd.NaT
        v = str(v).strip()
        for fmt in ["%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                return datetime.strptime(v, fmt).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                continue
        return pd.NaT
    return series.apply(parse)


def fill_rolling_median(df: pd.DataFrame, col: str, window: int = 24) -> pd.Series:
    s = df[col].copy()
    for idx in s[s.isna()].index:
        loc = df.index.get_loc(idx)
        window_data = s.iloc[max(0, loc - window): loc + window + 1]
        median = window_data.median()
        s.iloc[loc] = median if not pd.isna(median) else 0.0
    return s


def main():
    log("=== B-09 クレンジング開始 ===")

    with open(BASE / "config.yml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    csv_files = sorted(BASE.glob("*.csv"))
    if not csv_files:
        log("ERROR: CSVファイルが見つかりません")
        sys.exit(1)

    frames = []
    for f in csv_files:
        try:
            frames.append(load_csv(f))
        except Exception as e:
            log(f"  WARN: {f.name} スキップ ({e})")

    if not frames:
        log("ERROR: 有効なデータがありません")
        sys.exit(1)

    df = pd.concat(frames, ignore_index=True)
    log(f"結合後: {len(df)} rows")

    # タイムスタンプ正規化
    df["timestamp"] = normalize_timestamp(df["timestamp"])
    ts_na = df["timestamp"].isna().sum()
    if ts_na:
        log(f"  WARN: timestamp NaN {ts_na} 件を除去")
        df = df.dropna(subset=["timestamp"])

    # op_status 正規化
    df["op_status"] = pd.to_numeric(df["op_status"], errors="coerce").fillna(0).astype(int).clip(0, 1)

    # センサー列を数値化
    for col in SENSOR_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 停止中(op_status=0)はセンサー値を0にする
    mask_stopped = df["op_status"] == 0
    for col in SENSOR_COLS:
        if col in df.columns:
            df.loc[mask_stopped, col] = 0.0

    # 稼働中レコードの欠損をローリング中央値で補完
    mask_operating = df["op_status"] == 1
    df_op = df[mask_operating].copy()
    for eq_id, grp in df_op.groupby("equipment_id"):
        for col in SENSOR_COLS:
            if grp[col].isna().any():
                df_op.loc[grp.index, col] = fill_rolling_median(grp, col)
    df.update(df_op)

    # 残存NaN → 0で補完
    for col in SENSOR_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)

    # 負の値をclip
    for col in SENSOR_COLS:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    # 派生列
    df["is_operating"] = (df["op_status"] == 1).astype(int)

    # 不要列除去
    extra = [c for c in df.columns if c not in KEEP_COLS]
    if extra:
        log(f"  不要列除去: {extra}")
        df = df.drop(columns=extra)

    # ソート
    df = df.sort_values(["equipment_id", "timestamp"]).reset_index(drop=True)

    out_path = OUT / "cleaned_sensor_202401.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"=== 出力完了: {out_path} ({len(df)} rows) ===")

    with open(OUT / "cleanse.log", "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))


if __name__ == "__main__":
    main()
