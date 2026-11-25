"""
C-125: 顧客車検リマインダー・定期点検管理
分析ロジック: 車検期限・オイル交換推奨日の判定
"""

import pandas as pd
from datetime import timedelta
from pathlib import Path


def load_customers(csv_path):
    """
    顧客CSVを読み込む

    Parameters:
    -----------
    csv_path : str
        sample_customers.csv のパス

    Returns:
    --------
    df : DataFrame
        customer_id, name, phone, vehicle_type, last_inspection_date,
        next_inspection_due, last_oil_change, mileage, contact_status
    """
    df = pd.read_csv(csv_path)
    df['last_inspection_date'] = pd.to_datetime(df['last_inspection_date'])
    df['next_inspection_due'] = pd.to_datetime(df['next_inspection_due'])
    df['last_oil_change'] = pd.to_datetime(df['last_oil_change'])
    return df


def analyze_inspection_status(df, base_date=None):
    """
    車検期限ステータス判定

    Parameters:
    -----------
    df : DataFrame
        顧客データ
    base_date : datetime, optional
        基準日（デフォルト: 今日）

    Returns:
    --------
    df : DataFrame
        以下の列を追加：
        - days_until_inspection: 車検期限までの日数（負=期限切れ）
        - inspection_status: 'OK' / '30日以内' / '60日以内' / '期限切れ'
        - oil_change_needed: True/False（最終交換から6ヶ月超）
        - days_since_oil_change: 最終オイル交換からの日数
    """
    if base_date is None:
        base_date = pd.Timestamp.today()

    df = df.copy()

    # 車検期限までの日数
    df['days_until_inspection'] = (df['next_inspection_due'] - base_date).dt.days

    # 期限切れ判定
    df['is_overdue'] = df['days_until_inspection'] < 0

    # 車検ステータス判定
    def get_inspection_status(days):
        if days < 0:
            return '期限切れ'
        elif days <= 30:
            return '30日以内'
        elif days <= 60:
            return '60日以内'
        else:
            return 'OK'

    df['inspection_status'] = df['days_until_inspection'].apply(get_inspection_status)

    # オイル交換推奨判定（最終交換から6ヶ月超）
    df['days_since_oil_change'] = (base_date - df['last_oil_change']).dt.days
    df['oil_change_needed'] = df['days_since_oil_change'] > 180

    return df


def generate_summary_stats(df):
    """
    サマリー統計を生成

    Parameters:
    -----------
    df : DataFrame
        analyze_inspection_status() で処理済みのデータ

    Returns:
    --------
    stats : dict
        {
            'total_customers': 総顧客数,
            'overdue_count': 期限切れ件数,
            'within_30_days': 30日以内件数,
            'within_60_days': 60日以内件数,
            'oil_change_needed': オイル交換推奨件数,
            'judgment': 'good' / 'warning' / 'alert'
                good: 期限切れ=0 かつ 30日以内≤3
                warning: 30日以内≤10
                alert: 30日以内>10
        }
    """
    total = len(df)
    overdue = (df['is_overdue']).sum()
    within_30 = ((df['days_until_inspection'] >= 0) & (df['days_until_inspection'] <= 30)).sum()
    within_60 = ((df['days_until_inspection'] > 30) & (df['days_until_inspection'] <= 60)).sum()
    oil_needed = (df['oil_change_needed']).sum()

    # 判定ロジック
    if overdue == 0 and within_30 <= 3:
        judgment = 'good'
    elif within_30 <= 10:
        judgment = 'warning'
    else:
        judgment = 'alert'

    return {
        'total_customers': total,
        'overdue_count': int(overdue),
        'within_30_days': int(within_30),
        'within_60_days': int(within_60),
        'oil_change_needed': int(oil_needed),
        'judgment': judgment
    }


