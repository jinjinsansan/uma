# JRA週次更新スクリプト運用マニュアル

## 📝 概要
JRA統合ナレッジファイルを毎週更新するためのスクリプト運用手順書

## 🔧 スクリプト情報
- **ファイル名**: `/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/update_jra_weekly.py`
- **実行タイミング**: 毎週月曜日（週末レース終了後）
- **処理内容**: 土日のレースデータを既存ナレッジファイルに差分追加

## 📊 必須フィールド（38項目）
週次更新時、以下のフィールドがすべて含まれることを確認：
```
基本フィールド（30項目）:
- BAMEI, RACE_CODE, KAISAI_NEN, KAISAI_GAPPI, KAKUTEI_CHAKUJUN
- TANSHO_ODDS, TANSHO_NINKIJUN, FUTAN_JURYO, BATAIJU, ZOGEN_SA
- KISHUMEI_RYAKUSHO, CHOKYOSHIMEI_RYAKUSHO
- CORNER1_JUNI, CORNER2_JUNI, CORNER3_JUNI, CORNER4_JUNI
- SOHA_TIME, BAREI, SEIBETSU_CODE, KEIBAJO_CODE, RACE_BANGO
- KETTO_TOROKU_BANGO, TIME_SA, KYORI, TRACK_CODE
- SHIBA_BABAJOTAI_CODE, DIRT_BABAJOTAI_CODE, TENKO_CODE
- sire, broodmare_sire

追加フィールド（8項目）2025年9月追加:
- KYOSOMEI_HONDAI（レース名）
- GRADE_CODE（グレード）
- KOHAN_3F（個馬の後半3F）
- ZENHAN_3F（前半3F - ra.zenhan_3fから取得）
- RACE_KOHAN_3F（レース全体の後半3F - ra.kohan_3fから取得）
- DOCHAKU_TOSU（同着頭数）
- UMABAN（馬番）
- WAKUBAN（枠番）
```

## ⚠️ 重要な注意事項

### データベースフィールドのマッピング
```python
# 正しいマッピング（2025年9月24日確認済み）
- se.kohan_3f → KOHAN_3F（個馬の後半3F）
- ra.zenhan_3f → ZENHAN_3F（前半3F） ✅ 存在する
- ra.kohan_3f → RACE_KOHAN_3F（レース全体） ✅ 存在する
- ra.race_kohan_3f → ❌ 存在しない（使用不可）
```

### PostgreSQL接続情報
```python
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",  # ⚠️ keiba_dwではなくpckeiba
    "user": "postgres",
    "password": "postgres"
}
```

## 🚀 実行手順

### 1. 通常の週次更新
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 scripts/update_jra_weekly.py
```

### 2. 生成されるファイル
- ファイル名: `unified_knowledge_YYYYMMDD.json`
- サイズ: 約290-300MB
- 形式: JSON（horses構造）

### 3. CDNアップロード

#### 方法1: 新しいAPI認証情報でアップロード（2025年9月作成）
```python
# scripts/simple_upload.py を使用
ACCESS_KEY = "62b127c384fe4a78f4110c5fd3ebbf4e"
SECRET_KEY = "2876eb1b13d17ed1b002fb9164ce6db7d81f989cff3a848d72c17749a1f31a26"
ENDPOINT = "https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com"
BUCKET = "dlogic-knowledge-files"

# ファイル名を変更してからアップロード
mv unified_knowledge_YYYYMMDD.json unified_knowledge_20250903.json
python3 scripts/simple_upload.py
```

#### 方法2: Cloudflareダッシュボードから手動アップロード
- R2 Storage → dlogic-knowledge-files バケット
- ファイル名: `unified_knowledge_20250903.json`で上書き

### 4. 公開URL
```
https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json
```

## 🔍 動作確認

### 正常な実行結果の例
```
🏇 JRA週次更新処理開始
📥 既存ナレッジファイルをダウンロード中...
✅ 39768頭のデータをダウンロード完了
📅 更新対象: 2025年 0920(土) - 0921(日)
📊 PostgreSQL接続中...
🔍 週末のレースデータ取得中...
📊 更新結果:
  新規レース: 607件
  更新された馬: 0頭
  総馬数: 39768頭
💾 ファイル保存中: unified_knowledge_20250924.json
✅ 保存完了: 292.9MB
```

## ❌ トラブルシューティング

### エラー: 列が存在しません
- `race_kohan_3f`は存在しない → `ra.kohan_3f`を使用
- `se.zenhan_3f`は存在しない → `ra.zenhan_3f`を使用

### エラー: boto3がインストールされていない
```bash
pip3 install --break-system-packages boto3
# または
python3 scripts/simple_upload.py を使用（requestsのみ必要）
```

### エラー: SSL証明書エラー
- `simple_upload.py`を使用（requestsベースで回避済み）

## 📅 運用サイクル
1. **毎週月曜日朝**: 週次更新スクリプト実行
2. **確認**: 新規レース数と総馬数を確認
3. **アップロード**: CDNに新ファイルをアップロード
4. **検証**: 本番環境でViewLogic等のエンジンが正常動作することを確認

## 🔧 関連ファイル
- `/scripts/update_jra_weekly.py` - メイン更新スクリプト
- `/scripts/simple_upload.py` - CDNアップロード用
- `/services/dlogic_raw_data_manager.py` - CDN URLの設定場所

## 📝 更新履歴
- 2025-09-24: 不足していた8フィールドを追加、完全38フィールド対応
- 2025-09-24: 新しいCloudflare R2 API認証情報に更新
- 2025-09-24: simple_upload.pyでSSL問題を解決

## ⚠️ 絶対に守ること
1. **フィールドの完全性**: 38フィールドすべてが含まれていることを確認
2. **データの正確性**: デフォルト値や仮データは絶対に使用しない
3. **既存データの保護**: 差分更新時は既存データを破壊しない
4. **CDN URLの固定**: unified_knowledge_20250903.jsonの名前を維持

---
最終更新: 2025-09-24
作成者: Claude (週次更新スクリプト修正対応)