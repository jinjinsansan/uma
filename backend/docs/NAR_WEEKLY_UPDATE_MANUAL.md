# 地方競馬（南関東）週次更新完全マニュアル

**最終更新**: 2025-10-06  
**作成者**: Droid (週次更新スクリプト作成)

---

## 📝 概要

地方競馬統合ナレッジファイル（馬版・騎手版）を毎週更新するための完全手順書

### 🚨 重要な違い：JRA版との相違点

| 項目 | JRA | 地方競馬（南関東） |
|------|-----|------------------|
| **データソース** | 公式データ | 民間有志管理（PC-KEIBA） |
| **開催場所コード** | ✅ 信頼できる | ❌ でたらめ（使用不可） |
| **フィルター方法** | 開催場所コード | **スケジュールマスター（日付ベース）** |
| **データベーステーブル** | jvd_se, jvd_ra, jvd_um | **nvd_se, nvd_ra, nvd_um** |

---

## 🔧 スクリプト情報

### 馬のナレッジファイル
- **ファイル名**: `/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/update_nar_weekly.py`
- **実行タイミング**: 毎週月曜日（週末レース終了後）
- **処理内容**: 土日のレースデータを既存ナレッジファイルに差分追加

### 騎手のナレッジファイル
- **ファイル名**: `/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/update_nar_jockey_weekly.py`
- **実行タイミング**: 馬のナレッジファイル更新後
- **処理内容**: 土日のレースデータで騎手統計を更新

---

## 🎯 スケジュールマスターシステム

### スケジュールマスターとは

**問題**: PC-KEIBAの開催場所コードが信頼できない

**解決策**: 実際の開催日リストで日付ベースフィルタリング

### スケジュールマスターファイル

**場所**:
```
/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json
```

**構造**:
```json
{
  "metadata": {
    "period": "2019-01-01 to 2025-12-31",
    "total_days": 1223
  },
  "schedule_data": {
    "20250104": ["43"],  // 2025年1月4日は川崎で開催
    "20250105": ["42"],  // 2025年1月5日は大井で開催
    "20250106": ["44"]   // 2025年1月6日は船橋で開催
  }
}
```

### フィルタリング方法

```sql
-- ❌ 使えない方法（開催場所コードが信頼できない）
WHERE keibajo_code IN ('42', '43', '44', '45')

-- ✅ 正しい方法（スケジュールマスター + 開催場所コード両方でフィルタ）
WHERE se.kaisai_nen = '2025'
  AND se.kaisai_tsukihi IN ('1004', '1005')
  AND se.keibajo_code IN ('42', '43', '44', '45')
```

### 会場補正システム（4段階）

スクリプトは以下の順序で会場を補正します：

1. **公式重賞レース名チェック** - 東京大賞典、帝王賞など29レース
2. **スケジュールマスター照合** ← 最重要！90%以上の精度
3. **パターンマッチング** - レース名から会場を推測
4. **元のコードをそのまま使用** - 補正できない場合

---

## 🗄️ データベース情報

### PostgreSQL接続情報

```python
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",  # ⚠️ 小文字必須
    "user": "postgres",
    "password": "postgres"
}
```

### 使用テーブル

| テーブル | 説明 | 主要カラム |
|---------|------|-----------|
| `nvd_se` | レース成績 | bamei, kaisai_nen, kaisai_tsukihi, keibajo_code, kakutei_chakujun |
| `nvd_ra` | レース情報 | kyori, track_code, kyosomei_hondai, grade_code |
| `nvd_um` | 馬プロフィール | ketto_joho_01b (sire), ketto_joho_03b (broodmare_sire) |

⚠️ **注意**: JRA版は `jvd_*` だが、地方競馬版は `nvd_*`

---

## 🏇 対象競馬場（南関東）

| コード | 競馬場 | 英語名 |
|--------|--------|--------|
| 42 | 大井 | Oi |
| 43 | 川崎 | Kawasaki |
| 44 | 船橋 | Funabashi |
| 45 | 浦和 | Urawa |

---

## 🔐 Cloudflare R2 API認証情報（2025-10-06更新）

```python
ACCESS_KEY = "80bb7aca390fc82976b09b1005f7f531"
SECRET_KEY = "dd64d5ea1bedd6acfff0a42ebc771c81c459976fff03fd6677f5ba65b0e7fbbd"
ENDPOINT = "https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com"
BUCKET = "dlogic-knowledge-files"
```

---

## 🚀 実行手順

### ステップ1: 馬のナレッジファイル更新

