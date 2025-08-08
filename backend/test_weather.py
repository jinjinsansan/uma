#!/usr/bin/env python3
from services.dlogic_raw_data_manager import dlogic_manager

# ヤマニンバロネスの計算を再実行
print('改良版：ヤマニンバロネスのD-Logic計算...')
result = dlogic_manager.calculate_dlogic_realtime('ヤマニンバロネス')

print(f'\n計算結果:')
print(f'総合スコア: {result.get("total_score", 0):.2f}')
print(f'グレード: {result.get("grade", "未評価")}')

print(f'\n12項目スコア:')
scores = result.get('d_logic_scores', {})
for i, (key, value) in enumerate(scores.items(), 1):
    status = '✅' if value != 50.0 else '❌'
    print(f'{i:2d}. {status} {key[2:]}: {value:.2f}')

# 50点以外のスコアをカウント
non_default = sum(1 for v in scores.values() if v != 50.0)
print(f'\n🎯 完成度: {non_default}/12項目が計算されました')

if non_default == 12:
    print('\n🎉 祝！全12項目の計算が完成しました！')