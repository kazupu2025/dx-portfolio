"""
C-122 資材コスト・発注管理 テストスイート

8つのテストケース：
- 基本構造（データ読み込み・カテゴリ集計）
- 判定3段階（good/warning/alert）
- カテゴリDF形式
- 月次DF形式
- 総コスト正値
- 仕入先DF形式
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze import MaterialCostAnalyzer, run_analysis


@pytest.fixture
def analyzer():
    """アナライザーインスタンスを作成"""
    analyzer = MaterialCostAnalyzer(config_file="config.yml")
    analyzer.load_data("sample_material.csv")
    return analyzer


@pytest.fixture
def analyzed():
    """分析済みアナライザーを作成"""
    analyzer = run_analysis(
        csv_file="sample_material.csv",
        config_file="config.yml"
    )
    return analyzer


class TestBasicStructure:
    """基本構造テスト"""

    def test_data_loading(self, analyzer):
        """データ読み込みテスト"""
        assert analyzer.df is not None
        assert len(analyzer.df) >= 45  # sample_material.csv は 45+ 行
        assert "total_cost" in analyzer.df.columns
        assert "category" in analyzer.df.columns

    def test_category_aggregation(self, analyzer):
        """カテゴリ別集計テスト"""
        df_cat = analyzer.analyze_by_category()
        assert df_cat is not None
        assert len(df_cat) > 0
        # カテゴリは5種類
        assert len(df_cat) == 5


class TestVerdictLevels:
    """判定3段階テスト"""

    def test_verdict_good(self, analyzed):
        """good判定テスト"""
        verdict = analyzed.verdict
        assert verdict in ["good", "warning", "alert"]

    def test_verdict_consistency(self, analyzed):
        """判定の一貫性テスト"""
        verdict1 = analyzed.judge_verdict()
        verdict2 = analyzed.verdict
        assert verdict1 == verdict2

    def test_verdict_by_variance(self, analyzed):
        """変動率に基づく判定テスト"""
        analyzed.analyze_by_month()
        variances = analyzed.df_by_month["cost_variance_rate"].dropna().abs()
        max_var = variances.max() if len(variances) > 0 else 0

        if max_var <= 10:
            expected = "good"
        elif max_var <= 20:
            expected = "warning"
        else:
            expected = "alert"

        assert analyzed.verdict == expected


class TestCategoryDataFrame:
    """カテゴリDataFrameテスト"""

    def test_category_df_structure(self, analyzed):
        """カテゴリDF構造テスト"""
        df = analyzed.df_by_category
        assert isinstance(df, pd.DataFrame)
        expected_cols = ["total_cost", "avg_cost", "item_count", "total_quantity"]
        assert list(df.columns) == expected_cols

    def test_category_df_sorted(self, analyzed):
        """カテゴリDFがコスト降順ソート済みテスト"""
        df = analyzed.df_by_category
        assert df["total_cost"].is_monotonic_decreasing


class TestMonthlyDataFrame:
    """月次DataFrameテスト"""

    def test_monthly_df_structure(self, analyzed):
        """月次DF構造テスト"""
        df = analyzed.df_by_month
        assert isinstance(df, pd.DataFrame)
        expected_cols = [
            "year_month",
            "monthly_cost",
            "monthly_quantity",
            "cost_variance_rate",
        ]
        assert list(df.columns) == expected_cols

    def test_monthly_df_sorted(self, analyzed):
        """月次DFが日付順ソート済みテスト"""
        df = analyzed.df_by_month
        years = [str(x) for x in df["year_month"]]
        assert years == sorted(years)


class TestTotalCostPositive:
    """総コスト正値テスト"""

    def test_total_cost_positive(self, analyzed):
        """総コスト > 0 テスト"""
        stats = analyzed.get_summary_stats()
        assert stats["total_cost"] > 0

    def test_category_costs_positive(self, analyzed):
        """各カテゴリコスト > 0 テスト"""
        df = analyzed.df_by_category
        assert (df["total_cost"] > 0).all()

    def test_monthly_costs_positive(self, analyzed):
        """月次コスト > 0 テスト"""
        df = analyzed.df_by_month
        assert (df["monthly_cost"] > 0).all()


class TestSupplierDataFrame:
    """仕入先DataFrameテスト"""

    def test_supplier_df_structure(self, analyzed):
        """仕入先DF構造テスト"""
        df = analyzed.df_by_supplier
        assert isinstance(df, pd.DataFrame)
        expected_cols = ["total_cost", "avg_cost", "order_count", "total_quantity"]
        assert list(df.columns) == expected_cols

    def test_supplier_df_sorted(self, analyzed):
        """仕入先DFがコスト降順ソート済みテスト"""
        df = analyzed.df_by_supplier
        assert df["total_cost"].is_monotonic_decreasing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
