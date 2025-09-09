# 🏇 地方競馬版統合ナレッジファイル作成 完全指示書

## 📌 最重要事項
この指示書に従えば、新しいClaudeでも地方競馬版の統合ナレッジファイルを作成できます。
**作成するファイルは、現在のD-Logic、IM-Logic、I-Logic、ViewLogicエンジンがそのまま使用できる形式です。**

---

## 1. 🎯 目的と成果物

### 作成するファイル
1. **統合ナレッジファイル（南関東版）**: `unified_knowledge_nankan_YYYYMMDD.json`
2. **騎手ナレッジファイル（南関東版）**: `jockey_knowledge_nankan_YYYYMMDD.json`

### ファイル仕様
- **形式**: JSON
- **文字コード**: UTF-8
- **構造**: JRA版と完全互換（エンジンの変更不要）
- **サイズ見込み**: 統合ナレッジ約100MB、騎手ナレッジ約5MB

---

## 2. 🔧 環境設定

### 必要な環境
- **OS**: WSL2 (Ubuntu)
- **Python**: 3.x
- **必要パッケージ**:
  ```bash
  pip3 install --break-system-packages psycopg2-binary pandas
  ```

### PC-KEIBA Databaseアクセス情報
```python
CONNECTION_PARAMS = {
    "host": "172.25.160.1",  # WSL2からWindows hostへ
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}
```

