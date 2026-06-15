import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from pathlib import Path

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/10_service/01_inquiry_log")

operators = [
    ("OP-01", "田中"), ("OP-02", "鈴木"), ("OP-03", "佐藤"),
    ("OP-04", "高橋"), ("OP-05", "伊藤"), ("OP-06", "渡辺"),
    ("OP-07", "山本"), ("OP-08", "中村"),
]
channels = ["電話", "メール", "チャット", "SNS"]
channels_eng = ["Phone", "Email", "Chat", "SNS"]
resolution_std = ["解決済", "対応中", "未解決", "エスカレ済"]
resolution_eng = ["Resolved", "InProgress", "Unresolved", "Escalated"]
resolution_var = ["解決", "対応中", "未対応", "エスカレ"]

keyword_pool = {
    "請求・支払い": ["請求書の確認", "支払い方法を変更したい", "料金が間違っている", "課金について質問", "二重請求があった"],
    "製品不具合":   ["製品が壊れた", "エラーが出て動かない", "故障している", "不具合が発生した", "バグがある"],
    "使い方・操作方法": ["使い方を教えてほしい", "操作方法がわからない", "設定のやり方", "how to use", "チュートリアルが必要"],
    "配送・到着":   ["荷物が届かない", "配送が遅延している", "追跡番号を教えて", "到着予定日を確認したい", "配送業者に問い合わせたい"],
    "返品・交換":   ["返品したい", "交換をお願いしたい", "キャンセルしたい", "返金してほしい", "exchange request"],
    "その他":       ["一般的な質問", "その他の問い合わせ", "詳細を確認したい", "サービスについて", "その他"],
}

resolution_prob = {
    "請求・支払い": [0.70, 0.15, 0.05, 0.10],
    "製品不具合":   [0.50, 0.20, 0.10, 0.20],
    "使い方・操作方法": [0.85, 0.10, 0.03, 0.02],
    "配送・到着":   [0.65, 0.20, 0.08, 0.07],
    "返品・交換":   [0.60, 0.25, 0.05, 0.10],
    "その他":       [0.75, 0.15, 0.07, 0.03],
}

def gen_row(inquiry_id: str, style: str) -> dict:
    cat_weights = [0.20, 0.25, 0.18, 0.15, 0.12, 0.10]
    cat_name = random.choices(list(keyword_pool.keys()), weights=cat_weights)[0]
    keyword = random.choice(keyword_pool[cat_name])

    op = random.choice(operators)

    day     = rng.integers(1, 32)
    day     = min(day, 31)
    hour    = rng.integers(9, 18)
    minute  = rng.integers(0, 60)
    received = datetime(2024, 1, day, hour, minute)

    minutes_log = float(rng.normal(3.5, 0.8))
    minutes = max(5, int(np.exp(minutes_log)))
    completed = received + timedelta(minutes=minutes)

    probs = resolution_prob.get(cat_name, [0.7, 0.15, 0.1, 0.05])
    resolution_idx = random.choices(range(4), weights=probs)[0]
    escalation = 1 if resolution_idx == 3 else 0

    ch_idx = random.randrange(4)

    if style == "standard":
        return {
            "問い合わせID": inquiry_id,
            "受付日時":   received.strftime("%Y/%m/%d %H:%M"),
            "完了日時":   completed.strftime("%Y/%m/%d %H:%M"),
            "担当者ID":   op[0], "担当者名": op[1],
            "チャネル":   channels[ch_idx],
            "問い合わせ内容": keyword,
            "カテゴリ":   "",
            "解決状況":   resolution_std[resolution_idx],
            "エスカレーション": escalation,
        }
    elif style == "english":
        return {
            "InquiryID":    inquiry_id,
            "ReceivedAt":   received.strftime("%Y/%m/%d %H:%M"),
            "CompletedAt":  completed.strftime("%Y/%m/%d %H:%M"),
            "OperatorID":   op[0], "OperatorName": op[1],
            "Channel":      channels_eng[ch_idx],
            "InquiryKeyword": keyword,
            "Category":     "",
            "ResolutionStatus": resolution_eng[resolution_idx],
            "Escalation":   escalation,
        }
    else:
        return {
            "受付番号":    inquiry_id,
            "受付日時":    received.strftime("%Y/%m/%d %H:%M"),
            "対応完了時刻": completed.strftime("%Y/%m/%d %H:%M"),
            "担当者コード": op[0], "担当者": op[1],
            "受付チャネル": channels[ch_idx],
            "問い合わせ種別": keyword,
            "分類":        "",
            "対応結果":    resolution_var[resolution_idx],
            "上位エスカレ": escalation,
        }

batches = [
    (range(1,   201), "standard", "01_問い合わせログ_A_202401.csv"),
    (range(201, 351), "english",  "02_inquiry_log_B_202401.csv"),
    (range(351, 501), "variant",  "03_問い合わせログ_C_202401.csv"),
]

for id_range, style, filename in batches:
    rows = [gen_row(f"INQ-{i:05d}", style) for i in id_range]
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows")

print("サンプルデータ生成完了（500件）")
