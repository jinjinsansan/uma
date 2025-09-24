# 地方競馬（NAR）ナレッジファイル週次更新マニュアル

## 📅 更新タイミング
- **毎週月曜日 午前3:00（自動実行）**
- **手動実行も可能**（レース結果反映後）

---

## 🔧 自動更新設定（cron）

### 1. cronジョブの設定
```bash
# crontabを編集
crontab -e

# 以下の行を追加（毎週月曜日 午前3:00実行）
0 3 * * 1 /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/run_nar_knowledge_weekly.sh >> /mnt/e/dev/Cusor/chatbot/uma/backend/logs/nar_weekly_update.log 2>&1
```

### 2. 実行スクリプトの準備
```bash
# 実行権限を付与
chmod +x /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/run_nar_knowledge_weekly.sh
chmod +x /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/create_nar_horse_knowledge_v9_perfect_base.py
```

---

## 📝 手動更新手順

### 1. 作業ディレクトリへ移動
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
```

### 2. SDKツールの実行
```bash
python3 create_nar_horse_knowledge_v9_perfect_base.py
```

### 3. 実行結果の確認
実行後、以下の情報が表示されます：
- ✅ 総レコード数
- ✅ 馬数
- ✅ 保存レース数
- ✅ 補正済みレース数
- ✅ 補正率（目標: 40%以上）

### 4. 生成ファイルの確認
```bash
# 最新ファイルを確認
ls -lh nar_knowledge_*.json | tail -1

# ファイル構造を確認（metadata + horses の2層構造）
python3 -c "import json; f=open('nar_knowledge_YYYYMMDD_HHMMSS.json'); d=json.load(f); print('Keys:', list(d.keys())); print('Horses:', len(d.get('horses', {})))"
```

### 5. CDN用ファイル名にリネーム
```bash
# 最新のファイルをCDN用にコピー
cp nar_knowledge_YYYYMMDD_HHMMSS.json nankan_unified_knowledge_20250907.json
```

---

## ☁️ CDN（Cloudflare R2）へのアップロード

### 方法1: Webブラウザから手動アップロード
1. Cloudflare R2ダッシュボードにログイン
2. バケットを選択
3. 既存の `nankan_unified_knowledge_20250907.json` を削除
4. 新しいファイルをアップロード
5. パブリックURLを確認

### 方法2: スクリプトでアップロード（準備中）
```bash
# アップロードスクリプト実行
python3 upload_to_cloudflare.py nankan_unified_knowledge_20250907.json
```

---

## 🚀 Renderへのデプロイ

### オプション1: 自動デプロイ（推奨）
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
git add .gitignore  # JSONファイル以外の変更のみ
git commit -m "Weekly NAR knowledge update - $(date +%Y%m%d)"
git push origin main
```

### オプション2: Deploy Hook使用
```bash
curl -X POST "https://api.render.com/deploy/srv-d24gpo2dbo4c739naqt0?key=_5LHAJVNjl8"
```

### オプション3: Renderダッシュボードから
1. https://dashboard.render.com にログイン
2. サービス「uma」を選択
3. 「Manual Deploy」をクリック

---

## 📊 スケジュールマスターの管理

### スケジュールマスターファイルの場所
```
/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json
```

### 新しい年度のスケジュール追加（年1回）
```bash
# 例: 2026年のスケジュールを追加
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 add_2026_schedule.py  # 事前に作成必要
```

### スケジュール追加の重要ポイント
- **1ヶ月ごとに処理**（ユーザーの指示通り）
- **ダートレースの日は除外**
- **会場コード**: 42=大井, 43=川崎, 44=船橋, 45=浦和

---

## 🔍 動作確認

### 1. ナレッジファイルの検証
```bash
# ファイルサイズ確認（通常200-250MB）
ls -lh nankan_unified_knowledge_20250907.json

# JSON構造の検証
python3 -c "
import json
with open('nankan_unified_knowledge_20250907.json') as f:
    data = json.load(f)
    print(f'✅ metadata: {\"metadata\" in data}')
    print(f'✅ horses: {\"horses\" in data}')
    print(f'馬数: {len(data.get(\"horses\", {}))}')
    print(f'補正率: {data[\"metadata\"][\"correction_rate\"]}%')
"
```

### 2. エンジン動作テスト
1. https://uma-i30n.onrender.com にアクセス
2. 地方競馬のレースで各エンジンをテスト
   - D-Logic AI
   - MyLogic AI
   - I-Logic AI
   - ViewLogic AI

---

## ⚠️ トラブルシューティング

### 問題: 「データなし」エラーが多発
**原因**: JSON構造が不正
**解決**:
```bash
# 構造を確認
python3 -c "import json; d=json.load(open('ファイル名.json')); print(list(d.keys()))"
# 必ず 'metadata' と 'horses' の2つのキーが必要
```

### 問題: 補正率が低い（30%以下）
**原因**: スケジュールマスターが不完全
**解決**:
```bash
# スケジュールマスターを確認
python3 -c "
import json
with open('/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json') as f:
    data = json.load(f)
    print(f'期間: {data[\"metadata\"][\"period\"]}')
    print(f'総日数: {data[\"metadata\"][\"total_days\"]}')
"
```

### 問題: Renderデプロイが進まない
**解決手順**:
1. Deploy Hookを実行
2. 環境変数を追加/変更して強制デプロイ
3. Service Eventsでログ確認

### 問題: ファイルサイズが大きすぎてGitにプッシュできない
**解決**:
```bash
# .gitignoreに追加済み
echo "*.json" >> .gitignore
# JSONファイルはCDN経由でのみ配布
```

---

## 📞 サポート連絡先

### 技術的な問題
- SDKツールのエラー → このマニュアルのトラブルシューティングを確認
- データベース接続エラー → PostgreSQL設定を確認（172.25.160.1:5432）

### インフラの問題
- Cloudflare R2 → Cloudflareダッシュボード
- Render → https://render.com/docs/support

---

## 📅 定期メンテナンス

### 週次（月曜日）
- [ ] ナレッジファイル自動更新の確認
- [ ] 補正率のモニタリング（40%以上を維持）

### 月次
- [ ] スケジュールマスターの確認と更新
- [ ] ログファイルのローテーション

### 年次
- [ ] 新年度のスケジュール追加
- [ ] 古いデータのアーカイブ（7年以上前）

---

## 🔄 更新履歴
- 2025-09-25: マニュアル初版作成
- 補正率: 29.4% → 44.7%（+15.3ポイント改善）
- スケジュールマスター: 2019-2025年対応

---

## 💡 重要な注意事項

1. **スケジュールは1ヶ月ごとに慎重に追加**
   - 間違えると補正が無意味になる

2. **JSON構造は必ず2層**
   ```json
   {
     "metadata": {...},
     "horses": {...}
   }
   ```

3. **CDNファイル名は固定**
   - `nankan_unified_knowledge_20250907.json`
   - エンジンがこの名前を参照している

4. **大きなJSONファイルはGitにプッシュしない**
   - 100MB制限を超える
   - CDN経由でのみ配布

5. **データベース接続**
   - WSL2環境: 172.25.160.1
   - ポート: 5432
   - データベース: PC-KEIBA

---

**最終更新**: 2025-09-25