### Windows側の設定（必須）
1. **PC-KEIBA Database**を起動
2. **PostgreSQL設定ファイル**: `C:\Program Files\PostgreSQL\16\data\`
   - `postgresql.conf`: `listen_addresses = '*'` が設定済み
   - `pg_hba.conf`: 最後に `host all all 0.0.0.0/0 scram-sha-256` を追加済み
3. **PostgreSQLサービス**を再起動
4. **Windows Defenderファイアウォール**でポート5432を許可（または一時的に無効化）

---

## 3. 📊 データベース構造

### 主要テーブル
| テーブル名 | 説明 | レコード数 |
|-----------|------|-----------|
| nvd_se | 出走情報 | 3,135,536件 |
| nvd_ra | レース情報 | 315,509件 |
| nvd_um | 馬情報 | 100,452頭 |
| nvd_ks | 騎手情報 | 1,845名 |
| nvd_ch | 調教師情報 | 1,370名 |

### 南関東競馬場コード
```python
NANKAN_CODES = {
    '42': '浦和',
    '43': '船橋',
    '44': '大井',
    '45': '川崎'
}
```

---

## 4. 📝 データマッピング（JRA形式への変換）

### 統合ナレッジファイルの32フィールド

| No | JRAフィールド名 | 地方競馬データ取得元 | 変換処理 |
|----|---------------|-------------------|---------|
| 01 | BAMEI | nvd_se.bamei | トリム処理 |
| 02 | RACE_CODE | 生成 | kaisai_nen + kaisai_tsukihi + keibajo_code + race_bango + "00" |
| 03 | KAISAI_NEN | nvd_se.kaisai_nen | そのまま |
| 04 | KAISAI_GAPPI | nvd_se.kaisai_tsukihi | 後ろ4桁（月日部分） |
| 05 | KAKUTEI_CHAKUJUN | nvd_se.kakutei_chakujun | 2桁ゼロパディング |
| 06 | TANSHO_ODDS | nvd_se.tansho_odds | 4桁ゼロパディング |
| 07 | TANSHO_NINKIJUN | nvd_se.tansho_ninkijun | 2桁ゼロパディング |
| 08 | FUTAN_JURYO | nvd_se.futan_juryo | 3桁ゼロパディング |
| 09 | BATAIJU | nvd_se.bataiju | 3桁ゼロパディング |
| 10 | ZOGEN_SA | nvd_se.zogen_fugo + zogen_sa | 符号付き3桁 |
| 11 | KISHUMEI_RYAKUSHO | nvd_se.kishumei_ryakusho | そのまま |
| 12 | CHOKYOSHIMEI_RYAKUSHO | nvd_se.chokyoshimei_ryakusho | そのまま |
| 13 | CORNER1_JUNI | nvd_se.corner_1 | 2桁ゼロパディング |
| 14 | CORNER2_JUNI | nvd_se.corner_2 | 2桁ゼロパディング |
| 15 | CORNER3_JUNI | nvd_se.corner_3 | 2桁ゼロパディング |
| 16 | CORNER4_JUNI | nvd_se.corner_4 | 2桁ゼロパディング |
| 17 | SOHA_TIME | nvd_se.soha_time | 4桁文字列 |
| 18 | BAREI | nvd_um.barei | 2桁ゼロパディング |
| 19 | SEIBETSU_CODE | nvd_um.seibetsu_code | そのまま |
| 20 | KEIBAJO_CODE | nvd_se.keibajo_code | そのまま |
| 21 | RACE_BANGO | nvd_se.race_bango | 2桁ゼロパディング |
| 22 | KETTO_TOROKU_BANGO | nvd_se.ketto_toroku_bango | そのまま |
| 23 | TIME_SA | nvd_se.time_sa | "+XXX"形式 |
| 24 | KYORI | nvd_ra.kyori | 4桁文字列 |
| 25 | TRACK_CODE | nvd_ra.track_code | そのまま |
| 26 | SHIBA_BABAJOTAI_CODE | nvd_ra.shiba_babajotai_code | デフォルト"0" |
| 27 | DIRT_BABAJOTAI_CODE | nvd_ra.dirt_babajotai_code | デフォルト"0" |
| 28 | TENKO_CODE | nvd_ra.tenko_code | そのまま |
| 29 | sire | nvd_um.ketto_joho_01a | 血統情報 |
| 30 | dam | nvd_um.ketto_joho_01b | 血統情報 |
| 31 | broodmare_sire | nvd_um.ketto_joho_02a | 母父情報 |
| 32 | track_name | 変換 | keibajo_codeから名称変換 |

---

## 5. 💻 実装コード

### 完全版スクリプト

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬版統合ナレッジファイル作成スクリプト
"""

import psycopg2
import json
import sys
import io
from datetime import datetime
from collections import defaultdict
import pandas as pd

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# データベース接続情報
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

# 南関東競馬場
NANKAN_CODES = {
    '42': '浦和',
    '43': '船橋',
    '44': '大井',
    '45': '川崎'
}

def create_unified_knowledge():
    """統合ナレッジファイルを作成"""
    
    print("=" * 80)
    print("地方競馬版統合ナレッジファイル作成")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 対象期間（最新3年分）
        target_years = ['2022', '2023', '2024', '2025']
        
        # 南関東の馬データを取得するSQL
        query = """
        SELECT 
            se.bamei,
            se.kaisai_nen || se.kaisai_tsukihi || se.keibajo_code || 
                LPAD(se.race_bango::text, 2, '0') || '00' as race_code,
            se.kaisai_nen,
            SUBSTRING(se.kaisai_tsukihi, 1, 4) as kaisai_gappi,
            LPAD(COALESCE(se.kakutei_chakujun, '00'), 2, '0') as kakutei_chakujun,
            LPAD(COALESCE(se.tansho_odds::text, '0000'), 4, '0') as tansho_odds,
            LPAD(COALESCE(se.tansho_ninkijun, '00'), 2, '0') as tansho_ninkijun,
            LPAD(COALESCE(se.futan_juryo::text, '000'), 3, '0') as futan_juryo,
            LPAD(COALESCE(se.bataiju::text, '000'), 3, '0') as bataiju,
            CASE 
                WHEN se.zogen_fugo = '-' THEN '-' || LPAD(COALESCE(se.zogen_sa::text, '00'), 2, '0')
                ELSE '+' || LPAD(COALESCE(se.zogen_sa::text, '00'), 2, '0')
            END as zogen_sa,
            COALESCE(se.kishumei_ryakusho, '') as kishumei_ryakusho,
            COALESCE(se.chokyoshimei_ryakusho, '') as chokyoshimei_ryakusho,
            LPAD(COALESCE(se.corner_1, '00'), 2, '0') as corner1_juni,
            LPAD(COALESCE(se.corner_2, '00'), 2, '0') as corner2_juni,
            LPAD(COALESCE(se.corner_3, '00'), 2, '0') as corner3_juni,
            LPAD(COALESCE(se.corner_4, '00'), 2, '0') as corner4_juni,
            COALESCE(se.soha_time, '0000') as soha_time,
            LPAD(COALESCE(um.barei::text, '00'), 2, '0') as barei,
            COALESCE(um.seibetsu_code, '0') as seibetsu_code,
            se.keibajo_code,
            LPAD(se.race_bango::text, 2, '0') as race_bango,
            se.ketto_toroku_bango,
            CASE 
                WHEN se.time_sa LIKE '+%' THEN se.time_sa
                WHEN se.time_sa LIKE '-%' THEN se.time_sa
                ELSE '+' || LPAD(COALESCE(se.time_sa, '000'), 3, '0')
            END as time_sa,
            LPAD(COALESCE(ra.kyori::text, '0000'), 4, '0') as kyori,
            COALESCE(ra.track_code, '00') as track_code,
            COALESCE(ra.shiba_babajotai_code, '0') as shiba_babajotai_code,
            COALESCE(ra.dirt_babajotai_code, '0') as dirt_babajotai_code,
            COALESCE(ra.tenko_code, '0') as tenko_code,
            COALESCE(um.ketto_joho_01a, '') as sire,
            COALESCE(um.ketto_joho_01b, '') as dam,
            COALESCE(um.ketto_joho_02a, '') as broodmare_sire,
            CASE se.keibajo_code
                WHEN '42' THEN '浦和'
                WHEN '43' THEN '船橋'
                WHEN '44' THEN '大井'
                WHEN '45' THEN '川崎'
                ELSE se.keibajo_code
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
            AND se.kaisai_nen IN %s
            AND se.bamei IS NOT NULL
            AND se.bamei != ''
        ORDER BY se.bamei, se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        """
        
        print("データ取得中...")
        cur.execute(query, (tuple(target_years),))
        
        # 結果を馬ごとにグループ化
        horses_data = defaultdict(list)
        
        # カラム名を取得
        col_names = [
            "BAMEI", "RACE_CODE", "KAISAI_NEN", "KAISAI_GAPPI", "KAKUTEI_CHAKUJUN",
            "TANSHO_ODDS", "TANSHO_NINKIJUN", "FUTAN_JURYO", "BATAIJU", "ZOGEN_SA",
            "KISHUMEI_RYAKUSHO", "CHOKYOSHIMEI_RYAKUSHO", "CORNER1_JUNI", "CORNER2_JUNI",
            "CORNER3_JUNI", "CORNER4_JUNI", "SOHA_TIME", "BAREI", "SEIBETSU_CODE",
            "KEIBAJO_CODE", "RACE_BANGO", "KETTO_TOROKU_BANGO", "TIME_SA", "KYORI",
            "TRACK_CODE", "SHIBA_BABAJOTAI_CODE", "DIRT_BABAJOTAI_CODE", "TENKO_CODE",
            "sire", "dam", "broodmare_sire", "track_name"
        ]
        
        row_count = 0
        for row in cur:
            horse_name = row[0].strip()
            race_data = dict(zip(col_names, row))
            
            # 最新5走まで
            if len(horses_data[horse_name]) < 5:
                horses_data[horse_name].append(race_data)
            
            row_count += 1
            if row_count % 10000 == 0:
                print(f"  {row_count:,}件処理...")
        
        print(f"\n処理完了:")
        print(f"  総レコード数: {row_count:,}")
        print(f"  馬数: {len(horses_data):,}")
        
        # JSONファイルとして保存
        today = datetime.now().strftime("%Y%m%d")
        output_file = f"unified_knowledge_nankan_{today}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict(horses_data), f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ ファイル作成完了: {output_file}")
        
        # ファイルサイズ確認
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  ファイルサイズ: {file_size:.1f}MB")
        
        cur.close()
        conn.close()
        
        return output_file
        
    except Exception as e:
        print(f"エラー: {e}")
        return None

def create_jockey_knowledge():
    """騎手ナレッジファイルを作成"""
    
    print("\n" + "=" * 80)
    print("地方競馬版騎手ナレッジファイル作成")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 騎手別統計を集計
        query = """
        SELECT 
            se.kishumei_ryakusho,
            se.keibajo_code,
            ra.kyori,
            ra.track_code,
            se.wakuban,
            COUNT(*) as races,
            SUM(CASE WHEN se.kakutei_chakujun = '01' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN se.kakutei_chakujun IN ('01', '02', '03') THEN 1 ELSE 0 END) as top3
        FROM nvd_se se
        JOIN nvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        WHERE se.keibajo_code IN ('42', '43', '44', '45')
            AND se.kaisai_nen >= '2022'
            AND se.kishumei_ryakusho IS NOT NULL
            AND se.kishumei_ryakusho != ''
        GROUP BY 
            se.kishumei_ryakusho,
            se.keibajo_code,
            ra.kyori,
            ra.track_code,
            se.wakuban
        """
        
        print("騎手データ集計中...")
        cur.execute(query)
        
        # 騎手ごとのデータを整理
        jockey_data = defaultdict(lambda: {
            "venue_course_stats": {},
            "track_condition_stats": {},
            "post_position_stats": {},
            "overall_stats": {
                "total_races_analyzed": 0,
                "overall_win_rate": 0.0,
                "overall_top3_rate": 0.0
            },
            "last_updated": datetime.now().isoformat()
        })
        
        for row in cur:
            jockey_name = row[0].strip()
            keibajo = NANKAN_CODES.get(row[1], row[1])
            kyori = row[2]
            track_code = row[3]
            wakuban = row[4]
            races = row[5]
            wins = row[6]
            top3 = row[7]
            
            # 競馬場×距離別成績
            venue_course_key = f"{keibajo}_{kyori}"
            if venue_course_key not in jockey_data[jockey_name]["venue_course_stats"]:
                jockey_data[jockey_name]["venue_course_stats"][venue_course_key] = {
                    "races": 0,
                    "wins": 0,
                    "top3": 0,
                    "win_rate": 0.0,
                    "top3_rate": 0.0
                }
            
            stats = jockey_data[jockey_name]["venue_course_stats"][venue_course_key]
            stats["races"] += races
            stats["wins"] += wins
            stats["top3"] += top3
            if stats["races"] > 0:
                stats["win_rate"] = stats["wins"] / stats["races"]
                stats["top3_rate"] = stats["top3"] / stats["races"]
            
            # 総合成績更新
            overall = jockey_data[jockey_name]["overall_stats"]
            overall["total_races_analyzed"] += races
        
        # 総合勝率・複勝率を計算
        for jockey_name in jockey_data:
            total_races = jockey_data[jockey_name]["overall_stats"]["total_races_analyzed"]
            if total_races > 0:
                total_wins = sum(
                    s["wins"] for s in jockey_data[jockey_name]["venue_course_stats"].values()
                )
                total_top3 = sum(
                    s["top3"] for s in jockey_data[jockey_name]["venue_course_stats"].values()
                )
                jockey_data[jockey_name]["overall_stats"]["overall_win_rate"] = total_wins / total_races
                jockey_data[jockey_name]["overall_stats"]["overall_top3_rate"] = total_top3 / total_races
        
        print(f"\n騎手数: {len(jockey_data):,}")
        
        # JSONファイルとして保存
        today = datetime.now().strftime("%Y%m%d")
        output_file = f"jockey_knowledge_nankan_{today}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict(jockey_data), f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ ファイル作成完了: {output_file}")
        
        # ファイルサイズ確認
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  ファイルサイズ: {file_size:.1f}MB")
        
        cur.close()
        conn.close()
        
        return output_file
        
    except Exception as e:
        print(f"エラー: {e}")
        return None

def main():
    """メイン処理"""
    print("🏇 地方競馬版ナレッジファイル作成開始")
    print("=" * 80)
    
    # 1. 統合ナレッジファイル作成
    unified_file = create_unified_knowledge()
    
    # 2. 騎手ナレッジファイル作成
    jockey_file = create_jockey_knowledge()
    
    print("\n" + "=" * 80)
    print("🎉 作成完了!")
    print("=" * 80)
    
    if unified_file:
        print(f"✅ 統合ナレッジ: {unified_file}")
    if jockey_file:
        print(f"✅ 騎手ナレッジ: {jockey_file}")
    
    print("\n【次のステップ】")
    print("1. 作成されたJSONファイルをCDNにアップロード")
    print("2. services/dlogic_raw_data_manager.pyのURLを更新")
    print("3. V2チャットで南関東データを利用可能に")

if __name__ == "__main__":
    main()
```

