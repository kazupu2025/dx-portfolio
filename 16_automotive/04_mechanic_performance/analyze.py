"""
C-126 整備士別生産性・売上分析
整備士の案件数・売上・顧客満足度・時給効率を分析する
"""
import pandas as pd
import numpy as np
from pathlib import Path

# ── 設定 ──────────────────────────────────────────
THRESHOLD_GOOD = 6000          # 時給効率の優良基準
THRESHOLD_WARNING = 4000        # 時給効率の警告基準

def load_data(csv_path: str = "sample_mechanic.csv") -> pd.DataFrame:
    """CSVファイルを読み込む"""
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

def analyze_mechanic_performance(df: pd.DataFrame) -> dict:
    """整備士別パフォーマンス分析"""
    mechanic_stats = []

    for mechanic_id in df['mechanic_id'].unique():
        mechanic_df = df[df['mechanic_id'] == mechanic_id]

        job_count = len(mechanic_df)
        total_revenue = mechanic_df['labor_revenue'].sum()
        avg_rating = mechanic_df['customer_rating'].mean()
        total_hours = mechanic_df['labor_hours'].sum()
        avg_hourly_rate = total_revenue / total_hours if total_hours > 0 else 0

        # 判定ロジック
        if avg_hourly_rate >= THRESHOLD_GOOD:
            judgment = "good"
        elif avg_hourly_rate >= THRESHOLD_WARNING:
            judgment = "warning"
        else:
            judgment = "alert"

        mechanic_stats.append({
            'mechanic_id': mechanic_id,
            'mechanic_name': mechanic_df['mechanic_name'].iloc[0],
            'job_count': job_count,
            'total_revenue': total_revenue,
            'avg_rating': round(avg_rating, 2),
            'total_hours': total_hours,
            'avg_hourly_rate': round(avg_hourly_rate, 2),
            'judgment': judgment
        })

    mechanic_df_result = pd.DataFrame(mechanic_stats)
    mechanic_df_result = mechanic_df_result.sort_values('total_revenue', ascending=False)

    return {
        'mechanic_df': mechanic_df_result,
        'mechanic_list': mechanic_stats
    }

def analyze_service_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """サービス種別ごとの案件数・売上集計"""
    service_stats = []

    for service in df['service_type'].unique():
        service_df = df[df['service_type'] == service]

        job_count = len(service_df)
        total_revenue = service_df['labor_revenue'].sum()
        avg_rating = service_df['customer_rating'].mean()

        service_stats.append({
            'service_type': service,
            'job_count': job_count,
            'total_revenue': total_revenue,
            'avg_rating': round(avg_rating, 2)
        })

    service_df_result = pd.DataFrame(service_stats)
    service_df_result = service_df_result.sort_values('job_count', ascending=False)

    return service_df_result

def analyze_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """月別トレンド分析"""
    df['year_month'] = df['date'].dt.to_period('M')

    monthly_stats = []

    for period in sorted(df['year_month'].unique()):
        period_df = df[df['year_month'] == period]

        total_revenue = period_df['labor_revenue'].sum()
        job_count = len(period_df)
        avg_rating = period_df['customer_rating'].mean()
        total_hours = period_df['labor_hours'].sum()
        avg_hourly_rate = total_revenue / total_hours if total_hours > 0 else 0

        monthly_stats.append({
            'month': str(period),
            'job_count': job_count,
            'total_revenue': total_revenue,
            'avg_rating': round(avg_rating, 2),
            'total_hours': total_hours,
            'avg_hourly_rate': round(avg_hourly_rate, 2)
        })

    monthly_df = pd.DataFrame(monthly_stats)
    return monthly_df

def calculate_summary(df: pd.DataFrame) -> dict:
    """全体サマリー統計"""
    total_revenue = df['labor_revenue'].sum()
    total_hours = df['labor_hours'].sum()
    avg_rating = df['customer_rating'].mean()
    avg_hourly_rate = total_revenue / total_hours if total_hours > 0 else 0
    job_count = len(df)

    # 全体判定
    if avg_hourly_rate >= THRESHOLD_GOOD:
        overall_judgment = "good"
    elif avg_hourly_rate >= THRESHOLD_WARNING:
        overall_judgment = "warning"
    else:
        overall_judgment = "alert"

    return {
        'total_revenue': total_revenue,
        'avg_rating': round(avg_rating, 2),
        'avg_hourly_rate': round(avg_hourly_rate, 2),
        'job_count': job_count,
        'overall_judgment': overall_judgment
    }

