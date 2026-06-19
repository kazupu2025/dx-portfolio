"""Cp/Cpk ヒストグラム生成（matplotlib）"""
from __future__ import annotations
import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

matplotlib.rcParams["font.family"] = "BIZ UDGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

COLOR_NAVY = "#1e3a5f"
COLOR_RED = "#dc2626"
COLOR_GREEN = "#16a34a"
COLOR_AMBER = "#d97706"


def _verdict_color(verdict: str) -> str:
    if verdict in ("良好", "非常に良好"):
        return COLOR_GREEN
    if verdict == "要改善":
        return COLOR_AMBER
    return COLOR_RED


def plot_histogram(
    series: pd.Series,
    usl: float,
    lsl: float,
    cp: float,
    cpk: float,
    process: str,
    verdict: str,
) -> bytes:
    """
    ヒストグラム＋正規曲線＋規格外ゾーン着色のPNGをバイト列で返す。
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    mean = s.mean()
    std = s.std(ddof=1)

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor("#f5f7fa")
    ax.set_facecolor("#f5f7fa")

    # ヒストグラム
    n_bins = min(30, max(10, len(s) // 10))
    ax.hist(s, bins=n_bins, color="#3b82f6", alpha=0.7, edgecolor="white",
            linewidth=0.5, density=True, label="測定値分布")

    # 正規曲線オーバーレイ
    x = np.linspace(s.min() - 3 * std, s.max() + 3 * std, 300)
    ax.plot(x, stats.norm.pdf(x, mean, std), color=COLOR_NAVY,
            linewidth=2, label="正規分布近似")

    # 規格外ゾーン（赤）- xlim取得前に設定
    x_min = s.min() - 3 * std
    x_max = s.max() + 3 * std
    ax.set_xlim(x_min, x_max)

    ax.axvspan(x_min, lsl, alpha=0.15, color=COLOR_RED, label="規格外")
    ax.axvspan(usl, x_max, alpha=0.15, color=COLOR_RED)

    # 規格内ゾーン（緑）
    ax.axvspan(lsl, usl, alpha=0.07, color=COLOR_GREEN, label="規格内")

    # USL / LSL 縦線
    ax.axvline(lsl, color=COLOR_RED, linestyle="--", linewidth=1.5, label=f"LSL={lsl}")
    ax.axvline(usl, color=COLOR_RED, linestyle="--", linewidth=1.5, label=f"USL={usl}")

    # 平均線
    ax.axvline(mean, color=COLOR_NAVY, linestyle=":", linewidth=1.5,
               label=f"μ={mean:.4f}")

    color = _verdict_color(verdict)
    ax.set_title(
        f"{process}  |  Cp={cp:.2f}  Cpk={cpk:.2f}  n={len(s)}  [{verdict}]",
        fontsize=11, color=color, fontweight="bold", pad=8,
    )
    ax.set_xlabel("測定値", fontsize=9)
    ax.set_ylabel("密度", fontsize=9)
    ax.legend(fontsize=7, loc="upper right")
    ax.tick_params(labelsize=8)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