---

## 6. 📋 作業手順チェックリスト

### 事前準備
- [ ] PC-KEIBA Databaseが起動している
- [ ] PostgreSQLサービスが実行中
- [ ] pg_hba.confに外部接続許可設定がある
- [ ] Windows Defenderファイアウォールでポート5432を許可（または無効化）
- [ ] WSL2でpsycopg2-binaryとpandasがインストール済み

### 実行手順
1. [ ] 上記スクリプトを`create_nar_knowledge.py`として保存
2. [ ] `python3 create_nar_knowledge.py`を実行
3. [ ] 作成された2つのJSONファイルを確認
4. [ ] ファイルサイズと内容をチェック
5. [ ] CDNにアップロード
6. [ ] システムに組み込み

### トラブルシューティング
- **接続エラー**: Windows Defenderファイアウォールを確認
- **タイムアウト**: PostgreSQLサービスを再起動
- **文字化け**: UTF-8エンコーディングを確認
- **メモリ不足**: データ取得期間を短縮

---

## 7. 🔍 動作確認方法

### 作成されたファイルの検証
```python
# ファイル内容確認
import json

# 統合ナレッジ確認
with open('unified_knowledge_nankan_20250907.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"馬数: {len(data)}")
    # サンプル表示
    for horse_name, races in list(data.items())[:3]:
        print(f"\n{horse_name}: {len(races)}走")
        if races:
            print(f"  最新レース: {races[0]['KAISAI_NEN']}年{races[0]['KAISAI_GAPPI']}")

# 騎手ナレッジ確認  
with open('jockey_knowledge_nankan_20250907.json', 'r', encoding='utf-8') as f:
    jockey_data = json.load(f)
    print(f"\n騎手数: {len(jockey_data)}")
    # 上位騎手表示
    for jockey_name in list(jockey_data.keys())[:5]:
        win_rate = jockey_data[jockey_name]['overall_stats']['overall_win_rate']
        print(f"  {jockey_name}: 勝率{win_rate*100:.1f}%")
```

