"""
飲食×廃棄ロス 売上データパイプライン実行スクリプト
使用法: python run_pipeline.py
"""
import subprocess
import sys
from pathlib import Path

PYTHON = r"C:\Users\realp\miniconda3\python.exe"

def run(script: str, label: str):
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    result = subprocess.run([PYTHON, script])
    if result.returncode != 0:
        print(f"\nERROR: {label} が失敗しました")
        sys.exit(1)

run("output/cleanse.py",          "Step 1: データクレンジング")
run("output/validate.py",         "Step 2: クレンジング品質チェック（20項目）")
run("output/analyze.py",          "Step 3: 廃棄ロス分析")
run("output/validate_report.py",  "Step 4: レポート品質チェック（7項目）")
run("output/visualize.py",        "Step 5: グラフ生成")
print("\nパイプライン完了! streamlit run app.py で結果を確認してください")
