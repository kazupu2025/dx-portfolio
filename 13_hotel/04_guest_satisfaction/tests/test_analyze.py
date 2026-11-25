# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_MD = os.path.join(OUTPUT_DIR, "analysis_report.md")
JSON_PATH = os.path.join(OUTPUT_DIR, "result_analysis.json")


@pytest.fixture(scope="module")
def result_json():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_report_exists():
    assert os.path.exists(REPORT_MD), "analysis_report.md not found"


def test_json_result_exists():
    assert os.path.exists(JSON_PATH), "result_analysis.json not found"


def test_avg_overall_score_range(result_json):
    score = result_json["avg_overall_score"]
    assert 1.0 <= score <= 5.0, f"overall_score {score} out of range [1.0, 5.0]"


def test_judgment_good_when_score_gte_4(result_json):
    if result_json["avg_overall_score"] >= 4.0:
        assert result_json["overall_judgment"] == "good", "Judgment should be 'good' when score >= 4.0"


def test_judgment_warning_when_score_gte_3_5(result_json):
    if 3.5 <= result_json["avg_overall_score"] < 4.0:
        assert result_json["overall_judgment"] == "warning", "Judgment should be 'warning' when 3.5 <= score < 4.0"


def test_judgment_alert_when_score_lt_3_5(result_json):
    if result_json["avg_overall_score"] < 3.5:
        assert result_json["overall_judgment"] == "alert", "Judgment should be 'alert' when score < 3.5"


def test_repeat_rate_in_range(result_json):
    repeat_rate = result_json["repeat_rate"]
    assert 0.0 <= repeat_rate <= 1.0, f"repeat_rate {repeat_rate} out of range [0.0, 1.0]"


def test_channels_in_result(result_json):
    assert "channels" in result_json
    channels = result_json["channels"]
    assert len(channels) > 0, "No channels found in result"
    expected_channels = {"OTA", "直接予約", "旅行代理店", "法人"}
    assert set(channels).issubset(expected_channels), f"Unexpected channels: {channels}"


def test_room_types_in_result(result_json):
    assert "room_types" in result_json
    room_types = result_json["room_types"]
    assert len(room_types) > 0, "No room types found in result"
    expected_types = {"シングル", "ダブル", "ツイン", "スイート"}
    assert set(room_types).issubset(expected_types), f"Unexpected room types: {room_types}"


def test_report_contains_summary():
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        content = f.read()
    assert "総合サマリー" in content, "Report should contain '総合サマリー' section"


def test_report_contains_score_details():
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        content = f.read()
    assert "スコア別詳細" in content, "Report should contain 'スコア別詳細' section"


def test_report_contains_channel_analysis():
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        content = f.read()
    assert "チャネル別集計" in content, "Report should contain 'チャネル別集計' section"


def test_report_contains_room_type_analysis():
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        content = f.read()
    assert "客室タイプ別集計" in content, "Report should contain '客室タイプ別集計' section"


def test_score_components_in_range(result_json):
    scores = ["avg_room_score", "avg_food_score", "avg_service_score"]
    for score_key in scores:
        score = result_json[score_key]
        assert 1.0 <= score <= 5.0, f"{score_key} {score} out of range [1.0, 5.0]"
