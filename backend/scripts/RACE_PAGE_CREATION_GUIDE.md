# 📚 レースページ自動生成完全マニュアル（改訂版）

## 🚨🚨🚨 超重要：過去の重大ミスと教訓 🚨🚨🚨

### ❌ 2025年9月8日の重大な誤認識事例
1. **金沢競馬を浦和と誤認識** - コード45は金沢（北陸）であり、浦和ではなかった
2. **南関東以外のデータを混入** - 金沢は北陸地方であり南関東版には不要
3. **開催確認の怠慢** - ネット競馬での実際の開催確認を怠った

### ✅ 必ず実施すること
1. **ネット競馬で実際の開催を確認**
2. **南関東4場（大井・川崎・船橋・浦和）のみを対象とする**
3. **競馬場コードを正確に把握する**

## 🎯 概要
このマニュアルは、PostgreSQLの速報系データから自動的にレース情報ページを生成する方法を説明します。
手動でネット競馬からコピペする作業が完全に不要になります。

## 🗂️ システム構成

### ファイル構造
```
/mnt/e/dev/Cusor/
├── chatbot/uma/backend/scripts/
│   ├── generate_nankan_races.py  # 南関東レース自動生成スクリプト
│   └── generate_jra_races.py     # JRAレース生成（未作成）
├── front/d-logic-ai-frontend/
│   ├── src/data/
│   │   ├── v2-metadata.json      # レース一覧メタデータ
│   │   └── archive/
│   │       ├── local/             # 南関東レースTSファイル保存先
│   │       └── （JRAレース用）    # JRAレースTSファイル
│   └── src/app/v2/races/
│       ├── （JRAページ）          # /v2/races
│       └── local/                 # /v2/races/local（南関東専用）
```

## 🏇 競馬場コードマッピング（超重要）

### ⚠️⚠️⚠️ 正確な競馬場コード ⚠️⚠️⚠️

#### 南関東4場（これ以外は絶対に含めない）
```python
NANKAN_KEIBAJO_MAP = {
    '42': '大井',    # 東京シティ競馬
    '43': '川崎',    # 川崎競馬
    '44': '船橋',    # 船橋競馬
    '45': '川崎',    # ⚠️ 2025年9月9日確認：川崎が45を使用
    '46': '川崎',    # ⚠️ 2025年9月8日確認：川崎が46を使用
    '47': '浦和'     # 浦和競馬
}
```

#### その他の地方競馬（南関東版には含めない）
```python
# 以下は南関東版には絶対に含めない
OTHER_CHIHO_MAP = {
    '30': '門別',    # 北海道
    '35': '盛岡',    # 岩手
    '36': '水沢',    # 岩手
    '45': '金沢',    # ⚠️ 北陸（2025年9月8日の誤認識事例）
    '47': '笠松',    # ⚠️ 東海（2025年9月9日確認：笠松が47を使用）
    '48': '笠松',    # 東海
    '83': '帯広'     # ばんえい（200mレース）
}

### ⚠️⚠️⚠️ 超重要：競馬場コードの重複問題 ⚠️⚠️⚠️
**同じコードが複数の競馬場で使用されることがある！**
- コード45: 川崎（2025年9月9日）、金沢（2025年9月8日）
- コード46: 川崎（2025年9月8日）
- コード47: 浦和（通常）、笠松（2025年9月9日）

**対策：必ずレース名や調教師名から実際の競馬場を確認すること**
- レース名に「笠松」が含まれる → 笠松競馬
- レース名に「かながわ」「川崎」が含まれる → 川崎競馬
- 調教師が南関東所属 → 南関東4場のいずれか
```

## 🚀 使い方

### 0. 必ず最初に開催確認

```python
# 開催確認用SQLクエリ
SELECT 
    keibajo_code,
    COUNT(*) as race_count
FROM nvd_ra
WHERE kaisai_nen = '2025' 
  AND kaisai_tsukihi = '0908'  # MMDD形式
  AND keibajo_code IN ('42', '43', '44', '46', '47')  # 南関東のみ
GROUP BY keibajo_code;
```

### 1. 南関東（地方競馬）のレース生成

#### タイミング
- **レース前日夜または当日朝**: データが速報系に登録される

#### 実行前の確認事項
1. ネット競馬で実際の開催を確認
2. 南関東4場のどこが開催しているか確認
3. 複数場開催の可能性も考慮

#### 実行方法
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts

# 単一開催の場合
python3 generate_nankan_races.py --date 2025-09-08 --venue 川崎

