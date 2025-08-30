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
try:
    import httpx
except ImportError:
    httpx = None
import os

logger = logging.getLogger(__name__)

class V2AIHandler:
    """V2システム用のAIハンドラー"""
    
    def __init__(self):
        # IMLogicEngineは毎回新規作成するため、ここでは初期化しない
        # /logic-chatと同じ動作を保証
        # DLogicRawDataManagerは削除（IMLogicEngine内で既に初期化される）
        # self.dlogic_manager = DLogicRawDataManager()  # メモリ重複を避ける
        self.anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")) if Anthropic else None
        
        # AI選択キーワード
        self.AI_KEYWORDS = {
            'imlogic': ['分析', '評価', 'IMLogic', 'IM', 'アイエム'],
            'viewlogic_trend': ['傾向', 'トレンド', '統計', 'データ', '過去', 'コース傾向', '騎手成績', '血統', '枠順'],
            'viewlogic_opinion': ['見解', '意見', '予想', '推奨', 'おすすめ'],
            'viewlogic_flow': ['展開', 'ペース', '逃げ', '先行', '差し', '追込', '脚質', 'ハイペース', 'スローペース', '流れ'],
            'dlogic': ['d-logic', 'ディーロジック', 'D-Logic', 'Dロジック', '指数', 'スコア', '12項目', '評価点'],
            'ilogic': ['i-logic', 'ilogic', 'アイロジック', 'I-Logic', 'Iロジック', '騎手', '総合', 'レースアナリシス', 'アナリシス']
        }
    
        
    def determine_ai_type(self, message: str) -> Tuple[str, str]:
        """
        メッセージからAIタイプを判定
        
        Returns:
            (ai_type, sub_type) のタプル
            - ai_type: 'imlogic', 'viewlogic', 'dlogic', 'ilogic'
            - sub_type: 'analysis', 'trend', 'opinion' など
        """
        message_lower = message.lower()
        
        # D-Logic分析
        for keyword in self.AI_KEYWORDS['dlogic']:
            if keyword.lower() in message_lower:
                return ('dlogic', 'analysis')
        
        # ViewLogic展開予想（最優先）
        for keyword in self.AI_KEYWORDS['viewlogic_flow']:
            if keyword in message_lower:
                return ('viewlogic', 'flow')
        
        # ViewLogic傾向分析（I-Logicより優先）
        for keyword in self.AI_KEYWORDS['viewlogic_trend']:
            if keyword in message_lower:
                return ('viewlogic', 'trend')
        
        # I-Logic分析
        for keyword in self.AI_KEYWORDS['ilogic']:
            if keyword.lower() in message_lower:
                return ('ilogic', 'analysis')
        
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
                # 重要: /logic-chatと同じように毎回新しいエンジンを作成
                # メモリよりも正確性を優先
                from services.imlogic_engine import IMLogicEngine
                imlogic_engine_temp = IMLogicEngine()
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
                
                # 一時的なエンジンインスタンスで分析
                analysis_result = imlogic_engine_temp.analyze_race(
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
            emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
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
    ) -> Tuple[str, Optional[Dict]]:
        """
        ViewLogicメッセージ処理
        
        Returns:
            (content, analysis_data) のタプル
        """
        try:
            # ViewLogicエンジンをインポート・初期化
            from services.viewlogic_engine import ViewLogicEngine
            viewlogic_engine = ViewLogicEngine()
            
            venue = race_data.get('venue', '不明')
            race_number = race_data.get('race_number', '不明')
            
            if sub_type == 'flow':
                # 展開予想（高度な分析版を使用）
                result = viewlogic_engine.predict_race_flow_advanced(race_data)
                if result['status'] == 'success':
                    content = self._format_flow_prediction(result)
                    return (content, result)
                else:
                    return (f"展開予想に失敗しました: {result.get('message', '不明なエラー')}", None)
                    
            elif sub_type == 'trend':
                # コース傾向分析
                distance = race_data.get('distance')
                track_type = race_data.get('course_type', '芝')  # デフォルトは芝
                
                result = viewlogic_engine.analyze_course_trend(
                    venue=venue,
                    distance=distance,
                    track_type=track_type
                )
                
                if result['status'] == 'success':
                    content = self._format_trend_analysis(result)
                    return (content, result)
                else:
                    return (f"傾向分析に失敗しました: {result.get('message', '不明なエラー')}", None)
                    
            elif sub_type == 'opinion':
                # 見解（当日傾向として実装）
                import datetime
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                
                result = viewlogic_engine.analyze_daily_trend(
                    date=today,
                    venue=venue
                )
                
                if result['status'] == 'success':
                    content = self._format_daily_trend(result)
                    return (content, result)
                else:
                    # フォールバック: 基本的な見解を提供
                    return (f"""
🔮 ViewLogic見解
{venue} {race_number}R

本日の傾向データは限定的ですが、以下の点に注目してください：
• 脚質のバランスを確認
• 騎手の調子を重視
• 枠順の有利不利を考慮

詳細な分析には「展開予想」または「傾向分析」をご利用ください。
""", None)
            else:
                return ("ViewLogic機能をご利用いただきありがとうございます。「展開」「傾向」「見解」のいずれかをお試しください。", None)
                
        except ImportError as e:
            logger.error(f"ViewLogicエンジンのインポートエラー: {e}")
            return ("ViewLogicエンジンの読み込みに失敗しました。システム管理者にお問い合わせください。", None)
        except Exception as e:
            logger.error(f"ViewLogic処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return (f"ViewLogic分析中にエラーが発生しました: {str(e)}", None)
    
    def _format_flow_prediction(self, result: Dict[str, Any]) -> str:
        """展開予想結果をフォーマット（高度な分析版対応）"""
        lines = []
        lines.append("🏇 **ViewLogic展開予想**")
        
        # レース情報
        race_info = result.get('race_info', {})
        lines.append(f"{race_info.get('venue', '')} {race_info.get('race_number', '')}R - {race_info.get('race_name', '')}")
        if race_info.get('distance'):
            lines.append(f"距離: {race_info.get('distance', '')}")
        lines.append("")
        
        # 新形式（predict_race_flow_advanced）の場合
        if 'pace_prediction' in result:
            return self._format_flow_prediction_advanced(result)
        
        # 旧形式（predict_race_flow）のフォールバック
        prediction = result.get('prediction', {})
        lines.append(f"**【ペース予想】{prediction.get('pace', '不明')}**")
        lines.append(f"確信度: {prediction.get('pace_confidence', 0)}%")
        lines.append("")
        
        # 脚質分布
        lines.append("**【脚質分布】**")
        for style_data in prediction['style_distribution']:
            horses_str = ', '.join(style_data['horses']) if style_data['horses'] else ''
            lines.append(f"• {style_data['style']}: {style_data['count']}頭")
            if horses_str:
                lines.append(f"  {horses_str}")
        lines.append("")
        
        # 詳細な逃げ馬分析
        if prediction['detailed_escapes']:
            lines.append("**【逃げ馬詳細】**")
            for escape_type, horses in prediction['detailed_escapes'].items():
                if horses:
                    lines.append(f"• {escape_type}: {', '.join(horses)}")
            lines.append("")
        
        # 有利/不利
        if prediction['advantaged_horses']:
            lines.append("**🎯 有利な馬**")
            for horse in prediction['advantaged_horses']:
                lines.append(f"• {horse}")
            lines.append("")
        
        if prediction['disadvantaged_horses']:
            lines.append("**⚠️ 不利な馬**")
            for horse in prediction['disadvantaged_horses']:
                lines.append(f"• {horse}")
            lines.append("")
        
        lines.append(f"_分析馬数: {result.get('analyzed_horses', 0)}/{result.get('total_horses', 0)}頭_")
        
        return "\n".join(lines)
    
    def _format_flow_prediction_advanced(self, result: Dict[str, Any]) -> str:
        """高度な展開予想結果をフォーマット"""
        lines = []
        lines.append("🏇 **ViewLogic展開予想**")
        
        # レース情報
        race_info = result.get('race_info', {})
        lines.append(f"{race_info.get('venue', '')} {race_info.get('race_number', '')}R")
        if race_info.get('distance'):
            lines.append(f"距離: {race_info.get('distance', '')}")
        lines.append("")
        
        # ペース予想
        pace_pred = result.get('pace_prediction', {})
        pace = pace_pred.get('pace', '不明')
        confidence = pace_pred.get('confidence', 0)
        lines.append(f"**【ペース予想】{pace}**")
        lines.append(f"確信度: {confidence}%")
        lines.append("")
        
        # 詳細な脚質分類
        detailed_styles = result.get('detailed_styles', {})
        lines.append("**【展開予想】**")
        
        for main_style, sub_styles in detailed_styles.items():
            has_horses = any(horses for horses in sub_styles.values())
            if has_horses:
                lines.append(f"\n◆ {main_style}")
                for sub_style, horses in sub_styles.items():
                    if horses:
                        horses_str = ', '.join(horses[:3])  # 最初の3頭まで表示
                        if len(horses) > 3:
                            horses_str += f" 他{len(horses)-3}頭"
                        lines.append(f"  • {sub_style}: {horses_str}")
        lines.append("")
        
        # レースシミュレーション（ゴール予想のみ）
        simulation = result.get('race_simulation', {})
        if simulation and 'finish' in simulation:
            lines.append("**【上位予想】**")
            for i, entry in enumerate(simulation['finish'][:5], 1):
                horse = entry.get('horse_name', '不明')
                lines.append(f"{i}. {horse}")
            lines.append("")
        
        # ペースに応じた狙い目
        lines.append("**【狙い目】**")
        if 'ハイペース' in pace:
            lines.append("• 後方待機の差し・追込馬が有利")
            lines.append("• 前半飛ばす逃げ・先行馬は苦戦予想")
        elif 'スローペース' in pace:
            lines.append("• 前残りの可能性大")
            lines.append("• 逃げ・先行馬を重視")
            lines.append("• 追込一辺倒は厳しい展開")
        else:
            lines.append("• 平均ペースで力勝負")
            lines.append("• 総合力の高い馬を重視")
        
        return "\n".join(lines)
    
    def _format_trend_analysis(self, result: Dict[str, Any]) -> str:
        """コース傾向分析結果をフォーマット"""
        lines = []
        lines.append("📊 **ViewLogicコース傾向分析**")
        
        course = result['course_info']
        lines.append(f"{course['venue']} {course.get('distance', '')}m {course.get('track_type', '')}")
        lines.append("")
        
        trends = result['trends']
        
        # 騎手成績
        if trends.get('jockey_ranking'):
            lines.append("**【騎手成績TOP5】**")
            for i, jockey in enumerate(trends['jockey_ranking'], 1):
                lines.append(f"{i}. {jockey['name']}: 勝率{jockey['win_rate']:.0%} 複勝率{jockey['fukusho_rate']:.0%}")
            lines.append("")
        
        # 血統成績
        if trends.get('sire_ranking'):
            lines.append("**【血統成績TOP3】**")
            for i, sire in enumerate(trends['sire_ranking'], 1):
                lines.append(f"{i}. {sire['name']}: 複勝率{sire['fukusho_rate']:.0%}")
            lines.append("")
        
        # 枠順別成績
        if trends.get('post_position_stats'):
            lines.append("**【枠順別成績】**")
            for position, stats in trends['post_position_stats'].items():
                lines.append(f"• {position}: 勝率{stats['win_rate']:.0%} 複勝率{stats['fukusho_rate']:.0%}")
            lines.append("")
        
        # インサイト
        if result.get('insights'):
            lines.append("**💡 ポイント**")
            for insight in result['insights']:
                lines.append(f"• {insight}")
        
        return "\n".join(lines)
    
    def _format_daily_trend(self, result: Dict[str, Any]) -> str:
        """当日傾向分析結果をフォーマット"""
        lines = []
        lines.append("📈 **ViewLogic当日傾向**")
        lines.append(f"{result['venue']} - {result['date']}")
        lines.append(f"実施済み: {result['races_completed']}R")
        lines.append("")
        
        trends = result['trends']
        
        # 脚質別成績
        if trends.get('running_style_performance'):
            lines.append("**【脚質別成績】**")
            for style, perf in trends['running_style_performance'].items():
                lines.append(f"• {style}: {perf['wins']}勝/{perf['runs']}頭 (勝率{perf['win_rate']:.0%})")
            lines.append("")
        
        # 好調騎手
        if trends.get('hot_jockeys'):
            lines.append("**【好調騎手】**")
            for jockey in trends['hot_jockeys']:
                lines.append(f"• {jockey['name']}: {jockey['wins']}勝/{jockey['runs']}騎乗")
            lines.append("")
        
        # 馬場状態
        lines.append(f"**【馬場】** {trends.get('track_condition', '良')} / {trends.get('track_bias', 'フラット')}")
        lines.append("")
        
        # 推奨事項
        if result.get('recommendations'):
            lines.append("**⭐ 推奨**")
            for rec in result['recommendations']:
                lines.append(f"• {rec}")
        
        return "\n".join(lines)
    
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
            
            # レースに存在しない馬名が含まれているかチェック
            race_horses = race_data.get('horses', [])
            potential_horses = re.findall(r'[ア-ンー]+|[A-Za-z]+', message)
            
            for potential_horse in potential_horses:
                if len(potential_horse) >= 3:
                    is_in_race = False
                    for race_horse in race_horses:
                        if potential_horse in race_horse or race_horse in potential_horse:
                            is_in_race = True
                            break
                    
                    if not is_in_race and re.search(f'{potential_horse}(の|は|が|を|と|って|という)', message):
                        common_words = ['データ', 'レース', 'スコア', 'ポイント', 'システム', 'エラー']
                        if potential_horse not in common_words:
                            return {
                                'content': f"「{potential_horse}」は、{venue} {race_number}Rには出走しません。\nこのレースの出走馬は以下の通りです:\n" + "、".join(race_horses[:5]) + ("..." if len(race_horses) > 5 else ""),
                                'ai_type': determined_ai,
                                'sub_type': 'out_of_scope',
                                'analysis_data': None
                            }
            
            # 他のレースや開催場への言及の場合
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
        elif determined_ai == 'dlogic':
            result = await self.process_dlogic_message(message, race_data)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        elif determined_ai == 'ilogic':
            result = await self.process_ilogic_message(message, race_data)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        else:  # viewlogic
            result = await self.process_viewlogic_message(message, race_data, sub_type)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        
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
        
        # レースに存在しない馬名をチェック
        race_horses = race_data.get('horses', [])
        if race_horses:
            # メッセージから馬名らしい単語を抽出（カタカナまたは英字の連続）
            potential_horses = re.findall(r'[ア-ンー]+|[A-Za-z]+', message)
            
            for potential_horse in potential_horses:
                # 3文字以上で、かつレースの馬名リストに存在しない場合
                if len(potential_horse) >= 3:
                    # レースの馬名リストに存在するかチェック
                    is_in_race = False
                    for race_horse in race_horses:
                        if potential_horse in race_horse or race_horse in potential_horse:
                            is_in_race = True
                            break
                    
                    # 明らかに馬名として言及されている場合（〜の、〜は、など）
                    if not is_in_race and re.search(f'{potential_horse}(の|は|が|を|と|って|という)', message):
                        # 一般的な単語や助詞でないことを確認
                        common_words = ['データ', 'レース', 'スコア', 'ポイント', 'システム', 'エラー']
                        if potential_horse not in common_words:
                            return True
        
        return False
    
    async def process_dlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict]]:
        """
        D-Logicメッセージ処理
        """
        try:
            # D-Logic分析を実行する場合
            if self._should_analyze(message):
                # V2のD-Logicバッチ計算を使用
                from api.v2.dlogic import calculate_dlogic_batch
                
                # レース情報から馬名を抽出
                horses = race_data.get('horses', [])
                if not horses:
                    return ("分析対象の馬が指定されていません。", None)
                
                try:
                    # D-Logicバッチ計算を実行
                    dlogic_result = await calculate_dlogic_batch(horses)
                    
                    if not dlogic_result:
                        return ("D-Logic分析の実行に失敗しました。", None)
                    
                    # 結果をフォーマット
                    content = self._format_dlogic_batch_result(dlogic_result, race_data)
                    
                    # 分析データを抽出
                    analysis_data = {
                        'type': 'dlogic',
                        'scores': dlogic_result,
                        'top_horses': sorted(
                            [h for h in dlogic_result.keys() if dlogic_result[h].get('data_available', False)],
                            key=lambda h: dlogic_result[h].get('score', 0),
                            reverse=True
                        )[:5]
                    }
                    
                    return (content, analysis_data)
                    
                except Exception as e:
                    logger.error(f"D-Logic分析エラー: {e}")
                    import traceback
                    traceback.print_exc()
                    return ("D-Logic分析の実行中にエラーが発生しました。", None)
            
            # 通常の会話の場合
            else:
                # レースコンテキストを設定
                race_context = self.create_race_context_prompt(race_data)
                
                # D-Logicの説明
                dlogic_prompt = """
D-Logicは、12項目による馬の総合評価システムです。
各馬の能力を0-100点で評価し、ランキング形式で表示します。
分析をご希望の場合は「D-Logic指数を教えて」「評価して」などとお聞きください。
"""
                
                # Claude APIを呼び出し（会話用）
                if self.anthropic_client:
                    full_prompt = f"{race_context}\n\n{dlogic_prompt}\n\nユーザーの質問: {message}"
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
            logger.error(f"D-Logic処理エラー: {e}")
            return (f"申し訳ございません。D-Logic分析中にエラーが発生しました: {str(e)}", None)
    
    async def process_ilogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict]]:
        """
        I-Logicメッセージ処理 - V1と同じAPIエンドポイントを使用
        """
        try:
            # I-Logic分析を実行する場合
            if self._should_analyze(message):
                # レース情報を準備
                horses = race_data.get('horses', [])
                jockeys = race_data.get('jockeys', [])
                posts = race_data.get('posts', [])
                horse_numbers = race_data.get('horse_numbers', [])
                venue = race_data.get('venue', '')
                race_number = race_data.get('race_number', 0)
                
                if not horses:
                    return ("分析対象の馬が指定されていません。", None)
                
                # 騎手・枠順データが不足している場合
                if not jockeys or not posts:
                    return ("I-Logic分析には騎手・枠順情報が必要です。このレースでは分析できません。", None)
                
                try:
                    # HTTPリクエストではなく直接関数呼び出しを使用（Render環境対応）
                    logger.info(f"I-Logic直接関数呼び出し開始: {venue} {race_number}R")
                    
                    # race-analysis-v2/chat 関数を直接呼び出し
                    from api.race_analysis_v2 import race_analysis_chat
                    
                    # APIの期待する形式に合わせる
                    request_data = {
                        'message': f"{venue} {race_number}Rを分析して",
                        'race_info': {
                            'venue': venue,
                            'race_number': race_number,
                            'horses': horses,
                            'jockeys': jockeys,
                            'posts': posts,
                            'horse_numbers': horse_numbers or list(range(1, len(horses) + 1))
                        }
                    }
                    
                    logger.info(f"I-Logic関数呼び出しデータ: {request_data}")
                    
                    # 直接関数を呼び出し
                    result_data = await race_analysis_chat(request_data)
                    
                    logger.info(f"I-Logic関数レスポンス: {result_data}")
                    
                    # レスポンスの処理
                    if not result_data:
                        return ("I-Logic分析から空のレスポンスを受信しました。", None)
                    
                    if result_data.get('status') != 'success':
                        error_msg = result_data.get('response', 'I-Logic分析でエラーが発生しました')
                        return (error_msg, None)
                    
                    response_text = result_data.get('response', '')
                    
                    if not response_text:
                        return ("I-Logic分析結果が空です。", None)
                    
                    # レスポンステキストから馬名とスコアを抽出
                    scores = self._parse_ilogic_response(response_text, horses)
                    
                    # 分析データを抽出
                    analysis_data = {
                        'type': 'ilogic',
                        'response_text': response_text,
                        'top_horses': scores[:5] if scores else []
                    }
                    
                    return (response_text, analysis_data)
                    
                except Exception as e:
                    logger.error(f"I-Logic分析エラー: {e}")
                    import traceback
                    traceback.print_exc()
                    return ("I-Logic分析の実行中にエラーが発生しました。", None)
            
            # 通常の会話の場合
            else:
                # レースコンテキストを設定
                race_context = self.create_race_context_prompt(race_data)
                
                # I-Logicの説明
                ilogic_prompt = """
I-Logicは、馬の能力（70%）と騎手の適性（30%）を総合した分析システムです。
開催場適性、クラス補正、騎手の枠順適性などを考慮した精密な評価を行います。
分析をご希望の場合は「I-Logic分析して」「総合評価は？」などとお聞きください。
"""
                
                # Claude APIを呼び出し（会話用）
                if self.anthropic_client:
                    full_prompt = f"{race_context}\n\n{ilogic_prompt}\n\nユーザーの質問: {message}"
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
            logger.error(f"I-Logic処理エラー: {e}")
            return (f"申し訳ございません。I-Logic分析中にエラーが発生しました: {str(e)}", None)
    
    def _parse_dlogic_result(self, content: str) -> Optional[Dict]:
        """
        D-Logic結果からスコア情報を抽出
        """
        try:
            import re
            
            # D-Logic上位5頭を抽出するパターン
            top5_pattern = r'D-Logic上位5頭[：:]\s*([^、\n]+(?:、[^、\n]+){0,4})'
            match = re.search(top5_pattern, content)
            
            if match:
                top5_horses = [horse.strip() for horse in match.group(1).split('、')]
                return {
                    'type': 'dlogic',
                    'top_horses': top5_horses
                }
            
            return None
            
        except Exception as e:
            logger.error(f"D-Logic結果パースエラー: {e}")
            return None
    
    def _format_ilogic_result(self, analysis_result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """
        I-Logic分析結果をフォーマット
        """
        try:
            top_horses = analysis_result.get('top_horses', [])
            detailed_scores = analysis_result.get('detailed_scores', {})
            
            if not top_horses:
                return "I-Logic分析結果が取得できませんでした。"
            
            # 結果のフォーマット
            lines = []
            lines.append(f"👑 I-Logic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R")
            lines.append("")
            
            # 上位5頭を表示
            emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
            for i, horse_name in enumerate(top_horses[:5]):
                emoji = emojis[i] if i < 5 else f"{i+1}."
                
                # 詳細スコアがあれば表示
                if horse_name in detailed_scores:
                    score_info = detailed_scores[horse_name]
                    total_score = score_info.get('total_score', 0)
                    horse_score = score_info.get('horse_score', 0)
                    jockey_score = score_info.get('jockey_score', 0)
                    
                    lines.append(f"{emoji} {horse_name}: {total_score:.1f}点")
                    lines.append(f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点")
                else:
                    lines.append(f"{emoji} {horse_name}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"I-Logic結果フォーマットエラー: {e}")
            return "I-Logic分析結果の表示中にエラーが発生しました。"
    
    def _format_dlogic_batch_result(self, dlogic_result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """
        D-Logicバッチ計算結果をフォーマット
        """
        try:
            if not dlogic_result:
                return "D-Logic分析結果が取得できませんでした。"
            
            # スコアがある馬を抽出してソート
            valid_horses = []
            for horse_name, data in dlogic_result.items():
                if data.get('data_available', False) and data.get('score') is not None:
                    valid_horses.append((horse_name, data))
            
            # スコア順にソート
            valid_horses.sort(key=lambda x: x[1].get('score', 0), reverse=True)
            
            # 結果のフォーマット
            lines = []
            lines.append(f"🎯 D-Logic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R {race_data.get('race_name', '')}")
            
            # 上位5頭を表示
            emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
            for i, (horse_name, data) in enumerate(valid_horses[:5]):
                emoji = emojis[i] if i < 5 else f"{i+1}."
                score = data.get('score', 0)
                lines.append(f"{emoji} {horse_name}: {score:.1f}点")
                
                # 詳細スコアがあれば表示
                if data.get('details'):
                    details = data['details']
                    # 主要な項目を表示
                    if 'distance_aptitude' in details:
                        lines.append(f"   距離適性: {details['distance_aptitude']:.1f}")
                    if 'bloodline_evaluation' in details:
                        lines.append(f"   血統評価: {details['bloodline_evaluation']:.1f}")
            
            # 6位以下も簡潔に表示
            if len(valid_horses) > 5:
                lines.append("")
                lines.append("【6位以下】")
                for horse_name, data in valid_horses[5:]:
                    score = data.get('score', 0)
                    lines.append(f"{horse_name}: {score:.1f}点")
            
            # データがない馬がいる場合の注記
            no_data_horses = [name for name, data in dlogic_result.items() 
                            if not data.get('data_available', False)]
            if no_data_horses:
                lines.append("")
                lines.append("【データ不足】")
                lines.append(f"以下の馬はデータ不足のため分析できませんでした:")
                lines.append(f"{', '.join(no_data_horses)}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"D-Logic結果フォーマットエラー: {e}")
            return "D-Logic分析結果の表示中にエラーが発生しました。"
    
    def _parse_ilogic_response(self, response_text: str, horses: List[str]) -> List[str]:
        """
        I-Logicレスポンステキストから馬名順位を抽出
        """
        try:
            import re
            
            # テキストから馬名を順位順に抽出
            extracted_horses = []
            
            # 各馬名が何位に表示されているかチェック
            for horse in horses:
                for line in response_text.split('\n'):
                    if horse in line and ('位' in line or '🥇' in line or '🥈' in line or '🥉' in line or '🏅' in line):
                        if horse not in extracted_horses:
                            extracted_horses.append(horse)
                            break
            
            return extracted_horses
            
        except Exception as e:
            logger.error(f"I-Logicレスポンス解析エラー: {e}")
            return []
    
    def _format_ilogic_api_result(self, scores: List[Dict[str, Any]], race_data: Dict[str, Any]) -> str:
        """
        I-Logic API結果をフォーマット（V1互換）
        """
        try:
            if not scores:
                return "I-Logic分析結果が取得できませんでした。"
            
            # 結果のフォーマット
            lines = []
            lines.append(f"👑 I-Logic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R {race_data.get('race_name', '')}")
            
            # 上位5頭を表示
            emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
            for i, score_data in enumerate(scores[:5]):
                emoji = emojis[i] if i < 5 else f"{i+1}."
                horse_name = score_data.get('horse', '不明')
                total_score = score_data.get('score', 0)
                
                lines.append(f"{emoji} {horse_name}: {total_score:.1f}点")
            
            # 6位以下も簡潔に表示
            if len(scores) > 5:
                lines.append("")
                lines.append("【6位以下】")
                for score_data in scores[5:]:
                    horse_name = score_data.get('horse', '不明')
                    total_score = score_data.get('score', 0)
                    lines.append(f"{horse_name}: {total_score:.1f}点")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"I-Logic API結果フォーマットエラー: {e}")
            return "I-Logic分析結果の表示中にエラーが発生しました。"
    
    def _format_ilogic_batch_result(self, ilogic_result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """
        I-Logicバッチ計算結果をフォーマット
        """
        try:
            if not ilogic_result:
                return "I-Logic分析結果が取得できませんでした。"
            
            # スコアがある馬を抽出してソート
            valid_horses = []
            for horse_name, data in ilogic_result.items():
                if data.get('data_available', False) and data.get('score') is not None:
                    valid_horses.append((horse_name, data))
            
            # スコア順にソート
            valid_horses.sort(key=lambda x: x[1].get('score', 0), reverse=True)
            
            # 結果のフォーマット
            lines = []
            lines.append(f"👑 I-Logic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R {race_data.get('race_name', '')}")
            
            # 上位5頭を表示
            emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
            for i, (horse_name, data) in enumerate(valid_horses[:5]):
                emoji = emojis[i] if i < 5 else f"{i+1}."
                total_score = data.get('score', 0)
                horse_score = data.get('horse_score', 0)
                jockey_score = data.get('jockey_score', 0)
                
                lines.append(f"{emoji} {horse_name}: {total_score:.1f}点")
                lines.append(f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点")
            
            # 6位以下も簡潔に表示
            if len(valid_horses) > 5:
                lines.append("")
                lines.append("【6位以下】")
                for horse_name, data in valid_horses[5:]:
                    total_score = data.get('score', 0)
                    lines.append(f"{horse_name}: {total_score:.1f}点")
            
            # データがない馬がいる場合の注記
            no_data_horses = [name for name, data in ilogic_result.items() 
                            if not data.get('data_available', False)]
            if no_data_horses:
                lines.append("")
                lines.append("【データ不足】")
                lines.append(f"以下の馬はデータ不足のため分析できませんでした:")
                lines.append(f"{', '.join(no_data_horses)}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"I-Logic結果フォーマットエラー: {e}")
            return "I-Logic分析結果の表示中にエラーが発生しました。"