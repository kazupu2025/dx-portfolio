import numpy as np
from PIL import Image, ImageFilter
import io

THRESHOLDS = {
    "brightness_low": 0.25,   # 暗すぎる（汚れ）
    "brightness_high": 0.95,  # 明るすぎる（反射・過露光）
    "edge_density_high": 0.15, # エッジ過多（傷・亀裂）
    "dark_ratio_high": 0.20,   # 暗領域過多（穴・欠損）
    "color_variance_high": 60, # 色分散過大（色ムラ）
}

def extract_features(img_bytes: bytes) -> dict:
    """画像から特徴量を抽出"""
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((256, 256))
    arr = np.array(img, dtype=float)

    # 輝度
    gray = np.mean(arr, axis=2) / 255
    brightness = float(gray.mean())

    # エッジ密度
    gray_img = Image.fromarray((gray * 255).astype(np.uint8))
    edge_img = gray_img.filter(ImageFilter.FIND_EDGES)
    edge_arr = np.array(edge_img) / 255
    edge_density = float(edge_arr.mean())

    # 暗領域率（輝度 < 0.2 のピクセル割合）
    dark_ratio = float((gray < 0.2).mean())

    # 色分散
    color_variance = float(arr.std())

    return {
        "brightness": brightness,
        "edge_density": edge_density,
        "dark_ratio": dark_ratio,
        "color_variance": color_variance,
    }

def classify(features: dict) -> dict:
    """特徴量から不良判定を実施"""
    defects = []
    scores = {}

    # 輝度チェック
    if features["brightness"] < THRESHOLDS["brightness_low"]:
        defects.append("汚れ・変色（暗部過多）")
        scores["brightness"] = 1.0 - features["brightness"]
    elif features["brightness"] > THRESHOLDS["brightness_high"]:
        defects.append("過露光・反射")
        scores["brightness"] = features["brightness"] - THRESHOLDS["brightness_high"]
    else:
        scores["brightness"] = 0.0

    # エッジチェック
    if features["edge_density"] > THRESHOLDS["edge_density_high"]:
        defects.append("傷・亀裂（エッジ過多）")
    scores["edge"] = min(features["edge_density"] / THRESHOLDS["edge_density_high"], 1.0)

    # 暗領域チェック
    if features["dark_ratio"] > THRESHOLDS["dark_ratio_high"]:
        defects.append("穴・欠損（暗領域過多）")
    scores["dark"] = min(features["dark_ratio"] / THRESHOLDS["dark_ratio_high"], 1.0)

    # 色ムラチェック
    if features["color_variance"] > THRESHOLDS["color_variance_high"]:
        defects.append("色ムラ")
    scores["color"] = min(features["color_variance"] / THRESHOLDS["color_variance_high"], 1.0)

    defect_score = float(np.mean(list(scores.values())))
    verdict = "不合格（要確認）" if defects else "合格"

    return {
        "verdict": verdict,
        "defects": defects,
        "defect_score": defect_score,
        "scores": scores,
    }

def inspect(img_bytes: bytes) -> dict:
    """画像検査のメイン処理"""
    features = extract_features(img_bytes)
    result = classify(features)
    return {**features, **result}
