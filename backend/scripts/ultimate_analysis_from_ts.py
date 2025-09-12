#!/usr/bin/env python3
"""
究極の予測精度分析システム
TSファイルから正確な馬名→馬番変換による完全分析
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import defaultdict

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# TSファイルパス
TS_FILES = {
    '2025-08-31': '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250831.ts',
    '2025-09-06': [
        '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250906-中山.ts',
        '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250906-札幌.ts',
        '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250906-阪神.ts',
    ],
    '2025-09-07': [
        '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250907-中山.ts',
        '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250907-札幌.ts',
        '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250907-阪神.ts',
    ]
}

class UltimateAnalyzer:
    """究極の予測精度分析クラス"""
    
    def __init__(self):
        self.races = []
        self.predictions = []
        self.payouts = []
        self.ts_horse_mapping = {}  # date-venue-race -> {horse_name: number}
        self.analysis_results = defaultdict(dict)
        
    def load_data(self):
        """データ読み込み"""
        print("🚀 究極の予測精度分析システム")
        print("=" * 80)
        print("📊 データ読み込み開始")
        print("=" * 80)
        
        # Supabaseデータ取得
        races_response = supabase.table('jra_races').select('*').order('id').execute()
        self.races = races_response.data
        print(f"✅ レース情報: {len(self.races)}件")
        
        predictions_response = supabase.table('jra_predictions').select('*').execute()
        self.predictions = predictions_response.data
        print(f"✅ 予測データ: {len(self.predictions)}件")
        
        payouts_response = supabase.table('jra_payouts').select('*').execute()
        self.payouts = payouts_response.data
        print(f"✅ 払い戻しデータ: {len(self.payouts)}件")
        
        # データ整理
        self.race_dict = {r['id']: r for r in self.races}
        self.payout_dict = {p['race_id']: p for p in self.payouts}
        
        # 予測データをエンジン別に整理
        self.predictions_by_engine = defaultdict(dict)
        for pred in self.predictions:
            race_id = pred['race_id']
            engine = pred['エンジン名'].lower().replace('-', '')
            self.predictions_by_engine[engine][race_id] = pred
        
        print(f"✅ データ整理完了")
    
    def parse_ts_horse_data(self):
        """TSファイルから馬名→馬番マッピングを作成"""
        print("\n🔍 TSファイル解析による馬名→馬番マッピング作成")
        
        total_races_mapped = 0
        
        for date, file_paths in TS_FILES.items():
            if isinstance(file_paths, str):
                file_paths = [file_paths]
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 会場名を推定
                    venue = self.extract_venue_from_path(file_path)
                    
                    # レースデータを正規表現で抽出
                    race_blocks = self.extract_race_blocks(content)
                    
                    for race_data in race_blocks:
                        race_number = race_data.get('race_number')
                        horses = race_data.get('horses', [])
                        
                        if race_number and horses:
                            key = f"{date}-{venue}-{race_number}"
                            self.ts_horse_mapping[key] = {}
                            
                            # 配列インデックス → 馬番変換
                            for i, horse_name in enumerate(horses):
                                self.ts_horse_mapping[key][horse_name] = i + 1
                            
                            total_races_mapped += 1
                            print(f"  {key}: {len(horses)}頭")
                
                except Exception as e:
                    print(f"  ❌ {file_path} 読み込みエラー: {e}")
        
        print(f"✅ TSファイルマッピング完了: {total_races_mapped}レース")
        
        # サンプル表示
        sample_keys = list(self.ts_horse_mapping.keys())[:3]
        for key in sample_keys:
            mapping = self.ts_horse_mapping[key]
            print(f"  {key}:")
            for horse_name, number in list(mapping.items())[:3]:
                print(f"    {horse_name} → {number}番")
    
    def extract_venue_from_path(self, file_path: str) -> str:
        """ファイルパスから会場名を抽出"""
        if '中山' in file_path:
            return '中山'
        elif '阪神' in file_path:
            return '阪神'
        elif '札幌' in file_path:
            return '札幌'
        elif '新潟' in file_path:
            return '新潟'
        elif '中京' in file_path:
            return '中京'
        else:
            return '不明'
    
    def extract_race_blocks(self, content: str) -> List[Dict]:
        """TSファイルからレースブロックを抽出"""
        races = []
        
        # レースブロックを正規表現で抽出
        race_pattern = r'\{[^}]*race_number:\s*(\d+)[^}]*horses:\s*\[(.*?)\][^}]*\}'
        
        matches = re.finditer(race_pattern, content, re.DOTALL)
        
        for match in matches:
            race_number = int(match.group(1))
            horses_str = match.group(2)
            
            # 馬名を抽出
            horse_pattern = r'"([^"]+)"'
            horses = re.findall(horse_pattern, horses_str)
            
            races.append({
                'race_number': race_number,
                'horses': horses
            })
        
        return races
    
    def calculate_ultimate_accuracy(self):
        """究極の的中率計算"""
        print("\n" + "=" * 80)
        print("🎯 究極の的中率分析（TSファイル基準）")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        for engine in engines:
            hits = 0
            total = 0
            total_return = 0
            hit_details = []
            mapping_errors = 0
            
            engine_predictions = self.predictions_by_engine.get(engine, {})
            
            for race_id, payout in self.payout_dict.items():
                if race_id not in engine_predictions:
                    continue
                
                prediction = engine_predictions[race_id]
                race = self.race_dict.get(race_id, {})
                
                # レース情報から検索キーを作成
                race_date = race.get('開催日')
                venue = race.get('競馬場')
                race_number = race.get('レース番号')
                
                if not all([race_date, venue, race_number]):
                    continue
                
                search_key = f"{race_date}-{venue}-{race_number}"
                
                if search_key not in self.ts_horse_mapping:
                    mapping_errors += 1
                    continue
                
                mapping = self.ts_horse_mapping[search_key]
                
                # 予想1位の馬名
                predicted_horse_name = prediction.get('予想1位')
                # 実際の1着馬番
                actual_winner_num = payout.get('単勝_馬番')
                
                if not predicted_horse_name or not actual_winner_num:
                    continue
                
                # TSファイルから馬番を取得
                predicted_horse_num = mapping.get(predicted_horse_name)
                
                if predicted_horse_num is None:
                    mapping_errors += 1
                    continue
                
                total += 1
                actual_num = int(actual_winner_num)
                
                # 的中判定
                if predicted_horse_num == actual_num:
                    hits += 1
                    payout_amount = payout.get('単勝_払戻', 0)
                    total_return += payout_amount
                    
                    hit_details.append({
                        'race': f"{race_date} {venue} {race_number}R",
                        'race_name': race.get('レース名', ''),
                        'horse_name': predicted_horse_name,
                        'horse_num': actual_winner_num,
                        'payout': payout_amount,
                        'search_key': search_key
                    })
            
            accuracy = (hits / total * 100) if total > 0 else 0
            recovery_rate = (total_return / (total * 100) * 100) if total > 0 else 0
            
            self.analysis_results[engine]['単勝'] = {
                '的中数': hits,
                '総レース数': total,
                '的中率': accuracy,
                '回収率': recovery_rate,
                '総払戻': total_return,
                '的中詳細': hit_details,
                'マッピングエラー': mapping_errors
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  分析対象: {total}レース")
            print(f"  的中: {hits}/{total} ({accuracy:.1f}%)")
            print(f"  回収率: {recovery_rate:.1f}%")
            print(f"  総投資: {total * 100:,}円 → 総払戻: {total_return:,}円")
            print(f"  損益: {total_return - (total * 100):+,}円")
            print(f"  マッピングエラー: {mapping_errors}件")
            
            if hit_details:
                print(f"  🎯 的中例（最新5件）:")
                for detail in hit_details[-5:]:
                    print(f"    • {detail['race']} {detail['race_name']}")
                    print(f"      {detail['horse_name']}({detail['horse_num']}番) {detail['payout']}円")
    
    def calculate_ultimate_fukusho(self):
        """究極の複勝的中率計算"""
        print("\n" + "=" * 80)
        print("🎯 究極の複勝的中率分析")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        for engine in engines:
            hits_by_rank = [0, 0, 0, 0, 0]  # 1-5位予想
            total = 0
            
            engine_predictions = self.predictions_by_engine.get(engine, {})
            
            for race_id, payout in self.payout_dict.items():
                if race_id not in engine_predictions:
                    continue
                
                prediction = engine_predictions[race_id]
                race = self.race_dict.get(race_id, {})
                
                # レース情報から検索キーを作成
                race_date = race.get('開催日')
                venue = race.get('競馬場')
                race_number = race.get('レース番号')
                
                search_key = f"{race_date}-{venue}-{race_number}"
                
                if search_key not in self.ts_horse_mapping:
                    continue
                
                mapping = self.ts_horse_mapping[search_key]
                
                # 実際の3着以内の馬番
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
                
                total += 1
                
                # 各順位の予想をチェック
                for rank in range(1, 6):
                    predicted_horse_name = prediction.get(f'予想{rank}位')
                    if predicted_horse_name:
                        predicted_horse_num = mapping.get(predicted_horse_name)
                        if predicted_horse_num and predicted_horse_num in actual_top3:
                            hits_by_rank[rank - 1] += 1
            
            total_hits = sum(hits_by_rank)
            
            self.analysis_results[engine]['複勝'] = {
                '1位予想的中': hits_by_rank[0],
                '2位予想的中': hits_by_rank[1],
                '3位予想的中': hits_by_rank[2],
                '4位予想的中': hits_by_rank[3],
                '5位予想的中': hits_by_rank[4],
                '総的中数': total_hits,
                '総レース数': total,
                '総合的中率': (total_hits / (total * 5) * 100) if total > 0 else 0
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  分析対象: {total}レース")
            for rank in range(5):
                rate = (hits_by_rank[rank] / total * 100) if total > 0 else 0
                print(f"  {rank+1}位予想→3着内: {hits_by_rank[rank]}/{total} ({rate:.1f}%)")
            
            total_rate = (total_hits / (total * 5) * 100) if total > 0 else 0
            print(f"  総合的中率: {total_rate:.1f}%")
    
    def generate_ultimate_report(self):
        """究極レポート生成"""
        print("\n" + "=" * 80)
        print("👑 究極分析レポート（TSファイル基準の完全版）")
        print("=" * 80)
        
        # エンジン別総合評価
        engine_scores = {}
        
        for engine in ['dlogic', 'ilogic', 'viewlogic']:
            tansho = self.analysis_results[engine].get('単勝', {})
            fukusho = self.analysis_results[engine].get('複勝', {})
            
            # 総合スコア計算（重み付け）
            tansho_score = tansho.get('的中率', 0) * 3
            fukusho_score = fukusho.get('総合的中率', 0) * 2
            recovery_score = min(tansho.get('回収率', 0), 200) * 1.5  # 上限200%
            
            total_score = (tansho_score + fukusho_score + recovery_score) / 6.5
            
            engine_scores[engine] = {
                'engine_name': engine.upper(),
                'total_score': total_score,
                'tansho_hits': tansho.get('的中数', 0),
                'tansho_rate': tansho.get('的中率', 0),
                'tansho_recovery': tansho.get('回収率', 0),
                'fukusho_rate': fukusho.get('総合的中率', 0),
                'total_races': tansho.get('総レース数', 0),
                'profit': tansho.get('総払戻', 0) - (tansho.get('総レース数', 0) * 100),
                'roi': ((tansho.get('総払戻', 0) - (tansho.get('総レース数', 0) * 100)) / (tansho.get('総レース数', 0) * 100) * 100) if tansho.get('総レース数', 0) > 0 else 0
            }
        
        # 究極ランキング表示
        print("\n🏆 究極エンジンランキング（TSファイル完全版）")
        sorted_engines = sorted(engine_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        for rank, (engine, scores) in enumerate(sorted_engines, 1):
            print(f"\n第{rank}位: {scores['engine_name']}")
            print(f"  📊 総合スコア: {scores['total_score']:.2f}点")
            print(f"  🎯 対象レース: {scores['total_races']}レース")
            print(f"  🏁 単勝: {scores['tansho_hits']}的中 / {scores['tansho_rate']:.1f}%")
            print(f"  💰 回収率: {scores['tansho_recovery']:.1f}%")
            print(f"  🎪 複勝的中率: {scores['fukusho_rate']:.1f}%")
            print(f"  💵 ROI: {scores['roi']:+.1f}%")
            print(f"  📈 損益: {scores['profit']:+,}円")
        
        # 究極投資シミュレーション
        print(f"\n💎 究極投資シミュレーション")
        print(f"（TSファイル基準・実績{sorted_engines[0][1]['total_races']}レース）")
        
        for engine, perf in sorted_engines:
            investment = perf['total_races'] * 100
            returns = perf['profit'] + investment
            
            print(f"\n{perf['engine_name']}エンジン:")
            print(f"  投資額: {investment:,}円")
            print(f"  回収額: {returns:,}円") 
            print(f"  損益: {perf['profit']:+,}円")
            print(f"  ROI: {perf['roi']:+.1f}%")
            
            if perf['roi'] > 0:
                print(f"  🎉 利益確定！")
            else:
                print(f"  📉 要検討")
        
        # 究極戦略提案
        best_engine = sorted_engines[0]
        best_accuracy = max(engine_scores.items(), key=lambda x: x[1]['tansho_rate'])
        best_roi = max(engine_scores.items(), key=lambda x: x[1]['roi'])
        
        print(f"\n🎯 究極戦略提案")
        print(f"1. 総合最強: {best_engine[1]['engine_name']} (スコア{best_engine[1]['total_score']:.1f}点)")
        print(f"2. 的中重視: {best_accuracy[1]['engine_name']} (的中率{best_accuracy[1]['tansho_rate']:.1f}%)")
        print(f"3. 利益重視: {best_roi[1]['engine_name']} (ROI{best_roi[1]['roi']:+.1f}%)")
        
        return engine_scores

def main():
    """究極メイン処理"""
    analyzer = UltimateAnalyzer()
    
    # データ読み込み・整理
    analyzer.load_data()
    analyzer.parse_ts_horse_data()
    
    # 究極分析実行
    analyzer.calculate_ultimate_accuracy()
    analyzer.calculate_ultimate_fukusho()
    
    # 究極レポート
    performance = analyzer.generate_ultimate_report()
    
    # 結果保存
    with open('/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/ultimate_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(performance, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 究極分析レポートを保存: ultimate_analysis_result.json")
    print("=" * 80)
    print("🎉 究極分析完了！これで完璧です！")
    print("=" * 80)

if __name__ == '__main__':
    main()