#### 1.1 スケジュールマスター確認

```bash
# スケジュールマスターが存在するか確認
ls -lh /mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json

# 内容確認（最新日付をチェック）
python3 -c "
import json
with open('/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json') as f:
    data = json.load(f)
    print(f\"期間: {data['metadata']['period']}\")
    print(f\"総日数: {data['metadata']['total_days']}\")
    # 最新5日分を表示
    schedule = data['schedule_data']
    dates = sorted(schedule.keys())[-5:]
    for d in dates:
        print(f\"{d}: {schedule[d]}\")
"
```

**期待される出力:**
```
期間: 2019-01-01 to 2025-12-31
総日数: 1223
20251201: ['42']
20251202: ['43']
...
```

⚠️ **もし最新日付が古い場合**: スケジュールマスターを更新する必要があります

#### 1.2 週次更新スクリプト実行

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 update_nar_weekly.py
```

**期待される出力:**
```
================================================================================
🏇 地方競馬版（南関東）馬ナレッジファイル週次更新
================================================================================
✅ スケジュールマスター読み込み成功（1223日分）

📅 更新対象: 2025年 1004(土) - 1005(日)

📊 PostgreSQL接続中...
🔍 週末のレースデータ取得中...

📊 更新結果:
  新規レース: 124件
  更新された馬: 89頭
  総馬数: 12345頭
  会場補正適用: 112件
  コーナー補完適用レース: 45

💾 ファイル保存中: nar_unified_knowledge_20251006.json
✅ 保存完了: 120.5MB

================================================================================
🎉 週次更新完了!
================================================================================
✅ 出力ファイル: nar_unified_knowledge_20251006.json
✅ 新規レース数: 124
✅ 総馬数: 12345
✅ 会場補正率: 90.3%
```

#### 1.3 ファイル名を固定

⚠️ **重要**: CDN URLを変更しないため、ファイル名を固定

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
mv nar_unified_knowledge_YYYYMMDD.json nar_unified_knowledge.json
ls -lh nar_unified_knowledge.json
```

#### 1.4 CDNにアップロード

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 simple_upload_nar.py
```

**期待される出力:**
```
📁 アップロードファイル: nar_unified_knowledge.json
📊 サイズ: 120.5MB
⬆️ Cloudflare R2にアップロード中...
✅ アップロード成功！
🔗 公開URL:
  https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nar_unified_knowledge.json
```

#### 1.5 馬のナレッジファイル検証

```bash
# ヘッダー確認
curl -I https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nar_unified_knowledge.json

# メタデータ確認
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nar_unified_knowledge.json | \
python3 -c "import json, sys; data=json.load(sys.stdin); \
print(f\"総馬数: {data['metadata']['total_horses']}\"); \
print(f\"作成日時: {data['metadata']['created_at']}\"); \
print(f\"バージョン: {data['metadata']['version']}\")"

# 最新レースデータ確認（10月データが含まれるか）
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nar_unified_knowledge.json | \
python3 -c "
import json, sys
data = json.load(sys.stdin)
count = 0
for horse_name, horse in list(data['horses'].items())[:20]:
    for race in horse['races']:
        if race.get('KAISAI_GAPPI', '').startswith('10') and race.get('KAISAI_NEN') == '2025':
            print(f'{horse_name}: {race[\"KAISAI_NEN\"]}-{race[\"KAISAI_GAPPI\"]} {race.get(\"track_name\", \"不明\")} (last_update: {horse.get(\"last_update\", \"なし\")})')
            count += 1
            break
        if count >= 5:
            break
    if count >= 5:
        break
"

# last_updateフィールド確認
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nar_unified_knowledge.json | \
python3 -c "
import json, sys
data = json.load(sys.stdin)
sample_horses = list(data['horses'].keys())[:5]
for horse_name in sample_horses:
    horse = data['horses'][horse_name]
    print(f'{horse_name}: total_races={horse[\"total_races\"]}, last_update={horse.get(\"last_update\", \"なし\")}')
"
```

**期待される結果:**
- ✅ ファイルサイズ: 約100-150MB
- ✅ 総馬数: 10,000頭以上
- ✅ 作成日時: 実行日の日時
- ✅ 10月のレースデータが含まれる
- ✅ track_nameが「大井」「川崎」「船橋」「浦和」になっている
- ✅ レース追加馬の `last_update` が実行日の日時
- ✅ 会場補正率が90%以上

---

### ステップ2: 騎手のナレッジファイル更新

#### 2.1 週次更新スクリプト実行

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 update_nar_jockey_weekly.py
```

