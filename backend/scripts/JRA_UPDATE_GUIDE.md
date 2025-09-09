# JRA統合ナレッジファイル 週次差分更新 完全指示書

## 📅 更新スケジュール
- **実行日時**: 毎週月曜日
- **対象データ**: 週末（土日）開催のJRAレース結果
- **処理時間**: 約1-2分で完了

## ⚠️ 重要事項
- **PostgreSQL（PC-KEIBA）のみ使用** - MySQLは使用しません
- **既存データに追加更新** - 上書きではなく差分追加
- **9走制限を維持** - 新レース追加時は最古を削除

## 🔧 事前準備

### 1. PostgreSQL接続情報
```python
CONNECTION_PARAMS = {
    "host": "172.25.160.1",  # WSL2からWindowsのPostgreSQL
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}
```

### 2. 必要なPythonライブラリ
```bash
pip install psycopg2-binary requests
```

### 3. Cloudflare URLs
- 統合ナレッジ: `https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json`
- 騎手ナレッジ: `https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge_[日付].json`

## 📝 更新手順

### ステップ1: 更新スクリプトの実行

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 update_jra_weekly.py
```

## 🔄 更新ロジック

### 統合ナレッジファイル更新
1. **既存ファイルをCloudflareからダウンロード**
2. **週末の新レースデータをPostgreSQLから取得**
3. **各馬のデータを更新**:
   - 新レースを先頭に追加
   - 9走を超える場合は最古を削除
   - 血統情報（父名・母父名）も取得
4. **更新済みファイルを保存**

### 騎手ナレッジファイル更新
1. **既存ファイルをダウンロード**
2. **週末の騎手成績を取得**
3. **各統計を更新**:
   - venue_course_stats（競馬場×距離）
   - track_condition_stats（馬場状態）
   - post_position_stats（枠番）
   - sire_stats（種牡馬）
4. **複勝率を再計算**

## 💾 出力ファイル
- `unified_knowledge_[更新日].json` - 更新済み統合ナレッジ
- `jockey_knowledge_[更新日].json` - 更新済み騎手ナレッジ

## ✅ 確認項目
- [ ] PC-KEIBAが最新データを取得済み
- [ ] PostgreSQLサービスが起動中
- [ ] WSL2からPostgreSQLに接続可能
- [ ] Cloudflareから既存ファイルがダウンロード可能

## 🚨 トラブルシューティング

### PostgreSQL接続エラー
```bash
# Windows側でPostgreSQLサービス確認
netstat -an | findstr 5432

# ファイアウォール確認（PowerShell管理者権限）
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*PostgreSQL*"}
```

### データ取得エラー
- PC-KEIBAで最新データを更新（速報系データ更新）
- 土日のレースが月曜朝に反映されているか確認

## 📌 注意事項
- **血統情報**: ketto_joho_01b（父名）、ketto_joho_02b（母父名）を使用
- **競馬場コード**: 01-10のみ（海外レース除外）
- **データ品質**: 着順不明（kakutei_chakujun='00'）は除外

---

## 🔧 更新スクリプト本体

`update_jra_weekly.py`として以下のスクリプトを使用してください。