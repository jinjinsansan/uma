# JRA週次更新完全マニュアル

**最終更新**: 2025-10-06  
**作成者**: Droid (週次更新対応)

---

## 📝 概要

JRA統合ナレッジファイル（馬版・騎手版）を毎週更新するための完全手順書

---

## 🔧 スクリプト情報

### 馬のナレッジファイル
- **ファイル名**: `/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/update_jra_weekly.py`
- **実行タイミング**: 毎週月曜日（週末レース終了後）
- **処理内容**: 土日のレースデータを既存ナレッジファイルに差分追加

### 騎手のナレッジファイル
- **ファイル名**: `/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/update_jockey_weekly.py`
- **実行タイミング**: 馬のナレッジファイル更新後
- **処理内容**: 土日のレースデータで騎手統計を更新

---

## 📊 馬のナレッジファイル - 必須フィールド（38項目）

週次更新時、以下のフィールドがすべて含まれることを確認：

### 基本フィールド（30項目）
- BAMEI, RACE_CODE, KAISAI_NEN, KAISAI_GAPPI, KAKUTEI_CHAKUJUN
- TANSHO_ODDS, TANSHO_NINKIJUN, FUTAN_JURYO, BATAIJU, ZOGEN_SA
- KISHUMEI_RYAKUSHO, CHOKYOSHIMEI_RYAKUSHO
- CORNER1_JUNI, CORNER2_JUNI, CORNER3_JUNI, CORNER4_JUNI
- SOHA_TIME, BAREI, SEIBETSU_CODE, KEIBAJO_CODE, RACE_BANGO
- KETTO_TOROKU_BANGO, TIME_SA, KYORI, TRACK_CODE
- SHIBA_BABAJOTAI_CODE, DIRT_BABAJOTAI_CODE, TENKO_CODE
- sire, broodmare_sire

### 追加フィールド（8項目）※2025年9月追加
- KYOSOMEI_HONDAI（レース名）
- GRADE_CODE（グレード）
- KOHAN_3F（個馬の後半3F）
- ZENHAN_3F（前半3F）
- RACE_KOHAN_3F（レース全体の後半3F）
- DOCHAKU_TOSU（同着頭数）
- UMABAN（馬番）
- WAKUBAN（枠番）

### メタデータフィールド
- **last_update**: 各馬のデータ更新日時（ISO 8601形式）
  - ⚠️ **重要**: レースを追加した馬のみ更新される
  - 新規追加馬: 追加時の日時
  - 既存馬（レース追加あり）: 最新レース追加時の日時
  - 既存馬（レース追加なし）: 古い日時のまま（正常）

---

## ⚠️ データベースフィールドマッピング

### 正しいマッピング（2025年9月24日確認済み）

```python
# ✅ 正しい
se.kohan_3f → KOHAN_3F        # 個馬の後半3F
ra.zenhan_3f → ZENHAN_3F       # 前半3F
ra.kohan_3f → RACE_KOHAN_3F    # レース全体の後半3F

# ❌ 存在しない（使用不可）
ra.race_kohan_3f  # このフィールドは存在しない
se.zenhan_3f      # このフィールドは存在しない
```

---

## 🔌 PostgreSQL接続情報

```python
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",  # ⚠️ keiba_dwではなくpckeiba
    "user": "postgres",
    "password": "postgres"
}
```

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

#### 1.1 週次更新スクリプト実行

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 scripts/update_jra_weekly.py
```

**期待される出力:**
```
🏇 JRA統合ナレッジファイル週次更新
================================================================================
📥 既存ナレッジファイルをダウンロード中...
✅ 53638頭のデータをダウンロード完了

📅 更新対象: 2025年 1004(土) - 1005(日)

📊 PostgreSQL接続中...
🔍 週末のレースデータ取得中...

📊 更新結果:
  新規レース: 683件
  更新された馬: 137頭
  総馬数: 53638頭
  コーナー補完適用レース: 514

