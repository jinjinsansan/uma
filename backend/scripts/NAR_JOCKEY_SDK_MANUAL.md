# 🏇 地方競馬版騎手ナレッジファイルSDKツール運用マニュアル

## 📅 作成日: 2025-09-25
## 🎯 目的: 騎手統計データの週次更新と管理

---

## 🔧 概要

### ツール情報
- **スクリプト名**: `create_nar_jockey_knowledge_v1_perfect.py`
- **出力ファイル**: `nankan_jockey_knowledge_20250907.json`
- **データ期間**: 2019-2025年（7年間全データ）
- **制限**: なし（40走制限撤廃）
- **補正率**: 52.1%達成（2025-09-25実績）

### 主要機能
- 騎手別統計データの集計
- 4カテゴリー別複勝率計算
- 会場補正システム（4段階）
- JRA版と完全互換のJSON出力

---

## 📊 データ仕様

### 集計カテゴリー（全データ・制限なし）
1. **venue_course_stats** - 会場×距離別成績
2. **track_condition_stats** - 馬場状態別成績
3. **post_position_stats** - 枠番別成績
4. **sire_stats** - 種牡馬別成績

### 複勝率計算式
```
複勝率 = (3着以内の回数 ÷ 総騎乗回数) × 100
```

### 対象競馬場
- 42: 大井
- 43: 川崎
- 44: 船橋
- 45: 浦和
- 35: 盛岡
- 36: 水沢

---

## 🚀 実行手順

### 1. 作業ディレクトリへ移動
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
```

### 2. SDKツール実行
```bash
python3 create_nar_jockey_knowledge_v1_perfect.py
```

### 3. 実行時の出力確認
```
================================================================================
地方競馬版騎手ナレッジファイル作成 v1 Perfect
================================================================================

期待される出力:
✅ スケジュールマスター読み込み成功（1223日分）
✅ データ取得成功（約34万レコード）
✅ 騎手数（約380-400名）
✅ 補正率（50%以上が理想）
✅ ファイルサイズ（約300-350MB）
```

### 4. 生成ファイルの確認
```bash
# ファイルサイズとタイムスタンプ確認
ls -lh nankan_jockey_knowledge_20250907.json

# JSON構造の検証
python3 -c "
import json
with open('nankan_jockey_knowledge_20250907.json') as f:
    data = json.load(f)
    print(f'✅ metadata: {\"metadata\" in data}')
    print(f'✅ jockeys: {\"jockeys\" in data}')
    print(f'騎手数: {len(data.get(\"jockeys\", {}))}')
"
```

---

## ☁️ CDN（Cloudflare R2）へのアップロード

### 300MB以下の場合（Webコンソール）
1. Cloudflare R2ダッシュボードにログイン
2. `dlogic-knowledge-files`バケットを選択
3. 既存ファイルを削除
4. 新ファイルをアップロード

### 300MB超えの場合（APIアップロード）
```bash
# APIアップロードスクリプト実行
python3 simple_r2_upload.py