**期待される出力:**
```
================================================================================
🏇 地方競馬版（南関東）騎手ナレッジファイル週次更新
================================================================================
✅ スケジュールマスター読み込み成功（1223日分）

📅 更新対象: 2025年 1004(土) - 1005(日)

📊 PostgreSQL接続中...
🔍 週末の騎手成績データ取得中...
📊 複勝率を再計算中...

📊 更新結果:
  新規レース: 124件
  更新された騎手: 45名
  総騎手数: 380名

💾 ファイル保存中: nankan_jockey_knowledge_20251006.json
✅ 保存完了: 85.3MB

================================================================================
🎉 騎手ナレッジ週次更新完了!
================================================================================
✅ 出力ファイル: nankan_jockey_knowledge_20251006.json
✅ 新規レース数: 124
✅ 総騎手数: 380
```

#### 2.2 ファイル名を固定

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
mv nankan_jockey_knowledge_YYYYMMDD.json nankan_jockey_knowledge_20250907.json
ls -lh nankan_jockey_knowledge_20250907.json
```

⚠️ **注意**: 騎手版はファイル名に日付が含まれます（`20250907`は固定）

#### 2.3 CDNにアップロード

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 simple_upload_nar_jockey.py
```

**期待される出力:**
```
📁 アップロードファイル: nankan_jockey_knowledge_20250907.json
📊 サイズ: 85.3MB
⬆️ Cloudflare R2にアップロード中...
✅ アップロード成功！
🔗 公開URL:
  https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json
```

#### 2.4 騎手のナレッジファイル検証

```bash
# ヘッダー確認
curl -I https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json

# 基本情報確認
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json | \
python3 -c "import json, sys; data=json.load(sys.stdin); \
print(f'総騎手数: {len(data)}'); \
sample_jockey = list(data.keys())[0]; \
print(f'サンプル騎手: {sample_jockey}'); \
print(f'会場コース統計数: {len(data[sample_jockey][\"venue_course_stats\"])}')"

# 最新レースデータ確認（10月データが含まれるか）
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json | \
python3 -c "
import json, sys
data = json.load(sys.stdin)
count = 0
for jockey_name, jockey_data in data.items():
    if count >= 5:
        break
    for venue_key, stats in jockey_data.get('venue_course_stats', {}).items():
        for result in stats.get('results', [])[:1]:
            if result.get('date', '').startswith('2025-10'):
                print(f'{jockey_name} ({venue_key}): {result[\"date\"]} - {result[\"horse_name\"]} ({result[\"position\"]}着)')
                count += 1
                break
        if count >= 5:
            break
"
```

**期待される結果:**
- ✅ ファイルサイズ: 約80-100MB
- ✅ 総騎手数: 300名以上
- ✅ 10月のレースデータが含まれる
- ✅ 複勝率が再計算されている
- ✅ processed_atが更新されている

---

## 📦 ファイル構造

### 馬のナレッジファイル構造

```json
{
  "metadata": {
    "version": "1.0",
    "created_at": "2025-10-06T15:30:00.123456",
    "total_horses": 12345,
    "data_period": "None-2025",
    "sdk_version": "NAR_SDK_V1"
  },
  "horses": {
    "馬名": {
      "horse_name": "馬名",
      "total_races": 7,
      "races": [
        {
          "BAMEI": "馬名",
          "RACE_CODE": "20251005420612",
          "KAISAI_NEN": "2025",
          "KAISAI_GAPPI": "1005",
          "KEIBAJO_CODE": "42",
          "track_name": "大井",
          "KAKUTEI_CHAKUJUN": "01",
          ... (38フィールド)
        }
      ],
      "last_update": "2025-10-06T15:30:00.123456"
    }
  }
}
```

### 騎手のナレッジファイル構造

```json
{
  "騎手名": {
    "name": "騎手名",
    "venue_course_stats": {
      "大井_1200m": {
        "results": [
          {
            "date": "2025-1005",
            "horse_name": "馬名",
            "position": 1,
            "total_horses": 12,
            "is_fukusho": true
          }
        ],
        "fukusho_rate": 45.5,
        "race_count": 125
      }
    },
    "track_condition_stats": {...},
    "post_position_stats": {...},
    "sire_stats": {...},
    "processed_at": "2025-10-06T15:30:00.123456",
    "overall_stats": {
      "total_races_analyzed": 500,
      "overall_fukusho_rate": 35.2
    }
  }
}
```

---

## 📋 生成されるファイル一覧

