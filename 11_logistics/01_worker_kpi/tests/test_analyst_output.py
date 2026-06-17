# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
WORKER_CSV = os.path.join(OUTPUT_DIR, "worker_summary_202401.csv")


def test_report_exists():
    assert os.path.exists(REPORT_PATH)


def test_worker_csv_exists():
    assert os.path.exists(WORKER_CSV)


@pytest.fixture(scope="module")
def worker_df():
    assert os.path.exists(WORKER_CSV)
    return pd.read_csv(WORKER_CSV, encoding="utf-8-sig")


@pytest.fixture(scope="module")
def report_text():
    assert os.path.exists(REPORT_PATH)
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_report_has_worker_section(report_text):
    assert "Worker KPI Summary" in report_text


def test_report_has_zone_section(report_text):
    assert "Zone Analysis" in report_text


def test_report_has_task_section(report_text):
    assert "Task Type Analysis" in report_text


def test_worker_summary_columns(worker_df):
    for col in ["worker_id", "avg_throughput", "avg_error_rate", "kpi_flag"]:
        assert col in worker_df.columns


def test_worker_summary_count(worker_df):
    assert len(worker_df) >= 15


def test_worker_kpi_flag_valid(worker_df):
    valid_flags = {"優秀", "標準"}
    actual = set(worker_df["kpi_flag"].dropna().unique())
    assert actual.issubset(valid_flags)
