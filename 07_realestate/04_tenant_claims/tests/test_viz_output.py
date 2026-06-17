"""
C-39: 可視化出力テスト（4テスト以上）
"""

from pathlib import Path

import pytest

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_property_claims.png",
    "bar_claim_type.png",
    "bar_status_dist.png",
]


# 1. charts ディレクトリが存在する
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts directory not found: {CHARTS_DIR}"


# 2. 3枚のグラフファイルが存在する
@pytest.mark.parametrize("filename", EXPECTED_CHARTS)
def test_chart_file_exists(filename):
    path = CHARTS_DIR / filename
    assert path.exists(), f"Chart file not found: {path}"


# 3. 各グラフが空でない（サイズ > 0）
@pytest.mark.parametrize("filename", EXPECTED_CHARTS)
def test_chart_file_not_empty(filename):
    path = CHARTS_DIR / filename
    if not path.exists():
        pytest.skip(f"{filename} not found")
    assert path.stat().st_size > 0, f"Chart file is empty: {path}"


# 4. PNG ファイルのマジックバイトを確認（PNGシグネチャ）
@pytest.mark.parametrize("filename", EXPECTED_CHARTS)
def test_chart_is_valid_png(filename):
    path = CHARTS_DIR / filename
    if not path.exists():
        pytest.skip(f"{filename} not found")
    with open(path, "rb") as f:
        header = f.read(8)
    png_signature = b"\x89PNG\r\n\x1a\n"
    assert header == png_signature, f"{filename} is not a valid PNG file"
