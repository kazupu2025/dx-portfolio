"""C-92 analyze.py TDD — 8テスト（フォールバック動作確認）。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest

# APIキーなし環境でテスト → ルールベース分類が動くことを確認
sys.path.insert(0, str(Path(__file__).parent.parent))
import os
os.environ.pop("ANTHROPIC_API_KEY", None)  # テスト時はAPIキーを無効化
import analyze


def _make_df(texts):
    return pd.DataFrame({"description": texts})


def test_dimension_classification():
    """寸法系キーワード → 寸法系に分類"""
    df = _make_df(["外径が0.2mm大きい"])
    result = analyze.run_analysis(df)
    assert result["result_df"]["category"].iloc[0] == "寸法系"


def test_appearance_classification():
    """外観系キーワード → 外観系に分類"""
    df = _make_df(["表面に傷がある"])
    result = analyze.run_analysis(df)
    assert result["result_df"]["category"].iloc[0] == "外観系"


def test_function_classification():
    """機能系キーワード → 機能系に分類"""
    df = _make_df(["強度が不足している"])
    result = analyze.run_analysis(df)
    assert result["result_df"]["category"].iloc[0] == "機能系"


def test_material_classification():
    """材料系キーワード → 材料系に分類"""
    df = _make_df(["材料の硬度が低い"])
    result = analyze.run_analysis(df)
    assert result["result_df"]["category"].iloc[0] == "材料系"


def test_n_items():
    """n_items が正しく集計される"""
    df = _make_df(["傷あり", "寸法外れ", "材料不良"])
    result = analyze.run_analysis(df)
    assert result["n_items"] == 3


def test_top_category():
    """最多カテゴリが正しく抽出される"""
    df = _make_df(["傷", "外観不良", "色ムラ", "寸法外れ"])
    result = analyze.run_analysis(df)
    assert result["top_category"] == "外観系"


def test_fallback_verdict():
    """APIキーなし → フォールバック → verdict=warning"""
    df = _make_df(["傷あり"])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["llm_used"] == False


def test_missing_description_column_raises():
    """description列がない場合は ValueError を発生"""
    df = pd.DataFrame({"text": ["傷あり"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
