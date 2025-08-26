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
        self.imlogic_engine = IMLogicEngine()
        self.dlogic_manager = DLogicRawDataManager()
        self.anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")) if Anthropic else None
        
        # AI選択キーワード
        self.AI_KEYWORDS = {
            'imlogic': ['分析', '評価', 'IMLogic', 'IM', 'アイエム'],
            'viewlogic_trend': ['傾向', 'トレンド', '統計', 'データ', '過去'],
            'viewlogic_opinion': ['見解', '意見', '予想', '推奨', 'おすすめ']
        }
        
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
    ) -> str:
        """
        IMLogicメッセージ処理
        """
        try:
            # レースコンテキストを設定
            race_context = self.create_race_context_prompt(race_data)
            
            # IMLogicの設定を適用
            if settings:
                # ユーザーのIMLogic設定を反映
                imlogic_prompt = self._create_imlogic_prompt(settings)
            else:
                # デフォルトのIMLogic設定
                imlogic_prompt = """
IMLogicは、イクイノックスを基準とした独自の評価システムです。
以下の要素を重視して分析します：
- 血統的な素質（30%）
- 近走のパフォーマンス（25%）
- コース適性（20%）
- 騎手との相性（15%）
- 調教師の手腕（10%）
"""
            
            # 全体のプロンプトを構築
            full_prompt = f"{race_context}\n\n{imlogic_prompt}\n\nユーザーの質問: {message}"
            
            # Claude APIを呼び出し
            if self.anthropic_client:
                response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
                )
                
                return response.content[0].text
            else:
                return f"IMLogic分析機能は現在利用できません（Anthropic APIが設定されていません）"
            
        except Exception as e:
            logger.error(f"IMLogic処理エラー: {e}")
            return f"申し訳ございません。IMLogic分析中にエラーが発生しました。"
    
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
        if determined_ai == 'imlogic':
            content = await self.process_imlogic_message(message, race_data, settings)
        else:  # viewlogic
            content = await self.process_viewlogic_message(message, race_data, sub_type)
        
        return {
            'content': content,
            'ai_type': determined_ai,
            'sub_type': sub_type,
            'analysis_data': None  # 必要に応じて分析データを追加
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