import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

rng = np.random.default_rng(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/02_manufacturing/02_equipment_log")

equipments = [
    ("E-001", "旋盤機A",   {"temp": (70, 5),   "vib": (1.5, 0.3),  "prs": (1.1, 0.1),  "rpm": (1500, 30)}),
    ("E-002", "プレス機B", {"temp": (80, 6),   "vib": (2.0, 0.4),  "prs": (1.3, 0.12), "rpm": (1480, 25)}),
    ("E-003", "溶接機C",   {"temp": (75, 5),   "vib": (1.2, 0.25), "prs": (1.0, 0.08), "rpm": (1520, 20)}),
    ("E-004", "旋盤機D",   {"temp": (68, 4),   "vib": (1.8, 0.35), "prs": (1.2, 0.1),  "rpm": (1490, 35)}),
    ("E-005", "コンプレッサE", {"temp": (85, 7), "vib": (2.5, 0.5), "prs": (1.4, 0.15), "rpm": (1440, 40)}),
]

styles = {
    "E-001": ("standard", "01_旋盤機A_センサーログ_202401.csv"),
    "E-002": ("english",  "02_pressB_sensor_log_202401.csv"),
    "E-003": ("standard", "03_溶接機C_センサーログ_202401.csv"),
    "E-004": ("variant",  "04_旋盤機D_センサーログ_202401.csv"),
    "E-005": ("variant",  "05_コンプレッサE_センサーログ_202401.csv"),
}

start = datetime(2024, 1, 1, 0, 0, 0)
timestamps = [start + timedelta(hours=h) for h in range(31 * 24)]

for eq_id, eq_name, params in equipments:
    style, filename = styles[eq_id]
    rows = []
    anomaly_start = rng.integers(100, 200)
    anomaly_len   = rng.integers(6, 24)

    for i, ts in enumerate(timestamps):
        op_status = 0 if (ts.hour < 6 or ts.weekday() == 6) else 1

        if op_status == 0:
            temp = vib = prs = rpm = 0.0
        else:
            temp = float(rng.normal(params["temp"][0], params["temp"][1]))
            vib  = float(rng.normal(params["vib"][0],  params["vib"][1]))
            prs  = float(rng.normal(params["prs"][0],  params["prs"][1]))
            rpm  = float(rng.normal(params["rpm"][0],  params["rpm"][1]))

            if anomaly_start <= i < anomaly_start + anomaly_len:
                progress = (i - anomaly_start) / anomaly_len
                temp += params["temp"][1] * progress * 5
                vib  += params["vib"][1]  * progress * 4

            temp = round(max(0, temp), 2)
            vib  = round(max(0, vib), 3)
            prs  = round(max(0, prs), 3)
            rpm  = round(max(0, rpm), 1)

        ts_str = ts.strftime("%Y/%m/%d %H:%M")
        if style == "standard":
            rows.append({
                "日時": ts_str, "設備ID": eq_id, "設備名": eq_name,
                "温度(°C)": temp, "振動(mm/s)": vib, "圧力(MPa)": prs,
                "回転数(rpm)": rpm, "稼働状態": op_status,
            })
        elif style == "english":
            rows.append({
                "Timestamp": ts_str, "EquipmentID": eq_id, "EquipmentName": eq_name,
                "Temperature": temp, "Vibration": vib, "Pressure": prs,
                "RPM": rpm, "OperationStatus": op_status,
            })
        else:
            rows.append({
                "計測時刻": ts_str, "機番": eq_id, "機器名称": eq_name,
                "温度": temp, "振動値": vib, "圧力値": prs,
                "回転数": rpm, "稼働フラグ": op_status,
            })
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows")

print("サンプルデータ生成完了（5設備 × 744時間）")