| ファイル | サイズ | 説明 | CDN URL |
|---------|--------|------|---------|
| `nar_unified_knowledge.json` | 約120MB | 馬のナレッジファイル | https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nar_unified_knowledge.json |
| `nankan_jockey_knowledge_20250907.json` | 約85MB | 騎手のナレッジファイル | https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json |

---

## ❌ トラブルシューティング

### 問題: スケジュールマスターが見つからない

**症状:**
```
⚠️ スケジュールマスター読み込みエラー: [Errno 2] No such file or directory
```

**原因:**
- スケジュールマスターファイルが存在しない

**解決策:**
```bash
# ファイルの存在確認
ls -lh /mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json

# 存在しない場合は、スケジュールマスター作成スクリプトを実行
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 create_schedule_master.py  # ※存在する場合
```

---

### 問題: 会場補正率が低い（50%以下）

**症状:**
```
✅ 会場補正率: 45.2%
```

**原因:**
- スケジュールマスターが古い、または読み込まれていない

**解決策:**
1. スケジュールマスターの期間を確認
2. 必要に応じてスケジュールマスターを更新

```bash
# スケジュールマスターの期間確認
python3 -c "
import json
with open('/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json') as f:
    data = json.load(f)
    print(f\"期間: {data['metadata']['period']}\")
"
```

**正常値**: 会場補正率が90%以上であれば正常

---

### 問題: データベース接続エラー

**症状:**
```
UnicodeDecodeError: 'utf-8' codec can't decode
```

**原因:**
- データベース名が間違っている

**解決策:**
- データベース名を`pckeiba`（小文字）に確認
- スクリプト内の`CONNECTION_PARAMS`を確認

---

### 問題: テーブルが存在しない

**症状:**
```
ERROR: relation "nvd_se" does not exist
```

**原因:**
- JRA版のテーブル名（jvd_*）を使っている

**解決策:**
- 地方競馬版は `nvd_*` テーブルを使用
- スクリプトで正しいテーブル名を使用しているか確認

---

### 問題: 認証エラー

**症状:**
```
403 Forbidden
```

**原因:**
- Cloudflare R2のAPI認証情報が古い

**解決策:**
- 最新の認証情報を使用（2025-10-06更新済み）
- アップロードスクリプトの`ACCESS_KEY`と`SECRET_KEY`を確認

---

### 問題: last_updateフィールドがない

**症状:**
- 一部の馬に`last_update`フィールドが存在しない

**原因:**
- 新規追加馬でスクリプトの`last_update`追加処理が実行されていない

**解決策:**
- `update_nar_weekly.py`の以下の部分を確認:
```python
if horse_name not in horses_data:
    horses_data[horse_name] = {
        "horse_name": horse_name,
        "total_races": 0,
        "races": [],
        "last_update": datetime.now().isoformat()  # ← この行が必要
    }

# レース追加後
horses_data[horse_name]["last_update"] = datetime.now().isoformat()  # ← この行が必要
```

---

## 🔍 検証チェックリスト

### 馬のナレッジファイル

- [ ] ファイルサイズが100-150MB程度
- [ ] 総馬数が10,000頭以上
- [ ] metadataに`version`, `created_at`, `total_horses`が含まれる
- [ ] 最新の週末レースデータが含まれる
- [ ] track_nameが「大井」「川崎」「船橋」「浦和」になっている（会場補正成功）
- [ ] レース追加馬の`last_update`が更新日時になっている
- [ ] 既存馬（レース追加なし）の`last_update`が古いまま（正常）
- [ ] 会場補正率が90%以上
- [ ] CDN URLでアクセス可能
- [ ] ファイル名が`nar_unified_knowledge.json`で固定

### 騎手のナレッジファイル

- [ ] ファイルサイズが80-100MB程度
- [ ] 総騎手数が300名以上
- [ ] 最新の週末レースデータが含まれる
- [ ] 複勝率が再計算されている
- [ ] `venue_course_stats`, `track_condition_stats`などの統計が更新されている
- [ ] `processed_at`が更新されている
- [ ] CDN URLでアクセス可能
- [ ] ファイル名が`nankan_jockey_knowledge_20250907.json`で固定

---

## 🚨 絶対に守ること

### 1. スケジュールマスターの重要性
- ✅ スケジュールマスターは**絶対に削除禁止**（会場補正の生命線）
- ✅ 実行前に必ずスケジュールマスターの存在を確認
- ✅ スケジュールマスターの期間が最新であることを確認

