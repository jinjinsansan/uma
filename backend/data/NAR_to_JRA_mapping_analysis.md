# 地方競馬データ構造分析とJRAとの変換要件

## 📊 タスク②：PostgreSQL地方競馬データ構造調査結果

### データベース情報
- **DB名**: pckeiba
- **ホスト**: 127.0.0.1:5432
- **総レース数**: 315,509レース
- **総馬数**: 100,452頭
- **データ期間**: 2005年1月～2025年8月

### 主要テーブル構造

#### 1. nvd_ra（レース情報テーブル）
- **レコード数**: 315,509件
- **JRAのrace_shosaiに相当**
- **主要カラム**:
  - kaisai_nen（開催年）
  - kaisai_tsukihi（開催月日）
  - keibajo_code（競馬場コード）
  - race_bango（レース番号）
  - kyori（距離）
  - track_code（トラックコード：芝/ダート）
  - tenko_code（天候コード）

#### 2. nvd_se（出走情報テーブル）
- **レコード数**: 3,131,232件
- **JRAのumagoto_race_johoに相当**
- **主要カラム**:
  - ketto_toroku_bango（血統登録番号）
  - bamei（馬名）
  - kakutei_chakujun（確定着順）
  - tansho_odds（単勝オッズ）
  - tansho_ninkijun（単勝人気順）
  - futan_juryo（負担重量）
  - bataiju（馬体重）
  - zogen_fugo/zogen_sa（増減符号/差）
  - kishu_code/kishumei_ryakusho（騎手コード/名）
  - chokyoshi_code/chokyoshimei_ryakusho（調教師コード/名）
  - corner_1～4（各コーナー通過順位）
  - soha_time（走破タイム）
  - time_sa（タイム差）

#### 3. nvd_um（馬情報テーブル）
- **レコード数**: 100,452頭
- **JRAのuma_profに相当**
- **血統情報**: ketto_joho_01a/01b～14a/14b（14代血統）

#### 4. nvd_ks（騎手情報テーブル）
- **レコード数**: 1,845人
- **JRAのkishu_profに相当**

## 🔄 タスク③：JRAと地方競馬のデータ変換・正規化要件

### データマッピング表

| JRA統合ナレッジ | 地方競馬（nvd_se/nvd_ra） | 変換処理 |
|----------------|------------------------|----------|
| BAMEI | bamei | そのまま |
| RACE_CODE | kaisai_nen + kaisai_tsukihi + keibajo_code + race_bango | 結合生成 |
| KAISAI_NEN | kaisai_nen | そのまま |
| KAISAI_GAPPI | kaisai_tsukihi | 月日分割（後4桁） |
| KAKUTEI_CHAKUJUN | kakutei_chakujun | そのまま |
| TANSHO_ODDS | tansho_odds | そのまま |
| TANSHO_NINKIJUN | tansho_ninkijun | そのまま |
| FUTAN_JURYO | futan_juryo | そのまま |
| BATAIJU | bataiju | そのまま |
| ZOGEN_SA | zogen_fugo + zogen_sa | 符号結合 |
| KISHUMEI_RYAKUSHO | kishumei_ryakusho | そのまま |
| CHOKYOSHIMEI_RYAKUSHO | chokyoshimei_ryakusho | そのまま |
| CORNER1_JUNI | corner_1 | そのまま |
| CORNER2_JUNI | corner_2 | そのまま |
| CORNER3_JUNI | corner_3 | そのまま |
| CORNER4_JUNI | corner_4 | そのまま |
| SOHA_TIME | soha_time | そのまま |
| BAREI | nvd_um.barei（結合必要） | テーブル結合 |
| SEIBETSU_CODE | nvd_um.seibetsu_code | テーブル結合 |
| KEIBAJO_CODE | keibajo_code | そのまま |
| RACE_BANGO | race_bango | そのまま |
| KETTO_TOROKU_BANGO | ketto_toroku_bango | そのまま |
| TIME_SA | time_sa/chakusa_code_1～3 | 変換処理 |
| KYORI | nvd_ra.kyori | テーブル結合 |
| TRACK_CODE | nvd_ra.track_code | テーブル結合 |
| SHIBA_BABAJOTAI_CODE | nvd_ra.shiba_babajotai_code | テーブル結合 |
| DIRT_BABAJOTAI_CODE | nvd_ra.dirt_babajotai_code | テーブル結合 |
| TENKO_CODE | nvd_ra.tenko_code | テーブル結合 |
| sire | nvd_um.ketto_joho_01a | テーブル結合 |
| dam | nvd_um.ketto_joho_01b | テーブル結合 |
| broodmare_sire | nvd_um.ketto_joho_02a | テーブル結合 |
| track_name | keibajo_code → 名称変換 | コード変換 |

### 変換時の注意点

