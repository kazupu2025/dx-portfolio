import pytest
import numpy as np
from PIL import Image
import io
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from inspector import extract_features, classify, inspect, THRESHOLDS

def make_img_bytes(brightness=0.5, add_edges=False, dark_ratio=0.0):
    """PIL Image を bytes に変換するヘルパー"""
    arr = np.ones((256, 256, 3), dtype=np.uint8) * int(brightness * 255)
    if add_edges:
        # 格子状のエッジを追加
        arr[::8, :] = 0
        arr[:, ::8] = 0
    if dark_ratio > 0:
        n = int(256 * 256 * dark_ratio)
        arr.reshape(-1, 3)[:n] = [10, 10, 10]
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_extract_features_returns_dict():
    f = extract_features(make_img_bytes())
    assert isinstance(f, dict)

def test_feature_keys():
    f = extract_features(make_img_bytes())
    for k in ["brightness", "edge_density", "dark_ratio", "color_variance"]:
        assert k in f

def test_bright_image():
    f = extract_features(make_img_bytes(brightness=0.9))
    assert f["brightness"] > 0.7

def test_dark_image_detected():
    result = inspect(make_img_bytes(brightness=0.1))
    assert result["verdict"] == "不合格（要確認）"

def test_clean_image_passes():
    result = inspect(make_img_bytes(brightness=0.6))
    assert result["verdict"] == "合格"

def test_inspect_has_verdict():
    result = inspect(make_img_bytes())
    assert "verdict" in result

def test_defect_score_range():
    result = inspect(make_img_bytes())
    assert 0 <= result["defect_score"] <= 1.0

def test_edge_detection():
    f = extract_features(make_img_bytes(add_edges=True))
    f_clean = extract_features(make_img_bytes(add_edges=False))
    assert f["edge_density"] > f_clean["edge_density"]
