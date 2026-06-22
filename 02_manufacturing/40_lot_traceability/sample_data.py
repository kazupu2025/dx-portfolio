"""ロットトレーサビリティ サンプルデータ（12ノード, 複数ロット）。"""
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """3ロット × 12ノード のトレーサビリティサンプルデータ。"""
    rows = [
        # ロット L001
        ("鋼材A", "切削工程", "材料→工程", "L001", 100.0),
        ("切削工程", "組立工程", "工程→工程", "L001", 95.0),
        ("組立工程", "検査工程", "工程→工程", "L001", 95.0),
        ("検査工程", "得意先X", "工程→出荷", "L001", 90.0),
        # ロット L002
        ("鋼材A", "切削工程", "材料→工程", "L002", 80.0),
        ("樹脂B", "組立工程", "材料→工程", "L002", 20.0),
        ("切削工程", "組立工程", "工程→工程", "L002", 78.0),
        ("組立工程", "検査工程", "工程→工程", "L002", 95.0),
        ("検査工程", "得意先Y", "工程→出荷", "L002", 92.0),
        # ロット L003
        ("鋼材C", "プレス工程", "材料→工程", "L003", 50.0),
        ("プレス工程", "溶接工程", "工程→工程", "L003", 48.0),
        ("溶接工程", "得意先X", "工程→出荷", "L003", 46.0),
    ]
    return pd.DataFrame(rows, columns=["from_node", "to_node", "edge_type", "lot_id", "quantity"])


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_lot_traceability.csv", index=False)
    print(df)
    print(f"\nノード数: {len(set(df.from_node) | set(df.to_node))}")
    print(f"エッジ数: {len(df)}")
    print(f"ロット数: {df['lot_id'].nunique()}")
