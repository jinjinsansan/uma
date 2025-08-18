"""
レース分析統合エンジン
馬と騎手の総合評価を行う
"""
import logging
from typing import Dict, Any, List, Optional
from .modern_dlogic_engine import ModernDLogicEngine
from .jockey_data_manager import jockey_manager
from .jockey_name_mapper import normalize_jockey_name

logger = logging.getLogger(__name__)

class RaceAnalysisEngine:
    """レース全体を総合的に分析するエンジン"""
    
    # 馬と騎手の重み付け
    HORSE_WEIGHT = 0.7    # 70%
    JOCKEY_WEIGHT = 0.3   # 30%
    
    def __init__(self, fast_engine_instance=None):
        """初期化
        
        Args:
            fast_engine_instance: 既存のFastDLogicEngineインスタンス（オプション）
        """
        # fast_engine_instanceが渡されない場合は、ここで新規作成
        if fast_engine_instance is None:
            from .fast_dlogic_engine import FastDLogicEngine
            fast_engine_instance = FastDLogicEngine()
            logger.info("新しいFastDLogicEngineインスタンスを作成しました")
        else:
            logger.info("既存のFastDLogicEngineインスタンスを使用します")
            
        # モダンD-Logicエンジン（イクイノックス基準）
        self.modern_engine = ModernDLogicEngine(fast_engine_instance)
        # 騎手データマネージャー
        self.jockey_manager = jockey_manager
        
        logger.info("レース分析エンジンを初期化しました")
    
    def analyze_race(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レース全体を分析
        
        Args:
            race_data: {
                'venue': '札幌',
                'race_number': 11,
                'race_name': '札幌記念',
                'grade': 'G3',
                'distance': '2000m',
                'track_condition': '良',
                'horses': ['ドウデュース', ...],
                'jockeys': ['武豊', ...],
                'posts': [1, 2, ...],
                'horse_numbers': [1, 2, ...]
            }
        
        Returns:
            {
                'race_info': レース情報,
                'results': 分析結果（順位付き）,
                'analysis_type': 'race_analysis_v2',
                'base_horse': 'イクイノックス'
            }
        """
        try:
            # 入力検証
            if not self._validate_race_data(race_data):
                return {
                    'error': 'レースデータが不正です',
                    'analysis_type': 'race_analysis_v2'
                }
            
            # レース情報の準備
            context = {
                'venue': race_data.get('venue', ''),
                'grade': race_data.get('grade', ''),
                'distance': race_data.get('distance', ''),
                'track_condition': race_data.get('track_condition', '良')
            }
            
            # 各馬の分析
            results = []
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            posts = race_data.get('posts', [])
            horse_numbers = race_data.get('horse_numbers', [])
            
            for i in range(len(horses)):
                try:
                    horse_name = horses[i]
                    raw_jockey_name = jockeys[i] if i < len(jockeys) else ''
                    jockey_name = normalize_jockey_name(raw_jockey_name)
                    post = posts[i] if i < len(posts) else 1
                    horse_number = horse_numbers[i] if i < len(horse_numbers) else i + 1
                    
                    # 馬の評価（ベイズ推定を有効化）
                    horse_analysis = self.modern_engine.calculate_horse_score(
                        horse_name, 
                        context,
                        enable_bayesian=True
                    )
                    
                    # 騎手の評価
                    jockey_context = {
                        'venue': context['venue'],
                        'post': post,
                        'sire': self._get_horse_sire(horse_name)  # 父馬情報
                    }
                    jockey_analysis = self.jockey_manager.calculate_jockey_score(
                        jockey_name,
                        jockey_context
                    )
                    
                    # 総合評価
                    horse_score = horse_analysis.get('final_score', 50.0)
                    jockey_score = jockey_analysis.get('total_score', 0)
                    
                    total_score = (
                        horse_score * self.HORSE_WEIGHT +
                        jockey_score * self.JOCKEY_WEIGHT
                    )
                    
                    results.append({
                        'rank': 0,  # 後でソート
                        'horse_number': horse_number,
                        'post': post,
                        'horse': horse_name,
                        'jockey': jockey_name,
                        'total_score': round(total_score, 1),
                        'horse_score': round(horse_score, 1),
                        'jockey_score': round(jockey_score, 1),
                        'horse_details': {
                            'base': round(horse_analysis.get('base_score', 50.0), 1),
                            'venue_distance_bonus': horse_analysis.get('venue_distance_bonus', 0),
                            'class_factor': horse_analysis.get('class_factor', 1.0),
                            'track_bonus': horse_analysis.get('track_bonus', 0),
                            'venue_history': horse_analysis.get('details', {}).get('venue_history', {})
                        },
                        'jockey_details': {
                            'venue': jockey_analysis.get('venue_score', 0),
                            'post': jockey_analysis.get('post_score', 0),
                            'sire': jockey_analysis.get('sire_score', 0)
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"馬の分析エラー（{horses[i]}）: {e}")
                    # エラーでも結果に含める
                    results.append({
                        'rank': 999,
                        'horse_number': horse_numbers[i] if i < len(horse_numbers) else i + 1,
                        'post': posts[i] if i < len(posts) else 1,
                        'horse': horses[i],
                        'jockey': jockeys[i] if i < len(jockeys) else '',
                        'total_score': 0,
                        'horse_score': 0,
                        'jockey_score': 0,
                        'error': str(e)
                    })
            
            # スコア順にソート
            results.sort(key=lambda x: x['total_score'], reverse=True)
            
            # 順位付け
            for i, result in enumerate(results):
                result['rank'] = i + 1
            
            # 分析サマリーの作成
            summary = self._create_analysis_summary(results, context)
            
            return {
                'race_info': {
                    'venue': race_data.get('venue', ''),
                    'race_number': race_data.get('race_number', ''),
                    'race_name': race_data.get('race_name', ''),
                    'grade': race_data.get('grade', ''),
                    'distance': race_data.get('distance', ''),
                    'track_condition': race_data.get('track_condition', '良')
                },
                'results': results,
                'summary': summary,
                'analysis_type': 'race_analysis_v2',
                'base_horse': 'イクイノックス',
                'weights': {
                    'horse': self.HORSE_WEIGHT,
                    'jockey': self.JOCKEY_WEIGHT
                }
            }
            
        except Exception as e:
            logger.error(f"レース分析エラー: {e}")
            return {
                'error': f'分析中にエラーが発生しました: {str(e)}',
                'analysis_type': 'race_analysis_v2'
            }
    
    def _validate_race_data(self, race_data: Dict[str, Any]) -> bool:
        """レースデータの検証"""
        required_fields = ['horses']
        for field in required_fields:
            if field not in race_data or not race_data[field]:
                logger.warning(f"必須フィールドが不足: {field}")
                return False
        
        # 馬と騎手の数が一致しているか
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        if jockeys and len(horses) != len(jockeys):
            logger.warning(f"馬と騎手の数が不一致: 馬{len(horses)}頭、騎手{len(jockeys)}人")
            return False
        
        return True
    
    def _get_horse_sire(self, horse_name: str) -> str:
        """馬の父馬を取得"""
        try:
            # ナレッジファイルから父馬情報を取得
            horse_data = self.modern_engine.knowledge.get(horse_name, {})
            # 父馬情報は将来的に追加予定
            # 現在はデフォルト値を返す
            return horse_data.get('sire', '')
        except Exception:
            return ''
    
    def _create_analysis_summary(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """分析結果のサマリーを作成"""
        if not results:
            return {}
        
        top3 = results[:3]
        
        summary = {
            'top_horse': {
                'name': top3[0]['horse'],
                'jockey': top3[0]['jockey'],
                'score': top3[0]['total_score'],
                'advantage': []
            },
            'key_points': [],
            'venue_specialists': [],
            'cautions': []
        }
        
        # トップ馬の優位性
        if top3[0]['horse_details'].get('venue_distance_bonus', 0) >= 5:
            summary['top_horse']['advantage'].append(f"{context['venue']}巧者")
        
        if top3[0]['jockey_details']['venue'] >= 5:
            summary['top_horse']['advantage'].append(f"騎手も{context['venue']}で好成績")
        
        # 開催場スペシャリスト
        for result in results:
            if result['horse_details'].get('venue_distance_bonus', 0) >= 7:
                venue_history = result['horse_details']['venue_history']
                summary['venue_specialists'].append({
                    'horse': result['horse'],
                    'record': f"{venue_history.get('wins', 0)}勝/{venue_history.get('total', 0)}戦"
                })
        
        # 注意点
        if context['track_condition'] != '良':
            summary['key_points'].append(f"{context['track_condition']}馬場での適性を重視")
        
        return summary

# グローバルインスタンス（遅延初期化）
_race_analysis_engine = None

def get_race_analysis_engine(fast_engine_instance=None):
    """レース分析エンジンのシングルトンインスタンスを取得
    
    Args:
        fast_engine_instance: 既存のFastDLogicEngineインスタンス（オプション）
                            chat.pyから渡される共有インスタンス
    """
    global _race_analysis_engine
    if _race_analysis_engine is None:
        _race_analysis_engine = RaceAnalysisEngine(fast_engine_instance)
    return _race_analysis_engine