def get_alert_dataframe(df):
    """
    🚨 期限切れ顧客DF を返す

    Parameters:
    -----------
    df : DataFrame
        analyze_inspection_status() で処理済みのデータ

    Returns:
    --------
    alert_df : DataFrame
        期限切れ顧客のみ（customer_id, name, phone, days_until_inspection, contact_status）
    """
    alert_df = df[df['is_overdue']].copy()
    alert_df = alert_df[['customer_id', 'name', 'phone', 'days_until_inspection', 'contact_status']]
    alert_df = alert_df.sort_values('days_until_inspection')
    return alert_df


def get_urgent_dataframe(df):
    """
    ⚠️ 30日以内 顧客DF を返す（期限切れ除外）

    Parameters:
    -----------
    df : DataFrame
        analyze_inspection_status() で処理済みのデータ

    Returns:
    --------
    urgent_df : DataFrame
        30日以内（期限切れ除外）顧客
    """
    urgent_df = df[(df['days_until_inspection'] >= 0) & (df['days_until_inspection'] <= 30)].copy()
    urgent_df = urgent_df[['customer_id', 'name', 'phone', 'days_until_inspection', 'contact_status']]
    urgent_df = urgent_df.sort_values('days_until_inspection')
    return urgent_df


def get_caution_dataframe(df):
    """
    📅 60日以内 顧客DF を返す

    Parameters:
    -----------
    df : DataFrame
        analyze_inspection_status() で処理済みのデータ

    Returns:
    --------
    caution_df : DataFrame
        60日以内顧客（30日超）
    """
    caution_df = df[(df['days_until_inspection'] > 30) & (df['days_until_inspection'] <= 60)].copy()
    caution_df = caution_df[['customer_id', 'name', 'phone', 'days_until_inspection', 'contact_status']]
    caution_df = caution_df.sort_values('days_until_inspection')
    return caution_df


def get_oil_change_dataframe(df):
    """
    オイル交換推奨顧客DF を返す

    Parameters:
    -----------
    df : DataFrame
        analyze_inspection_status() で処理済みのデータ

    Returns:
    --------
    oil_df : DataFrame
        オイル交換推奨顧客（最終交換から6ヶ月超）
    """
    oil_df = df[df['oil_change_needed']].copy()
    oil_df = oil_df[['customer_id', 'name', 'phone', 'days_since_oil_change', 'mileage', 'contact_status']]
    oil_df = oil_df.sort_values('days_since_oil_change', ascending=False)
    return oil_df


def get_contact_status_summary(df):
    """
    連絡ステータス別サマリーDF を返す

    Parameters:
    -----------
    df : DataFrame
        analyze_inspection_status() で処理済みのデータ

    Returns:
    --------
    summary_df : DataFrame
        contact_status ごとの顧客数
    """
    summary_df = df.groupby('contact_status').size().reset_index(name='count')
    summary_df = summary_df.sort_values('count', ascending=False)
    return summary_df


def get_vehicle_type_summary(df):
    """
    車種別アラート集計DF を返す

    Parameters:
    -----------
    df : DataFrame
        analyze_inspection_status() で処理済みのデータ

    Returns:
    --------
    summary_df : DataFrame
        vehicle_type ごとの（期限切れ + 30日以内）件数
    """
    alert_or_urgent = df[df['days_until_inspection'] <= 30].copy()
    summary_df = alert_or_urgent.groupby('vehicle_type').size().reset_index(name='alert_count')
    summary_df = summary_df.sort_values('alert_count', ascending=False)
    return summary_df


if __name__ == '__main__':
    # 使用例
    csv_path = Path(__file__).parent / 'sample_customers.csv'
    df = load_customers(str(csv_path))

    df = analyze_inspection_status(df)
    stats = generate_summary_stats(df)

    print("\n=== Summary Stats ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n=== Alert (Overdue) ===")
    print(get_alert_dataframe(df))

    print("\n=== Urgent (Within 30 days) ===")
    print(get_urgent_dataframe(df))

    print("\n=== Caution (60 days) ===")
    print(get_caution_dataframe(df))

    print("\n=== Oil Change Needed ===")
    print(get_oil_change_dataframe(df))