# 注意: 使用後は必ずAPIトークンを無効化
```

### パブリックURL
```
https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json
```

---

## 🔄 週次更新スケジュール

### 推奨更新タイミング
- **毎週月曜日 午前4:00**（馬ナレッジの1時間後）
- レース結果確定後の更新が理想

### cron設定例
```bash
# crontab -e
0 4 * * 1 cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts && python3 create_nar_jockey_knowledge_v1_perfect.py >> /mnt/e/dev/Cusor/chatbot/uma/backend/logs/jockey_weekly.log 2>&1
```

---

## 🛠️ 重要な依存関係

### 必須ファイル
1. **スケジュールマスター**
   ```
   /mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json
   ```
   - 会場補正の要（絶対に削除禁止）

2. **データベース接続**
   ```python
   CONNECTION_PARAMS = {
       "host": "172.25.160.1",
       "port": "5432",
       "database": "pckeiba",  # 小文字必須！
       "user": "postgres",
       "password": "postgres"
   }
   ```

3. **使用テーブル**
   - `nvd_se` - レース成績
   - `nvd_ra` - レース情報（kyosomei_hondai使用）
   - `nvd_um` - 馬プロフィール（血統情報）

---

## 🔍 トラブルシューティング

### 問題: データベース接続エラー
```
UnicodeDecodeError: 'utf-8' codec can't decode
```
**解決**: データベース名を`pckeiba`（小文字）に確認

### 問題: レース名カラムが見つからない
**解決**: `ra.kyosomei_hondai`または`ra.kyosomei_ryakusho_10`を使用

### 問題: 補正率が低い（40%以下）
**原因**: スケジュールマスター未読み込み
**解決**:
```bash
# スケジュールマスター確認
ls -lh /mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json
```

### 問題: ファイルサイズが300MB超え
**解決**: APIアップロードスクリプト使用
```bash
python3 simple_r2_upload.py
```

### 問題: メモリ不足エラー
**解決**: 他のプロセスを停止してから実行

---

## 📈 品質指標

### 正常値の目安
- **騎手数**: 380-400名
- **総レコード数**: 34万-40万
- **会場補正率**: 50%以上
- **ファイルサイズ**: 300-350MB
- **処理時間**: 約30-60秒

### 上位騎手の複勝率目安
- トップジョッキー: 45-55%
- 中堅騎手: 25-35%
- 新人騎手: 15-25%

---

## 🔐 バックアップ

### 定期バックアップ推奨
```bash
# バックアップディレクトリ作成
BACKUP_DIR="/mnt/e/dev/Cusor/chatbot/uma/BACKUP_JOCKEY_$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 重要ファイルのバックアップ
cp nankan_jockey_knowledge_20250907.json "$BACKUP_DIR/"
cp create_nar_jockey_knowledge_v1_perfect.py "$BACKUP_DIR/"

echo "✅ バックアップ完了: $BACKUP_DIR"
```

---

## 📝 更新履歴

| 日付 | バージョン | 内容 | 補正率 |
|------|------------|------|--------|
| 2025-09-25 | v1.0 | 初版作成 | 52.1% |
| | | 40走制限撤廃 | |
| | | 7年間全データ使用 | |

---

## ⚠️ 注意事項

### 絶対厳守
1. **データベース名は小文字**: `pckeiba`（PC-KEIBAではない）
2. **スケジュールマスター削除禁止**: 会場補正の生命線
3. **ファイル名固定**: `nankan_jockey_knowledge_20250907.json`
4. **40走制限なし**: 7年間全データを使用

### APIトークン管理
- 使用後は必ず無効化
- トークンをコードに残さない
- 定期的に再生成

### データ品質
- 補正率50%以上を維持
- 騎手数の急激な変動に注意
- 異常値があれば原因調査

---

## 📞 関連ドキュメント

- 馬ナレッジマニュアル: `NAR_WEEKLY_UPDATE_MANUAL.md`
- 実装計画書: `NAR_JOCKEY_SDK_PLAN.md`
- スケジュール追加: `add_YYYY_schedule.py`

---

## 🚨 緊急時対応

データ異常や処理エラーが発生した場合：

1. **ログ確認**
   ```bash
   tail -n 100 /mnt/e/dev/Cusor/chatbot/uma/backend/logs/jockey_weekly.log
   ```

2. **前回の正常ファイルを復元**
   ```bash
   cp /mnt/e/dev/Cusor/chatbot/uma/BACKUP_JOCKEY_*/nankan_jockey_knowledge_20250907.json .
   ```

3. **手動で再実行**
   ```bash
   python3 create_nar_jockey_knowledge_v1_perfect.py
   ```

---

**最終更新**: 2025-09-25
**作成者**: Claude
**SDKバージョン**: NAR_JOCKEY_SDK_V1_PERFECT