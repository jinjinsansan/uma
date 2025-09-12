"""
F-Logicバッチ処理システム
複数レースを一括で分析し、投資価値の高い馬を抽出
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from services.flogic_engine import flogic_engine
from services.odds_manager import odds_manager

logger = logging.getLogger(__name__)

class FLogicBatchProcessor:
    """F-Logicバッチ処理クラス"""
    
    def __init__(self):
        """初期化"""
        self.flogic = flogic_engine
        self.odds_mgr = odds_manager
        self.executor = ThreadPoolExecutor(max_workers=4)
        logger.info("F-Logicバッチプロセッサーを初期化しました")
    
    def process_single_race(
        self,
        race_data: Dict[str, Any],
        use_real_odds: bool = True
    ) -> Dict[str, Any]:
        """
        単一レースの処理（同期版）
        
        Args:
            race_data: レースデータ
            use_real_odds: リアルオッズを使用するか
        
        Returns:
            分析結果
        """
        try:
            venue = race_data.get('venue')
            race_number = race_data.get('race_number')
            horses = race_data.get('horses', [])
            
            # オッズ取得
            market_odds = None
            if use_real_odds:
                market_odds = self.odds_mgr.get_real_time_odds(
                    venue=venue,
                    race_number=race_number,
                    horses=horses
                )
            
            # F-Logic分析
            result = self.flogic.analyze_race(race_data, market_odds)
            
            # 投資価値の高い馬を抽出
            if result.get('status') == 'success':
                valuable_horses = []
                for ranking in result.get('rankings', []):
                    if 'investment_signal' in ranking:
                        if '買い' in ranking['investment_signal']:
                            valuable_horses.append({
                                'horse': ranking['horse'],
                                'fair_odds': ranking['fair_odds'],
                                'market_odds': ranking.get('market_odds'),
                                'odds_divergence': ranking.get('odds_divergence'),
                                'investment_signal': ranking['investment_signal'],
                                'expected_value': ranking.get('expected_value'),
                                'roi_estimate': ranking.get('roi_estimate')
                            })
                
                result['valuable_horses'] = valuable_horses
                result['valuable_count'] = len(valuable_horses)
            
            return result
            
        except Exception as e:
            logger.error(f"レース処理エラー: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'race_info': race_data
            }
    
    async def process_multiple_races(
        self,
        races_data: List[Dict[str, Any]],
        use_real_odds: bool = True
    ) -> Dict[str, Any]:
        """
        複数レースの非同期バッチ処理
        
        Args:
            races_data: レースデータのリスト
            use_real_odds: リアルオッズを使用するか
        
        Returns:
            バッチ処理結果
        """
        try:
            start_time = datetime.now()
            
            # 非同期処理のループを取得
            loop = asyncio.get_event_loop()
            
            # 各レースを並列処理
            tasks = []
            for race_data in races_data:
                task = loop.run_in_executor(
                    self.executor,
                    self.process_single_race,
                    race_data,
                    use_real_odds
                )
                tasks.append(task)
            
            # 全レースの処理完了を待つ
            results = await asyncio.gather(*tasks)
            
            # 結果を集計
            total_races = len(races_data)
            success_races = sum(1 for r in results if r.get('status') == 'success')
            error_races = sum(1 for r in results if r.get('status') == 'error')
            
            # 全レースの投資価値馬を集計
            all_valuable_horses = []
            for i, result in enumerate(results):
                if result.get('status') == 'success':
                    race_info = races_data[i]
                    for horse in result.get('valuable_horses', []):
                        horse['venue'] = race_info.get('venue')
                        horse['race_number'] = race_info.get('race_number')
                        horse['race_name'] = race_info.get('race_name', '')
                        all_valuable_horses.append(horse)
            
            # 期待値でソート（高い順）
            all_valuable_horses.sort(
                key=lambda x: x.get('expected_value', 0),
                reverse=True
            )
            
            # 処理時間計算
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'success',
                'summary': {
                    'total_races': total_races,
                    'success_races': success_races,
                    'error_races': error_races,
                    'total_valuable_horses': len(all_valuable_horses),
                    'processing_time': round(processing_time, 2)
                },
                'valuable_horses': all_valuable_horses,
                'race_results': results,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"バッチ処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def find_best_investments(
        self,
        batch_result: Dict[str, Any],
        top_n: int = 5,
        min_expected_value: float = 0.2
    ) -> List[Dict[str, Any]]:
        """
        バッチ処理結果から最良の投資機会を抽出
        
        Args:
            batch_result: バッチ処理結果
            top_n: 上位何頭を返すか
            min_expected_value: 最低期待値閾値
        
        Returns:
            投資推奨馬のリスト
        """
        if batch_result.get('status') != 'success':
            return []
        
        valuable_horses = batch_result.get('valuable_horses', [])
        
        # 期待値でフィルタリング
        filtered = [
            h for h in valuable_horses
            if h.get('expected_value', 0) >= min_expected_value
        ]
        
        # 上位N頭を返す
        return filtered[:top_n]
    
    def generate_investment_report(
        self,
        batch_result: Dict[str, Any]
    ) -> str:
        """
        投資レポートを生成
        
        Args:
            batch_result: バッチ処理結果
        
        Returns:
            レポート文字列
        """
        if batch_result.get('status') != 'success':
            return "分析エラーが発生しました"
        
        summary = batch_result.get('summary', {})
        valuable_horses = batch_result.get('valuable_horses', [])
        
        report = []
        report.append("=" * 80)
        report.append("F-Logic 投資価値レポート")
        report.append("=" * 80)
        report.append("")
        
        # サマリー
        report.append("【分析サマリー】")
        report.append(f"分析レース数: {summary.get('total_races')}レース")
        report.append(f"成功: {summary.get('success_races')}レース")
        report.append(f"投資価値のある馬: {summary.get('total_valuable_horses')}頭")
        report.append(f"処理時間: {summary.get('processing_time')}秒")
        report.append("")
        
        # トップ5投資機会
        report.append("【TOP5 投資推奨馬】")
        report.append("-" * 40)
        
        top_horses = self.find_best_investments(batch_result, top_n=5)
        
        for i, horse in enumerate(top_horses, 1):
            report.append(f"\n{i}位: {horse['horse']}")
            report.append(f"  開催: {horse['venue']} {horse['race_number']}R {horse.get('race_name', '')}")
            report.append(f"  フェア値: {horse['fair_odds']}倍")
            report.append(f"  市場オッズ: {horse.get('market_odds', 'N/A')}倍")
            report.append(f"  オッズ乖離率: {horse.get('odds_divergence', 'N/A')}")
            report.append(f"  期待値: {horse.get('expected_value', 0)}")
            report.append(f"  推定ROI: {horse.get('roi_estimate', 0)}%")
            report.append(f"  投資判断: {horse['investment_signal']}")
        
        # カテゴリ別集計
        report.append("\n【投資シグナル別集計】")
        report.append("-" * 40)
        
        signal_counts = {}
        for horse in valuable_horses:
            signal = horse.get('investment_signal', '不明')
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        for signal, count in sorted(signal_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"{signal}: {count}頭")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def __del__(self):
        """デストラクタ"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

# グローバルインスタンス
flogic_batch_processor = FLogicBatchProcessor()