💾 ファイル保存中: unified_knowledge_20251006.json
✅ 保存完了: 475.8MB
```

#### 1.2 ファイル名を固定

⚠️ **重要**: CDN URLを変更しないため、ファイル名を固定

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
mv unified_knowledge_YYYYMMDD.json unified_knowledge_20250903.json
ls -lh unified_knowledge_20250903.json
```

#### 1.3 CDNにアップロード

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 scripts/simple_upload.py
```

**期待される出力:**
```
📁 アップロードファイル: unified_knowledge_20250903.json
📊 サイズ: 475.8MB
⬆️ Cloudflare R2にアップロード中...
✅ アップロード成功！
🔗 公開URL:
  https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json
```

#### 1.4 馬のナレッジファイル検証

```bash
# ヘッダー確認
curl -I https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json

# メタデータ確認
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json | \
python3 -c "import json, sys; data=json.load(sys.stdin); \
print(f\"総馬数: {data['metadata']['total_horses']}\"); \
print(f\"作成日時: {data['metadata']['created_at']}\"); \
print(f\"バージョン: {data['metadata']['version']}\")"

# 最新レースデータ確認（10月データが含まれるか）
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json | \
python3 -c "
import json, sys
data = json.load(sys.stdin)
# 10月のレースがある馬を探す
for horse_name, horse in list(data['horses'].items())[:10]:
    for race in horse['races']:
        if race.get('KAISAI_GAPPI', '').startswith('10') and race.get('KAISAI_NEN') == '2025':
            print(f'{horse_name}: {race[\"KAISAI_NEN\"]}-{race[\"KAISAI_GAPPI\"]} (last_update: {horse.get(\"last_update\", \"なし\")})')
            break
"

# last_updateフィールド確認
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json | \
python3 -c "
import json, sys
data = json.load(sys.stdin)
sample_horses = list(data['horses'].keys())[:5]
for horse_name in sample_horses:
    horse = data['horses'][horse_name]
    print(f'{horse_name}: last_update={horse.get(\"last_update\", \"なし\")}')
"
```

**期待される結果:**
- ✅ ファイルサイズ: 約475-476MB
- ✅ 総馬数: 53,000頭以上
- ✅ 作成日時: 実行日の日時
- ✅ 10月のレースデータが含まれる
- ✅ レース追加馬の `last_update` が実行日の日時

---

### ステップ2: 騎手のナレッジファイル更新

#### 2.1 週次更新スクリプト実行

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 scripts/update_jockey_weekly.py
```

**期待される出力:**
```
🏇 JRA騎手ナレッジファイル週次更新
================================================================================
📥 既存騎手ナレッジファイルをダウンロード中...
✅ 239名の騎手データをダウンロード完了

📅 更新対象: 2025年 1004(土) - 1005(日)

📊 PostgreSQL接続中...
🔍 週末の騎手成績データ取得中...
📊 複勝率を再計算中...

📊 更新結果:
  新規レース: 683件
  更新された騎手: 114名
  総騎手数: 239名

💾 ファイル保存中: jockey_knowledge_20251006.json
✅ 保存完了: 75.9MB
```

#### 2.2 ファイル名を固定

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
mv jockey_knowledge_YYYYMMDD.json jockey_knowledge.json
ls -lh jockey_knowledge.json
```

#### 2.3 CDNにアップロード

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 scripts/simple_upload_jockey.py
```

**期待される出力:**
```
📁 アップロードファイル: jockey_knowledge.json
📊 サイズ: 75.9MB
⬆️ Cloudflare R2にアップロード中...
✅ アップロード成功！
🔗 公開URL:
  https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json
```

#### 2.4 騎手のナレッジファイル検証

