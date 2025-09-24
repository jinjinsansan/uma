# 🏇 地方競馬版騎手ナレッジファイルSDKツール作成計画書

## 📅 作成日: 2025-09-25
## 🎯 目的: 7年間全データ（2019-2025）の騎手統計ファイル生成

---

## ✅ Phase 1: 環境確認とスケジュールマスター検証（5分）

### 1.1 必要ファイルの確認
```bash
# スケジュールマスター（馬版で作成済み）
ls -lh /mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json

# 馬版SDKツールの確認（参考用）
ls -lh /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/create_nar_horse_knowledge_v9_perfect_base.py
```

### 1.2 PostgreSQL接続テスト
```python
import psycopg2
# 接続パラメータ（馬版と同じ）
CONNECTION_PARAMS = {
    "host": "172.25.160.1",  # WSL2からWindows
    "port": "5432",
    "database": "PC-KEIBA",
    "user": "postgres",
    "password": "postgres"
}
```

### 1.3 Python環境確認
```bash
python3 --version
pip3 list | grep psycopg2
```

---

## ✅ Phase 2: データベース構造の調査とSQL設計（10分）

### 2.1 騎手データ関連テーブル確認
```sql
-- 騎手名の取得可能フィールド確認
SELECT column_name FROM information_schema.columns
WHERE table_name = 'nvd_se' AND column_name LIKE '%kishu%';

-- サンプルデータ確認
SELECT
    kishumei_ryakusho,
    COUNT(*) as race_count
FROM nvd_se
WHERE kaisai_nen = '2024'
    AND keibajo_code IN ('42','43','44','45')
GROUP BY kishumei_ryakusho
ORDER BY race_count DESC
LIMIT 10;
```

### 2.2 メインクエリの設計
```sql
-- 7年間全データ取得（制限なし）
SELECT
    se.kishumei_ryakusho,                    -- 騎手名
    se.kaisai_nen || se.kaisai_tsukihi as race_date,  -- レース日
    se.keibajo_code,                         -- 会場コード（補正対象）
    ra.kyori,                                -- 距離
    ra.track_code,                           -- トラック（1:芝, 2:ダート）
    ra.babajotai_code_shiba,                 -- 芝馬場状態
    ra.babajotai_code_dirt,                  -- ダート馬場状態
    ra.racenamef,                           -- レース名（会場補正用）
    se.wakuban,                             -- 枠番
    se.bamei,                               -- 馬名
    se.kakutei_chakujun,                    -- 確定着順
    ra.shusso_tosu,                         -- 出走頭数
    um.ketto_joho_01b as sire               -- 種牡馬名
FROM nvd_se se
JOIN nvd_ra ra ON (
    se.kaisai_nen = ra.kaisai_nen
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
)
LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
WHERE se.kaisai_nen BETWEEN '2019' AND '2025'
    AND se.keibajo_code IN ('42','43','44','45','35','36')  -- 南関東+盛岡+水沢
    AND se.kishumei_ryakusho IS NOT NULL
    AND se.kishumei_ryakusho != ''
    AND se.kakutei_chakujun IS NOT NULL
    AND se.kakutei_chakujun != '00'
ORDER BY se.kishumei_ryakusho, race_date DESC;
```

---

## ✅ Phase 3: 会場補正システムの実装（15分）

### 3.1 馬版の補正ロジックを流用
```python
# 4段階補正システム
def correct_venue_perfect(keibajo_code, race_name, race_date):
    """
    馬版で成功した4段階補正をそのまま使用
    補正率44.7%達成の実績あり
    """
    # 1. 重賞レース辞書
    # 2. 非重賞パターン
    # 3. スケジュールマスター（最重要）
    # 4. パターンマッチング
```

### 3.2 スケジュールマスター読み込み
```python
import json

def load_schedule_master():
    master_file = "../data/nankan_schedule_master_2019_2025.json"
    with open(master_file, 'r', encoding='utf-8') as f:
        master = json.load(f)
    return master['schedule_data']
```

---

## ✅ Phase 4: 騎手データ集計ロジックの実装（30分）

### 4.1 データ構造の定義
```python
jockey_data = {
    "騎手名": {
        "name": "騎手名",
        "venue_course_stats": {},      # 会場×距離別
        "track_condition_stats": {},   # 馬場状態別
        "post_position_stats": {},     # 枠番別
        "sire_stats": {},              # 種牡馬別
        "overall_stats": {
            "total_races_analyzed": 0,
            "overall_fukusho_rate": 0.0
        },
        "processed_at": ""
    }
}
```

### 4.2 複勝率計算関数
```python
def calculate_fukusho_rate(results):
    """
    複勝率 = (3着以内の回数 ÷ 総騎乗回数) × 100
    """
    if not results:
        return 0.0

    fukusho_count = sum(1 for r in results if r['is_fukusho'])
    total_count = len(results)

    return round((fukusho_count / total_count) * 100, 1)
```

