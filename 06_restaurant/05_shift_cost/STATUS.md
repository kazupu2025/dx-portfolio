# C-110 アルバイトシフト管理・人件費集計

- status: production-ready
- industry: 飲食
- difficulty: ★★☆
- path: 06_restaurant/03_shift_cost/

## 概要

飲食店のアルバイトシフトデータを管理し、人件費と人件費率を可視化するシステム。

### 機能
- シフトデータのCSVアップロード
- 実働時間計算（休憩時間を差し引き）
- 日次・スタッフ別・役割別の人件費集計
- 人件費率の判定（good/warning/alert）
- 複数の角度からの可視化グラフ

### 判定基準
- 人件費率 ≤25% → good（良好）
- 人件費率 ≤35% → warning（注意）
- 人件費率 >35% → alert（危険）
