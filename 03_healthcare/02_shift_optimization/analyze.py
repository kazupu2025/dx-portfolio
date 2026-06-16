"""
analyze.py
cleaned_shift_202401.csv を分析し、
output/analysis_report.md と output/shift_summary_202401.csv を出力する。
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_shift_202401.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "shift_summary_202401.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    return df


# ── 分析関数 ────────────────────────────────────────────────────────────

def analyze_role_shift(df: pd.DataFrame) -> pd.DataFrame:
    """役職別シフト分布（夜勤比率、休み希望率）"""
    g = df.groupby("role")["preferred_shift"].value_counts(normalize=True).unstack(fill_value=0)
    g["夜勤比率"] = g.get("夜勤", 0)
    g["休み希望率"] = g.get("休み", 0)
    return g


def analyze_staff_night(df: pd.DataFrame) -> pd.DataFrame:
    """スタッフ別夜勤希望回数"""
    g = (
        df[df["preferred_shift"] == "夜勤"]
        .groupby(["staff_id", "name", "role"])
        .size()
        .reset_index(name="night_count")
        .sort_values("night_count", ascending=False)
    )
    return g


def analyze_employment_shift(df: pd.DataFrame) -> pd.DataFrame:
    """雇用形態別シフト希望パターン"""
    g = df.groupby("employment_type")["preferred_shift"].value_counts(normalize=True).unstack(fill_value=0)
    return g


def analyze_facility_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """施設別の希望充足率分析（夜勤・日勤の充足）"""
    # source_file から施設名を推定
    df = df.copy()
    df["facility"] = df["source_file"].str.extract(r"0\d_(.+)_shift")
    g = df.groupby(["facility", "preferred_shift"]).size().unstack(fill_value=0)
    return g


def detect_consecutive_night(df: pd.DataFrame, threshold: int = 3) -> pd.DataFrame:
    """連続夜勤希望者を検知（同一スタッフが threshold 日以上連続夜勤希望）"""
    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df = df.sort_values(["staff_id", "date_dt"])

    risks = []
    for staff_id, grp in df.groupby("staff_id"):
        grp = grp.reset_index(drop=True)
        consecutive = 1
        max_consecutive = 1
        start_date = None
        for i in range(1, len(grp)):
            if grp.loc[i, "preferred_shift"] == "夜勤" and grp.loc[i - 1, "preferred_shift"] == "夜勤":
                if i == 1:
                    start_date = grp.loc[i - 1, "date"]
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        # 連続3日以上の夜勤を持つスタッフ
        night_count = (grp["preferred_shift"] == "夜勤").sum()
        # 改めて連続チェック
        max_run = 0
        run = 0
        for _, row in grp.iterrows():
            if row["preferred_shift"] == "夜勤":
                run += 1
                max_run = max(max_run, run)
            else:
                run = 0

        if max_run >= threshold:
            risks.append(
                {
                    "staff_id": staff_id,
                    "name": grp.iloc[0]["name"],
                    "role": grp.iloc[0]["role"],
                    "max_consecutive_night": max_run,
                    "total_night_count": night_count,
                }
            )

    return pd.DataFrame(risks)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """スタッフ別集計サマリー"""
    g = df.groupby(["staff_id", "name", "role"]).agg(
        total_days=("date", "count"),
        night_count=("is_night", "sum"),
        off_count=("is_off", "sum"),
    ).reset_index()
    g["night_ratio"] = (g["night_count"] / g["total_days"]).round(4)
    return g


def generate_report(
    df: pd.DataFrame,
    role_shift: pd.DataFrame,
    staff_night: pd.DataFrame,
    emp_shift: pd.DataFrame,
    facility_cov: pd.DataFrame,
    consec_risk: pd.DataFrame,
    summary: pd.DataFrame,
) -> str:
    lines = []
    lines.append("# シフト希望・配置分析レポート（2024年1月）\n")

    # ── 基本統計 ───────────────────────────────────────────────────────
    lines.append("## 1. 基本統計\n")
    lines.append(f"- 総レコード数: **{len(df):,}件**")
    lines.append(f"- スタッフ総数: **{df['staff_id'].nunique()}名**")
    lines.append(f"- 対象期間: {df['date'].min()} 〜 {df['date'].max()}")
    lines.append(f"- 施設数: {df['source_file'].nunique()}施設")
    lines.append("")

    # ── 役職別シフト分布 ──────────────────────────────────────────────
    lines.append("## 2. 役職別シフト分布（夜勤比率・休み希望率）\n")
    for role in role_shift.index:
        night = role_shift.loc[role, "夜勤比率"] if "夜勤比率" in role_shift.columns else 0
        off = role_shift.loc[role, "休み希望率"] if "休み希望率" in role_shift.columns else 0
        lines.append(f"- **{role}**: 夜勤比率 {night:.1%}、休み希望率 {off:.1%}")
    lines.append("")

    # ── スタッフ別夜勤希望回数 ────────────────────────────────────────
    lines.append("## 3. スタッフ別夜勤希望回数\n")
    lines.append("### 夜勤希望多い上位10名\n")
    top10 = staff_night.head(10)
    for _, row in top10.iterrows():
        lines.append(f"- {row['name']} ({row['role']}): {int(row['night_count'])}回")
    lines.append("")
    lines.append("### 夜勤希望少ない下位10名\n")
    bot10 = staff_night.tail(10)
    for _, row in bot10.iterrows():
        lines.append(f"- {row['name']} ({row['role']}): {int(row['night_count'])}回")
    lines.append("")

    # ── 雇用形態別シフト希望パターン ─────────────────────────────────
    lines.append("## 4. 雇用形態別シフト希望パターン\n")
    for emp in emp_shift.index:
        night_r = emp_shift.loc[emp, "夜勤"] if "夜勤" in emp_shift.columns else 0
        off_r = emp_shift.loc[emp, "休み"] if "休み" in emp_shift.columns else 0
        lines.append(f"- **{emp}**: 夜勤 {night_r:.1%}、休み {off_r:.1%}")
    lines.append("")

    # ── 施設別希望充足率 ──────────────────────────────────────────────
    lines.append("## 5. 施設別シフト希望分布\n")
    for fac in facility_cov.index:
        night_cnt = int(facility_cov.loc[fac, "夜勤"]) if "夜勤" in facility_cov.columns else 0
        day_cnt = int(facility_cov.loc[fac, "日勤"]) if "日勤" in facility_cov.columns else 0
        total = facility_cov.loc[fac].sum()
        lines.append(f"- **{fac}**: 夜勤 {night_cnt}件、日勤 {day_cnt}件（合計 {int(total)}件）")
    lines.append("")

    # ── 疲労リスク（連続夜勤検知） ────────────────────────────────────
    lines.append("## 6. 夜勤連続希望による疲労リスク検知\n")
    if consec_risk.empty:
        lines.append("連続3日以上の夜勤希望者はいませんでした。")
    else:
        lines.append(f"[WARN] **{len(consec_risk)}名** が連続3日以上の夜勤を希望しています。\n")
        for _, row in consec_risk.iterrows():
            lines.append(
                f"- {row['name']} ({row['role']}): "
                f"最大連続 {int(row['max_consecutive_night'])}日、"
                f"夜勤総数 {int(row['total_night_count'])}回"
            )
    lines.append("")

    # ── インサイトと提案 ──────────────────────────────────────────────
    lines.append("## 7. インサイトと改善提案\n")

    # 夜勤比率が最も高い役職
    if "夜勤比率" in role_shift.columns:
        top_role = role_shift["夜勤比率"].idxmax()
        top_ratio = role_shift["夜勤比率"].max()
        lines.append(
            f"1. **{top_role}** は夜勤比率が最も高く（{top_ratio:.1%}）、"
            f"夜勤負担が集中しています。担当シフトのローテーション強化を推奨します。"
        )

    # 疲労リスク者への対応
    if not consec_risk.empty:
        lines.append(
            f"2. 連続夜勤希望者が **{len(consec_risk)}名** 検知されました。"
            f"シフト割当時に3連続夜勤を回避する制約を設けることで疲労リスクを低減できます。"
        )
    else:
        lines.append(
            "2. 連続夜勤希望者は検知されませんでした。現状のシフト希望パターンは健全です。"
        )

    # パートの夜勤参加
    if "夜勤" in emp_shift.columns and "パート" in emp_shift.index:
        part_night = emp_shift.loc["パート", "夜勤"]
        lines.append(
            f"3. パートスタッフの夜勤希望率は **{part_night:.1%}** です。"
            f"夜勤体制の強化には正社員への依存が高い傾向があります。"
        )

    lines.append(
        "4. 各施設のシフト希望数と実際の必要人員を照合し、"
        f"希望充足率を定期的にモニタリングすることを推奨します。"
    )
    lines.append(
        "5. スキルレベル別の夜勤配置を見直し、"
        "上級スタッフが夜勤リーダーとして適切に配置されているか確認してください。"
    )
    lines.append("")

    # ── スタッフサマリー統計 ─────────────────────────────────────────
    lines.append("## 8. スタッフ夜勤サマリー統計\n")
    lines.append(f"- 平均夜勤回数: **{summary['night_count'].mean():.1f}回**")
    lines.append(f"- 最大夜勤回数: **{summary['night_count'].max()}回**")
    lines.append(f"- 夜勤0回スタッフ: **{(summary['night_count'] == 0).sum()}名**")
    lines.append(f"- 平均夜勤比率: **{summary['night_ratio'].mean():.1%}**")
    lines.append("")

    return "\n".join(lines)


def main():
    print("[分析開始] analyze.py")
    df = load_data()
    print(f"[読込] {len(df)}行, {df['staff_id'].nunique()}名")

    role_shift = analyze_role_shift(df)
    staff_night = analyze_staff_night(df)
    emp_shift = analyze_employment_shift(df)
    facility_cov = analyze_facility_coverage(df)
    consec_risk = detect_consecutive_night(df, threshold=3)
    summary = build_summary(df)

    # レポート出力
    report = generate_report(df, role_shift, staff_night, emp_shift, facility_cov, consec_risk, summary)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[出力] {REPORT_FILE}")

    # サマリーCSV出力
    summary_cols = ["staff_id", "name", "role", "total_days", "night_count", "off_count", "night_ratio"]
    summary[summary_cols].to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")
    print(f"[出力] {SUMMARY_FILE}  ({len(summary)}行)")

    if not consec_risk.empty:
        print(f"[警告] 疲労リスク者: {len(consec_risk)}名")

    print("\n[OK] 分析完了")


if __name__ == "__main__":
    main()
