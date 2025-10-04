"""
N-Logic学習データ準備スクリプト
PostgreSQLから過去レース結果を取得し、特徴量付きCSVを生成
"""

import os
import sys
import pandas as pd
from datetime import datetime

# バックエンドパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.viewlogic_data_manager import ViewLogicDataManager

def extract_race_results_from_knowledge(viewlogic_manager):
    """unified_knowledge.jsonから過去レース結果を抽出"""
    print("=" * 60)
    print("Step 1: unified_knowledge.jsonからレース結果抽出")
    print("=" * 60)
    
    # 競馬場コードマップ
    venue_code_map = {
        '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
        '05': '東京', '06': '中山', '07': '中京', '08': '京都',
        '09': '阪神', '10': '小倉'
    }
    
    race_records = []
    horses_data = viewlogic_manager.knowledge_data.get('horses', {})
    total_horses = len(horses_data)
    
    print(f"処理中: {total_horses}頭の馬データ...")
    
    processed = 0
    for horse_name, horse_data in horses_data.items():
        processed += 1
        if processed % 1000 == 0:
            print(f"  進捗: {processed}/{total_horses} ({processed/total_horses*100:.1f}%)")
        
        if 'races' not in horse_data:
            continue
        
        races = horse_data['races']
        
        for race in races:
            # 着順チェック（文字列"04"などを整数に変換）
            actual_rank = _safe_int(race.get('KAKUTEI_CHAKUJUN'))
            if actual_rank <= 0 or actual_rank >= 99:
                continue
            
            # オッズチェック（文字列"0123"などを整数に変換）
            odds_value = _safe_int(race.get('TANSHO_ODDS'))
            if odds_value <= 0:
                continue  # オッズ0は未確定レース
            
            actual_odds = odds_value / 10.0  # 10倍されているので戻す
            
            # レースメタ情報
            venue_code = str(race.get('KEIBAJO_CODE', '00')).zfill(2)
            race_number = _safe_int(race.get('RACE_BANGO'))
            distance = _safe_int(race.get('KYORI'))
            
            # 日付（KAISAI_NENとKAISAI_GAPPIを組み合わせる）
            kaisai_nen = str(race.get('KAISAI_NEN', '')).strip()
            kaisai_gappi = str(race.get('KAISAI_GAPPI', '')).strip()
            if not kaisai_nen or not kaisai_gappi:
                continue
            
            # KAISAI_NEN="2024", KAISAI_GAPPI="0831" → "20240831"
            date_str = kaisai_nen + kaisai_gappi.zfill(4)
            if len(date_str) != 8:
                continue
            
            # race_id生成
            race_id = f"{date_str}-{venue_code}-{race_number}"
            
            # レコード追加
            race_records.append({
                'race_id': race_id,
                'date': date_str,
                'venue_code': venue_code,
                'venue_name': venue_code_map.get(venue_code, '不明'),
                'race_number': race_number,
                'distance': distance,
                'horse_name': horse_name,
                'actual_rank': actual_rank,
                'actual_odds': actual_odds,
            })
    
    df = pd.DataFrame(race_records)
    
    print(f"✅ {len(df)}件のレース結果を抽出")
    print(f"   ユニークレース数: {df['race_id'].nunique()}")
    print(f"   ユニーク馬数: {df['horse_name'].nunique()}")
    
    return df

