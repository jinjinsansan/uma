# 地方競馬（NAR）ナレッジファイル生成システム v9 Perfect Base

## 概要
地方競馬の全馬データを自動取得し、ViewLogic互換のJSONファイルを生成するSDKツールです。

## 主な機能
- 実行日から7年間のデータを自動取得
- 各馬最新9走までのレース情報（41フィールド）
- 会場補正システム（90%以上の精度）
- 既存CDN構造との完全互換性
- 毎週自動実行対応

## システム構成

### メインファイル
- `create_nar_horse_knowledge_v9_perfect_base.py` - メインSDKツール
- `run_nar_knowledge_weekly.sh` - 週次自動実行スクリプト
- `test_db_connection.py` - データベース接続テスト
- `test_venue_correction.py` - 会場補正システムテスト

### データファイル
- `/data/nankan_schedule_master_2024_2025.json` - スケジュールマスター（2024-2025年）
- `/data/nar_knowledge/nar_knowledge_latest.json` - 最新のナレッジファイル
- `/data/nar_knowledge/archive/` - 過去のナレッジファイルアーカイブ

## 実行方法

### 手動実行
```bash
# メインスクリプトを直接実行
python3 create_nar_horse_knowledge_v9_perfect_base.py

# または週次スクリプトを使用
./run_nar_knowledge_weekly.sh
```

### 自動実行（cron設定）
```bash
# 毎週月曜日午前2時に実行
0 2 * * 1 /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/run_nar_knowledge_weekly.sh
```

## データベース接続
```python
CONNECTION_PARAMS = {
    "host": "172.25.160.1",    # WSL2からWindowsのPostgreSQL
    "port": "5432",
    "database": "pckeiba",      # PC-KEIBAデータベース
    "user": "postgres",
    "password": "postgres"
}
```

## 会場補正システム

### 4段階補正
1. **公式重賞レース辞書** - 29レースの固定会場情報
2. **非重賞パターン** - 特定レース名パターンによる補正
3. **スケジュールマスター** - 日付ベースの正確な会場情報
4. **パターンマッチング** - レース名からの推定（フォールバック）

### 対象会場コード
- `42`: 大井
- `43`: 川崎
- `44`: 船橋
- `45`: 浦和
- `35`: 盛岡
- `36`: 水沢

## 出力形式

### JSONデータ構造
```json
{
  "馬名": {
    "horse_name": "馬名",
    "total_races": 9,
    "races": [
      {
        "BAMEI": "馬名",
        "RACE_CODE": "20210701420700",
        "KAISAI_NEN": "2021",
        "KAISAI_GAPPI": "0701",
        "KEIBAJO_CODE": "42",
        ... (全41フィールド)
      }
    ],
    "last_update": "2025-09-24T22:00:00"
  }
}
```

## 性能指標
- 処理馬数: 約25,000頭
- 処理レース数: 約170,000レース
- 会場補正率: 29.4%（スケジュールマスター依存）
- ファイルサイズ: 約220MB
- 処理時間: 約2-3分

## 注意事項
- PostgreSQLサービスが起動している必要があります
- スケジュールマスターファイルは定期的な更新が必要です（現在2024-2025年分）
- 生成ファイルは100MBを超えるため、GitHubにプッシュしないでください

## 今後の拡張予定
- 2023年以前のスケジュールマスター追加
- 会場補正率の向上（目標: 50%以上）
- CDNへの自動アップロード機能
- エラー通知機能の追加

## 更新履歴
- 2025-09-24: v9 Perfect Base 初版完成
  - 7年間データ自動取得
  - 会場補正システム実装
  - JSON出力機能実装
  - 自動実行スクリプト作成