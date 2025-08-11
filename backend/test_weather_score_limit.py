#!/usr/bin/env python3
"""
天候適性D-Logicの100点上限問題をテスト
"""

# 現在の計算方法をシミュレート
def current_weather_calculation(base_score: float, baba_condition: int, key: str) -> float:
    """現在の実装での計算"""
    if key == "6_weather_aptitude":
        weight_multiplier = {2: 1.5, 3: 2.0, 4: 2.5}[baba_condition]
        return base_score * weight_multiplier
    elif key == "12_time_index":
        weight_reducer = {2: 0.8, 3: 0.6, 4: 0.4}[baba_condition]
        return base_score * weight_reducer
    else:
        # 仮の調整係数（実際は複雑な計算）
        adjustment = 1.1  # 平均的な値
        return base_score * adjustment

# 修正案での計算
def proposed_weather_calculation(base_score: float, baba_condition: int, key: str) -> float:
    """修正案での計算（100点上限）"""
    if key == "6_weather_aptitude":
        # 最大20%の加点に制限
        bonus_factor = {2: 1.05, 3: 1.10, 4: 1.20}[baba_condition]
        return min(100.0, base_score * bonus_factor)
    elif key == "12_time_index":
        # タイム指数は減点のみ（変更なし）
        weight_reducer = {2: 0.8, 3: 0.6, 4: 0.4}[baba_condition]
        return base_score * weight_reducer
    else:
        # その他の項目は最大10%の変動に制限
        adjustment = {2: 1.05, 3: 1.08, 4: 1.10}[baba_condition]
        return min(100.0, base_score * adjustment)

# テストケース
print("=== 天候適性D-Logic 100点上限問題のテスト ===\n")

# ケース1: 高得点馬の不良馬場
print("【ケース1】高得点馬（90点）の不良馬場")
base_scores = {
    "6_weather_aptitude": 90.0,
    "12_time_index": 85.0,
    "1_distance_aptitude": 88.0
}

for key, base in base_scores.items():
    current = current_weather_calculation(base, 4, key)  # 不良
    proposed = proposed_weather_calculation(base, 4, key)
    print(f"{key}: {base:.1f}点")
    print(f"  現在: {current:.1f}点 {'⚠️ 100点超え!' if current > 100 else ''}")
    print(f"  修正: {proposed:.1f}点")

# ケース2: ダンスインザダーク（基準馬）
print("\n【ケース2】ダンスインザダーク（基準100点）の各馬場")
for condition, name in [(1, "良"), (2, "稍重"), (3, "重"), (4, "不良")]:
    if condition == 1:
        continue  # 良馬場はスキップ
    
    current = current_weather_calculation(100.0, condition, "6_weather_aptitude")
    proposed = proposed_weather_calculation(100.0, condition, "6_weather_aptitude")
    print(f"\n{name}馬場:")
    print(f"  現在: {current:.1f}点 {'⚠️ 基準を超える!' if current > 100 else ''}")
    print(f"  修正: {proposed:.1f}点 ✅")

# 総合スコアのシミュレーション
print("\n【ケース3】総合スコアへの影響")
print("12項目の平均が85点の馬の場合:")

weights = [1.2, 1.1, 1.0, 1.0, 1.1, 0.9, 0.8, 0.9, 0.8, 1.0, 1.1, 1.2]
base_total = 85.0

for condition, name in [(2, "稍重"), (3, "重"), (4, "不良")]:
    # 現在の方式（単純化）
    current_total = base_total * 1.2  # 平均的な上昇
    # 修正案（上限付き）
    proposed_total = min(100.0, base_total * 1.08)
    
    print(f"\n{name}馬場:")
    print(f"  標準: {base_total:.1f}点")
    print(f"  現在: {current_total:.1f}点 {'⚠️' if current_total > 100 else ''}")
    print(f"  修正: {proposed_total:.1f}点")

print("\n=== 修正方針 ===")
print("1. 個別スコアは100点を上限とする")
print("2. 天候による加点は最大20%に制限")
print("3. ダンスインザダーク（基準馬）は常に100点を維持")
print("4. 総合スコアも100点を超えない")