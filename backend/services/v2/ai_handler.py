"""
V2 AI統合ハンドラー
レース限定分析とAI自然言語切り替えを実装
"""
import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from services.imlogic_engine import IMLogicEngine
from services.dlogic_raw_data_manager import DLogicRawDataManager
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
import os

logger = logging.getLogger(__name__)

class V2AIHandler:
    """V2システム用のAIハンドラー"""
    
    def __init__(self):
        # IMLogicEngineを遅延初期化にする（使用時に初期化）
        self._imlogic_engine = None
        # DLogicRawDataManagerは削除（IMLogicEngine内で既に初期化される）
        # self.dlogic_manager = DLogicRawDataManager()  # メモリ重複を避ける
        self.anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")) if Anthropic else None
        
        # AI選択キーワード
        self.AI_KEYWORDS = {
            'imlogic': ['分析', '評価', 'IMLogic', 'IM', 'アイエム'],
            'viewlogic_trend': ['傾向', 'トレンド', '統計', 'データ', '過去'],
            'viewlogic_opinion': ['見解', '意見', '予想', '推奨', 'おすすめ']
        }
    
    @property
    def imlogic_engine(self):
        """IMLogicEngineの遅延初期化"""
        if self._imlogic_engine is None:
            logger.info("IMLogicEngineを初期化します...")
            self._imlogic_engine = IMLogicEngine()
            logger.info("IMLogicEngineの初期化完了")
        return self._imlogic_engine
        
    def determine_ai_type(self, message: str) -> Tuple[str, str]:
        """
        メッセージからAIタイプを判定
        
        Returns:
            (ai_type, sub_type) のタプル
            - ai_type: 'imlogic' または 'viewlogic'
            - sub_type: 'analysis', 'trend', 'opinion' など
        """
        message_lower = message.lower()
        
        # ViewLogic傾向分析
        for keyword in self.AI_KEYWORDS['viewlogic_trend']:
            if keyword in message_lower:
                return ('viewlogic', 'trend')
        
        # ViewLogic見解
        for keyword in self.AI_KEYWORDS['viewlogic_opinion']:
            if keyword in message_lower:
                return ('viewlogic', 'opinion')
        
        # デフォルトはIMLogic分析
        return ('imlogic', 'analysis')
    
    def create_race_context_prompt(self, race_data: Dict[str, Any]) -> str:
        """
        レース限定のコンテキストプロンプトを生成
        """
        horses_list = race_data.get('horses', [])
        horses_str = '、'.join(horses_list) if horses_list else '情報なし'
        
        prompt = f"""
あなたは競馬予想の専門AIです。以下のレースについてのみ分析・回答してください。

【対象レース情報】
- 開催日: {race_data.get('race_date', '不明')}
- 開催場: {race_data.get('venue', '不明')}
- レース番号: {race_data.get('race_number', '不明')}R
- レース名: {race_data.get('race_name', '不明')}
- 距離: {race_data.get('distance', '不明')}
- 馬場状態: {race_data.get('track_condition', '不明')}
- 出走馬: {horses_str}

【重要な制約】
1. 上記レース以外の情報や分析は一切行わないでください
2. 他のレースについて聞かれても「このチャットは{race_data.get('venue')} {race_data.get('race_number')}R専用です」と回答
3. 出走馬リストにない馬については分析できません
4. レース当日の最新情報（オッズ、馬体重等）は持っていません
"""
        return prompt
    
    async def process_imlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[Dict]]:
        """
        IMLogicメッセージ処理（既存のIMLogicEngineを使用）
        """
        try:
            # 分析を実行する場合
            if self._should_analyze(message):
                # デフォルトの設定を使用（設定が無い場合）
                if not settings:
                    settings = self._get_default_imlogic_settings()
                
                # IMLogicEngineで分析
                # フロントエンドからのデータ構造に対応
                horse_weight = settings.get('horse_weight') or settings.get('horse_ratio', 70)
                jockey_weight = settings.get('jockey_weight') or settings.get('jockey_ratio', 30)
                raw_weights = settings.get('item_weights') or settings.get('weights', {})
                
                # フロントエンドのキー形式が番号付きか番号なしかを判定
                if '1_distance_aptitude' in raw_weights:
                    # すでに番号付き形式
                    item_weights = raw_weights
                elif 'distance_aptitude' in raw_weights:
                    # 番号なし形式から番号付き形式に変換
                    item_weights = {
                        '1_distance_aptitude': raw_weights.get('distance_aptitude', 8.33),
                        '2_bloodline_evaluation': raw_weights.get('bloodline_evaluation', 8.33),
                        '3_jockey_compatibility': raw_weights.get('jockey_compatibility', 8.33),
                        '4_trainer_evaluation': raw_weights.get('trainer_evaluation', 8.33),
                        '5_track_aptitude': raw_weights.get('track_aptitude', 8.33),
                        '6_weather_aptitude': raw_weights.get('weather_aptitude', 8.33),
                        '7_popularity_factor': raw_weights.get('popularity_factor', 8.33),
                        '8_weight_impact': raw_weights.get('weight_impact', 8.33),
                        '9_horse_weight_impact': raw_weights.get('horse_weight_impact', 8.33),
                        '10_corner_specialist': raw_weights.get('corner_specialist', 8.33),
                        '11_margin_analysis': raw_weights.get('margin_analysis', 8.33),
                        '12_time_index': raw_weights.get('time_index', 8.37)
                    }
                else:
                    # デフォルト値を使用
                    item_weights = {
                        '1_distance_aptitude': 8.33,
                        '2_bloodline_evaluation': 8.33,
                        '3_jockey_compatibility': 8.33,
                        '4_trainer_evaluation': 8.33,
                        '5_track_aptitude': 8.33,
                        '6_weather_aptitude': 8.33,
                        '7_popularity_factor': 8.33,
                        '8_weight_impact': 8.33,
                        '9_horse_weight_impact': 8.33,
                        '10_corner_specialist': 8.33,
                        '11_margin_analysis': 8.33,
                        '12_time_index': 8.37
                    }
                
                analysis_result = self.imlogic_engine.analyze_race(
                    race_data=race_data,
                    horse_weight=horse_weight,
                    jockey_weight=jockey_weight,
                    item_weights=item_weights
                )
                
                # 結果が空の場合のチェック（'scores'と'results'の両方をチェック）
                if not analysis_result or (not analysis_result.get('scores') and not analysis_result.get('results')):
                    logger.error(f"IMLogic分析結果が空: {analysis_result}")
                    return ("分析に失敗しました。馬名が正しいか確認してください。", None)
                
                # 結果のフォーマット
                formatted_content = self._format_imlogic_result(analysis_result, race_data)
                return (formatted_content, analysis_result)
            
            # 通常の会話の場合
            else:
                # レースコンテキストを設定
                race_context = self.create_race_context_prompt(race_data)
                
                # IMLogicの設定説明
                if settings:
                    imlogic_prompt = self._create_imlogic_prompt(settings)
                else:
                    imlogic_prompt = """
IMLogicは、ユーザーがカスタマイズ可能な分析システムです。
馬と騎手の比率、12項目の重み付けを自由に設定できます。
"""
                
                # Claude APIを呼び出し（会話用）
                if self.anthropic_client:
                    full_prompt = f"{race_context}\n\n{imlogic_prompt}\n\nユーザーの質問: {message}"
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=2000,
                        temperature=0.7,
                        messages=[
                            {"role": "user", "content": full_prompt}
                        ]
                    )
                    return (response.content[0].text, None)
                else:
                    return ("会話機能は現在利用できません", None)
            
        except Exception as e:
            logger.error(f"IMLogic処理エラー: {e}")
            return (f"申し訳ございません。IMLogic分析中にエラーが発生しました: {str(e)}", None)
    
    def _should_analyze(self, message: str) -> bool:
        """メッセージが分析要求かどうかを判定"""
        analyze_keywords = ['分析', '評価', '順位', '上位', '予想', 'ランキング', 'スコア']
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in analyze_keywords)
    
    def _get_default_imlogic_settings(self) -> Dict[str, Any]:
        """デフォルトのIMLogic設定を返す"""
        return {
            'horse_ratio': 70,
            'jockey_ratio': 30,
            'weights': self._get_default_weights()
        }
    
    def _get_default_weights(self) -> Dict[str, float]:
        """デフォルトの12項目重み付けを返す"""
        return {
            'distance_aptitude': 10,
            'track_aptitude': 8,
            'growth_potential': 7,
            'trainer_skill': 6,
            'breakthrough_potential': 8,
            'strength_score': 10,
            'winning_percentage': 9,
            'recent_performance': 10,
            'course_experience': 8,
            'distance_experience': 8,
            'stability': 8,
            'jockey_compatibility': 8
        }
    
    def _format_imlogic_result(self, analysis_result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """IMLogic分析結果をフォーマット"""
        try:
            # 'scores'と'results'の両方に対応
            scores = analysis_result.get('scores') or analysis_result.get('results', [])
            if not scores:
                return "分析結果が取得できませんでした。"
            
            # スコア順にソート（Noneの場合は-1として扱う）
            scores.sort(key=lambda x: x.get('total_score') if x.get('total_score') is not None else -1, reverse=True)
            
            # 結果のフォーマット
            lines = []
            lines.append(f"🎯 IMLogic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R")
            lines.append("")
            
            # 上位5頭を表示（スコアがある馬のみ）
            emojis = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
            valid_scores = [s for s in scores if s.get('total_score') is not None]
            
            for i, score_data in enumerate(valid_scores[:5]):
                emoji = emojis[i] if i < 5 else f"{i+1}."
                # 'horse_name'と'horse'の両方に対応
                horse_name = score_data.get('horse_name') or score_data.get('horse', '不明')
                total_score = score_data.get('total_score', 0)
                horse_score = score_data.get('horse_score', 0)
                jockey_score = score_data.get('jockey_score', 0)
                
                lines.append(f"{emoji} {horse_name}: {total_score:.1f}点")
                lines.append(f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点")
            
            # 6位以下も簡潔に表示（スコアがある馬のみ）
            if len(valid_scores) > 5:
                lines.append("")
                lines.append("【6位以下】")
                for score_data in valid_scores[5:]:
                    # 'horse_name'と'horse'の両方に対応
                    horse_name = score_data.get('horse_name') or score_data.get('horse', '不明')
                    total_score = score_data.get('total_score', 0)
                    lines.append(f"{horse_name}: {total_score:.1f}点")
            
            # データがない馬がいる場合の注記
            no_data_horses = [s.get('horse_name') or s.get('horse', '不明') 
                            for s in scores if s.get('total_score') is None]
            if no_data_horses:
                lines.append("")
                lines.append("【データ不足】")
                lines.append(f"以下の馬はデータ不足のため分析できませんでした: {', '.join(no_data_horses)}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"結果フォーマットエラー: {e}")
            return "分析結果の表示中にエラーが発生しました。"
    
    async def process_viewlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any],
        sub_type: str = 'trend'
    ) -> str:
        """
        ViewLogicメッセージ処理（将来実装用）
        """
        # 現在はプレースホルダー
        venue = race_data.get('venue', '不明')
        race_number = race_data.get('race_number', '不明')
        
        if sub_type == 'trend':
            return f"""
ViewLogic傾向分析（開発中）
{venue} {race_number}Rの傾向分析機能は現在開発中です。
近日中に以下の分析が可能になります：
- 過去の類似レースデータ分析
- 開催場別の傾向
- 騎手・調教師の成績傾向
"""
        elif sub_type == 'opinion':
            return f"""
ViewLogic見解（開発中）
{venue} {race_number}Rの見解機能は現在開発中です。
近日中に以下の情報が提供されます：
- AIによる推奨馬
- 穴馬の可能性
- 馬券の組み立て提案
"""
        else:
            return "ViewLogic機能は現在開発中です。"
    
    def _create_imlogic_prompt(self, settings: Dict[str, Any]) -> str:
        """
        IMLogic設定からプロンプトを生成
        """
        weights = settings.get('weights', {})
        horse_ratio = settings.get('horse_ratio', 70)
        jockey_ratio = settings.get('jockey_ratio', 30)
        
        prompt_parts = [
            f"IMLogicカスタム設定による分析",
            f"馬の能力: {horse_ratio}%、騎手の能力: {jockey_ratio}%の比率で評価",
            "",
            "重視する項目（優先順位）:"
        ]
        
        # 重み付けをソートして優先順位を決定
        sorted_weights = sorted(
            weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for i, (item, weight) in enumerate(sorted_weights, 1):
            if weight > 0:
                item_name = self._get_item_display_name(item)
                prompt_parts.append(f"{i}. {item_name} (重要度: {weight})")
        
        return "\n".join(prompt_parts)
    
    def _get_item_display_name(self, item_key: str) -> str:
        """
        項目キーから表示名を取得
        """
        display_names = {
            'distance_aptitude': '距離適性',
            'track_aptitude': 'コース適性',
            'growth_potential': '成長力',
            'trainer_skill': '調教師',
            'breakthrough_potential': '爆発力',
            'strength_score': '強さ',
            'winning_percentage': '勝率',
            'recent_performance': '近走',
            'course_experience': 'コース経験',
            'distance_experience': '距離実績',
            'stability': '安定感',
            'jockey_compatibility': '騎手相性'
        }
        return display_names.get(item_key, item_key)
    
    async def process_message(
        self,
        message: str,
        race_data: Dict[str, Any],
        ai_type: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        統合メッセージ処理
        
        Returns:
            {
                'content': str,  # 応答内容
                'ai_type': str,  # 使用したAI
                'sub_type': str,  # サブタイプ
                'analysis_data': dict  # 分析データ（あれば）
            }
        """
        # AI タイプの決定
        if ai_type:
            determined_ai = ai_type
            sub_type = 'manual'
        else:
            determined_ai, sub_type = self.determine_ai_type(message)
        
        # レース外の質問をチェック
        if self._is_out_of_scope(message, race_data):
            venue = race_data.get('venue', '')
            race_number = race_data.get('race_number', '')
            return {
                'content': f"このチャットは{venue} {race_number}R専用です。他のレースについては新しいチャットを作成してください。",
                'ai_type': determined_ai,
                'sub_type': 'out_of_scope',
                'analysis_data': None
            }
        
        # AI種別に応じて処理
        analysis_data = None
        if determined_ai == 'imlogic':
            result = await self.process_imlogic_message(message, race_data, settings)
            # タプルまたは辞書の場合は分解
            if isinstance(result, tuple):
                content, analysis_data = result
            elif isinstance(result, dict):
                content = result.get('content', '')
                analysis_data = result.get('analysis_data')
            else:
                content = result
        else:  # viewlogic
            content = await self.process_viewlogic_message(message, race_data, sub_type)
        
        return {
            'content': content,
            'ai_type': determined_ai,
            'sub_type': sub_type,
            'analysis_data': analysis_data
        }
    
    def _is_out_of_scope(self, message: str, race_data: Dict[str, Any]) -> bool:
        """
        メッセージがレース範囲外かチェック
        """
        # 他のレース番号への言及をチェック
        other_race_pattern = r'\d+R(?![\d])'  # 数字+R（後に数字が続かない）
        matches = re.findall(other_race_pattern, message)
        
        current_race_num = str(race_data.get('race_number', ''))
        for match in matches:
            race_num = match[:-1]  # 'R'を除去
            if race_num != current_race_num:
                return True
        
        # 他の開催場への言及をチェック
        venues = ['東京', '中山', '阪神', '京都', '中京', '小倉', '新潟', '福島', '札幌', '函館']
        current_venue = race_data.get('venue', '')
        
        for venue in venues:
            if venue in message and venue != current_venue:
                # 明確に他の開催場のレースについて聞いている場合
                if re.search(f'{venue}\\d+R', message):
                    return True
        
        return False