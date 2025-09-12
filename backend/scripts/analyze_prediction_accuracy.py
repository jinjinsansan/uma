#!/usr/bin/env python3
"""
エンジン予測精度分析システム
75レースの予測と実際の払い戻し結果を比較し、的中率・回収率を計算
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from collections import defaultdict
import json

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class PredictionAnalyzer:
    """予測精度分析クラス"""
    
    def __init__(self):
        self.races = []
        self.predictions = []
        self.payouts = []
        self.analysis_results = defaultdict(dict)
        
    def load_data(self):
        """データ読み込み"""
        print("=" * 80)
        print("📊 データ読み込み開始")
        print("=" * 80)
        
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
        
        # race_idをキーにした辞書を作成
        self.race_dict = {r['id']: r for r in self.races}
        self.prediction_dict = {p['race_id']: p for p in self.predictions}
        self.payout_dict = {p['race_id']: p for p in self.payouts}
        
    def calculate_tansho_accuracy(self):
        """単勝的中率計算"""
        print("\n" + "=" * 80)
        print("🎯 単勝的中率分析")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        for engine in engines:
            hits = 0
            total = 0
            total_return = 0
            hit_details = []
            
            for race_id, payout in self.payout_dict.items():
                if race_id not in self.prediction_dict:
                    continue
                    
                prediction = self.prediction_dict[race_id]
                race = self.race_dict.get(race_id, {})
                
                # 予想1位の馬番
                predicted_horse = prediction.get(f'{engine}_予想1位')
                # 実際の1着馬番
                actual_winner = payout.get('単勝_馬番')
                
                if predicted_horse and actual_winner:
                    total += 1
                    # 馬番を数値に変換して比較
                    try:
                        pred_num = int(predicted_horse.replace('番', '')) if '番' in str(predicted_horse) else int(predicted_horse)
                        actual_num = int(actual_winner)
                        
                        if pred_num == actual_num:
                            hits += 1
                            payout_amount = payout.get('単勝_払戻', 0)
                            total_return += payout_amount
                            
                            hit_details.append({
                                'race': f"{race.get('開催日', '')} {race.get('競馬場', '')} {race.get('レース番号', '')}R",
                                'race_name': race.get('レース名', ''),
                                'horse_num': actual_winner,
                                'payout': payout_amount
                            })
                    except (ValueError, TypeError):
                        pass
            
            accuracy = (hits / total * 100) if total > 0 else 0
            recovery_rate = (total_return / (total * 100) * 100) if total > 0 else 0
            
            self.analysis_results[engine]['単勝'] = {
                '的中数': hits,
                '総レース数': total,
                '的中率': accuracy,
                '回収率': recovery_rate,
                '総払戻': total_return,
                '的中詳細': hit_details
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  的中: {hits}/{total} ({accuracy:.1f}%)")
            print(f"  回収率: {recovery_rate:.1f}%")
            print(f"  総投資: {total * 100}円 → 総払戻: {total_return}円")
            
            if hit_details[:3]:  # 最新3件の的中を表示
                print(f"  最新的中例:")
                for detail in hit_details[:3]:
                    print(f"    • {detail['race']} {detail['horse_num']}番 {detail['payout']}円")
    
    def calculate_fukusho_accuracy(self):
        """複勝的中率計算（上位3頭が3着以内）"""
        print("\n" + "=" * 80)
        print("🎯 複勝的中率分析")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        for engine in engines:
            hits_1st = 0  # 1位予想が3着以内
            hits_2nd = 0  # 2位予想が3着以内
            hits_3rd = 0  # 3位予想が3着以内
            total = 0
            
            for race_id, payout in self.payout_dict.items():
                if race_id not in self.prediction_dict:
                    continue
                    
                prediction = self.prediction_dict[race_id]
                
                # 実際の3着以内の馬番
                actual_top3 = []
                for i in range(1, 4):
                    horse = payout.get(f'複勝_馬番_{i}')
                    if horse:
                        try:
                            actual_top3.append(int(horse))
                        except (ValueError, TypeError):
                            pass
                
                if not actual_top3:
                    continue
                
                total += 1
                
                # 各順位の予想をチェック
                for rank in range(1, 4):
                    predicted = prediction.get(f'{engine}_予想{rank}位')
                    if predicted:
                        try:
                            pred_num = int(predicted.replace('番', '')) if '番' in str(predicted) else int(predicted)
                            if pred_num in actual_top3:
                                if rank == 1:
                                    hits_1st += 1
                                elif rank == 2:
                                    hits_2nd += 1
                                elif rank == 3:
                                    hits_3rd += 1
                        except (ValueError, TypeError):
                            pass
            
            total_hits = hits_1st + hits_2nd + hits_3rd
            avg_accuracy = (total_hits / (total * 3) * 100) if total > 0 else 0
            
            self.analysis_results[engine]['複勝'] = {
                '1位予想的中': hits_1st,
                '2位予想的中': hits_2nd,
                '3位予想的中': hits_3rd,
                '総的中数': total_hits,
                '総レース数': total,
                '平均的中率': avg_accuracy
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  1位予想→3着内: {hits_1st}/{total} ({hits_1st/total*100:.1f}%)")
            print(f"  2位予想→3着内: {hits_2nd}/{total} ({hits_2nd/total*100:.1f}%)")
            print(f"  3位予想→3着内: {hits_3rd}/{total} ({hits_3rd/total*100:.1f}%)")
            print(f"  平均的中率: {avg_accuracy:.1f}%")
    
    def calculate_umaren_wide_accuracy(self):
        """馬連・ワイド的中率計算"""
        print("\n" + "=" * 80)
        print("🎯 馬連・ワイド的中率分析")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        for engine in engines:
            umaren_hits = 0
            wide_hits = 0
            total = 0
            
            for race_id, payout in self.payout_dict.items():
                if race_id not in self.prediction_dict:
                    continue
                    
                prediction = self.prediction_dict[race_id]
                
                # 予想上位5頭を取得
                predicted_horses = []
                for rank in range(1, 6):
                    horse = prediction.get(f'{engine}_予想{rank}位')
                    if horse:
                        try:
                            num = int(horse.replace('番', '')) if '番' in str(horse) else int(horse)
                            predicted_horses.append(num)
                        except (ValueError, TypeError):
                            pass
                
                if len(predicted_horses) < 2:
                    continue
                
                total += 1
                
                # 馬連チェック（上位2頭）
                umaren_actual = payout.get('馬連_馬番', '')
                if umaren_actual and len(predicted_horses) >= 2:
                    try:
                        # 馬連は "01-02" 形式
                        nums = [int(n) for n in umaren_actual.split('-')]
                        if set(nums) == set(predicted_horses[:2]):
                            umaren_hits += 1
                    except:
                        pass
                
                # ワイドチェック（上位3頭から2頭）
                for i in range(1, 4):
                    wide_actual = payout.get(f'ワイド_馬番_{i}', '')
                    if wide_actual and len(predicted_horses) >= 3:
                        try:
                            nums = [int(n) for n in wide_actual.split('-')]
                            # 上位3頭の組み合わせをチェック
                            if all(n in predicted_horses[:3] for n in nums):
                                wide_hits += 1
                                break  # 1つでも的中すればOK
                        except:
                            pass
            
            umaren_accuracy = (umaren_hits / total * 100) if total > 0 else 0
            wide_accuracy = (wide_hits / total * 100) if total > 0 else 0
            
            self.analysis_results[engine]['馬連'] = {
                '的中数': umaren_hits,
                '総レース数': total,
                '的中率': umaren_accuracy
            }
            
            self.analysis_results[engine]['ワイド'] = {
                '的中数': wide_hits,
                '総レース数': total,
                '的中率': wide_accuracy
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  馬連的中率: {umaren_hits}/{total} ({umaren_accuracy:.1f}%)")
            print(f"  ワイド的中率: {wide_hits}/{total} ({wide_accuracy:.1f}%)")
    
    def analyze_by_conditions(self):
        """条件別分析（競馬場、クラス、距離）"""
        print("\n" + "=" * 80)
        print("📊 条件別分析")
        print("=" * 80)
        
        # 競馬場別
        venue_stats = defaultdict(lambda: defaultdict(lambda: {'hits': 0, 'total': 0}))
        
        for race_id, payout in self.payout_dict.items():
            if race_id not in self.prediction_dict:
                continue
                
            race = self.race_dict.get(race_id, {})
            prediction = self.prediction_dict[race_id]
            venue = race.get('競馬場', '不明')
            
            actual_winner = payout.get('単勝_馬番')
            if not actual_winner:
                continue
            
            for engine in ['dlogic', 'ilogic', 'viewlogic']:
                predicted = prediction.get(f'{engine}_予想1位')
                if predicted:
                    try:
                        pred_num = int(predicted.replace('番', '')) if '番' in str(predicted) else int(predicted)
                        actual_num = int(actual_winner)
                        
                        venue_stats[venue][engine]['total'] += 1
                        if pred_num == actual_num:
                            venue_stats[venue][engine]['hits'] += 1
                    except:
                        pass
        
        # 競馬場別結果出力
        print("\n【競馬場別的中率】")
        for venue in sorted(venue_stats.keys()):
            print(f"\n{venue}:")
            for engine in ['dlogic', 'ilogic', 'viewlogic']:
                stats = venue_stats[venue][engine]
                if stats['total'] > 0:
                    accuracy = stats['hits'] / stats['total'] * 100
                    print(f"  {engine.upper()}: {stats['hits']}/{stats['total']} ({accuracy:.1f}%)")
    
    def calculate_combined_analysis(self):
        """複合分析（複数エンジンの組み合わせ）"""
        print("\n" + "=" * 80)
        print("🔄 複合エンジン分析")
        print("=" * 80)
        
        # 2エンジン以上が同じ馬を1位予想した場合
        consensus_hits = 0
        consensus_total = 0
        
        # 全エンジンが一致した場合
        unanimous_hits = 0
        unanimous_total = 0
        
        for race_id, payout in self.payout_dict.items():
            if race_id not in self.prediction_dict:
                continue
                
            prediction = self.prediction_dict[race_id]
            actual_winner = payout.get('単勝_馬番')
            if not actual_winner:
                continue
            
            # 各エンジンの1位予想を取得
            predictions_1st = []
            for engine in ['dlogic', 'ilogic', 'viewlogic']:
                pred = prediction.get(f'{engine}_予想1位')
                if pred:
                    try:
                        num = int(pred.replace('番', '')) if '番' in str(pred) else int(pred)
                        predictions_1st.append(num)
                    except:
                        pass
            
            if len(predictions_1st) < 2:
                continue
            
            try:
                actual_num = int(actual_winner)
                
                # 最頻値を取得（2エンジン以上の合意）
                from collections import Counter
                counter = Counter(predictions_1st)
                most_common = counter.most_common(1)[0]
                
                if most_common[1] >= 2:  # 2つ以上のエンジンが同じ予想
                    consensus_total += 1
                    if most_common[0] == actual_num:
                        consensus_hits += 1
                
                # 全エンジン一致
                if len(set(predictions_1st)) == 1 and len(predictions_1st) == 3:
                    unanimous_total += 1
                    if predictions_1st[0] == actual_num:
                        unanimous_hits += 1
            except:
                pass
        
        consensus_accuracy = (consensus_hits / consensus_total * 100) if consensus_total > 0 else 0
        unanimous_accuracy = (unanimous_hits / unanimous_total * 100) if unanimous_total > 0 else 0
        
        print(f"\n【複数エンジン合意】")
        print(f"  2エンジン以上一致: {consensus_hits}/{consensus_total} ({consensus_accuracy:.1f}%)")
        print(f"  全エンジン一致: {unanimous_hits}/{unanimous_total} ({unanimous_accuracy:.1f}%)")
    
    def generate_report(self):
        """総合レポート生成"""
        print("\n" + "=" * 80)
        print("📈 総合分析レポート")
        print("=" * 80)
        
        # エンジン別総合評価
        engine_scores = {}
        
        for engine in ['dlogic', 'ilogic', 'viewlogic']:
            tansho = self.analysis_results[engine].get('単勝', {})
            fukusho = self.analysis_results[engine].get('複勝', {})
            umaren = self.analysis_results[engine].get('馬連', {})
            wide = self.analysis_results[engine].get('ワイド', {})
            
            # 総合スコア計算（重み付け）
            score = 0
            score += tansho.get('的中率', 0) * 3  # 単勝は3倍の重み
            score += fukusho.get('平均的中率', 0) * 2  # 複勝は2倍
            score += umaren.get('的中率', 0) * 1.5  # 馬連は1.5倍
            score += wide.get('的中率', 0) * 1  # ワイドは1倍
            
            engine_scores[engine] = {
                '総合スコア': score / 7.5,  # 正規化
                '単勝的中率': tansho.get('的中率', 0),
                '単勝回収率': tansho.get('回収率', 0),
                '複勝的中率': fukusho.get('平均的中率', 0),
                '馬連的中率': umaren.get('的中率', 0),
                'ワイド的中率': wide.get('的中率', 0)
            }
        
        # ランキング表示
        print("\n🏆 エンジン総合ランキング")
        sorted_engines = sorted(engine_scores.items(), key=lambda x: x[1]['総合スコア'], reverse=True)
        
        for rank, (engine, scores) in enumerate(sorted_engines, 1):
            print(f"\n第{rank}位: {engine.upper()}")
            print(f"  総合スコア: {scores['総合スコア']:.2f}")
            print(f"  単勝: 的中率 {scores['単勝的中率']:.1f}% / 回収率 {scores['単勝回収率']:.1f}%")
            print(f"  複勝: 的中率 {scores['複勝的中率']:.1f}%")
            print(f"  馬連: 的中率 {scores['馬連的中率']:.1f}%")
            print(f"  ワイド: 的中率 {scores['ワイド的中率']:.1f}%")
        
        # 推奨戦略
        print("\n" + "=" * 80)
        print("💡 推奨戦略")
        print("=" * 80)
        
        best_tansho = max(engine_scores.items(), key=lambda x: x[1]['単勝的中率'])
        best_recovery = max(engine_scores.items(), key=lambda x: x[1]['単勝回収率'])
        best_fukusho = max(engine_scores.items(), key=lambda x: x[1]['複勝的中率'])
        
        print(f"\n1. 単勝狙い → {best_tansho[0].upper()} (的中率 {best_tansho[1]['単勝的中率']:.1f}%)")
        print(f"2. 回収率重視 → {best_recovery[0].upper()} (回収率 {best_recovery[1]['単勝回収率']:.1f}%)")
        print(f"3. 安定重視 → {best_fukusho[0].upper()} (複勝的中率 {best_fukusho[1]['複勝的中率']:.1f}%)")
        
        # レポート保存
        report = {
            'analysis_date': datetime.now().isoformat(),
            'total_races': len(self.payout_dict),
            'engine_scores': engine_scores,
            'recommendations': {
                'best_accuracy': best_tansho[0],
                'best_recovery': best_recovery[0],
                'best_stability': best_fukusho[0]
            }
        }
        
        with open('/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/prediction_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("\n✅ 分析レポートを保存しました: prediction_analysis_report.json")

def main():
    """メイン処理"""
    analyzer = PredictionAnalyzer()
    
    # データ読み込み
    analyzer.load_data()
    
    # 各種分析実行
    analyzer.calculate_tansho_accuracy()
    analyzer.calculate_fukusho_accuracy()
    analyzer.calculate_umaren_wide_accuracy()
    analyzer.analyze_by_conditions()
    analyzer.calculate_combined_analysis()
    
    # レポート生成
    analyzer.generate_report()
    
    print("\n" + "=" * 80)
    print("✨ 分析完了")
    print("=" * 80)

if __name__ == '__main__':
    main()