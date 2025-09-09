# 🏇 南関東騎手ナレッジファイル作成 完全指示書（正規版）

## 📋 概要
南関東4競馬場（大井・川崎・船橋・浦和）の騎手成績データを集計したナレッジファイルを作成します。
JRA騎手ナレッジファイルと完全互換性を持ち、全エンジンで動作します。

## ⚠️ 重要事項
- **nvd_テーブルのみ使用** - jvd_テーブルは絶対に使用しません
- **南関東4場のみ** - 競馬場コード42-45のみを対象
- **JRAと完全同一構造** - データ構造の互換性を維持
- **7年分のデータ** - 2019年～2025年を対象

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

## 📊 データ構造

JRA騎手ナレッジファイルと完全に同一の構造：

```json
{
  "騎手名": {
    "name": "騎手名",
    "venue_course_stats": {
      "競馬場_距離m": {
        "results": [
          {
            "date": "YYYY-MMDD",
            "horse_name": "馬名",
            "position": 着順,
            "total_horses": 頭数,
            "is_fukusho": true/false
          }
        ],
        "fukusho_rate": 複勝率,
        "race_count": レース数
      }
    },
    "track_condition_stats": {
      "芝/ダート(馬場状態)": {
        "results": [],
        "fukusho_rate": 複勝率,
        "race_count": レース数
      }
    },
    "post_position_stats": {
      "枠X": {
        "results": [],
        "fukusho_rate": 複勝率,
        "race_count": レース数
      }
    },
    "sire_stats": {
      "種牡馬名": {
        "results": [],
        "fukusho_rate": 複勝率,
        "race_count": レース数
      }
    },
    "processed_at": "処理日時",
    "overall_stats": {
      "total_races_analyzed": 総レース数,
      "overall_fukusho_rate": 総合複勝率
    }
  }
}
```

## 📝 SQLクエリ

```sql
SELECT 
    se.kishumei_ryakusho,
    se.kaisai_nen,
    se.kaisai_tsukihi,
    se.keibajo_code,
    ra.kyori,
    ra.track_code,
    COALESCE(ra.babajotai_code_shiba, '0') || COALESCE(ra.babajotai_code_dirt, '0') as baba_code,
    se.wakuban,
    se.bamei,
    se.kakutei_chakujun,
    ra.shusso_tosu,
    COALESCE(um.ketto_joho_01b, '') as sire
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
    AND se.kishumei_ryakusho IS NOT NULL
    AND se.kishumei_ryakusho != ''
    AND se.kakutei_chakujun IS NOT NULL
    AND se.kakutei_chakujun != '00'
ORDER BY se.kishumei_ryakusho, se.kaisai_tsukihi DESC
```

## 🚀 処理フロー

1. **PostgreSQL接続**
   - PC-KEIBAのPostgreSQLに接続
   - nvd_テーブルの存在確認

2. **データ取得**
   - 南関東4場の騎手成績データを取得
   - 7年分（2019-2025）のデータ

3. **データ集計**
   - 騎手ごとに成績を集計
   - 4つのカテゴリー別に統計作成
   - 複勝率を計算（3着以内の割合）

4. **ファイル出力**
   - JSON形式で保存
   - ファイル名: `nankan_jockey_knowledge_YYYYMMDD.json`

## 🎯 集計カテゴリー

### 1. venue_course_stats（競馬場×距離別）
- 例: "大井_1200m", "川崎_1400m"
- 競馬場と距離の組み合わせごとに集計

### 2. track_condition_stats（馬場状態別）
- 芝/ダートと馬場状態の組み合わせ
- 例: "芝(10)", "ダート(24)"

### 3. post_position_stats（枠番別）
- 枠1～枠8の成績
- 例: "枠1", "枠2"

### 4. sire_stats（種牡馬別）
- 騎乗した馬の種牡馬別成績
- 例: "サウスヴィグラス", "ゴールドアリュール"

## ✅ 品質チェック項目

- [ ] 南関東4場（42-45）のみのデータ
- [ ] 着順不明（kakutei_chakujun='00'）除外
- [ ] 騎手名なしデータ除外
- [ ] 複勝率の正確な計算（3着以内÷総レース数）
- [ ] 各カテゴリーのデータ整合性

## 🎯 期待される結果

- **処理時間**: 約5-10秒
- **騎手数**: 約300-500名
- **ファイルサイズ**: 約50-100MB
- **データ期間**: 7年分（2019-2025）

## 🚨 注意事項

1. **テーブル混在禁止**
   - nvd_テーブルのみ使用
   - jvd_テーブルは絶対に参照しない

2. **JRA版との互換性**
   - データ構造を完全に同一にする
   - フィールド名を変更しない

3. **データ品質**
   - 複勝率は小数点第1位まで
   - 日付フォーマットはYYYY-MMDD

## 📊 実行確認

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 create_nankan_jockey_knowledge.py
```

## 🔄 週次更新

毎週月曜日に週末開催分を差分更新：
1. 既存ファイルをダウンロード
2. 週末の新レース成績を追加
3. 複勝率を再計算
4. 更新済みファイルをアップロード

---

**作成日**: 2025年1月
**対象システム**: ViewLogic競馬予想エンジン群
**データソース**: PC-KEIBA PostgreSQL (nvd_テーブル)