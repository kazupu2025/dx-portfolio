"""
C-122 資材コスト・発注管理 分析モジュール

カテゴリ別・プロジェクト別コスト集計、月次推移、単価変動、仕入先別発注を分析。
月次コスト変動率で good/warning/alert の判定を実施。
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import yaml


class MaterialCostAnalyzer:
    """資材コスト分析クラス"""

    def __init__(self, config_file: str = "config.yml"):
        """
        初期化

        Args:
            config_file: 設定ファイルパス
        """
        self.config = self._load_config(config_file)
        self.df = None
        self.df_by_category = None
        self.df_by_month = None
        self.df_by_project = None
        self.df_by_supplier = None
        self.verdict = "good"

    def _load_config(self, config_file: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_file, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_data(self, csv_file: str) -> pd.DataFrame:
        """
        CSVデータを読み込む

        Args:
            csv_file: CSVファイルパス

        Returns:
            読み込んだデータフレーム
        """
        self.df = pd.read_csv(csv_file)
        self.df["date"] = pd.to_datetime(self.df["date"])
        return self.df

    def analyze_by_category(self) -> pd.DataFrame:
        """
        カテゴリ別コスト集計

        Returns:
            カテゴリ別集計DataFrame
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        self.df_by_category = (
            self.df.groupby("category")
            .agg(
                {
                    "total_cost": ["sum", "mean", "count"],
                    "quantity": "sum",
                }
            )
            .round(0)
        )
        self.df_by_category.columns = [
            "total_cost",
            "avg_cost",
            "item_count",
            "total_quantity",
        ]
        self.df_by_category = self.df_by_category.sort_values(
            "total_cost", ascending=False
        )
        return self.df_by_category

    def analyze_by_month(self) -> pd.DataFrame:
        """
        月次コスト推移集計

        Returns:
            月次集計DataFrame
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        self.df["year_month"] = self.df["date"].dt.to_period("M")
        df_monthly = (
            self.df.groupby("year_month")
            .agg({"total_cost": "sum", "quantity": "sum"})
            .reset_index()
        )
        df_monthly.columns = ["year_month", "monthly_cost", "monthly_quantity"]
        df_monthly = df_monthly.sort_values("year_month")

        # 月次変動率を計算
        df_monthly["cost_variance_rate"] = (
            df_monthly["monthly_cost"].pct_change() * 100
        ).round(1)
        self.df_by_month = df_monthly
        return self.df_by_month

    def analyze_by_project(self) -> pd.DataFrame:
        """
        プロジェクト別コスト集計

        Returns:
            プロジェクト別集計DataFrame
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        self.df_by_project = (
            self.df.groupby("project_id")
            .agg(
                {
                    "total_cost": ["sum", "mean"],
                    "quantity": "sum",
                    "material_name": "count",
                }
            )
            .round(0)
        )
        self.df_by_project.columns = [
            "total_cost",
            "avg_cost",
            "total_quantity",
            "item_count",
        ]
        self.df_by_project = self.df_by_project.sort_values(
            "total_cost", ascending=False
        )
        return self.df_by_project

    def analyze_by_supplier(self) -> pd.DataFrame:
        """
        仕入先別発注金額集計

        Returns:
            仕入先別集計DataFrame
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        self.df_by_supplier = (
            self.df.groupby("supplier")
            .agg(
                {
                    "total_cost": ["sum", "mean", "count"],
                    "quantity": "sum",
                }
            )
            .round(0)
        )
        self.df_by_supplier.columns = [
            "total_cost",
            "avg_cost",
            "order_count",
            "total_quantity",
        ]
        self.df_by_supplier = self.df_by_supplier.sort_values(
            "total_cost", ascending=False
        )
        return self.df_by_supplier

    def analyze_unit_price_variance(self) -> pd.DataFrame:
        """
        単価変動率分析（材料別・月別）

        Returns:
            単価変動分析DataFrame
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        self.df["year_month"] = self.df["date"].dt.to_period("M")
        df_variance = self.df.groupby(
            ["material_name", "year_month"]
        ).agg({"unit_price": "mean"}).reset_index()
        df_variance = df_variance.sort_values(["material_name", "year_month"])

        # 前月比変動率を計算
        df_variance["price_variance_rate"] = (
            df_variance.groupby("material_name")["unit_price"].pct_change() * 100
        ).round(1)
        return df_variance

    def judge_verdict(self) -> str:
        """
        月次コスト変動率に基づいて判定を実施

        Returns:
            'good'/'warning'/'alert'
        """
        if self.df_by_month is None:
            self.analyze_by_month()

        # NaN を除外した変動率を取得
        variances = self.df_by_month["cost_variance_rate"].dropna().abs()

        if len(variances) == 0:
            self.verdict = "good"
            return self.verdict

        max_variance = variances.max()
        threshold_good = (
            self.config.get("cost_variance_threshold_good", 0.10) * 100
        )
        threshold_warning = (
            self.config.get("cost_variance_threshold_warning", 0.20) * 100
        )

        if max_variance <= threshold_good:
            self.verdict = "good"
        elif max_variance <= threshold_warning:
            self.verdict = "warning"
        else:
            self.verdict = "alert"

        return self.verdict

    def get_summary_stats(self) -> dict:
        """
        サマリー統計情報を取得

        Returns:
            統計情報dict
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        total_cost = self.df["total_cost"].sum()
        item_count = len(self.df)
        category_with_max_cost = self.df.groupby("category")[
            "total_cost"
        ].sum().idxmax()
        max_cost = self.df.groupby("category")["total_cost"].sum().max()

        return {
            "total_cost": total_cost,
            "item_count": item_count,
            "category_with_max_cost": category_with_max_cost,
            "max_cost": max_cost,
            "verdict": self.judge_verdict(),
        }

    def to_dict(self) -> dict:
        """
        分析結果を辞書形式で取得

        Returns:
            分析結果dict
        """
        return {
            "summary": self.get_summary_stats(),
            "by_category": (
                self.df_by_category.to_dict() if self.df_by_category is not None
                else {}
            ),
            "by_month": (
                self.df_by_month.to_dict() if self.df_by_month is not None
                else {}
            ),
            "by_project": (
                self.df_by_project.to_dict() if self.df_by_project is not None
                else {}
            ),
            "by_supplier": (
                self.df_by_supplier.to_dict() if self.df_by_supplier is not None
                else {}
            ),
        }


def run_analysis(csv_file: str = "sample_material.csv",
                 config_file: str = "config.yml") -> MaterialCostAnalyzer:
    """
    分析を実行して結果を返す

    Args:
        csv_file: CSVファイルパス
        config_file: 設定ファイルパス

    Returns:
        MaterialCostAnalyzer インスタンス
    """
    analyzer = MaterialCostAnalyzer(config_file)
    analyzer.load_data(csv_file)
    analyzer.analyze_by_category()
    analyzer.analyze_by_month()
    analyzer.analyze_by_project()
    analyzer.analyze_by_supplier()
    analyzer.judge_verdict()
    return analyzer


if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    analyzer = run_analysis()
    print("=" * 60)
    print("C-122 資材コスト・発注管理 分析結果")
    print("=" * 60)

    stats = analyzer.get_summary_stats()
    print(f"\n【サマリー】")
    print(f"  総発注額: {stats['total_cost']:,.0f}円")
    print(f"  品目数: {stats['item_count']} 件")
    print(f"  最多カテゴリ: {stats['category_with_max_cost']} ({stats['max_cost']:,.0f}円)")
    print(f"  判定: {stats['verdict'].upper()}")

    print(f"\n【カテゴリ別コスト】")
    print(analyzer.df_by_category)

    print(f"\n【月次コスト推移】")
    print(analyzer.df_by_month)

    print(f"\n【プロジェクト別コスト】")
    print(analyzer.df_by_project)

    print(f"\n【仕入先別発注額】")
    print(analyzer.df_by_supplier)
