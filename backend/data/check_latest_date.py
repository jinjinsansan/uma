import json
import random

with open('jockey_knowledge.json') as f:
    d = json.load(f)

# ランダムに騎手を選択
jockey = random.choice(list(d.keys()))
races = d[jockey]['venue_course_stats']
latest = ''

for venue, stats in races.items():
    for result in stats['results']:
        if result['date'] > latest:
            latest = result['date']

print(f'騎手: {jockey}')
print(f'最新レース日: {latest}')

# 新規追加騎手の確認
new_jockeys = ['ハマーハ', 'ゴンサル', 'トーレス']
for j in new_jockeys:
    if j in d:
        print(f'\n新規騎手 {j} のデータ: 存在確認OK')
        print(f'  競馬場数: {len(d[j]["venue_course_stats"])}')
