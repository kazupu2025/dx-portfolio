"""品質予測モデル — RandomForest 学習 + 精度評価 + verdict。"""
from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

REQUIRED_COLS_BASE = ["result"]  # 最低1つの特徴量 + result が必要
TEST_SIZE = 0.2
RANDOM_STATE = 42


def _verdict(accuracy: float) -> str:
    """精度に基づいて verdict を判定。"""
    if accuracy >= 90.0:
        return "good"
    elif accuracy >= 70.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    """RandomForest 分類モデルを学習・評価。

    Args:
        df: "result" 列（pass/fail）+ 複数の特徴量列

    Returns:
        dict: {
            "model": RandomForestClassifier,
            "accuracy": float（%）,
            "feature_importances": pd.DataFrame（feature/importance列）,
            "classification_report": dict,
            "n_samples": int,
            "n_features": int,
            "verdict": str,
        }
    """
    if "result" not in df.columns:
        raise ValueError("必須列 'result' が不足しています。")

    feature_cols = [c for c in df.columns if c != "result"]
    if len(feature_cols) == 0:
        raise ValueError("特徴量列が1つ以上必要です。")

    data = df.copy()
    for col in feature_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna()

    if len(data) < 10:
        raise ValueError("有効なデータが少なすぎます（10行以上必要）。")

    X = data[feature_cols].values
    y = data["result"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    accuracy = float(accuracy_score(y_test, y_pred) * 100)
    cr = classification_report(y_test, y_pred, output_dict=True)
    importances = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_.tolist(),
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    return {
        "model": model,
        "accuracy": accuracy,
        "feature_importances": importances,
        "classification_report": cr,
        "n_samples": len(data),
        "n_features": len(feature_cols),
        "verdict": _verdict(accuracy),
    }
