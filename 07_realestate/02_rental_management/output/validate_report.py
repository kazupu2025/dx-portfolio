"""
B-14 レポートバリデーション (7チェック)
"""
import sys
from pathlib import Path

OUT = Path(__file__).parent
REPORT = OUT / "analysis_report.md"

def main():
    results = {}

    # 1. report_exists
    results["report_exists"] = REPORT.exists()

    if not REPORT.exists():
        for k in results:
            print(f"[{'PASS' if results[k] else 'FAIL'}] {k}")
        return 1

    text = REPORT.read_text(encoding="utf-8")

    # 2. all_sections
    results["all_sections"] = all(kw in text for kw in ["エリア", "タイプ", "修繕費", "KPI", "インサイト"])
    # 3. all_areas_in_report
    results["all_areas_in_report"] = all(a in text for a in ["渋谷区", "新宿区", "港区", "世田谷区", "品川区"])
    # 4. insight_keywords
    results["insight_keywords"] = all(kw in text for kw in ["空室率", "収益", "修繕"])
    # 5. area_section_content
    area_section_lines = [l for l in text.split("\n") if "エリア" in l or "区" in l]
    results["area_section_content"] = len(area_section_lines) >= 4
    # 6. numeric_present
    import re
    results["numeric_present"] = bool(re.search(r'\d+', text))
    # 7. alert_section
    results["alert_section"] = any(kw in text for kw in ["アラート", "要改善", "要対応"])

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Report validation: {passed}/{total} PASS")
    for name, ok in results.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
