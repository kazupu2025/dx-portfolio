"""工程パラメータ × 品質合否 サンプルデータ（200行）。"""
import numpy as np
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """200行の工程パラメータ×合否データを生成。

    ルール: temp>210 かつ pressure>5.3 → 70%でpass、それ以外は80%でpass
    """
    rng = np.random.default_rng(42)
    n = 200
    temp = rng.normal(200, 10, n)
    pressure = rng.normal(5.0, 0.5, n)
    speed = rng.normal(100, 15, n)
    humidity = rng.normal(50, 8, n)

    result = []
    for i in range(n):
        if temp[i] > 210 and pressure[i] > 5.3:
            result.append("pass" if rng.random() < 0.70 else "fail")
        else:
            result.append("pass" if rng.random() < 0.80 else "fail")

    return pd.DataFrame({
        "temp": temp.round(1),
        "pressure": pressure.round(2),
        "speed": speed.round(1),
        "humidity": humidity.round(1),
        "result": result,
    })


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_quality_prediction.csv", index=False)
    print(df.head())
    print(f"pass: {(df.result == 'pass').sum()}, fail: {(df.result == 'fail').sum()}")
