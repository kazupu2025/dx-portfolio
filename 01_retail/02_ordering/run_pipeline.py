"""
発注最適化・需要予測パイプライン
クレンジング → 品質チェック → 分析 → レポート品質チェック → 可視化 を1コマンドで実行する

使い方:
    python run_pipeline.py
"""
import json
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable


def run(label, script):
    print(f"\n{'─'*52}")
    print(f"  {label}")
    print(f"{'─'*52}")
    result = subprocess.run([PYTHON, script], capture_output=False)
    return result.returncode == 0


def check_result(json_path, label):
    if not Path(json_path).exists():
        print(f"  [ERROR] {json_path} が存在しない")
        return False
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    passed = data.get("passed", 0)
    total = passed + data.get("failed", 0)
    all_passed = data.get("all_passed", False)
    status = "全PASS" if all_passed else f"{data['failed']}項目FAIL"
    print(f"\n  {label}: {passed}/{total} ({status})")
    if not all_passed:
        for r in data.get("results", []):
            if r["status"] == "FAIL":
                print(f"  [FAIL] #{r['id']:02d} {r['name']}: {r['detail']}")
    return all_passed


print("=" * 52)
print("  発注最適化・需要予測パイプライン 開始")
print("=" * 52)

# Step 1: クレンジング
if not run("Step 1: クレンジング", "output/cleanse.py"):
    print("\n[STOP] クレンジングに失敗しました。")
    sys.exit(1)

# Step 2: データ品質チェック
run("Step 2: データ品質チェック（18項目）", "output/validate.py")
if not check_result("output/result.json", "データ品質"):
    print("\n[STOP] データ品質チェックに失敗しました。output/result.json を確認してください。")
    sys.exit(1)

# Step 3: 分析レポート生成
if not run("Step 3: 需要予測・分析レポート生成", "output/analyze.py"):
    print("\n[STOP] 分析スクリプトに失敗しました。")
    sys.exit(1)

# Step 4: レポート品質チェック
run("Step 4: レポート品質チェック（7項目）", "output/validate_report.py")
if not check_result("output/result_analysis.json", "レポート品質"):
    print("\n[WARN] レポート品質チェックに問題があります。続行します。")

# Step 5: グラフ生成
if not run("Step 5: グラフ生成（3チャート）", "output/visualize.py"):
    print("\n[STOP] 可視化スクリプトに失敗しました。")
    sys.exit(1)

print(f"\n{'='*52}")
print("  パイプライン完了")
print(f"{'='*52}")
print("  出力ファイル:")
outputs = [
    "output/cleaned_order_2023Q4.csv",
    "output/forecast_202401.csv",
    "output/analysis_report.md",
    "output/charts/bar_category_forecast.png",
    "output/charts/bar_stockout_risk.png",
    "output/charts/scatter_stock_forecast.png",
]
for p in outputs:
    exists = "[OK]  " if Path(p).exists() else "[--]  "
    print(f"  {exists}{p}")