---

## 8. 📞 サポート情報

### 関連ファイル
- **JRA版ナレッジ構造**: `/mnt/e/dev/Cusor/chatbot/uma/backend/data/JRA_knowledge_structure_report.md`
- **変換要件分析**: `/mnt/e/dev/Cusor/chatbot/uma/backend/data/NAR_to_JRA_mapping_analysis.md`
- **既存スクリプト**: `/mnt/e/dev/takigawa/takigawa/takigawa/scripts/`

### データベース情報
- **総レース数**: 315,509レース
- **総馬数**: 100,452頭
- **対象期間**: 2005年～2025年
- **南関東4場**: 浦和(42)、船橋(43)、大井(44)、川崎(45)

---

## 9. ⚠️ 注意事項

1. **データ量**: 南関東4場だけでも大量のデータ。メモリに注意
2. **処理時間**: 全データ処理には10-20分程度かかる可能性
3. **文字コード**: 必ずUTF-8で処理（Windows環境は特に注意）
4. **NULL値処理**: 地方競馬はNULL値が多いため、適切にデフォルト値を設定
5. **セキュリティ**: 作業後は必ずWindows Defenderファイアウォールを再有効化

---

## 10. ✅ 完了確認

この指示書に従って作成したナレッジファイルは：
- **D-Logic AI**でそのまま使用可能
- **IM-Logic**でそのまま使用可能  
- **I-Logic**でそのまま使用可能
- **ViewLogic**でそのまま使用可能

エンジンのコード変更は一切不要です。

---

作成日: 2025-09-07
作成者: Claude (D-Logic AIプロジェクト)