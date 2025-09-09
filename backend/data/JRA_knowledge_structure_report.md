# JRAナレッジファイル構造分析レポート

## 📊 概要
JRAのV2チャットシステムで使用されている2つの主要ナレッジファイルの構造を分析しました。

## 1. 統合ナレッジファイル (unified_knowledge_20250903.json)

### 基本情報
- **ファイルサイズ**: 約280MB
- **収録馬数**: 34,388頭
- **データ形式**: JSON
- **構造**: 馬名をキーとした辞書形式

### データ構造
```json
{
  "馬名": [
    {
      // レース1のデータ（32フィールド）
    },
    {
      // レース2のデータ
    },
    // ... 最大5走分
  ]
}
```

### フィールド詳細（32項目）

| No | フィールド名 | 説明 | データ型 | 例 |
|----|------------|------|---------|-----|
| 01 | BAMEI | 馬名 | String | "マイネルグスタフ" |
| 02 | RACE_CODE | レースコード | String | "2023071507030512" |
| 03 | KAISAI_NEN | 開催年 | String | "2023" |
| 04 | KAISAI_GAPPI | 開催月日 | String | "0715" |
| 05 | KAKUTEI_CHAKUJUN | 確定着順 | String | "13" |
| 06 | TANSHO_ODDS | 単勝オッズ | String | "1536" |
| 07 | TANSHO_NINKIJUN | 単勝人気順 | String | "14" |
| 08 | FUTAN_JURYO | 負担重量 | String | "580" |
| 09 | BATAIJU | 馬体重 | String | "510" |
| 10 | ZOGEN_SA | 増減差 | String | "000" |
| 11 | KISHUMEI_RYAKUSHO | 騎手名（略称） | String | "幸英明　" |
| 12 | CHOKYOSHIMEI_RYAKUSHO | 調教師名（略称） | String | "吉田直弘" |
| 13 | CORNER1_JUNI | 第1コーナー順位 | String | "00" |
| 14 | CORNER2_JUNI | 第2コーナー順位 | String | "00" |
| 15 | CORNER3_JUNI | 第3コーナー順位 | String | "11" |
| 16 | CORNER4_JUNI | 第4コーナー順位 | String | "09" |
| 17 | SOHA_TIME | 走破タイム | String | "1148" |
| 18 | BAREI | 馬齢 | String | "05" |
| 19 | SEIBETSU_CODE | 性別コード | String | "1" |
| 20 | KEIBAJO_CODE | 競馬場コード | String | "07" |
| 21 | RACE_BANGO | レース番号 | String | "12" |
| 22 | KETTO_TOROKU_BANGO | 血統登録番号 | String | "2018102133" |
| 23 | TIME_SA | タイム差 | String | "+031" |
| 24 | KYORI | 距離 | String | "1200" |
| 25 | TRACK_CODE | トラックコード | String | "23" |
| 26 | SHIBA_BABAJOTAI_CODE | 芝馬場状態コード | String | "0" |
| 27 | DIRT_BABAJOTAI_CODE | ダート馬場状態コード | String | "1" |
| 28 | TENKO_CODE | 天候コード | String | "1" |
| 29 | sire | 父馬 | String | "" |
| 30 | dam | 母馬 | String | "" |
| 31 | broodmare_sire | 母父馬 | String | "" |
| 32 | track_name | 競馬場名 | String | "中京" |

## 2. 騎手ナレッジファイル (extended_jockey_knowledge.json)

### 基本情報
- **ファイルサイズ**: 約10MB
- **収録騎手数**: 562名
- **データ形式**: JSON
- **構造**: 騎手名をキーとした辞書形式

### データ構造
```json
{
  "騎手名": {
    "venue_course_stats": { /* 競馬場×距離別成績 */ },
    "track_condition_stats": { /* 馬場状態別成績 */ },
    "post_position_stats": { /* 枠順別成績 */ },
    "sire_stats": { /* 父馬別成績 */ },
    "overall_stats": { /* 総合成績 */ },
    "venue_course_full_stats": { /* 詳細競馬場×距離別成績 */ },
    "bloodline_stats": { /* 血統系統別成績 */ },
    "post_position_by_course": { /* コース別枠順成績 */ },
    "last_updated": "更新日時"
  }
}
```

### 各統計データの構造

#### venue_course_stats（競馬場×距離別成績）
```json
"中山_2000": {
  "races": 1,        // 出走数
  "wins": 0,         // 勝利数
  "top3": 0,         // 3着以内数
  "win_rate": 0.0,   // 勝率
  "top3_rate": 0.0   // 複勝率
}
```

#### track_condition_stats（馬場状態別成績）
```json
"良": {
  "races": 8,
  "wins": 1,
  "top3": 4,
  "win_rate": 0.125,
  "top3_rate": 0.5
}
```

#### overall_stats（総合成績）
```json
{
  "total_races_analyzed": 9,
  "overall_win_rate": 0.1111,
  "overall_top3_rate": 0.4444
}
```

## 3. データ更新プロセス

1. **データソース**: ローカルMySQL（keiba_dw）
2. **更新頻度**: 毎週月曜日
3. **更新方式**: 差分更新
4. **配信**: CDN経由でシステムに提供

## 4. 地方競馬版作成に向けた要件

### 必要なデータマッピング

統合ナレッジファイルには以下のデータが必要：
- 馬名、レースコード、開催情報
- 着順、オッズ、人気順位
- 馬体重、負担重量
- 騎手名、調教師名
- コーナー通過順位
- 走破タイム、タイム差
- 距離、馬場状態、天候
- 血統情報（父、母、母父）

騎手ナレッジファイルには以下の集計が必要：
- 競馬場×距離別成績
- 馬場状態別成績
- 枠順別成績
- 血統系統別成績
- 総合成績

### PostgreSQLからのデータ変換時の注意点

1. **文字コード**: 全て文字列型で保存
2. **数値フォーマット**: ゼロパディング（例: "01", "0715"）
3. **欠損値**: 空文字列で処理
4. **日付形式**: YYYYMMDD形式を年(YYYY)と月日(MMDD)に分割
5. **騎手名**: 全角スペースでパディング（例: "幸英明　"）

---
作成日: 2025-09-07