def add_features(df, viewlogic_manager):
    """特徴量を追加"""
    print("\n" + "=" * 60)
    print("Step 2: 特徴量計算")
    print("=" * 60)
    
    # 競馬場コードマップ
    venue_code_map = {
        '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
        '05': '東京', '06': '中山', '07': '中京', '08': '京都',
        '09': '阪神', '10': '小倉'
    }
    
    features_list = []
    total = len(df)
    
    print(f"特徴量計算開始（{total}件）...")
    
    for idx, row in df.iterrows():
        if (idx + 1) % 1000 == 0:
            print(f"  処理中: {idx + 1}/{total} ({(idx+1)/total*100:.1f}%)")
        
        horse_name = row['horse_name']
        venue_code = str(row['venue_code']).zfill(2)
        venue = row.get('venue_name', venue_code_map.get(venue_code, '不明'))
        distance = int(row['distance']) if pd.notna(row['distance']) else 2000
        
        # ナレッジデータ取得
        horse_data = viewlogic_manager.get_horse_data(horse_name)
        
        if horse_data and 'races' in horse_data:
            races = horse_data['races']
            
            # 基本統計
            total_races = len(races)
            wins = sum(1 for r in races if _safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
            places = sum(1 for r in races if _safe_int(r.get('KAKUTEI_CHAKUJUN')) <= 3)
            
            win_rate = wins / total_races if total_races > 0 else 0.0
            place_rate = places / total_races if total_races > 0 else 0.0
            
            # 平均着順
            finishes = [_safe_int(r.get('KAKUTEI_CHAKUJUN')) for r in races 
                       if _safe_int(r.get('KAKUTEI_CHAKUJUN')) > 0]
            avg_finish = sum(finishes) / len(finishes) if finishes else 10.0
            
            # 平均人気
            popularities = [_safe_int(r.get('NINKIJUN')) for r in races 
                           if _safe_int(r.get('NINKIJUN')) > 0]
            avg_popularity = sum(popularities) / len(popularities) if popularities else 8.0
            
            # 平均4コーナー順位
            corner4s = [_safe_int(r.get('CORNER4_JUNI')) for r in races 
                       if _safe_int(r.get('CORNER4_JUNI')) > 0]
            avg_corner4 = sum(corner4s) / len(corner4s) if corner4s else 8.0
            
            # 平均後半3F
            kohan3fs = [_safe_int(r.get('KOHAN3F_TIME')) for r in races 
                       if _safe_int(r.get('KOHAN3F_TIME')) > 0]
            avg_kohan3f = sum(kohan3fs) / len(kohan3fs) if kohan3fs else 400
            
            # コース別成績
            track_races = [r for r in races 
                          if r.get('KEIBAJO_CODE', '').zfill(2) == venue_code]
            
            if track_races:
                track_wins = sum(1 for r in track_races 
                                if _safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
                track_win_rate = track_wins / len(track_races)
                
                track_finishes = [_safe_int(r.get('KAKUTEI_CHAKUJUN')) 
                                 for r in track_races 
                                 if _safe_int(r.get('KAKUTEI_CHAKUJUN')) > 0]
                track_avg_finish = sum(track_finishes) / len(track_finishes) if track_finishes else 10.0
            else:
                track_win_rate = 0.0
                track_avg_finish = 10.0
            
            # 距離適性
            similar_races = [r for r in races 
                            if abs(_safe_int(r.get('KYORI')) - distance) <= 200]
            if similar_races:
                distance_wins = sum(1 for r in similar_races 
                                   if _safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
                distance_aptitude = distance_wins / len(similar_races)
            else:
                distance_aptitude = 0.5
                
        else:
            # ナレッジがない場合のデフォルト値
            total_races = 0
            win_rate = 0.0
            place_rate = 0.0
            avg_finish = 10.0
            avg_popularity = 8.0
            avg_corner4 = 8.0
            avg_kohan3f = 400
            track_win_rate = 0.0
            track_avg_finish = 10.0
            distance_aptitude = 0.5
        
        # 実際の支持率を計算（0.8 / オッズ）
        actual_odds = row['actual_odds']
        if pd.notna(actual_odds) and actual_odds > 0:
            actual_support_rate = 0.8 / actual_odds
        else:
            actual_support_rate = 0.0
        
        # 特徴量辞書
        features = {
            'race_id': row['race_id'],
            'horse_name': horse_name,
            'actual_rank': int(row['actual_rank']),
            'actual_odds': actual_odds if pd.notna(actual_odds) else 0.0,
            'actual_support_rate': actual_support_rate,
            
            # 特徴量
            'knowledge_total_races': total_races,
            'knowledge_win_rate': win_rate,
            'knowledge_place_rate': place_rate,
            'knowledge_avg_finish': avg_finish,
            'knowledge_avg_popularity': avg_popularity,
            'knowledge_avg_corner4': avg_corner4,
            'knowledge_avg_kohan3f': avg_kohan3f,
            'track_win_rate': track_win_rate,
            'track_avg_finish': track_avg_finish,
            'distance_aptitude': distance_aptitude,
            'venue_code': int(venue_code),
            'distance': distance,
        }
        
        features_list.append(features)
    
    print(f"✅ 特徴量計算完了")
    
    return pd.DataFrame(features_list)

def _safe_int(value, default=0):
    """安全に整数に変換"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def main():
    """メイン処理"""
    print("\n🚀 N-Logic 学習データ準備")
    print("=" * 60)
    
    # ViewLogicDataManager初期化
    print("\nViewLogicDataManager初期化中...")
    viewlogic_manager = ViewLogicDataManager()
    print(f"✅ ナレッジデータ読み込み完了: {len(viewlogic_manager.horses_dict)}頭")
    
    # Step 1: レース結果抽出
    df_results = extract_race_results_from_knowledge(viewlogic_manager)
    
    # Step 2: 特徴量追加
    df_with_features = add_features(df_results, viewlogic_manager)
    
    # Step 3: CSV保存
    print("\n" + "=" * 60)
    print("Step 3: データ保存")
    print("=" * 60)
    
    output_path = os.path.join(os.path.dirname(__file__), 'nlogic_training_data.csv')
    df_with_features.to_csv(output_path, index=False)
    
    print(f"✅ 学習データ保存: {output_path}")
    print(f"   総レコード数: {len(df_with_features)}")
    print(f"   ユニークレース数: {df_with_features['race_id'].nunique()}")
    print(f"   ファイルサイズ: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    
    # データ統計
    print("\n【データ統計】")
    print(f"  総レース数: {df_with_features['race_id'].nunique()}")
    print(f"  総馬数: {df_with_features['horse_name'].nunique()}")
    print(f"  平均出走頭数: {len(df_with_features) / df_with_features['race_id'].nunique():.1f}頭/レース")
    
    print("\n🎉 学習データ準備完了！")
    print("\n次のステップ:")
    print(f"  python3 scripts/train_nlogic_model.py --data {output_path}")

if __name__ == '__main__':
    main()
