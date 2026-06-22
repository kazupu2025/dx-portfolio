# -*- coding: utf-8 -*-
import yaml, sys, collections
from datetime import date

with open("catalog.yml", encoding="utf-8") as f:
    items = yaml.safe_load(f)

ready = [i for i in items if i.get("status") == "production-ready"]
idea  = [i for i in items if i.get("status") == "idea"]
today = date.today().strftime("%Y-%m-%d")

industry_count = collections.Counter(i.get("industry", "不明") for i in ready)
diff_count = collections.Counter(i.get("difficulty", "") for i in ready if i.get("difficulty"))

lines = []
lines.append("# DX ポートフォリオ ダッシュボード")
lines.append("")
lines.append(f"> 最終更新: {today}  |  総システム数: {len(items)}  |  Production-ready: {len(ready)}")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 状態サマリー")
lines.append("")
lines.append("| 状態 | 件数 |")
lines.append("|------|------|")
lines.append(f"| ✅ Production-ready | {len(ready)} |")
lines.append(f"| 💡 Idea | {len(idea)} |")
lines.append(f"| **合計** | **{len(items)}** |")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 業種別 内訳")
lines.append("")
lines.append("| 業種 | 件数 |")
lines.append("|------|------|")
for k, v in sorted(industry_count.items(), key=lambda x: -x[1]):
    lines.append(f"| {k} | {v} |")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 難易度別 内訳（製造 C-74〜C-94）")
lines.append("")
lines.append("| 難易度 | 件数 | 特徴 |")
lines.append("|--------|------|------|")
diff_labels = {
    "★★★": "config 調整のみで転用可",
    "★★☆": "統計分析ロジック実装",
    "★☆☆": "ML・CRUD・グラフ構造",
}
for k in ["★★★", "★★☆", "★☆☆"]:
    v = diff_count.get(k, 0)
    if v:
        lines.append(f"| {k} | {v} | {diff_labels[k]} |")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 全システム一覧")
lines.append("")
lines.append("| ID | 業種 | システム名 | 難易度 | 優先度 | パス |")
lines.append("|----|------|-----------|--------|--------|------|")
for i in sorted(ready, key=lambda x: str(x.get("id", ""))):
    iid  = i.get("id", "")
    ind  = i.get("industry", "")
    name = i.get("name", "")
    diff = i.get("difficulty", "")
    pri  = i.get("priority", "")
    path = i.get("path", "")
    lines.append(f"| {iid} | {ind} | {name} | {diff} | {pri} | `{path}` |")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 💡 Idea（未着手）")
lines.append("")
lines.append("| 業種 | システム名 |")
lines.append("|------|-----------|")
for i in idea:
    ind  = i.get("industry", "")
    name = i.get("name", "")
    lines.append(f"| {ind} | {name} |")

with open("PORTFOLIO.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"PORTFOLIO.md 生成完了: {len(lines)} 行")
