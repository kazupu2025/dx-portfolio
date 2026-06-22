"""不良原因テキストサンプル（10件）。"""
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """Sample defect descriptions for testing."""
    return pd.DataFrame({"description": [
        "外径が設計値より0.2mm大きい",
        "表面に細かい引っかき傷が多数",
        "締め付けトルクが規定値を下回る",
        "材料硬度がHRC45を下回っている",
        "溶接部に気泡が発生している",
        "製品の高さが5.0mmでなく4.8mm",
        "色ムラがあり外観不良",
        "動作時に異音が発生",
        "成分分析でMn比率が規格外",
        "ネジの締め付けが緩い",
    ]})


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_defect_text.csv", index=False)
    print(df)
