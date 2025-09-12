#!/usr/bin/env python3
"""
高度重複分析システム
3つのエンジンの予想重複パターン別的中率分析
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import defaultdict
import json

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class AdvancedOverlapAnalyzer:
    """高度重複分析クラス"""
    
    def __init__(self):
        self.races = []
        self.predictions = []
        self.payouts = []
        self.horses = []
        self.horse_mapping = {}
        self.predictions_by_engine = defaultdict(dict)
        self.overlap_results = defaultdict(dict)
        
    def load_all_data(self):
        """全データ読み込み"""
        print("🔬 高度重複分析システム")
        print("=" * 80)
        print("📊 データ読み込み開始")
        
        # レース情報取得
        races_response = supabase.table('jra_races').select('*').order('id').execute()
        self.races = races_response.data
        print(f"✅ レース情報: {len(self.races)}件")
        
        # 予測データ取得
        predictions_response = supabase.table('jra_predictions').select('*').execute()
        self.predictions = predictions_response.data
        print(f"✅ 予測データ: {len(self.predictions)}件")
        
        # 払い戻しデータ取得
        payouts_response = supabase.table('jra_payouts').select('*').execute()
        self.payouts = payouts_response.data
        print(f"✅ 払い戻しデータ: {len(self.payouts)}件")
        
        # 出走馬データ取得
        horses_response = supabase.table('jra_horses').select('*').execute()
        self.horses = horses_response.data
        print(f"✅ 出走馬データ: {len(self.horses)}件")
        
        # データ整理
        self.race_dict = {r['id']: r for r in self.races}
        self.payout_dict = {p['race_id']: p for p in self.payouts}
        
        # 予測データをエンジン別に整理
        for pred in self.predictions:
            race_id = pred['race_id']
            engine = pred['エンジン名'].lower().replace('-', '')
            self.predictions_by_engine[engine][race_id] = pred
        
        # 馬名→馬番マッピング作成
        for horse in self.horses:
            race_id = horse['race_id']
            horse_name = horse['馬名']
            horse_number = horse.get('馬番')
            
            if horse_number is not None:
                if race_id not in self.horse_mapping:
                    self.horse_mapping[race_id] = {}
                self.horse_mapping[race_id][horse_name] = horse_number
        
        print("✅ データ整理完了")
    
    def analyze_overlap_patterns(self):
        """重複パターン別分析"""
        print("\n" + "=" * 80)
        print("🎯 重複パターン別分析")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        # 各レースで重複パターンを分析
        pattern_stats = {
            'all_3_overlap': {'total': 0, 'hits': 0, 'details': []},
            'dlogic_ilogic': {'total': 0, 'hits': 0, 'details': []},
            'dlogic_viewlogic': {'total': 0, 'hits': 0, 'details': []},
            'ilogic_viewlogic': {'total': 0, 'hits': 0, 'details': []},
            'no_overlap': {'total': 0, 'hits': 0, 'details': []},
            'top1_overlap': {'total': 0, 'hits': 0, 'details': []},
            'top3_overlap': {'total': 0, 'hits': 0, 'details': []},
            'top5_all_match': {'total': 0, 'hits': 0, 'details': []},
        }
        
        for race_id, payout in self.payout_dict.items():
            if (race_id not in self.predictions_by_engine['dlogic'] or 
                race_id not in self.predictions_by_engine['ilogic'] or 
                race_id not in self.predictions_by_engine['viewlogic'] or
                race_id not in self.horse_mapping):
                continue
            
            # 各エンジンの予想を取得
            d_pred = self.predictions_by_engine['dlogic'][race_id]
            i_pred = self.predictions_by_engine['ilogic'][race_id]
            v_pred = self.predictions_by_engine['viewlogic'][race_id]
            
            mapping = self.horse_mapping[race_id]
            race_info = self.race_dict.get(race_id, {})
            
            # 実際の3着以内
            actual_top3 = []
            for i in range(1, 4):
                horse_num = payout.get(f'複勝_馬番_{i}')
                if horse_num:
                    try:
                        actual_top3.append(int(horse_num))
                    except:
                        pass
            
            if not actual_top3:
                continue
            
            # 各エンジンの上位5頭を馬番に変換
            def get_horse_numbers(pred, mapping):
                numbers = []
                for rank in range(1, 6):
                    horse_name = pred.get(f'予想{rank}位')
                    if horse_name and horse_name in mapping:
                        numbers.append(mapping[horse_name])
                return numbers
            
            d_top5 = get_horse_numbers(d_pred, mapping)
            i_top5 = get_horse_numbers(i_pred, mapping)
            v_top5 = get_horse_numbers(v_pred, mapping)
            
            if not all([d_top5, i_top5, v_top5]):
                continue
            
            # TOP1重複分析
            d_top1 = d_top5[0] if d_top5 else None
            i_top1 = i_top5[0] if i_top5 else None
            v_top1 = v_top5[0] if v_top5 else None
            
            if d_top1 == i_top1 == v_top1:
                pattern_stats['top1_overlap']['total'] += 1
                if d_top1 in actual_top3:
                    pattern_stats['top1_overlap']['hits'] += 1
                    pattern_stats['top1_overlap']['details'].append({
                        'race': f"{race_info.get('開催日', '')} {race_info.get('競馬場', '')} {race_info.get('レース番号', '')}R",
                        'horse_num': d_top1,
                        'horse_name': d_pred.get('予想1位', ''),
                    })
            
            # TOP3重複分析
            d_top3_set = set(d_top5[:3])
            i_top3_set = set(i_top5[:3])
            v_top3_set = set(v_top5[:3])
            
            common_top3 = d_top3_set & i_top3_set & v_top3_set
            if common_top3:
                pattern_stats['top3_overlap']['total'] += len(common_top3)
                hits = len(common_top3 & set(actual_top3))
                pattern_stats['top3_overlap']['hits'] += hits
                
                if hits > 0:
                    pattern_stats['top3_overlap']['details'].append({
                        'race': f"{race_info.get('開催日', '')} {race_info.get('競馬場', '')} {race_info.get('レース番号', '')}R",
                        'common_horses': list(common_top3 & set(actual_top3)),
                    })
            
            # TOP5完全一致分析
            if set(d_top5) == set(i_top5) == set(v_top5):
                pattern_stats['top5_all_match']['total'] += 1
                hits = len(set(d_top5) & set(actual_top3))
                if hits > 0:
                    pattern_stats['top5_all_match']['hits'] += hits
                    pattern_stats['top5_all_match']['details'].append({
                        'race': f"{race_info.get('開催日', '')} {race_info.get('競馬場', '')} {race_info.get('レース番号', '')}R",
                        'matched_count': hits,
                    })
            
            # 2つのエンジン重複分析
            if set(d_top5) == set(i_top5):
                pattern_stats['dlogic_ilogic']['total'] += 1
                hits = len(set(d_top5) & set(actual_top3))
                if hits > 0:
                    pattern_stats['dlogic_ilogic']['hits'] += hits
            
            if set(d_top5) == set(v_top5):
                pattern_stats['dlogic_viewlogic']['total'] += 1
                hits = len(set(d_top5) & set(actual_top3))
                if hits > 0:
                    pattern_stats['dlogic_viewlogic']['hits'] += hits
            
            if set(i_top5) == set(v_top5):
                pattern_stats['ilogic_viewlogic']['total'] += 1
                hits = len(set(i_top5) & set(actual_top3))
                if hits > 0:
                    pattern_stats['ilogic_viewlogic']['hits'] += hits
        
        return pattern_stats
    
    def analyze_consensus_strength(self):
        """コンセンサス強度分析"""
        print("\n" + "=" * 80)
        print("🤝 コンセンサス強度分析")
        print("=" * 80)
        
        consensus_levels = {
            '3_engine_consensus': {'total': 0, 'hits': 0, 'details': []},
            '2_engine_consensus': {'total': 0, 'hits': 0, 'details': []},
            'no_consensus': {'total': 0, 'hits': 0, 'details': []},
        }
        
        for race_id, payout in self.payout_dict.items():
            if (race_id not in self.predictions_by_engine['dlogic'] or 
                race_id not in self.predictions_by_engine['ilogic'] or 
                race_id not in self.predictions_by_engine['viewlogic'] or
                race_id not in self.horse_mapping):
                continue
            
            # 各エンジンの1位予想馬を取得
            d_pred = self.predictions_by_engine['dlogic'][race_id]
            i_pred = self.predictions_by_engine['ilogic'][race_id]
            v_pred = self.predictions_by_engine['viewlogic'][race_id]
            
            mapping = self.horse_mapping[race_id]
            
            d_top1_name = d_pred.get('予想1位')
            i_top1_name = i_pred.get('予想1位')
            v_top1_name = v_pred.get('予想1位')
            
            d_top1_num = mapping.get(d_top1_name) if d_top1_name else None
            i_top1_num = mapping.get(i_top1_name) if i_top1_name else None
            v_top1_num = mapping.get(v_top1_name) if v_top1_name else None
            
            if not all([d_top1_num, i_top1_num, v_top1_num]):
                continue
            
            # 実際の1着馬番
            actual_winner = payout.get('単勝_馬番')
            if not actual_winner:
                continue
            
            actual_winner_num = int(actual_winner)
            
            # コンセンサス判定
            if d_top1_num == i_top1_num == v_top1_num:
                # 3エンジンコンセンサス
                consensus_levels['3_engine_consensus']['total'] += 1
                if d_top1_num == actual_winner_num:
                    consensus_levels['3_engine_consensus']['hits'] += 1
                    consensus_levels['3_engine_consensus']['details'].append({
                        'race': f"{self.race_dict.get(race_id, {}).get('開催日', '')} {self.race_dict.get(race_id, {}).get('競馬場', '')} {self.race_dict.get(race_id, {}).get('レース番号', '')}R",
                        'horse_name': d_top1_name,
                        'horse_num': d_top1_num,
                        'payout': payout.get('単勝_払戻', 0)
                    })
            
            elif (d_top1_num == i_top1_num or d_top1_num == v_top1_num or i_top1_num == v_top1_num):
                # 2エンジンコンセンサス
                consensus_levels['2_engine_consensus']['total'] += 1
                consensus_horse = d_top1_num if d_top1_num == i_top1_num else (d_top1_num if d_top1_num == v_top1_num else i_top1_num)
                if consensus_horse == actual_winner_num:
                    consensus_levels['2_engine_consensus']['hits'] += 1
            
            else:
                # コンセンサスなし
                consensus_levels['no_consensus']['total'] += 1
                if actual_winner_num in [d_top1_num, i_top1_num, v_top1_num]:
                    consensus_levels['no_consensus']['hits'] += 1
        
        return consensus_levels
    
    def generate_advanced_report(self):
        """高度分析レポート生成"""
        print("\n" + "=" * 80)
        print("📊 高度重複分析レポート")
        print("=" * 80)
        
        # 重複パターン分析実行
        overlap_stats = self.analyze_overlap_patterns()
        consensus_stats = self.analyze_consensus_strength()
        
        print("\n🎯 重複パターン別的中率")
        print("-" * 60)
        
        for pattern, stats in overlap_stats.items():
            if stats['total'] > 0:
                accuracy = (stats['hits'] / stats['total'] * 100)
                print(f"{pattern.replace('_', ' ').title():20}: {stats['hits']:2d}/{stats['total']:2d} ({accuracy:5.1f}%)")
                
                # 的中例表示
                if stats['details'] and len(stats['details']) > 0:
                    print(f"  🏆 的中例:")
                    for detail in stats['details'][:2]:  # 最新2件
                        if 'horse_name' in detail:
                            print(f"    • {detail['race']} {detail['horse_name']}({detail['horse_num']}番)")
                        elif 'common_horses' in detail:
                            print(f"    • {detail['race']} 共通的中: {detail['common_horses']}")
        
        print("\n🤝 コンセンサス強度別的中率")
        print("-" * 60)
        
        for level, stats in consensus_stats.items():
            if stats['total'] > 0:
                accuracy = (stats['hits'] / stats['total'] * 100)
                print(f"{level.replace('_', ' ').title():20}: {stats['hits']:2d}/{stats['total']:2d} ({accuracy:5.1f}%)")
                
                # 的中例表示（3エンジンコンセンサスのみ）
                if level == '3_engine_consensus' and stats['details']:
                    print(f"  🎉 全エンジン一致的中:")
                    for detail in stats['details'][:3]:
                        print(f"    • {detail['race']} {detail['horse_name']}({detail['horse_num']}番) {detail['payout']}円")
        
        # 結果保存
        advanced_results = {
            'overlap_patterns': overlap_stats,
            'consensus_levels': consensus_stats,
            'analysis_date': datetime.now().isoformat(),
            'total_races_analyzed': len([r for r in self.payout_dict.keys() if all([
                r in self.predictions_by_engine['dlogic'],
                r in self.predictions_by_engine['ilogic'], 
                r in self.predictions_by_engine['viewlogic'],
                r in self.horse_mapping
            ])])
        }
        
        return advanced_results

def main():
    """高度分析メイン処理"""
    analyzer = AdvancedOverlapAnalyzer()
    
    # データ読み込み
    analyzer.load_all_data()
    
    # 高度分析実行
    results = analyzer.generate_advanced_report()
    
    # 結果保存
    with open('/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/advanced_overlap_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 高度重複分析レポート保存: advanced_overlap_analysis_result.json")
    print("=" * 80)
    print("🎉 高度分析完了！エンジン間の相関関係が明らかになりました！")
    print("=" * 80)

if __name__ == '__main__':
    main()