#### 1. 文字コード・フォーマット
- **文字列型統一**: 全フィールドを文字列として保存
- **ゼロパディング**: 
  - 着順: "01", "02"... 
  - 月日: "0715"
  - コーナー順位: "00", "01"...
- **騎手名パディング**: 全角スペースで統一（例: "幸英明　"）

#### 2. 欠損値処理
- **NULL/空文字列**: 空文字列("")に統一
- **未通過コーナー**: "00"として処理
- **血統不明**: 空文字列として処理

#### 3. 競馬場コード変換
```python
KEIBAJO_NAME_MAP = {
    '42': '浦和',
    '43': '船橋', 
    '44': '大井',
    '45': '川崎'
}
```

#### 4. レースコード生成
```python
# JRA形式: YYYYMMDDCCRRSS（14桁）
# 地方競馬: kaisai_nen(4) + kaisai_tsukihi(4) + keibajo_code(2) + race_bango(2) + "00"
race_code = f"{kaisai_nen}{kaisai_tsukihi}{keibajo_code}{race_bango:02d}00"
```

#### 5. タイム処理
- **4桁文字列形式**: "1234" = 1分23秒4
- **タイム差**: プラス記号付き（例: "+031"）

### 騎手ナレッジファイル変換要件

#### 必要な集計処理
1. **venue_course_stats**: 競馬場×距離別成績
   - GROUP BY keibajo_code, kyori
   
2. **track_condition_stats**: 馬場状態別成績  
   - GROUP BY babajotai_code

3. **post_position_stats**: 枠順別成績
   - GROUP BY wakuban

4. **overall_stats**: 総合成績
   - 全レースの勝率・複勝率計算

5. **bloodline_stats**: 血統系統別成績
   - 父系統でグループ化（要血統マスタ）

### データ取得SQL例

```sql
-- 南関東の馬データ取得（統合ナレッジ用）
SELECT 
    se.bamei,
    se.kaisai_nen || se.kaisai_tsukihi || se.keibajo_code || LPAD(se.race_bango::text, 2, '0') || '00' as race_code,
    se.kaisai_nen,
    SUBSTRING(se.kaisai_tsukihi, 3, 4) as kaisai_gappi,
    se.kakutei_chakujun,
    se.tansho_odds,
    se.tansho_ninkijun,
    se.futan_juryo,
    se.bataiju,
    COALESCE(se.zogen_fugo, '') || LPAD(se.zogen_sa::text, 3, '0') as zogen_sa,
    se.kishumei_ryakusho,
    se.chokyoshimei_ryakusho,
    COALESCE(se.corner_1, '00') as corner1_juni,
    COALESCE(se.corner_2, '00') as corner2_juni,
    COALESCE(se.corner_3, '00') as corner3_juni,
    COALESCE(se.corner_4, '00') as corner4_juni,
    se.soha_time,
    um.barei,
    um.seibetsu_code,
    se.keibajo_code,
    LPAD(se.race_bango::text, 2, '0') as race_bango,
    se.ketto_toroku_bango,
    COALESCE(se.time_sa, '') as time_sa,
    ra.kyori,
    ra.track_code,
    COALESCE(ra.shiba_babajotai_code, '0') as shiba_babajotai_code,
    COALESCE(ra.dirt_babajotai_code, '0') as dirt_babajotai_code,
    ra.tenko_code,
    um.ketto_joho_01a as sire,
    um.ketto_joho_01b as dam,
    um.ketto_joho_02a as broodmare_sire,
    CASE se.keibajo_code
        WHEN '42' THEN '浦和'
        WHEN '43' THEN '船橋'
        WHEN '44' THEN '大井'
        WHEN '45' THEN '川崎'
    END as track_name
FROM nvd_se se
JOIN nvd_ra ra ON (
    se.kaisai_nen = ra.kaisai_nen
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
)
LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
WHERE se.keibajo_code IN ('42', '43', '44', '45')
    AND se.kaisai_nen >= '2020'
ORDER BY se.bamei, se.kaisai_nen DESC, se.kaisai_tsukihi DESC
```

## ✅ 変換可能性の結論

**結論：変換可能**

地方競馬のPostgreSQLデータからJRA形式のナレッジファイルを作成することは**完全に可能**です。

### 必要な処理：
1. **テーブル結合**: nvd_se + nvd_ra + nvd_um
2. **フォーマット変換**: ゼロパディング、文字列化
3. **コード変換**: 競馬場コード→名称
4. **欠損値処理**: NULL→空文字列
5. **集計処理**: 騎手統計の計算

### 推奨実装手順：
1. PostgreSQL接続確立
2. データ抽出SQLの実行
3. Python/Pandasでデータ整形
4. JSON形式で出力
5. CDNへアップロード

---
作成日: 2025-09-07