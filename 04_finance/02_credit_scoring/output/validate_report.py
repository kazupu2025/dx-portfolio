"""
B-11: 与信スコアリング 分析レポートバリデーション（7チェック）
"""
import sys
import re
from pathlib import Path

OUT = Path(__file__).parent
REPORT_PATH = OUT / "credit_report_202401.txt"

results = []


def check(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f": {detail}"
    print(msg)
    results.append((name, passed))
    return passed


def main():
    # 1. レポートファイル存在
    if not check("report_exists", REPORT_PATH.exists(), str(REPORT_PATH)):
        print("CRITICAL: レポートが存在しません。analyze.py を先に実行してください。")
        sys.exit(1)

    text = REPORT_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 2. 全セクション存在確認
    required_sections = ["リスク分類", "職業", "申込用途", "負債比率", "スコア分布", "インサイト"]
    missing = [s for s in required_sections if s not in text]
    check("all_sections", len(missing) == 0,
          f"不足セクション: {missing}" if missing else "全6セクションOK")

    # 3. 3リスク分類すべて含まれる
    risk_cats = ["高リスク", "中リスク", "低リスク"]
    missing_cats = [c for c in risk_cats if c not in text]
    check("all_risk_categories", len(missing_cats) == 0,
          f"不足カテゴリ: {missing_cats}" if missing_cats else "全3カテゴリOK")

    # 4. インサイトキーワード
    insight_keywords = ["スコア", "リスク", "年収"]
    missing_kw = [kw for kw in insight_keywords if kw not in text]
    check("insight_keywords", len(missing_kw) == 0,
          f"不足キーワード: {missing_kw}" if missing_kw else "全キーワードOK")

    # 5. リスク分類セクションが4行以上
    risk_section_lines = [ln for ln in lines if "リスク" in ln and ("件" in ln or "%" in ln or "点" in ln)]
    check("risk_section_content", len(risk_section_lines) >= 4,
          f"リスク関連行数: {len(risk_section_lines)}")

    # 6. 数値・%・点が含まれる
    has_numeric = bool(re.search(r"\d+[件点%万]", text))
    check("numeric_present", has_numeric, "数値表現あり" if has_numeric else "数値表現なし")

    # 7. アラートセクション存在
    alert_keywords = ["アラート", "要注意", "高リスク"]
    has_alert = any(kw in text for kw in alert_keywords)
    check("alert_section", has_alert,
          f"キーワード検出: {[kw for kw in alert_keywords if kw in text]}")

    # --- 集計 ---
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'='*40}")
    print(f"レポートバリデーション結果: {passed}/{total} PASS")
    if passed < total:
        print(f"FAIL項目: {[name for name, ok in results if not ok]}")
    print(f"{'='*40}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