# 複数開催の場合
python3 generate_nankan_races.py --date 2025-09-08 --venue 川崎,大井
```

### 2. JRA（中央競馬）のレース生成

#### タイミング
- **金曜日夜**: 週末のレース情報が速報系に登録される

#### 実行方法
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 generate_jra_races.py --date 2025-09-07
```

## 📊 データソース

### PostgreSQL接続情報
```python
CONNECTION_PARAMS = {
    "host": "172.25.160.1",     # WSL2からWindowsのPostgreSQL
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}
```

### テーブル構造

#### 南関東（地方競馬）
- `nvd_ra`: レース情報
- `nvd_se`: 出馬表
- カラム名の注意:
  - `kyosomei_hondai` (レース名)
  - `hasso_jikoku` (発走時刻)
  - `kishumei_ryakusho` (騎手名)
  - `seibetsu_code` (性別コード: 1=牡, 2=牝, 3=セ)
  - `barei` (馬齢)

#### JRA（中央競馬）
- `jvd_ra`: レース情報
- `jvd_se`: 出馬表

## 🔧 スクリプトの動作

### generate_nankan_races.py の処理フロー

1. **開催確認**（最重要）
   ```python
   # 必ず実装すること
   def check_kaisai(date):
       # 指定日の南関東開催を確認
       # 南関東以外は除外
       return valid_venues
   ```

2. **データ取得**
   - PostgreSQLのnvd_ra/nvd_seテーブルから取得
   - **南関東4場のみ**をフィルタリング

3. **TSファイル生成**
   - `/src/data/archive/local/races-YYYYMMDD-競馬場.ts`形式で保存

4. **メタデータ更新**
   - `v2-metadata.json`のlocalセクションに自動追加

## 🌐 フロントエンド表示

### ⚠️⚠️⚠️ 超重要：JRAと地方競馬は完全に別ルート ⚠️⚠️⚠️

#### JRA（中央競馬）のURLパス
```
https://www.dlogicai.in/v2/races                    # JRAレース一覧
https://www.dlogicai.in/v2/races/2025-09-07         # 日付別
https://www.dlogicai.in/v2/races/2025-09-07/中山    # 競馬場別
```

#### 南関東（地方競馬）のURLパス
```
https://www.dlogicai.in/v2/races/local                     # 地方競馬一覧
https://www.dlogicai.in/v2/races/local/2025-09-08          # 日付別
https://www.dlogicai.in/v2/races/local/2025-09-08/川崎     # 競馬場別
```

### 🚫 絶対にやってはいけないこと

1. ❌ 南関東以外（金沢、盛岡等）のデータを含める
2. ❌ 競馬場コードを確認せずに生成
3. ❌ ネット競馬での開催確認を怠る
4. ❌ JRAと地方競馬を混在させる
5. ❌ 北陸・東海・北海道等のデータを南関東版に含める

## 🚨 トラブルシューティング

### 競馬場コードの確認方法
```sql
-- 調教師名から競馬場を特定
SELECT 
    keibajo_code,
    chokyoshimei_ryakusho,
    COUNT(*) as count
FROM nvd_se
WHERE kaisai_nen = '2025' 
  AND kaisai_tsukihi = '0908'
GROUP BY keibajo_code, chokyoshimei_ryakusho
ORDER BY keibajo_code, count DESC;
```

### データ検証チェックリスト
- [ ] ネット競馬で開催確認した
- [ ] 南関東4場のみ対象にした
- [ ] 競馬場コードを正確に確認した
- [ ] 生成したTSファイルの競馬場名が正しい
- [ ] v2-metadata.jsonに正しく追加された

## 📅 運用スケジュール案

### 手動実行時の確認事項
1. ネット競馬で開催スケジュール確認
2. 南関東の開催場のみ抽出
3. スクリプト実行
4. 生成データの検証

### 自動化する場合の注意
```bash
# cronで自動化する前に必ず開催判定ロジックを実装
# 南関東以外を除外する処理を必須とする
```

## 🎉 まとめ

### 成功のための3原則
1. **ネット競馬で必ず開催確認**
2. **南関東4場のみを対象**
3. **競馬場コードを正確に把握**

これで新しいClaudeでも間違いなくレース情報ページを生成できます！

## 📝 最終更新: 2025-09-08
### 更新内容: 金沢を浦和と誤認識した重大ミスを踏まえ、競馬場コードと開催確認を最重要事項として改訂