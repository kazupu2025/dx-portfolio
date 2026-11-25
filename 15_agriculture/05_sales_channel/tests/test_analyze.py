import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path for import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze import analyze, REQUIRED_COLUMNS


@pytest.fixture
def sample_data():
    """Load sample sales channel data."""
    sample_file = Path(__file__).parent.parent / "sample_sales_channel.csv"
    return pd.read_csv(sample_file, encoding="utf-8")


@pytest.fixture
def config():
    """Default configuration."""
    return {
        "direct_sales_good": 0.30,
        "direct_sales_warning": 0.15,
    }


class TestBasicStructure:
    """Test 1: Basic analysis structure"""

    def test_analyze_returns_dict_with_required_keys(self, sample_data, config):
        result = analyze(sample_data, config)
        required_keys = [
            "df",
            "channel_df",
            "crop_df",
            "monthly_df",
            "channel_crop_df",
            "total_revenue",
            "avg_unit_price",
            "direct_sales_ratio",
            "verdict",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"


class TestVerdictLogic:
    """Test 2-4: Verdict determination (3-way logic)"""

    def test_verdict_good_when_direct_sales_ratio_gte_30(self):
        """Direct sales ratio >= 30% → good"""
        df = pd.DataFrame({
            "month": ["2024-01"] * 3,
            "crop": ["A"] * 3,
            "channel": ["直販", "直販", "市場出荷"],
            "quantity_kg": [100, 100, 50],
            "unit_price": [300, 300, 200],
            "revenue": [30000, 30000, 10000],
            "grade": ["A品"] * 3,
        })
        result = analyze(df)
        # Direct sales: 60000 / 70000 = 85.7% >= 30%
        assert result["verdict"] == "good"

    def test_verdict_warning_when_direct_sales_ratio_15_to_30(self):
        """Direct sales ratio 15% ~ 30% → warning"""
        df = pd.DataFrame({
            "month": ["2024-01"] * 4,
            "crop": ["A"] * 4,
            "channel": ["直販", "市場出荷", "市場出荷", "市場出荷"],
            "quantity_kg": [50, 100, 100, 100],
            "unit_price": [300, 200, 200, 200],
            "revenue": [15000, 20000, 20000, 20000],
            "grade": ["A品"] * 4,
        })
        result = analyze(df)
        # Direct sales: 15000 / 75000 = 20% (between 15% and 30%)
        assert result["verdict"] == "warning"

    def test_verdict_alert_when_direct_sales_ratio_lt_15(self):
        """Direct sales ratio < 15% → alert"""
        df = pd.DataFrame({
            "month": ["2024-01"] * 5,
            "crop": ["A"] * 5,
            "channel": ["直販", "市場出荷", "市場出荷", "JA出荷", "JA出荷"],
            "quantity_kg": [25, 100, 100, 100, 100],
            "unit_price": [300, 200, 200, 200, 200],
            "revenue": [7500, 20000, 20000, 20000, 20000],
            "grade": ["A品"] * 5,
        })
        result = analyze(df)
        # Direct sales: 7500 / 87500 = 8.6% < 15%
        assert result["verdict"] == "alert"


class TestChannelDataFrame:
    """Test 5: Channel-level aggregation"""

    def test_channel_df_aggregates_correctly(self, sample_data, config):
        result = analyze(sample_data, config)
        channel_df = result["channel_df"]

        # Check columns
        expected_cols = [
            "channel",
            "total_quantity",
            "total_revenue",
            "avg_unit_price",
            "num_records",
        ]
        for col in expected_cols:
            assert col in channel_df.columns, f"Missing column: {col}"

        # Check that it's sorted by revenue
        assert (
            channel_df["total_revenue"].values
            == sorted(channel_df["total_revenue"].values, reverse=True)
        ).all()


class TestCropDataFrame:
    """Test 6: Crop-level aggregation"""

    def test_crop_df_aggregates_correctly(self, sample_data, config):
        result = analyze(sample_data, config)
        crop_df = result["crop_df"]

        # Check columns
        expected_cols = ["crop", "total_quantity", "total_revenue", "avg_unit_price"]
        for col in expected_cols:
            assert col in crop_df.columns, f"Missing column: {col}"

        # Check that crops exist
        assert len(crop_df) > 0
        assert crop_df["crop"].nunique() > 0


class TestMonthlyDataFrame:
    """Test 7: Monthly trend data"""

    def test_monthly_df_has_time_series_data(self, sample_data, config):
        result = analyze(sample_data, config)
        monthly_df = result["monthly_df"]

        # Check columns
        expected_cols = ["month", "total_revenue", "total_quantity", "avg_unit_price"]
        for col in expected_cols:
            assert col in monthly_df.columns, f"Missing column: {col}"

        # Check month is datetime
        assert pd.api.types.is_datetime64_any_dtype(monthly_df["month"])

        # Check that data is sorted by month
        assert (
            monthly_df["month"].values
            == sorted(monthly_df["month"].values)
        ).all()


class TestTotalRevenuePositive:
    """Test 8: Total revenue is positive"""

    def test_total_revenue_is_positive(self, sample_data, config):
        result = analyze(sample_data, config)
        assert result["total_revenue"] > 0, "Total revenue should be positive"
        assert result["avg_unit_price"] > 0, "Average unit price should be positive"
        assert (
            0 <= result["direct_sales_ratio"] <= 1
        ), "Direct sales ratio should be between 0 and 1"
