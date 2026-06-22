"""不良原因テキスト → カテゴリ分類（Claude API + ルールベースフォールバック）。"""
from __future__ import annotations
import os
import re
from pathlib import Path

# python-dotenv が入っている場合のみ .env 読み込み
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent.parent.parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

CATEGORIES = ["寸法系", "外観系", "機能系", "材料系", "その他"]

_RULES = {
    "寸法系": ["寸法", "サイズ", "長さ", "径", "肉厚", "高さ", "幅", "直径", "外径", "内径"],
    "外観系": ["外観", "傷", "汚れ", "色", "光沢", "へこ", "凹", "バリ", "欠け", "クラック"],
    "機能系": ["機能", "動作", "強度", "耐久", "漏れ", "割れ", "折れ", "断線", "接触"],
    "材料系": ["材料", "材質", "硬度", "成分", "組成", "化学", "金属", "樹脂"],
}


def _rule_classify(text: str) -> tuple[str, float]:
    """ルールベース分類。(category, confidence) を返す。"""
    text_lower = text.lower()
    scores = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in _RULES.items():
        for kw in keywords:
            if kw in text_lower:
                scores[cat] += 1
    best_cat = max(scores, key=lambda c: scores[c])
    best_score = scores[best_cat]
    if best_score == 0:
        return "その他", 0.5
    conf = min(0.5 + best_score * 0.1, 0.9)
    return best_cat, round(conf, 2)


def _llm_classify(texts: list[str]) -> list[tuple[str, float]] | None:
    """Claude API 一括分類。失敗時は None を返す。"""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
        prompt = f"""以下の製造不良説明文を、5つのカテゴリ（寸法系/外観系/機能系/材料系/その他）に分類してください。
各行を「番号: カテゴリ名, 信頼度(0.0-1.0)」の形式で出力してください。

説明文:
{numbered}

出力例:
1: 寸法系, 0.95
2: 外観系, 0.87"""
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = response.content[0].text.strip().split("\n")
        results = []
        for line in lines:
            m = re.match(r"\d+:\s*(.+),\s*([\d.]+)", line.strip())
            if m:
                cat = m.group(1).strip()
                conf = float(m.group(2))
                cat = cat if cat in CATEGORIES else "その他"
                results.append((cat, conf))
            else:
                results.append(("その他", 0.5))
        if len(results) != len(texts):
            return None
        return results
    except Exception:
        return None


def classify_batch(texts: list[str]) -> tuple[list[tuple[str, float]], bool]:
    """テキストリストを分類する。(results, llm_used) を返す。"""
    llm_results = _llm_classify(texts)
    if llm_results is not None:
        return llm_results, True
    return [_rule_classify(t) for t in texts], False