### 2. テーブル名の違い
- ✅ 地方競馬版は `nvd_*` テーブル（JRAの `jvd_*` ではない）
- ❌ テーブル名を間違えない

### 3. 会場補正率の確認
- ✅ 会場補正率が90%以上であることを確認
- ❌ 50%以下の場合は何か問題がある

### 4. データの正確性
- ✅ PostgreSQLから取得したデータをそのまま使用
- ❌ 手動でデータを編集しない

### 5. 既存データの保護
- ✅ 差分更新のみ実行（既存データを破壊しない）
- ✅ 既存ナレッジファイルをCDNからダウンロードしてから更新

### 6. CDN URLの固定
- ✅ ファイル名を固定
  - 馬版: `nar_unified_knowledge.json`
  - 騎手版: `nankan_jockey_knowledge_20250907.json`
- ❌ ファイル名を変更しない（URL変更が必要になる）

### 7. last_updateフィールドの更新
- ✅ レースを追加した馬のみ`last_update`を更新
- ✅ 新規追加馬にも`last_update`を設定
- ❌ レース追加がない馬の`last_update`は更新しない

---

## 📅 運用サイクル

1. **毎週月曜日朝**: 週次更新スクリプト実行（馬 → 騎手の順）
2. **スケジュールマスター確認**: 期間が最新であることを確認
3. **検証**: ローカルファイルの整合性確認（会場補正率など）
4. **ファイル名変更**: 固定ファイル名に変更
5. **アップロード**: CDNに新ファイルをアップロード
6. **本番確認**: CDN URLで正常性確認
7. **会場補正率確認**: 90%以上であることを確認

---

## 📊 品質指標

### 正常値の目安

**馬のナレッジファイル:**
- **総馬数**: 10,000-15,000頭
- **ファイルサイズ**: 100-150MB
- **会場補正率**: 90%以上（最重要！）
- **処理時間**: 約30-60秒

**騎手のナレッジファイル:**
- **総騎手数**: 300-400名
- **ファイルサイズ**: 80-100MB
- **複勝率範囲**: トップジョッキー40-50%、中堅20-30%
- **処理時間**: 約20-40秒

---

## 📞 関連ドキュメント

- JRA週次更新マニュアル: `JRA_WEEKLY_UPDATE_MANUAL.md`
- 地方競馬騎手SDKマニュアル: 提供済みのマニュアル参照
- スケジュールマスター作成方法: `add_YYYY_schedule.py`

---

## 🆚 JRA版との主な違いまとめ

| 項目 | JRA | 地方競馬（南関東） |
|------|-----|------------------|
| **テーブル名** | jvd_se, jvd_ra, jvd_um | **nvd_se, nvd_ra, nvd_um** |
| **開催場所コード信頼性** | ✅ 高い | ❌ 低い（使用不可） |
| **フィルター方法** | 開催場所コード | **スケジュールマスター + 開催場所コード** |
| **会場補正** | 不要 | **4段階補正システム（必須）** |
| **補正率目標** | - | **90%以上** |
| **スケジュールマスター** | 不要 | **必須（削除禁止）** |
| **対象競馬場** | 10場（札幌-小倉） | **4場（大井、川崎、船橋、浦和）** |
| **データベース** | pckeiba | pckeiba（同じ） |
| **CDN URL** | unified_knowledge_20250903.json | nar_unified_knowledge.json |
| **騎手CDN URL** | jockey_knowledge.json | nankan_jockey_knowledge_20250907.json |

---

## 🚨 緊急時対応

データ異常や処理エラーが発生した場合：

1. **ログ確認**
   ```bash
   # エラーメッセージを確認
   tail -n 100 /mnt/e/dev/Cusor/chatbot/uma/backend/logs/nar_weekly.log
   ```

2. **スケジュールマスター確認**
   ```bash
   ls -lh /mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json
   ```

3. **会場補正率確認**
   - 90%以上: 正常
   - 50-90%: 警告（要調査）
   - 50%以下: 異常（スケジュールマスター問題）

4. **前回の正常ファイルを復元**
   ```bash
   # バックアップから復元（バックアップがある場合）
   cp /mnt/e/dev/Cusor/chatbot/uma/BACKUP_NAR_*/nar_unified_knowledge.json .
   ```

5. **手動で再実行**
   ```bash
   python3 update_nar_weekly.py
   ```

---

**最終更新**: 2025-10-06  
**次回更新予定**: 2025-10-13 (月曜日)

**重要**: このマニュアルは地方競馬版（南関東）専用です。JRA版とは手順が異なります。
