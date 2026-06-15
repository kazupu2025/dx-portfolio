"""
B-09 クレンジング出力テスト (14テスト)
Run: cd 02_manufacturing/02_equipment_log && pytest tests/ -v
"""
import pytest
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT  = BASE / "output"
CSV  = OUT / "cleaned_sensor_202401.csv"
ANOMALY_CSV = OUT / "anomaly_sensor_202401.csv"

KEEP_COLS = ["timestamp", "equipment_id", "equipment_name",
             "temperature", "vibration", "pressure", "rpm",
             "op_status", "is_operating", "source_file"]

@pytest.fixture(scope="module")
def df():
    assert CSV.exists(), f"{CSV} が存在しない"
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV.exists()


def test_row_count(df):
    assert 3000 <= len(df) <= 5000, f"行数: {len(df)}"


def test_required_columns(df):
    missing = [c for c in KEEP_COLS if c not in df.columns]
    assert missing == [], f"不足列: {missing}"


def test_timestamp_no_null(df):
    assert df["timestamp"].isna().sum() == 0


def test_equipment_id_no_null(df):
    assert df["equipment_id"].isna().sum() == 0


def test_temperature_no_null(df):
    assert df["temperature"].isna().sum() == 0


def test_vibration_no_null(df):
    assert df["vibration"].isna().sum() == 0


def test_pressure_no_null(df):
    assert df["pressure"].isna().sum() == 0


def test_rpm_no_null(df):
    assert df["rpm"].isna().sum() == 0


def test_temperature_nonneg(df):
    assert (df["temperature"] >= 0).all()


def test_vibration_nonneg(df):
    assert (df["vibration"] >= 0).all()


def test_pressure_nonneg(df):
    assert (df["pressure"] >= 0).all()


def test_rpm_nonneg(df):
    assert (df["rpm"] >= 0).all()


def test_op_status_values(df):
    assert df["op_status"].isin([0, 1]).all()


def test_equipment_count(df):
    assert df["equipment_id"].nunique() == 5


def test_timestamp_parseable(df):
    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    assert ts.isna().sum() == 0


def test_timestamp_range(df):
    ts = pd.to_datetime(df["timestamp"])
    assert ((ts.dt.year == 2024) & (ts.dt.month == 1)).all()


def test_is_operating_exists(df):
    assert "is_operating" in df.columns


def test_anomaly_csv_exists():
    assert ANOMALY_CSV.exists(), f"{ANOMALY_CSV} が存在しない"
