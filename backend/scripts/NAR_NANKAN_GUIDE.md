# 🏇 南関東競馬統合ナレッジファイル作成 完全指示書（正規版）

## 📋 概要
南関東4競馬場（大井・川崎・船橋・浦和）の統合ナレッジファイルを作成する完全ガイドです。
JRA版と完全互換性を持ち、全エンジン（D-Logic、I-Logic、IM-Logic、ViewLogic）で動作します。

## ⚠️ 重要事項
- **nvd_テーブルのみ使用** - jvd_テーブルは絶対に使用しません
- **南関東4場のみ** - 競馬場コード42-45のみを対象
- **JRAと完全同一構造** - 32フィールドを維持
- **エンジン互換性必須** - 既存エンジンでそのまま動作

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

### 2. 競馬場コード（南関東）
```python
NANKAN_KEIBAJO_MAP = {
    '42': '大井',
    '43': '川崎', 
    '44': '船橋',
    '45': '浦和'
}
```

### 3. 必要なPythonライブラリ
```bash
pip install psycopg2-binary
```

## 📊 データ構造（32フィールド）

JRA版と完全に同一のフィールド構造を維持：

| フィールド名 | 内容 | 取得元 |
|------------|------|--------|
| BAMEI | 馬名 | nvd_se.bamei |
| RACE_CODE | レースコード | 年月日場R馬番結合 |
| KAISAI_NEN | 開催年 | nvd_se.kaisai_nen |
| KAISAI_GAPPI | 開催月日 | nvd_se.kaisai_tsukihi |
| KAKUTEI_CHAKUJUN | 確定着順 | nvd_se.kakutei_chakujun |
| TANSHO_ODDS | 単勝オッズ | nvd_se.tansho_odds |
| TANSHO_NINKIJUN | 単勝人気順 | nvd_se.tansho_ninkijun |
| FUTAN_JURYO | 負担重量 | nvd_se.futan_juryo |
| BATAIJU | 馬体重 | nvd_se.bataiju |
| ZOGEN_SA | 増減差 | nvd_se.zogen_sa |
| KISHUMEI_RYAKUSHO | 騎手名 | nvd_se.kishumei_ryakusho |
| CHOKYOSHIMEI_RYAKUSHO | 調教師名 | nvd_se.chokyoshimei_ryakusho |
| CORNER1_JUNI | 1角順位 | nvd_se.corner_1 |
| CORNER2_JUNI | 2角順位 | nvd_se.corner_2 |
| CORNER3_JUNI | 3角順位 | nvd_se.corner_3 |
| CORNER4_JUNI | 4角順位 | nvd_se.corner_4 |
| SOHA_TIME | 走破タイム | nvd_se.soha_time |
| BAREI | 馬齢 | 計算値 |
| SEIBETSU_CODE | 性別コード | nvd_um.seibetsu_code |
| KEIBAJO_CODE | 競馬場コード | nvd_se.keibajo_code |
| RACE_BANGO | レース番号 | nvd_se.race_bango |
| KETTO_TOROKU_BANGO | 血統登録番号 | nvd_se.ketto_toroku_bango |
| TIME_SA | タイム差 | nvd_se.time_sa |
| KYORI | 距離 | nvd_ra.kyori |
| TRACK_CODE | トラックコード | nvd_ra.track_code |
| SHIBA_BABAJOTAI_CODE | 芝馬場状態 | nvd_ra.babajotai_code_shiba |
| DIRT_BABAJOTAI_CODE | ダート馬場状態 | nvd_ra.babajotai_code_dirt |
| TENKO_CODE | 天候コード | nvd_ra.tenko_code |
| sire | 父名 | nvd_um.ketto_joho_01b |
| dam | 母名 | （空文字） |
| broodmare_sire | 母父名 | nvd_um.ketto_joho_02b |
| track_name | 競馬場名 | NANKAN_KEIBAJO_MAP変換 |

## 📝 SQLクエリ

```sql
SELECT 
    se.bamei,
    se.kaisai_nen || se.kaisai_tsukihi || se.keibajo_code || 
        LPAD(se.race_bango::text, 2, '0') || LPAD(se.umaban::text, 2, '0') as race_code,
    se.kaisai_nen,
    se.kaisai_tsukihi as kaisai_gappi,
    CASE 
        WHEN se.kakutei_chakujun IS NULL OR se.kakutei_chakujun = '' THEN '00'
        ELSE LPAD(se.kakutei_chakujun::text, 2, '0')
    END as kakutei_chakujun,
    -- 以下、全フィールド同様に処理
FROM nvd_se se
JOIN nvd_ra ra ON (
    se.kaisai_nen = ra.kaisai_nen
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
)
LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
WHERE se.kaisai_nen BETWEEN '2019' AND '2025'
    AND se.keibajo_code IN ('42','43','44','45')  -- 南関東4場のみ
    AND se.ketto_toroku_bango != '0000000000'
    AND se.kakutei_chakujun IS NOT NULL
    AND se.kakutei_chakujun != '00'
    AND se.bamei IS NOT NULL
    AND se.bamei != ''
ORDER BY se.bamei, se.kaisai_nen DESC, se.kaisai_tsukihi DESC
```

## 🚀 処理フロー

1. **PostgreSQL接続**
   - PC-KEIBAのPostgreSQLに接続
   - nvd_テーブルの存在確認

2. **データ取得**
   - 南関東4場のレースデータを取得
   - 7年分（2019-2025）のデータ

3. **データ処理**
   - 馬名ごとにグループ化
   - 最新9走まで保持
   - 血統情報（父名・母父名）を追加

4. **ファイル出力**
   - JSON形式で保存
   - ファイル名: `nankan_unified_knowledge_YYYYMMDD.json`

## ✅ 品質チェック項目

- [ ] 南関東4場（42-45）のみのデータ
- [ ] 着順不明（kakutei_chakujun='00'）除外
- [ ] 血統登録番号ゼロ除外
- [ ] 最大9走制限の確認
- [ ] 血統情報（父・母父）の確認
- [ ] 全32フィールドの存在確認

## 🎯 期待される結果

- **処理時間**: 約2-5秒
- **出力馬数**: 約3,000-5,000頭
- **ファイルサイズ**: 約20-30MB
- **データ品質**: 95%以上（血統情報含む）

## 🚨 注意事項

1. **テーブル混在禁止**
   - nvd_テーブルのみ使用
   - jvd_テーブルは絶対に参照しない

2. **エンジン互換性**
   - フィールド名・構造を変更しない
   - JRA版と完全に同じ構造を維持

3. **データ品質**
   - 欠損データは適切にデフォルト値設定
   - 血統情報は可能な限り取得

## 📊 実行確認

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 create_nankan_knowledge.py
```

## 🔄 週次更新

毎週月曜日に週末開催分を差分更新：
1. 既存ファイルをダウンロード
2. 週末の新レースを追加
3. 9走を超える場合は最古を削除
4. 更新済みファイルをアップロード

---

**作成日**: 2025年1月
**対象システム**: ViewLogic競馬予想エンジン群
**データソース**: PC-KEIBA PostgreSQL (nvd_テーブル)