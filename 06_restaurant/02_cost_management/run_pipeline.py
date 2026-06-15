import subprocess
import sys

PYTHON = r"C:\Users\realp\miniconda3\python.exe"


def run(script: str, label: str):
    print(f"\n{'='*50}\n  {label}\n{'='*50}")
    result = subprocess.run([PYTHON, script])
    if result.returncode != 0:
        print(f"\nERROR: {label} が失敗しました")
        sys.exit(1)


run("output/cleanse.py",         "Step 1: データクレンジング")
run("output/validate.py",        "Step 2: クレンジング品質チェック（18項目）")
run("output/analyze.py",         "Step 3: 原価・食材ロス分析")
run("output/validate_report.py", "Step 4: レポート品質チェック（7項目）")
run("output/visualize.py",       "Step 5: グラフ生成")
print("\nパイプライン完了! streamlit run app.py で結果を確認してください")
