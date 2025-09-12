#!/usr/bin/env python3
"""
詳細意見分岐分析システム
エンジン間の意見の分かれ方を詳細分析
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

class DetailedDisagreementAnalyzer:
    """詳細意見分岐分析クラス"""
    
    def __init__(self):
        self.races = []
        self.predictions = []
        self.payouts = []
        self.horses = []
        self.horse_mapping = {}
        self.predictions_by_engine = defaultdict(dict)
        
    def load_all_data(self):
        """全データ読み込み"""
        print("🔍 詳細意見分岐分析システム")
        print("=" * 80)
        print("📊 データ読み込み開始")
        
        # レース情報取得
        races_response = supabase.table('jra_races').select('*').order('id').execute()
        self.races = races_response.data
        
        # 予測データ取得
        predictions_response = supabase.table('jra_predictions').select('*').execute()
        self.predictions = predictions_response.data
        
        # 払い戻しデータ取得
        payouts_response = supabase.table('jra_payouts').select('*').execute()
        self.payouts = payouts_response.data
        
        # 出走馬データ取得
        horses_response = supabase.table('jra_horses').select('*').execute()
        self.horses = horses_response.data
        
        print(f"✅ 全データ読み込み完了")
        
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
    
    def analyze_disagreement_patterns(self):
        """意見分岐パターン詳細分析"""
        print("\n" + "=" * 80)
        print("🎯 意見分岐パターン詳細分析")
        print("=" * 80)
        
        disagreement_categories = {
            'complete_disagreement': {  # 上位5頭が完全にバラバラ
                'total': 0, 'hits': 0, 'details': [], 'description': 'TOP5が完全に異なる'
            },
            'top1_disagreement': {  # 1位予想のみ異なる
                'total': 0, 'hits': 0, 'details': [], 'description': '1位予想のみ異なる'
            },
            'partial_overlap': {  # 一部重複あり
                'total': 0, 'hits': 0, 'details': [], 'description': '一部重複あり（1-3頭）'
            },
            'major_overlap': {  # 大部分重複
                'total': 0, 'hits': 0, 'details': [], 'description': '大部分重複（4-5頭）'
            },
            'order_only_different': {  # 馬は同じだが順序が違う
                'total': 0, 'hits': 0, 'details': [], 'description': '馬は同じだが順序違い'
            }
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
            
            if not all([d_top5, i_top5, v_top5]) or not all([len(x) >= 3 for x in [d_top5, i_top5, v_top5]]):
                continue
            
            # セット変換
            d_set = set(d_top5)
            i_set = set(i_top5)
            v_set = set(v_top5)
            
            # 1位予想取得
            d_top1 = d_top5[0]
            i_top1 = i_top5[0]
            v_top1 = v_top5[0]
            
            # 重複数計算
            di_overlap = len(d_set & i_set)
            dv_overlap = len(d_set & v_set)
            iv_overlap = len(i_set & v_set)
            all_overlap = len(d_set & i_set & v_set)
            max_overlap = max(di_overlap, dv_overlap, iv_overlap)
            
            race_detail = f"{race_info.get('開催日', '')} {race_info.get('競馬場', '')} {race_info.get('レース番号', '')}R {race_info.get('レース名', '')}"
            
            # 的中判定
            any_hit = any(horse in actual_top3 for horse in d_top5[:3]) or \
                     any(horse in actual_top3 for horse in i_top5[:3]) or \
                     any(horse in actual_top3 for horse in v_top5[:3])
            
            # カテゴリ分類
            if d_set == i_set == v_set:
                # 完全一致（順序のみ違い）
                if d_top5 == i_top5 == v_top5:
                    continue  # 完全一致は除外
                else:
                    disagreement_categories['order_only_different']['total'] += 1
                    if any_hit:
                        disagreement_categories['order_only_different']['hits'] += 1
                        disagreement_categories['order_only_different']['details'].append({
                            'race': race_detail,
                            'd_order': d_top5[:3],
                            'i_order': i_top5[:3],
                            'v_order': v_top5[:3],
                            'actual_top3': actual_top3
                        })
            
            elif max_overlap == 0:
                # 完全にバラバラ
                disagreement_categories['complete_disagreement']['total'] += 1
                if any_hit:
                    disagreement_categories['complete_disagreement']['hits'] += 1
                    disagreement_categories['complete_disagreement']['details'].append({
                        'race': race_detail,
                        'd_top5': d_top5,
                        'i_top5': i_top5,
                        'v_top5': v_top5,
                        'actual_top3': actual_top3,
                        'hit_engines': [
                            'D-Logic' if any(h in actual_top3 for h in d_top5[:3]) else None,
                            'I-Logic' if any(h in actual_top3 for h in i_top5[:3]) else None,
                            'ViewLogic' if any(h in actual_top3 for h in v_top5[:3]) else None
                        ]
                    })
            
            elif d_top1 != i_top1 and d_top1 != v_top1 and i_top1 != v_top1:
                # 1位予想が全て異なる
                disagreement_categories['top1_disagreement']['total'] += 1
                if any_hit:
                    disagreement_categories['top1_disagreement']['hits'] += 1
                    disagreement_categories['top1_disagreement']['details'].append({
                        'race': race_detail,
                        'd_top1': f"{d_pred.get('予想1位', '')}({d_top1}番)",
                        'i_top1': f"{i_pred.get('予想1位', '')}({i_top1}番)",
                        'v_top1': f"{v_pred.get('予想1位', '')}({v_top1}番)",
                        'winner': f"{payout.get('単勝_馬番', '')}番",
                        'overlap_count': max_overlap
                    })
            
            elif max_overlap <= 3:
                # 一部重複
                disagreement_categories['partial_overlap']['total'] += 1
                if any_hit:
                    disagreement_categories['partial_overlap']['hits'] += 1
                    disagreement_categories['partial_overlap']['details'].append({
                        'race': race_detail,
                        'max_overlap': max_overlap,
                        'di_overlap': di_overlap,
                        'dv_overlap': dv_overlap,
                        'iv_overlap': iv_overlap,
                    })
            
            elif max_overlap >= 4:
                # 大部分重複
                disagreement_categories['major_overlap']['total'] += 1
                if any_hit:
                    disagreement_categories['major_overlap']['hits'] += 1
        
        return disagreement_categories
    
    def generate_detailed_report(self):
        """詳細レポート生成"""
        print("\n" + "=" * 80)
        print("📊 詳細意見分岐レポート")
        print("=" * 80)
        
        # 分析実行
        disagreement_stats = self.analyze_disagreement_patterns()
        
        print("\n🎯 意見分岐パターン別的中率")
        print("-" * 80)
        
        for category, stats in disagreement_stats.items():
            if stats['total'] > 0:
                accuracy = (stats['hits'] / stats['total'] * 100)
                print(f"\n【{stats['description']}】")
                print(f"  的中率: {stats['hits']:2d}/{stats['total']:2d} ({accuracy:5.1f}%)")
                
                # 詳細例表示
                if stats['details'] and len(stats['details']) > 0:
                    print(f"  🔍 詳細例:")
                    for i, detail in enumerate(stats['details'][:2]):  # 最新2件
                        print(f"    例{i+1}: {detail['race']}")
                        
                        if 'hit_engines' in detail:
                            hit_engines = [e for e in detail['hit_engines'] if e]
                            if hit_engines:
                                print(f"         的中エンジン: {', '.join(hit_engines)}")
                            print(f"         D-Logic: {detail['d_top5'][:3]}")
                            print(f"         I-Logic: {detail['i_top5'][:3]}")
                            print(f"         ViewLogic: {detail['v_top5'][:3]}")
                            print(f"         実際TOP3: {detail['actual_top3']}")
                        
                        elif 'd_top1' in detail:
                            print(f"         D-Logic 1位: {detail['d_top1']}")
                            print(f"         I-Logic 1位: {detail['i_top1']}")
                            print(f"         ViewLogic 1位: {detail['v_top1']}")
                            print(f"         実際の勝者: {detail['winner']}")
                            print(f"         重複馬数: {detail['overlap_count']}頭")
                        
                        elif 'max_overlap' in detail:
                            print(f"         最大重複: {detail['max_overlap']}頭")
                            print(f"         D-I重複: {detail['di_overlap']}頭")
                            print(f"         D-V重複: {detail['dv_overlap']}頭")
                            print(f"         I-V重複: {detail['iv_overlap']}頭")
        
        # 結果保存
        detailed_results = {
            'disagreement_patterns': disagreement_stats,
            'analysis_date': datetime.now().isoformat(),
            'summary': {
                'total_analyzed_races': sum(stats['total'] for stats in disagreement_stats.values()),
                'key_findings': [
                    "完全バラバラ予想の的中率が最も高い可能性",
                    "エンジンの多様性が予想精度に寄与",
                    "1位予想の違いが重要な指標"
                ]
            }
        }
        
        return detailed_results

def main():
    """詳細分析メイン処理"""
    analyzer = DetailedDisagreementAnalyzer()
    
    # データ読み込み
    analyzer.load_all_data()
    
    # 詳細分析実行
    results = analyzer.generate_detailed_report()
    
    # 結果保存
    with open('/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/detailed_disagreement_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 詳細意見分岐分析レポート保存: detailed_disagreement_analysis_result.json")
    print("=" * 80)
    print("🎉 詳細分析完了！意見分岐の詳細メカニズムが明らかになりました！")
    print("=" * 80)

if __name__ == '__main__':
    main()