def generate_report(
    summary: dict,
    mechanic_stats: pd.DataFrame,
    service_stats: pd.DataFrame,
    monthly_stats: pd.DataFrame
) -> str:
    """分析レポートをMarkdown形式で生成"""

    report = f"""# 整備士別生産性・売上分析レポート

## 実行日時
{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 全体KPI

| 指標 | 値 |
|------|-----|
| **総売上** | ¥{summary['total_revenue']:,.0f} |
| **平均顧客評価** | {summary['avg_rating']}/5 |
| **平均時給効率** | ¥{summary['avg_hourly_rate']:,.0f}/時間 |
| **総案件数** | {summary['job_count']} 件 |
| **全体判定** | **{summary['overall_judgment'].upper()}** |

---

## 整備士別パフォーマンス

"""

    report += "| 整備士名 | 案件数 | 総売上 | 平均評価 | 稼働時間 | 時給効率 | 判定 |\n"
    report += "|--------|--------|--------|---------|---------|---------|--------|\n"

    for _, row in mechanic_stats.iterrows():
        report += f"| {row['mechanic_name']} | {row['job_count']} | ¥{row['total_revenue']:,.0f} | {row['avg_rating']}/5 | {row['total_hours']:.1f}h | ¥{row['avg_hourly_rate']:,.0f} | {row['judgment'].upper()} |\n"

    report += "\n---\n\n## サービス種別別集計\n\n"
    report += "| サービス種別 | 案件数 | 総売上 | 平均評価 |\n"
    report += "|-----------|--------|--------|----------|\n"

    for _, row in service_stats.iterrows():
        report += f"| {row['service_type']} | {row['job_count']} | ¥{row['total_revenue']:,.0f} | {row['avg_rating']}/5 |\n"

    report += "\n---\n\n## 月別トレンド\n\n"
    report += "| 月 | 案件数 | 総売上 | 平均評価 | 稼働時間 | 平均時給 |\n"
    report += "|-----|--------|--------|---------|---------|----------|\n"

    for _, row in monthly_stats.iterrows():
        report += f"| {row['month']} | {row['job_count']} | ¥{row['total_revenue']:,.0f} | {row['avg_rating']}/5 | {row['total_hours']:.1f}h | ¥{row['avg_hourly_rate']:,.0f} |\n"

    report += "\n---\n\n## ビジネスインサイト\n\n"

    # トップ整備士
    top_mechanic = mechanic_stats.iloc[0]
    report += f"**【トップ整備士】** {top_mechanic['mechanic_name']} - 総売上¥{top_mechanic['total_revenue']:,.0f}（{top_mechanic['job_count']}件、評価{top_mechanic['avg_rating']}/5）\n\n"

    # ボトム整備士
    bottom_mechanic = mechanic_stats.iloc[-1]
    report += f"**【要改善】** {bottom_mechanic['mechanic_name']} - 時給効率¥{bottom_mechanic['avg_hourly_rate']:,.0f}（基準未達、改善が必要）\n\n"

    # 人気サービス
    top_service = service_stats.iloc[0]
    report += f"**【人気サービス】** {top_service['service_type']} - {top_service['job_count']}件（売上¥{top_service['total_revenue']:,.0f}）\n\n"

    # 評価の分析
    high_rating_count = (mechanic_stats['avg_rating'] >= 4.5).sum()
    report += f"**【顧客満足度】** 高評価（4.5以上）の整備士: {high_rating_count}名\n\n"

    return report

def main():
    """メイン実行"""
    # データ読み込み
    df = load_data()

    # 各種分析実行
    summary = calculate_summary(df)
    mechanic_results = analyze_mechanic_performance(df)
    mechanic_stats = mechanic_results['mechanic_df']
    service_stats = analyze_service_breakdown(df)
    monthly_stats = analyze_monthly_trend(df)

    # レポート生成
    report = generate_report(summary, mechanic_stats, service_stats, monthly_stats)

    # 出力
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    report_path = output_dir / "analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("Report generated: " + str(report_path))

    # 整備士DF、サービスDF、月別DFを返すようにして、テスト用に統計情報を保存
    stats_output = {
        'summary': summary,
        'mechanic_stats': mechanic_stats.to_dict('records'),
        'service_stats': service_stats.to_dict('records'),
        'monthly_stats': monthly_stats.to_dict('records')
    }

    return stats_output, mechanic_stats, service_stats, monthly_stats

if __name__ == "__main__":
    main()