```bash
# ヘッダー確認
curl -I https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json

# 基本情報確認
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json | \
python3 -c "import json, sys; data=json.load(sys.stdin); \
print(f'総騎手数: {len(data)}'); \
sample_jockey = list(data.keys())[0]; \
print(f'サンプル騎手: {sample_jockey}'); \
print(f'会場コース統計数: {len(data[sample_jockey][\"venue_course_stats\"])}')"

# 最新レースデータ確認（10月データが含まれるか）
curl -s https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json | \
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
- ✅ ファイルサイズ: 約75-76MB
- ✅ 総騎手数: 200名以上
- ✅ 10月のレースデータが含まれる
- ✅ 複勝率が再計算されている

---

## 📦 ファイル構造

### 馬のナレッジファイル構造

```json
{
  "metadata": {
    "version": "3.0",
    "created_at": "2025-10-06T22:57:47.309848",
    "total_horses": 53638,
    "data_period": "None-2025",
    "sdk_version": "JRA_SDK_V2",
    "engines": {
      "D-Logic": {
        "description": "標準12項目分析",
        "required_fields": [...]
      },
      "I-Logic": {...},
      "ViewLogic": {...}
    }
  },
  "horses": {
    "馬名": {
      "horse_name": "馬名",
      "total_races": 7,
      "races": [
        {
          "BAMEI": "馬名",
          "RACE_CODE": "20251005060612",
          "KAISAI_NEN": "2025",
          "KAISAI_GAPPI": "1005",
          "KAKUTEI_CHAKUJUN": "01",
          ... (38フィールド)
        }
      ],
      "last_update": "2025-10-06T22:57:47.303044"
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
      "競馬場_距離": {
        "results": [
          {
            "date": "2025-1005",
            "horse_name": "馬名",
            "position": 1,
            "total_horses": 16,
            "is_fukusho": true
          }
        ],
        "fukusho_rate": 50.0,
        "race_count": 10
      }
    },
    "track_condition_stats": {...},
    "post_position_stats": {...},
    "sire_stats": {...},
    "processed_at": "2025-10-06T23:14:11.123456",
    "overall_stats": {
      "total_races_analyzed": 100,
      "overall_fukusho_rate": 30.0
    }
  }
}
```

---

## 📋 生成されるファイル一覧

| ファイル | サイズ | 説明 | CDN URL |
|---------|--------|------|---------|
| `unified_knowledge_20250903.json` | 約476MB | 馬のナレッジファイル | https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json |
| `jockey_knowledge.json` | 約76MB | 騎手のナレッジファイル | https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json |

---

## ❌ トラブルシューティング

### エラー: 列が存在しません

**症状:**
```
ERROR: column "race_kohan_3f" does not exist
```

**原因:**
- `ra.race_kohan_3f`は存在しない
- `se.zenhan_3f`は存在しない

**解決策:**
- `ra.kohan_3f` → `RACE_KOHAN_3F` を使用
- `ra.zenhan_3f` → `ZENHAN_3F` を使用

---

### エラー: SSL証明書エラー

**症状:**
```
SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol (_ssl.c:2406)'))
```

**原因:**
- ファイルサイズが大きく、デフォルトタイムアウトで失敗

**解決策:**
- `simple_upload.py`で`timeout=600`を指定済み（10分）
- ネットワーク環境を確認

---

### エラー: 認証エラー

**症状:**
```
403 Forbidden
```

**原因:**
- Cloudflare R2のAPI認証情報が古い

**解決策:**
- 最新の認証情報を使用（2025-10-06更新済み）
- `simple_upload.py`の`ACCESS_KEY`と`SECRET_KEY`を確認

---

### エラー: last_updateフィールドがない

**症状:**
- 一部の馬に`last_update`フィールドが存在しない

**原因:**
- 新規追加馬でスクリプトの`last_update`追加処理が実行されていない

**解決策:**
- `update_jra_weekly.py`の以下の部分を確認:
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

### エラー: PostgreSQL接続失敗

**症状:**
```
could not connect to server: Connection refused
```

**原因:**
- データベースホストが起動していない
- 接続情報が間違っている

**解決策:**
- データベース接続情報を確認:
  - Host: `172.25.160.1`
  - Port: `5432`
  - Database: `pckeiba` (⚠️ `keiba_dw`ではない)
  - User: `postgres`
  - Password: `postgres`

---

## 🔍 検証チェックリスト

### 馬のナレッジファイル

- [ ] ファイルサイズが475-476MB程度
- [ ] 総馬数が53,000頭以上
- [ ] metadataに`version`, `created_at`, `total_horses`が含まれる
- [ ] 38必須フィールドが全て含まれる
- [ ] 最新の週末レースデータが含まれる
- [ ] レース追加馬の`last_update`が更新日時になっている
- [ ] 既存馬（レース追加なし）の`last_update`が古いまま（正常）
- [ ] CDN URLでアクセス可能
- [ ] ファイル名が`unified_knowledge_20250903.json`で固定

### 騎手のナレッジファイル

- [ ] ファイルサイズが75-76MB程度
- [ ] 総騎手数が200名以上
- [ ] 最新の週末レースデータが含まれる
- [ ] 複勝率が再計算されている
- [ ] `venue_course_stats`, `track_condition_stats`などの統計が更新されている
- [ ] CDN URLでアクセス可能
- [ ] ファイル名が`jockey_knowledge.json`で固定

---

## 🚨 絶対に守ること

### 1. フィールドの完全性
- ✅ 38フィールドすべてが含まれていることを確認
- ❌ デフォルト値や仮データは絶対に使用しない

### 2. データの正確性
- ✅ PostgreSQLから取得したデータをそのまま使用
- ❌ 手動でデータを編集しない

### 3. 既存データの保護
- ✅ 差分更新のみ実行（既存データを破壊しない）
- ✅ 既存ナレッジファイルをCDNからダウンロードしてから更新

### 4. CDN URLの固定
- ✅ ファイル名を固定（`unified_knowledge_20250903.json`, `jockey_knowledge.json`）
- ❌ ファイル名を変更しない（URL変更が必要になる）

### 5. last_updateフィールドの更新
- ✅ レースを追加した馬のみ`last_update`を更新
- ✅ 新規追加馬にも`last_update`を設定
- ❌ レース追加がない馬の`last_update`は更新しない

---

## 📅 運用サイクル

1. **毎週月曜日朝**: 週次更新スクリプト実行
2. **確認**: 新規レース数と総数を確認
3. **検証**: ローカルファイルの整合性確認
4. **アップロード**: CDNに新ファイルをアップロード
5. **本番確認**: CDN URLで正常性確認
6. **動作確認**: 本番環境でエンジンが正常動作することを確認

---

## 📊 更新履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2025-09-24 | 38フィールド対応、新API認証情報 | Claude |
| 2025-10-06 | last_updateフィールド追加、騎手ナレッジ対応 | Droid |

---

## 🔗 関連ファイル

### スクリプト
- `/scripts/update_jra_weekly.py` - 馬のナレッジ週次更新
- `/scripts/update_jockey_weekly.py` - 騎手のナレッジ週次更新
- `/scripts/simple_upload.py` - 馬のナレッジCDNアップロード
- `/scripts/simple_upload_jockey.py` - 騎手のナレッジCDNアップロード

### 設定ファイル
- データベース接続情報は各スクリプト内にハードコード
- Cloudflare R2認証情報は各アップロードスクリプト内にハードコード

### データファイル
- `/services/dlogic_raw_data_manager.py` - CDN URLの設定場所

---

## 📞 サポート

問題が発生した場合:
1. エラーメッセージを確認
2. トラブルシューティングセクションを参照
3. データベース接続とAPI認証情報を確認
4. 検証チェックリストで問題箇所を特定

---

**最終確認日**: 2025-10-06  
**次回更新予定**: 2025-10-13 (月曜日)