### 4.3 カテゴリー別集計
```python
def aggregate_jockey_stats(rows):
    jockeys = {}

    for row in rows:
        jockey_name = row['kishumei_ryakusho']

        # 騎手データ初期化
        if jockey_name not in jockeys:
            jockeys[jockey_name] = initialize_jockey_data(jockey_name)

        # 会場補正
        corrected_venue = correct_venue_perfect(
            row['keibajo_code'],
            row['racenamef'],
            row['race_date']
        )

        # 結果データ作成
        result = {
            'date': format_date(row['race_date']),
            'horse_name': row['bamei'],
            'position': int(row['kakutei_chakujun']),
            'total_horses': int(row['shusso_tosu']),
            'is_fukusho': int(row['kakutei_chakujun']) <= 3
        }

        # 1. venue_course_stats（制限なし、全データ）
        key = f"{corrected_venue['venue_name']}_{row['kyori']}m"
        add_result_to_category(jockeys[jockey_name]['venue_course_stats'], key, result)

        # 2. track_condition_stats（制限なし、全データ）
        track_key = get_track_condition_key(row)
        add_result_to_category(jockeys[jockey_name]['track_condition_stats'], track_key, result)

        # 3. post_position_stats（制限なし、全データ）
        post_key = f"枠{row['wakuban']}"
        add_result_to_category(jockeys[jockey_name]['post_position_stats'], post_key, result)

        # 4. sire_stats（制限なし、全データ）
        if row['sire']:
            add_result_to_category(jockeys[jockey_name]['sire_stats'], row['sire'], result)

    return jockeys
```

---

## ✅ Phase 5: JSON出力とファイル生成（10分）

### 5.1 出力フォーマット
```python
def save_jockey_knowledge(jockeys, output_file):
    """
    JRA版と完全互換の構造で出力
    """
    output_data = {
        "metadata": {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "total_jockeys": len(jockeys),
            "data_period": "2019-2025",
            "sdk_version": "NAR_JOCKEY_SDK_V1"
        },
        "jockeys": jockeys
    }

    # ファイル保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
```

### 5.2 CDN用ファイル名
```python
# 固定ファイル名（馬版と同様）
output_filename = "nankan_jockey_knowledge_20250907.json"
```

---

## ✅ Phase 6: テストとバリデーション（10分）

### 6.1 データ品質チェック
```python
def validate_output(jockeys):
    """
    出力データの妥当性確認
    """
    checks = {
        "騎手数": len(jockeys) > 300,  # 300名以上
        "データ量": all(j['overall_stats']['total_races_analyzed'] > 0 for j in jockeys.values()),
        "複勝率範囲": all(0 <= j['overall_stats']['overall_fukusho_rate'] <= 100 for j in jockeys.values()),
        "会場補正": check_venue_correction_rate(jockeys)  # 40%以上
    }
    return all(checks.values()), checks
```

### 6.2 サンプル出力確認
```python
# 上位騎手の確認
top_jockeys = sorted(jockeys.items(),
                     key=lambda x: x[1]['overall_stats']['total_races_analyzed'],
                     reverse=True)[:5]

for name, data in top_jockeys:
    print(f"{name}: {data['overall_stats']['total_races_analyzed']}騎乗, "
          f"複勝率{data['overall_stats']['overall_fukusho_rate']}%")
```

---

## 📊 期待される成果

### メトリクス
- **処理時間**: 約30-60秒（7年間全データ）
- **騎手数**: 約400-500名
- **データ量**: 1騎手あたり平均1000騎乗
- **ファイルサイズ**: 約150-200MB
- **会場補正率**: 40%以上（馬版実績:44.7%）

### 出力ファイル構造
```
nankan_jockey_knowledge_20250907.json
├── metadata
│   ├── version: "1.0"
│   ├── created_at: "2025-09-25T..."
│   ├── total_jockeys: 447
│   └── data_period: "2019-2025"
└── jockeys
    ├── "笹川翼"
    │   ├── venue_course_stats
    │   │   └── "大井_1200m": {results: [...], fukusho_rate: 45.5, race_count: 150}
    │   ├── track_condition_stats
    │   ├── post_position_stats
    │   ├── sire_stats
    │   └── overall_stats
    └── ...（他の騎手）
```

---

## 🚀 実行コマンド

```bash
# スクリプト作成
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
vim create_nar_jockey_knowledge_v1_perfect.py

# 実行
python3 create_nar_jockey_knowledge_v1_perfect.py

# 結果確認
ls -lh nankan_jockey_knowledge_20250907.json
```

---

## ⚠️ 重要な注意事項

1. **40走制限の撤廃**
   - 7年間の全データを使用
   - カテゴリーごとの制限なし

2. **会場補正の重要性**
   - スケジュールマスターは必須
   - 馬版で成功した4段階補正を流用

3. **複勝率の計算**
   - 3着以内 ÷ 総騎乗数 × 100
   - 小数点第1位まで

4. **JRA版との互換性**
   - データ構造を完全に同一に
   - フィールド名の変更禁止

---

## 📅 タイムライン

| Phase | 作業内容 | 所要時間 |
|-------|---------|----------|
| Phase 1 | 環境確認 | 5分 |
| Phase 2 | DB調査・SQL設計 | 10分 |
| Phase 3 | 会場補正実装 | 15分 |
| Phase 4 | 集計ロジック実装 | 30分 |
| Phase 5 | JSON出力 | 10分 |
| Phase 6 | テスト・検証 | 10分 |
| **合計** | | **約80分** |

---

**作成者**: Claude
**最終更新**: 2025-09-25
**ベース**: 馬版SDKツール（補正率44.7%達成）の成功事例