"""
V2 AI統合ハンドラー
レース限定分析とAI自然言語切り替えを実装
"""
import re
import json
import logging
import traceback
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
        # DLogicRawDataManagerは血統分析で使用するため初期化
        from services.dlogic_raw_data_manager import DLogicRawDataManager
        self.dlogic_manager = DLogicRawDataManager()  # 血統分析用（一度だけ初期化）

        # SirePerformanceAnalyzerをシングルトンで初期化（高速化）
        from services.sire_performance_analyzer import get_sire_performance_analyzer
        self.sire_analyzer = get_sire_performance_analyzer()
        logger.info("✅ SirePerformanceAnalyzer初期化完了")

        self.anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")) if Anthropic else None
        
        # 地方競馬場リスト（南関東4場）
        self.LOCAL_VENUES = ['川崎', '大井', '船橋', '浦和']
        
        # AI選択キーワード
        self.AI_KEYWORDS = {
            'imlogic': ['分析', '評価', 'IMLogic', 'IM', 'アイエム'],
            'viewlogic_trend': ['騎手分析', '傾向', 'トレンド', '統計', 'データ', '過去', 'コース傾向', '騎手成績', '血統', '枠順'],
            'viewlogic_recommendation': ['推奨', 'おすすめ', '買い目', '馬券', '予想'],
            'viewlogic_flow': ['展開', 'ペース', '逃げ', '先行', '差し', '追込', '脚質', 'ハイペース', 'スローペース', '流れ'],
            'viewlogic_history': ['過去データ', '直近', '前走', '戦績', '成績', '最近のレース', '過去のレース', '５走', '5走', '使い方'],  # 新規追加
            'viewlogic_sire': ['種牡馬分析', '種牡馬', '父', '母父', '血統分析', '父馬', '母馬', '母父馬', 'sire', 'dam', 'broodmare'],  # 種牡馬分析サブエンジン
            'dlogic': ['d-logic', 'ディーロジック', 'D-Logic', 'Dロジック', '指数', 'スコア', '12項目', '評価点'],
            'ilogic': ['i-logic', 'ilogic', 'アイロジック', 'I-Logic', 'Iロジック', '騎手', '総合', 'レースアナリシス', 'アナリシス'],
            'flogic': ['f-logic', 'flogic', 'エフロジック', 'F-Logic', 'Fロジック', 'フェア値']
        }
    
        
    def determine_ai_type(self, message: str) -> Tuple[str, str]:
        """
        メッセージからAIタイプを判定

        Returns:
            (ai_type, sub_type) のタプル
            - ai_type: 'imlogic', 'viewlogic', 'dlogic', 'ilogic', 'column'
            - sub_type: 'analysis', 'trend', 'opinion', 'display' など
        """
        message_lower = message.lower()

        # コラム表示の判定（最優先）
        if 'コラム' in message and ('表示' in message or '見せて' in message or '見る' in message or 'を教えて' in message):
            return ('column', 'display')

        # 特定のAIキーワードを最優先で判定（他のキーワードより優先）
        # MetaLogic分析（メタ予想システム - 最優先）
        if 'metalogic' in message_lower or 'meta-logic' in message_lower or 'メタロジック' in message or 'メタ予想' in message or 'メタログic' in message:
            return ('metalogic', 'analysis')
        
        # F-Logic分析（明示的な指定を最優先）
        if 'f-logic' in message_lower or 'flogic' in message_lower or 'エフロジック' in message or 'フェア値' in message:
            return ('flogic', 'analysis')
        
        # D-Logic分析（明示的な指定を優先）
        if 'd-logic' in message_lower or 'dlogic' in message_lower or 'ディーロジック' in message:
            return ('dlogic', 'analysis')
        
        # IMLogic分析（明示的な指定を優先）
        if 'imlogic' in message_lower or 'アイエムロジック' in message:
            return ('imlogic', 'analysis')
        
        # 「馬70騎手30」などのIMLogic特有のパターン
        if '馬' in message and '騎手' in message and ('％' in message or '%' in message or '分析' in message):
            return ('imlogic', 'analysis')
        
        # ViewLogic５走の使い方案内（最優先）
        if '使い方' in message and ('ViewLogic' in message or 'viewlogic' in message_lower or '５走' in message or '5走' in message):
            return ('viewlogic', 'history')
        
        # ViewLogic過去データ（馬名・騎手名が含まれる場合を優先）
        # レースデータから馬名と騎手名を取得して判定に使用
        if hasattr(self, 'current_race_data'):
            horses = self.current_race_data.get('horses', [])
            jockeys = self.current_race_data.get('jockeys', [])
            
            # 馬名が含まれているかチェック
            for horse in horses:
                if horse in message:
                    # 過去データ関連のキーワードもあるか、または馬名だけでも反応
                    for keyword in self.AI_KEYWORDS['viewlogic_history']:
                        if keyword in message_lower:
                            return ('viewlogic', 'history')
                    # 馬名だけでも反応（ただし他のAIキーワードがない場合）
                    if not any(kw in message_lower for kw_list in [
                        self.AI_KEYWORDS['dlogic'], 
                        self.AI_KEYWORDS['imlogic'],
                        self.AI_KEYWORDS['ilogic'],
                        self.AI_KEYWORDS['viewlogic_flow'],
                        self.AI_KEYWORDS['viewlogic_trend'],
                        self.AI_KEYWORDS['viewlogic_recommendation']
                    ] for kw in kw_list):
                        return ('viewlogic', 'history')
            
            # 騎手名が含まれているかチェック（部分一致と短縮名対応）
            for jockey in jockeys:
                if jockey:
                    # フルネームでの一致
                    if jockey in message:
                        for keyword in self.AI_KEYWORDS['viewlogic_history']:
                            if keyword in message_lower:
                                return ('viewlogic', 'history')
                        # 騎手名だけでも反応
                        if not any(kw in message_lower for kw_list in [
                            self.AI_KEYWORDS['dlogic'], 
                            self.AI_KEYWORDS['imlogic'],
                            self.AI_KEYWORDS['ilogic'],
                            self.AI_KEYWORDS['viewlogic_flow'],
                            self.AI_KEYWORDS['viewlogic_trend'],
                            self.AI_KEYWORDS['viewlogic_recommendation']
                        ] for kw in kw_list):
                            return ('viewlogic', 'history')
                    
                    # 短縮名での一致（例：川田将雅 → 川田、C.ルメール → ルメール）
                    if len(jockey) >= 2:
                        short_name = jockey[:2]  # 最初の2文字
                        if short_name in message:
                            for keyword in self.AI_KEYWORDS['viewlogic_history']:
                                if keyword in message_lower:
                                    return ('viewlogic', 'history')
                            # 短縮名だけでも反応
                            if not any(kw in message_lower for kw_list in [
                                self.AI_KEYWORDS['dlogic'], 
                                self.AI_KEYWORDS['imlogic'],
                                self.AI_KEYWORDS['ilogic'],
                                self.AI_KEYWORDS['viewlogic_flow'],
                                self.AI_KEYWORDS['viewlogic_trend'],
                                self.AI_KEYWORDS['viewlogic_recommendation']
                            ] for kw in kw_list):
                                return ('viewlogic', 'history')
                    
                    # 外国人騎手の場合（C.ルメール → ルメール）
                    if '.' in jockey:
                        last_part = jockey.split('.')[-1]
                        if last_part in message:
                            for keyword in self.AI_KEYWORDS['viewlogic_history']:
                                if keyword in message_lower:
                                    return ('viewlogic', 'history')
                            if not any(kw in message_lower for kw_list in [
                                self.AI_KEYWORDS['dlogic'], 
                                self.AI_KEYWORDS['imlogic'],
                                self.AI_KEYWORDS['ilogic'],
                                self.AI_KEYWORDS['viewlogic_flow'],
                                self.AI_KEYWORDS['viewlogic_trend'],
                                self.AI_KEYWORDS['viewlogic_recommendation']
                            ] for kw in kw_list):
                                return ('viewlogic', 'history')

        # ViewLogic種牡馬分析（優先度高）
        for keyword in self.AI_KEYWORDS['viewlogic_sire']:
            if keyword in message_lower or keyword in message:  # 「父」「母父」は漢字なのでmessageでも確認
                return ('viewlogic', 'sire')

        # ViewLogic展開予想（優先度高）
        for keyword in self.AI_KEYWORDS['viewlogic_flow']:
            if keyword in message_lower:
                return ('viewlogic', 'flow')
        
        # ViewLogic傾向分析（I-Logicより優先）
        for keyword in self.AI_KEYWORDS['viewlogic_trend']:
            if keyword in message_lower:
                return ('viewlogic', 'trend')
        
        # F-Logic分析（投資価値判定）
        for keyword in self.AI_KEYWORDS['flogic']:
            if keyword.lower() in message_lower:
                return ('flogic', 'analysis')
        
        # I-Logic分析
        for keyword in self.AI_KEYWORDS['ilogic']:
            if keyword.lower() in message_lower:
                return ('ilogic', 'analysis')
        
        # ViewLogic推奨
        for keyword in self.AI_KEYWORDS['viewlogic_recommendation']:
            if keyword in message_lower:
                return ('viewlogic', 'recommendation')
        
        # その他のD-Logicキーワード
        for keyword in self.AI_KEYWORDS['dlogic']:
            if keyword.lower() in message_lower:
                return ('dlogic', 'analysis')
        
        # その他のIMLogicキーワード
        for keyword in self.AI_KEYWORDS['imlogic']:
            if keyword.lower() in message_lower:
                return ('imlogic', 'analysis')
        
        # 「標準分析」はD-Logicとして扱う
        if '標準' in message_lower and '分析' in message_lower:
            return ('dlogic', 'analysis')
        
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
    
    def _is_local_racing(self, venue: str) -> bool:
        """地方競馬場かどうかを判定"""
        return venue in self.LOCAL_VENUES
    
    async def process_imlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[Dict]]:
        """
        IMLogicメッセージ処理（地方競馬対応版）
        """
        try:
            # 分析を実行する場合
            if self._should_analyze(message):
                venue = race_data.get('venue', '')
                
                # 地方競馬場の場合は地方競馬版エンジンを使用
                if self._is_local_racing(venue):
                    from services.local_imlogic_engine_v2 import local_imlogic_engine_v2
                    imlogic_engine_temp = local_imlogic_engine_v2
                    logger.info(f"🏇 地方競馬版IMLogicエンジンを使用: {venue}")
                else:
                    # JRA版（既存）
                    from services.imlogic_engine import get_imlogic_engine
                    imlogic_engine_temp = get_imlogic_engine()
                    logger.info(f"🏇 JRA版IMLogicエンジンを使用: {venue}")
                
                # デフォルトの設定を使用（設定が無い場合）
                if not settings:
                    settings = self._get_default_imlogic_settings()
                
                # IMLogicEngineで分析
                # フロントエンドからのデータ構造に対応
                # 0も有効な値として扱うため、Noneチェックを使用
                if 'horse_weight' in settings:
                    horse_weight = settings['horse_weight']
                elif 'horse_ratio' in settings:
                    horse_weight = settings['horse_ratio']
                else:
                    horse_weight = 70
                    
                if 'jockey_weight' in settings:
                    jockey_weight = settings['jockey_weight']
                elif 'jockey_ratio' in settings:
                    jockey_weight = settings['jockey_ratio']
                else:
                    jockey_weight = 30
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
                logger.info(f"IMLogic分析開始 - venue: {venue}, horses: {race_data.get('horses', [])}")
                logger.info(f"IMLogic重み設定 - horse: {horse_weight}%, jockey: {jockey_weight}%")
                
                analysis_result = imlogic_engine_temp.analyze_race(
                    race_data=race_data,
                    horse_weight=horse_weight,
                    jockey_weight=jockey_weight,
                    item_weights=item_weights
                )
                
                logger.info(f"IMLogic分析結果: status={analysis_result.get('status')}, results数={len(analysis_result.get('results', []))}")
                
                # 結果が空の場合のチェック（'scores'と'results'の両方をチェック）
                if not analysis_result or (not analysis_result.get('scores') and not analysis_result.get('results')):
                    logger.error(f"IMLogic分析結果が空: {analysis_result}")
                    logger.error(f"race_data詳細: {race_data}")
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
            import traceback
            logger.error(f"IMLogic処理エラー: {e}")
            logger.error(f"IMLogicスタックトレース: {traceback.format_exc()}")
            logger.error(f"IMLogicエラー時のrace_data: {race_data}")
            return (f"申し訳ございません。IMLogic分析中にエラーが発生しました: {str(e)}", None)
    
    def _should_analyze(self, message: str) -> bool:
        """メッセージが分析要求かどうかを判定"""
        analyze_keywords = ['分析', '評価', '順位', '上位', '予想', 'ランキング', 'スコア', '計算']
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
            
            # 全頭を順位付きで表示（I-Logic形式）
            emojis = ['🥇', '🥈', '🥉']
            # -1はデータ不足なので、有効なスコアから除外
            valid_scores = [s for s in scores if s.get('total_score') is not None and s.get('total_score') >= 0]
            no_data_scores = [s for s in scores if s.get('total_score') == -1]
            
            for i, score_data in enumerate(valid_scores):
                # 上位3位まで絵文字、4位以降は数字表示
                if i < 3:
                    rank_display = f"{emojis[i]} {i+1}位:"
                else:
                    rank_display = f"{i+1}位:"
                
                # 'horse_name'と'horse'の両方に対応
                horse_name = score_data.get('horse_name') or score_data.get('horse', '不明')
                total_score = score_data.get('total_score', 0)
                horse_score = score_data.get('horse_score', 0)
                jockey_score = score_data.get('jockey_score', 0)
                
                lines.append(f"{rank_display} {horse_name}: {total_score:.1f}点")
                lines.append(f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点")
                
                # 次の馬との間に空行を追加（最後の馬以外）
                if i < len(valid_scores) - 1:
                    lines.append("")
                
                # 6位目に区切り線を追加
                if i == 5:
                    lines.append("【6位以下】")
            
            # データがない馬がいる場合の注記
            if no_data_scores:
                no_data_horses = [s.get('horse_name') or s.get('horse', '不明') for s in no_data_scores]
                lines.append("")
                lines.append("【データ不足】")
                lines.append(f"以下の馬はデータベースにデータがありません: {', '.join(no_data_horses)}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"結果フォーマットエラー: {e}")
            return "分析結果の表示中にエラーが発生しました。"
    
    async def process_metalogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict]]:
        """
        MetaLogicメッセージ処理（メタ予想システム）
        I-Logic 40%, D-Logic 30%, ViewLogic 30%の重み付けアンサンブル
        
        Returns:
            (content, analysis_data) のタプル
        """
        try:
            from services.metalogic_engine import metalogic_engine
            
            # レースデータの準備
            analysis_result = await metalogic_engine.analyze_race(race_data)
            
            if analysis_result.get('status') != 'success':
                return (analysis_result.get('message', '分析に失敗しました'), None)
            
            # 結果のフォーマット
            content = self._format_metalogic_result(analysis_result)
            
            return (content, analysis_result)
            
        except Exception as e:
            logger.error(f"MetaLogic処理エラー: {e}")
            traceback.print_exc()
            return ("MetaLogicの分析中にエラーが発生しました。", None)
    
    def _format_metalogic_result(self, result: Dict[str, Any]) -> str:
        """MetaLogic結果のフォーマット"""
        try:
            rankings = result.get('rankings', [])
            
            if not rankings:
                return "分析結果がありません。"
            
            content = "🎯 **MetaLogic メタ予想システム**\n"
            content += "（I-Logic 40% + D-Logic 30% + ViewLogic 30% + 市場評価）\n\n"
            content += "**推奨馬（メタスコア順）**\n\n"
            
            for item in rankings[:5]:
                horse = item.get('horse', '不明')
                score = item.get('meta_score', 0)
                details = item.get('details', {})
                
                # 信頼度インジケーター
                if details.get('engine_count', 0) >= 3:
                    confidence = "⭐⭐⭐"
                elif details.get('engine_count', 0) >= 2:
                    confidence = "⭐⭐"
                else:
                    confidence = "⭐"
                
                content += f"**{item.get('rank')}位 {horse}** {confidence}\n"
                content += f"  メタスコア: **{score:.1f}点**\n"
                content += f"  - D-Logic: {details.get('d_logic', 0):.1f}点\n"
                content += f"  - I-Logic: {details.get('i_logic', 0):.1f}点\n"
                content += f"  - ViewLogic: {details.get('view_logic', 0):.1f}点\n"
                content += f"  - オッズ評価: {details.get('odds_factor', 0):.1f}点\n\n"
            
            content += "\n💡 **解説**\n"
            content += "MetaLogicは3つのAIエンジンと市場評価を統合した\n"
            content += "アンサンブル予想システムです。\n"
            content += "I-Logicの高精度を活かしつつ、複数視点での検証により\n"
            content += "安定性を向上させています。\n"
            
            return content
            
        except Exception as e:
            logger.error(f"MetaLogic結果フォーマットエラー: {e}")
            return "結果の表示中にエラーが発生しました。"
    
    async def process_viewlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any],
        sub_type: str = 'trend'
    ) -> Tuple[str, Optional[Dict]]:
        """
        ViewLogicメッセージ処理（地方競馬対応版）
        
        Returns:
            (content, analysis_data) のタプル
        """
        try:
            venue = race_data.get('venue', '不明')
            race_number = race_data.get('race_number', '不明')
            
            # 地方競馬場の場合は地方競馬版エンジンを使用
            if self._is_local_racing(venue):
                from services.local_viewlogic_engine_v2 import local_viewlogic_engine_v2
                viewlogic_engine = local_viewlogic_engine_v2
                logger.info(f"🏇 地方競馬版ViewLogicエンジンを使用: {venue}")
            else:
                # JRA版（既存）
                from services.viewlogic_engine import ViewLogicEngine
                viewlogic_engine = ViewLogicEngine()
                logger.info(f"🏇 JRA版ViewLogicエンジンを使用: {venue}")
            
            if sub_type == 'flow':
                # 展開予想（高度な分析版を使用）
                logger.info(f"ViewLogic展開予想開始: venue={venue}, horses={race_data.get('horses', [])}")
                result = viewlogic_engine.predict_race_flow_advanced(race_data)
                logger.info(f"ViewLogic展開予想結果: status={result.get('status')}, type={result.get('type')}")
                
                if result.get('status') == 'success':
                    # 外部フォーマット関数を使用
                    from services.v2.ai_handler_format_advanced import format_flow_prediction_advanced
                    content = format_flow_prediction_advanced(result)
                    return (content, result)
                else:
                    logger.error(f"ViewLogic展開予想エラー詳細: {result}")
                    return (f"展開予想に失敗しました: {result.get('message', '不明なエラー')}", None)
                    
            elif sub_type == 'trend':
                # コース傾向分析（実際の出場馬・騎手データを使用）
                import signal
                import time
                
                # タイムアウトハンドラー
                def timeout_handler(signum, frame):
                    raise TimeoutError("傾向分析がタイムアウトしました")
                
                try:
                    # 25秒のタイムアウトを設定（Renderの30秒制限より短く）
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(25)
                    
                    result = viewlogic_engine.analyze_course_trend(race_data)
                    
                    # タイムアウトをリセット
                    signal.alarm(0)
                    
                    if result['status'] == 'success':
                        content = self._format_trend_analysis(result)
                        return (content, result)
                    else:
                        return (f"傾向分析に失敗しました: {result.get('message', '不明なエラー')}", None)
                        
                except TimeoutError:
                    signal.alarm(0)  # タイムアウトをリセット
                    logger.error("ViewLogic傾向分析がタイムアウトしました（25秒）")
                    return ("傾向分析の処理に時間がかかりすぎています。データ量が多い可能性があります。", None)
                except Exception as e:
                    signal.alarm(0)  # タイムアウトをリセット
                    logger.error(f"ViewLogic傾向分析中にエラー: {e}")
                    return (f"傾向分析中にエラーが発生しました: {str(e)}", None)
                    
            elif sub_type == 'recommendation':
                # 推奨馬券（馬券推奨として実装）
                result = viewlogic_engine.recommend_betting_tickets(
                    race_data=race_data
                )
                
                if result['status'] == 'success':
                    content = self._format_betting_recommendations(result)
                    return (content, result)
                else:
                    # フォールバック: 基本的な推奨を提供
                    return (f"""
🎯 ViewLogic推奨馬券
{venue} {race_number}R

申し訳ございません。現在、推奨馬券の生成ができません。
以下の分析機能をご利用ください：

• 「展開予想」- レースの流れを予想
• 「傾向分析」- コース・騎手成績を分析

これらの結果を参考に馬券をご検討ください。
""", None)
            
            elif sub_type == 'history':
                # 使い方案内の判定
                if '使い方' in message or 'ViewLogic５走の使い方' in message:
                    return self._get_viewlogic_5race_guide(race_data), None
                
                # 過去データ表示（新機能）
                # メッセージから馬名または騎手名を抽出
                horses = race_data.get('horses', [])
                jockeys = race_data.get('jockeys', [])
                
                # 馬名チェック
                target_horse = None
                for horse in horses:
                    if horse in message:
                        target_horse = horse
                        break
                
                # 騎手名チェック
                target_jockey = None
                if not target_horse:
                    for jockey in jockeys:
                        if jockey and jockey in message:
                            target_jockey = jockey
                            break
                
                # プログレスバー表示用のメッセージを最初に返す
                if target_horse:
                    progress_message = "ViewLogic過去データを取得中...\n" + target_horse + "の履歴を検索しています..."
                elif target_jockey:
                    progress_message = "ViewLogic過去データを取得中...\n" + target_jockey + "騎手の履歴を検索しています..."
                else:
                    return ("分析対象の馬名または騎手名が見つかりませんでした。", None)
                
                # 実際のデータ取得処理
                if target_horse:
                    # 馬の過去データ取得
                    result = viewlogic_engine.get_horse_history(target_horse)
                    if result['status'] == 'success':
                        content = self._format_horse_history(result, target_horse)
                        # プログレスメッセージと実際のコンテンツを結合
                        full_content = f"{progress_message}\n\n{content}"
                        return (full_content, result)
                    else:
                        return (f"{progress_message}\n\n{target_horse}の過去データが見つかりませんでした。", None)
                
                elif target_jockey:
                    # 騎手の過去データ取得
                    result = viewlogic_engine.get_jockey_history(target_jockey)
                    if result['status'] == 'success':
                        content = self._format_jockey_history(result, target_jockey)
                        # プログレスメッセージと実際のコンテンツを結合
                        full_content = f"{progress_message}\n\n{content}"
                        return (full_content, result)
                    else:
                        return (f"{progress_message}\n\n{target_jockey}騎手の過去データが見つかりませんでした。", None)
                
                else:
                    # 馬名も騎手名も見つからない場合
                    example_horse = horses[0] if horses else 'ドウデュース'
                    return (f"出走馬または騎手の名前を指定してください。例：「{example_horse}の過去データ」", None)

            elif sub_type == 'sire':
                # 種牡馬分析
                return self._generate_sire_analysis(race_data)

            else:
                return ("ViewLogic機能をご利用いただきありがとうございます。「展開」「傾向」「推奨」のいずれかをお試しください。", None)
                
        except ImportError as e:
            logger.error(f"ViewLogicエンジンのインポートエラー: {e}")
            return ("ViewLogicエンジンの読み込みに失敗しました。システム管理者にお問い合わせください。", None)
        except Exception as e:
            import traceback
            logger.error(f"ViewLogic処理エラー: {e}")
            logger.error(f"ViewLogicスタックトレース: {traceback.format_exc()}")
            logger.error(f"ViewLogicエラー時のrace_data: {race_data}")
            logger.error(f"ViewLogicエラー時のsub_type: {sub_type}")
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
        """コース傾向分析結果をフォーマット（新しい4項目構造対応）"""
        lines = []
        lines.append("📊 **ViewLogicコース傾向分析**")
        
        course = result['course_info']
        course_key = course.get('course_key', f"{course['venue']}コース")
        lines.append(f"{course_key}")
        lines.append("")
        
        trends = result['trends']
        
        # 1. 出場馬の該当コース成績複勝率
        if trends.get('horse_course_performance'):
            lines.append("**【出場馬の当コース成績】**")
            horses = trends['horse_course_performance']
            
            # 成績がある馬のみ表示
            horses_with_data = [h for h in horses if h.get('status') == 'found' and h.get('total_runs', 0) > 0]
            horses_no_data = [h for h in horses if h.get('status') != 'found' or h.get('total_runs', 0) == 0]
            
            if horses_with_data:
                for i, horse in enumerate(horses_with_data, 1):
                    total_runs = horse.get('total_runs', 0)
                    fukusho_rate = horse.get('fukusho_rate', 0.0)
                    lines.append(f"{i}. **{horse['horse_name']}**: {total_runs}戦 複勝率{fukusho_rate:.1f}%")
                
                # 完結メッセージを追加
                lines.append("")
                lines.append(f"以上が当コースで出走経験のある{len(horses_with_data)}頭です。")
                if horses_no_data:
                    no_data_names = [h['horse_name'] for h in horses_no_data[:5]]  # 最初の5頭のみ表示
                    if len(horses_no_data) > 5:
                        lines.append(f"その他の馬（{', '.join(no_data_names)}他）は当コースでの出走経験がありません。")
                    else:
                        lines.append(f"その他の馬（{', '.join(no_data_names)}）は当コースでの出走経験がありません。")
            else:
                lines.append("出場馬全頭が当コースでの出走経験がありません。")
                lines.append("過去のデータがないため、他の要素での判断が重要になります。")
            lines.append("")
        
        # 2. 騎手の該当コース成績複勝率
        if trends.get('jockey_course_performance'):
            lines.append("**【騎手の当コース成績】**")
            jockeys = trends['jockey_course_performance']
            
            # 成績がある騎手のみ表示
            jockeys_with_data = [j for j in jockeys if j.get('status') == 'found' and j.get('total_runs', 0) > 0]
            jockeys_no_data = [j for j in jockeys if j.get('status') != 'found' or j.get('total_runs', 0) == 0]
            
            if jockeys_with_data:
                for i, jockey in enumerate(jockeys_with_data, 1):
                    total_runs = jockey.get('total_runs', 0)
                    win_rate = jockey.get('win_rate', 0.0)
                    fukusho_rate = jockey.get('fukusho_rate', 0.0)
                    # 騎手ナレッジファイルは直近5戦のデータのみ保持
                    display_runs = f"直近{total_runs}戦" if total_runs <= 5 else f"{total_runs}戦"
                    lines.append(f"{i}. **{jockey['jockey_name']}**: {display_runs} 勝率{win_rate:.1f}% 複勝率{fukusho_rate:.1f}%")
                
                # 完結メッセージを追加
                lines.append("")
                lines.append(f"以上が当コースで騎乗経験のある{len(jockeys_with_data)}名です（直近データより）。")
                if jockeys_no_data:
                    lines.append(f"その他の騎手は当コースでの騎乗経験がありません（直近5戦内）。")
            else:
                lines.append("出場騎手全員が当コースでの騎乗経験がありません。")
                lines.append("騎手の適性よりも馬の能力を重視した方がよいでしょう。")
            lines.append("")
        
        # 3. 騎手の枠順別複勝率
        if trends.get('jockey_post_performance'):
            lines.append("**【騎手の枠順別成績】**")
            jockey_post_data = trends['jockey_post_performance']
            
            # デバッグログ追加
            logger.info(f"🐎 騎手枠順別成績データ取得: type={type(jockey_post_data)}, keys={list(jockey_post_data.keys()) if isinstance(jockey_post_data, dict) else 'not dict'}")
            if isinstance(jockey_post_data, dict) and jockey_post_data:
                first_key = list(jockey_post_data.keys())[0]
                logger.info(f"   サンプル（{first_key}）: {jockey_post_data[first_key]}")
            
            # jockey_post_dataの型チェック
            if jockey_post_data and isinstance(jockey_post_data, dict):
                # 各騎手の個別成績を表示
                jockey_count = 0
                for jockey_name, post_stats in jockey_post_data.items():
                    # post_statsの型チェック
                    if not isinstance(post_stats, dict):
                        logger.error(f"騎手 {jockey_name} のpost_statsが辞書ではありません: type={type(post_stats)}")
                        continue
                    
                    # 今回の枠番情報を取得
                    assigned_post = post_stats.get('assigned_post')
                    post_category = post_stats.get('post_category')
                    
                    # 該当する枠番での成績を取得
                    if assigned_post and post_category:
                        # assigned_post_statsがあればそれを使用、なければall_post_statsから取得
                        assigned_stats = post_stats.get('assigned_post_stats')
                        if not assigned_stats and post_category:
                            all_stats = post_stats.get('all_post_stats', {})
                            if isinstance(all_stats, dict):
                                assigned_stats = all_stats.get(post_category, {})
                        
                        if assigned_stats and isinstance(assigned_stats, dict):
                            race_count = assigned_stats.get('race_count', 0)
                            fukusho_rate = assigned_stats.get('fukusho_rate', 0.0)
                            
                            if race_count > 0:
                                jockey_count += 1
                                # 複勝率を正常範囲（0-100%）に修正
                                if fukusho_rate > 100:
                                    # 異常に大きい値は100で割る
                                    display_rate = fukusho_rate / 100
                                elif fukusho_rate > 1.0:
                                    # 1を超える値はそのまま使用（パーセント値）
                                    display_rate = fukusho_rate
                                else:
                                    # 0.0-1.0の場合は100倍してパーセント値に
                                    display_rate = fukusho_rate * 100
                                # 100%を上限とする
                                display_rate = min(display_rate, 100.0)
                                # レース数は表示せず、複勝率のみを表示
                                lines.append(f"{jockey_count}. **{jockey_name}**（{assigned_post}枠）: 複勝率{display_rate:.1f}%")
                            else:
                                jockey_count += 1
                                lines.append(f"{jockey_count}. **{jockey_name}**（{assigned_post}枠）: データなし")
                        else:
                            jockey_count += 1
                            lines.append(f"{jockey_count}. **{jockey_name}**（{assigned_post}枠）: データなし")
                    else:
                        # 枠番情報がない場合は全体の成績を表示
                        all_stats = post_stats.get('all_post_stats', {})
                        if isinstance(all_stats, dict):
                            total_races = 0
                            total_fukusho = 0
                            for category, stats in all_stats.items():
                                if isinstance(stats, dict):
                                    races = stats.get('race_count', 0)
                                    rate = stats.get('fukusho_rate', 0.0)
                                    if races > 0:
                                        total_races += races
                                        total_fukusho += races * rate
                            
                            if total_races > 0:
                                avg_fukusho = total_fukusho / total_races
                                jockey_count += 1
                                # 全体成績でも同じ正規化を適用
                                if avg_fukusho > 100:
                                    display_avg = avg_fukusho / 100
                                elif avg_fukusho > 1.0:
                                    display_avg = avg_fukusho
                                else:
                                    display_avg = avg_fukusho * 100
                                # 100%を上限とする
                                display_avg = min(display_avg, 100.0)
                                lines.append(f"{jockey_count}. **{jockey_name}**: 複勝率{display_avg:.1f}%")
                            else:
                                jockey_count += 1
                                lines.append(f"{jockey_count}. **{jockey_name}**: データなし")
                        else:
                            jockey_count += 1
                            lines.append(f"{jockey_count}. **{jockey_name}**: データなし")
                
                # 完結メッセージを追加
                if jockey_count > 0:
                    lines.append("")
                    lines.append(f"以上が出場騎手{jockey_count}名の枠順別成績です。")
                else:
                    lines.append("出場騎手の枠順別データがありません。")
                    
            elif jockey_post_data and not isinstance(jockey_post_data, dict):
                logger.error(f"jockey_post_dataが辞書ではありません: type={type(jockey_post_data)}")
                lines.append("• 枠順別データの取得に失敗しました")
            else:
                lines.append("• 枠順別データなし")
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
                win_rate = perf.get('win_rate', 0)
                if win_rate > 1:
                    win_rate = win_rate / 100
                wins = perf.get('wins', 0)
                runs = perf.get('runs', 0)
                lines.append(f"• {style}: {wins}勝/{runs}頭 (勝率{win_rate:.0%})")
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
        settings: Optional[Dict[str, Any]] = None,
        user_email: Optional[str] = None
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
        # レースデータを保持（determine_ai_typeで使用）
        self.current_race_data = race_data
        
        # まず出走馬チェック（AI判定の前に必ず実行）
        venue = race_data.get('venue', '')
        race_number = race_data.get('race_number', '')
        race_horses = race_data.get('horses', [])

        # レースに存在しない馬名が含まれているかチェック
        # カタカナの馬名を正しく抽出（ァ-ヴーを使用）
        potential_horses = re.findall(r'[ァ-ヴー]+', message)

        for potential_horse in potential_horses:
            if len(potential_horse) >= 3:
                is_in_race = False
                for race_horse in race_horses:
                    if potential_horse in race_horse or race_horse in potential_horse:
                        is_in_race = True
                        break

                # 助詞チェックを緩和（馬名単体でも検出）
                if not is_in_race:
                    common_words = ['データ', 'レース', 'スコア', 'ポイント', 'システム', 'エラー', 'ViewLogic', 'IMLogic', 'DLogic', 'ILogic', 'FLogic', 'フェア', 'オッズ', 'ロジック', 'エフロジック', 'コラム']  # 'コラム'を除外単語に追加
                    if potential_horse not in common_words:
                        return {
                            'content': f"「{potential_horse}」は、{venue} {race_number}Rには出走しません。\nこのレースの出走馬は以下の通りです:\n" + "、".join(race_horses),
                            'ai_type': 'imlogic',  # デフォルトでimlogicを返す
                            'sub_type': 'out_of_scope',
                            'analysis_data': None
                        }
        
        # 次にレース外の質問をチェック
        if self._is_out_of_scope(message, race_data):
            # 他のレースや開催場への言及の場合
            return {
                'content': f"このチャットは{venue} {race_number}R専用です。他のレースについては新しいチャットを作成してください。",
                'ai_type': 'imlogic',  # デフォルトでimlogicを返す
                'ai_display_name': 'IMLogic AI',
                'sub_type': 'out_of_scope',
                'analysis_data': None
            }
        
        # AI タイプの決定（レース外チェックの後に移動）
        if ai_type:
            determined_ai = ai_type
            logger.info(f"AI判定(手動指定): ai_type={ai_type}, determined_ai={determined_ai}")
            # ViewLogicの場合は、メッセージからサブタイプを決定
            if ai_type == 'viewlogic':
                _, sub_type = self.determine_ai_type(message)
                # ViewLogic以外が判定された場合はデフォルトに
                if sub_type not in ['flow', 'trend', 'opinion']:
                    sub_type = 'manual'
            elif ai_type == 'flogic':
                sub_type = 'analysis'  # F-Logicは分析タイプ
            elif ai_type == 'metalogic':
                sub_type = 'analysis'  # MetaLogicは分析タイプ
            else:
                sub_type = 'manual'
        else:
            determined_ai, sub_type = self.determine_ai_type(message)
            logger.info(f"AI判定(自動): message='{message[:50]}...', determined_ai={determined_ai}, sub_type={sub_type}")

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
        elif determined_ai == 'flogic':
            result = await self.process_flogic_message(message, race_data)
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
        elif determined_ai == 'metalogic':
            result = await self.process_metalogic_message(message, race_data)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        elif determined_ai == 'column':
            logger.info(f"コラム処理開始: determined_ai={determined_ai}, user_email={user_email}")
            # コラム表示の処理 - Supabaseからコラムを取得して返す
            from supabase import create_client
            from datetime import datetime
            import os

            def strip_html_tags(text):
                """HTMLタグを除去してプレーンテキストに変換"""
                # HTMLタグを除去
                clean = re.compile('<.*?>')
                text = re.sub(clean, '', text)
                # HTMLエンティティを変換
                text = text.replace('&nbsp;', ' ')
                text = text.replace('&lt;', '<')
                text = text.replace('&gt;', '>')
                text = text.replace('&amp;', '&')
                text = text.replace('&quot;', '"')
                text = text.replace('&#39;', "'")
                return text.strip()

            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            supabase = create_client(supabase_url, supabase_key)

            # 管理者チェック
            is_admin = user_email in ['goldbenchan@gmail.com', 'kusanokiyoshi1@gmail.com']

            # ユーザー情報を取得（LINE連携状態とポイント残高）
            user_has_line = False
            user_points = 0
            user_id = None
            if user_email:
                try:
                    # v2_usersテーブルからユーザー情報を一括取得（id, line_user_id）
                    users_response = supabase.table('v2_users').select('id, line_user_id').eq('email', user_email).execute()

                    if users_response.data and len(users_response.data) > 0:
                        user_data = users_response.data[0]
                        user_id = user_data.get('id')
                        line_user_id = user_data.get('line_user_id')
                        user_has_line = line_user_id is not None and line_user_id != ''
                        logger.info(f"LINE連携判定: line_user_id={line_user_id}, user_has_line={user_has_line}")

                        # user_idでポイント残高を確認
                        if user_id:
                            points_response = supabase.table('v2_user_points').select('current_points').eq('user_id', user_id).execute()
                            if points_response.data and len(points_response.data) > 0:
                                user_points = points_response.data[0].get('current_points', 0)

                    logger.info(f"ユーザー情報取得: email={user_email}, is_admin={is_admin}, has_line={user_has_line}, points={user_points}")
                except Exception as e:
                    logger.error(f"ユーザー情報取得エラー: {str(e)}")

            # race_idを構成（管理者パネル形式に合わせる）
            race_date = race_data.get('race_date', '')
            year = race_date.split('-')[0] if race_date else '2025'
            venue_map = {
                '中山': 'nakayama', '東京': 'tokyo', '阪神': 'hanshin', '京都': 'kyoto',
                '中京': 'chukyo', '新潟': 'niigata', '福島': 'fukushima', '札幌': 'sapporo',
                '函館': 'hakodate', '小倉': 'kokura', '大井': 'ooi', '川崎': 'kawasaki',
                '浦和': 'urawa', '船橋': 'funabashi'
            }
            venue_code = venue_map.get(race_data.get('venue', ''), race_data.get('venue', '').lower())
            race_id = f"{year}_{venue_code}_r{race_data.get('race_number', '')}"

            # コラムを取得
            logger.info(f"コラム検索: race_id={race_id}")
            response = supabase.table('v2_columns').select('*').eq('race_id', race_id).eq('display_in_llm', True).eq('is_published', True).execute()

            if response.data and len(response.data) > 0:
                columns_html = "## このレースのコラム\n\n"
                logger.info(f"取得したコラム数: {len(response.data)}")
                for col in response.data:
                    logger.info(f"コラム: title={col.get('title')}, access_type={col.get('access_type')}, required_points={col.get('required_points')}")

                    # access_typeを取得（Null/空文字対応）
                    actual_access_type = col.get('access_type')
                    if actual_access_type is None or actual_access_type == '':
                        actual_access_type = 'free'
                        logger.warning(f"access_typeがNullまたは空のため、freeとして扱います")
                    # 文字列の前後の空白を削除
                    actual_access_type = str(actual_access_type).strip() if actual_access_type else 'free'

                    # アクセスタイプに応じた表示テキスト
                    if actual_access_type == 'free':
                        access_text = "無料"
                    elif actual_access_type == 'line_only' or actual_access_type == 'line_linked':  # line_linkedもサポート
                        access_text = "LINE連携限定"
                    elif actual_access_type == 'paid' or actual_access_type == 'point_required':
                        access_text = f"{col.get('required_points', 1)}ポイント"
                    else:
                        # デフォルトケース - 値を明示
                        access_text = f"不明({actual_access_type})"
                        logger.warning(f"予期しないaccess_type: '{actual_access_type}'")

                    columns_html += f"### 📝 {col['title']} ({access_text})\n"

                    # summaryもHTMLタグ除去
                    summary = strip_html_tags(col.get('summary', ''))
                    if summary:
                        columns_html += f"{summary}\n\n"

                    # アクセス権限チェック
                    can_access = False
                    access_reason = ""

                    logger.info(f"アクセスチェック開始: access_type={actual_access_type}, user_has_line={user_has_line}, user_points={user_points}")

                    if actual_access_type == 'free':
                        # 無料コラムは誰でもアクセス可能
                        can_access = True
                        logger.info("→ 無料コラムのためアクセス許可")
                    elif actual_access_type == 'line_only' or actual_access_type == 'line_linked':  # line_linkedもサポート
                        # LINE連携者限定コラム
                        # 管理者は無料で閲覧可能
                        if is_admin:
                            can_access = True
                            logger.info("→ 管理者のためLINE連携チェックをスキップ")
                        elif user_has_line:
                            can_access = True
                            logger.info("→ LINE連携済みのためアクセス許可")
                        else:
                            access_reason = "📱 **このコラムの本文を読むにはLINE連携が必要です**\n\n[マイページからLINE連携を行ってください]"
                            logger.info(f"→ LINE未連携のためアクセス拒否 (user_has_line={user_has_line}, line_user_id存在={user_has_line})")
                    elif actual_access_type == 'paid' or actual_access_type == 'point_required':
                        # ポイント消費コラム
                        required_points = col.get('required_points', 1)

                        # 管理者は無料で閲覧可能
                        if is_admin:
                            can_access = True
                            logger.info("→ 管理者のためポイント消費をスキップ")
                        else:
                            # 既読チェック
                            if user_id:
                                read_check = supabase.table('v2_column_reads').select('id').eq('column_id', col['id']).eq('user_id', user_id).execute()
                                if read_check.data:
                                    # 既読の場合は無料で表示
                                    can_access = True
                                    logger.info(f"→ 既読のためポイント消費なし")
                                elif user_points >= required_points:
                                    # 初回閲覧でポイント十分
                                    can_access = True
                                    points_consumed = False
                                    # ポイント消費処理
                                    try:
                                        # ポイント減算
                                        new_points = user_points - required_points
                                        update_response = supabase.table('v2_user_points').update({
                                            'current_points': new_points,
                                            'updated_at': datetime.now().isoformat()
                                        }).eq('user_id', user_id).execute()

                                        # 既読記録を作成
                                        read_record = supabase.table('v2_column_reads').insert({
                                            'column_id': col['id'],
                                            'user_id': user_id,
                                            'read_at': datetime.now().isoformat()
                                        }).execute()

                                        points_consumed = True
                                        logger.info(f"→ {required_points}ポイント消費して表示")
                                    except Exception as e:
                                        logger.error(f"ポイント消費処理エラー: {str(e)}")
                                        can_access = False
                                        access_reason = "⚠️ **ポイント消費処理でエラーが発生しました**\n\nしばらくしてから再度お試しください。"
                                else:
                                    access_reason = f"💰 **このコラムの本文を読むには{required_points}ポイントが必要です**\n\n現在の残高: {user_points}ポイント\n不足ポイント: {required_points - user_points}ポイント\n\n[ポイントを購入する]"
                    else:
                        # 予期しないaccess_typeの場合
                        logger.error(f"未処理のaccess_type: '{actual_access_type}'")
                        access_reason = f"⚠️ **このコラムのタイプ({actual_access_type})は認識できません**\n\n管理者にお問い合わせください。"

                    if can_access:
                        # ポイント消費メッセージを追加
                        if actual_access_type in ['paid', 'point_required'] and not is_admin:
                            if 'points_consumed' in locals() and points_consumed:
                                columns_html += f"✅ **{required_points}ポイント消費しました**\n\n---\n\n"

                        # contentのHTMLタグを除去
                        content_text = strip_html_tags(col.get('content', ''))
                        columns_html += f"{content_text}\n\n"
                    else:
                        columns_html += f"{access_reason}\n\n"
                content = columns_html
            else:
                content = "このレースには表示するコラムがありません。"

            analysis_data = None
        else:  # viewlogic
            result = await self.process_viewlogic_message(message, race_data, sub_type)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        
        # 表示名の設定
        ai_display_names = {
            'metalogic': 'MetaLogic AI',
            'flogic': 'F-Logic AI',
            'dlogic': 'D-Logic AI',
            'ilogic': 'I-Logic AI',
            'imlogic': 'IMLogic AI',
            'viewlogic': 'ViewLogic AI',
            'column': 'コラムシステム'
        }
        
        # デバッグログ追加
        logger.info(f"最終レスポンス生成: determined_ai={determined_ai}, display_name={ai_display_names.get(determined_ai, 'IMLogic AI')}")

        return {
            'content': content,
            'ai_type': determined_ai,
            'ai_display_name': ai_display_names.get(determined_ai, 'IMLogic AI'),
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
            # メッセージから馬名らしい単語を抽出（全カタカナ文字と英字の連続）
            # ァ-ヴ で全てのカタカナ（小文字含む）とヴをカバー
            potential_horses = re.findall(r'[ァ-ヴー]+|[A-Za-z]+', message)
            
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
                    # ただしコラムは除外
                    if potential_horse == 'コラム':
                        continue  # コラムは馬名ではないのでスキップ

                    if not is_in_race and re.search(f'{potential_horse}(の|は|が|を|と|って|という)', message):
                        # 一般的な単語や助詞でないことを確認
                        common_words = ['データ', 'レース', 'スコア', 'ポイント', 'システム', 'エラー', 'ViewLogic', 'IMLogic', 'DLogic', 'ILogic', 'FLogic', 'フェア', 'オッズ', 'ロジック', 'エフロジック', 'コラム']
                        if potential_horse not in common_words:
                            logger.info(f"レース外の馬を検出: {potential_horse}")
                            return True
        
        return False
    
    async def process_dlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict]]:
        """
        D-Logicメッセージ処理（地方競馬対応版）
        """
        try:
            # D-Logic分析を実行する場合
            if self._should_analyze(message):
                venue = race_data.get('venue', '')
                
                # 地方競馬場の場合は地方競馬版エンジンを使用
                if self._is_local_racing(venue):
                    from services.local_fast_dlogic_engine_v2 import local_fast_dlogic_engine_v2
                    logger.info(f"🏇 地方競馬版D-Logicエンジンを使用: {venue}")
                    
                    # レース情報から馬名を抽出
                    horses = race_data.get('horses', [])
                    if not horses:
                        return ("分析対象の馬が指定されていません。", None)
                    
                    # 地方競馬版D-Logic計算
                    dlogic_result = {}
                    for horse_name in horses:
                        score_data = local_fast_dlogic_engine_v2.raw_manager.calculate_dlogic_realtime(horse_name)
                        if score_data and not score_data.get('error'):
                            # total_scoreをscoreとして使用
                            dlogic_result[horse_name] = {
                                'score': score_data.get('total_score', 0),
                                'data_available': True,
                                'details': score_data
                            }
                        else:
                            dlogic_result[horse_name] = {
                                'score': 0,
                                'data_available': False
                            }
                    
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
                    
                else:
                    # JRA版（既存）
                    from api.v2.dlogic import calculate_dlogic_batch
                    logger.info(f"🏇 JRA版D-Logicエンジンを使用: {venue}")
                    
                    # レース情報から馬名を抽出
                    horses = race_data.get('horses', [])
                    if not horses:
                        return ("分析対象の馬が指定されていません。", None)
                    
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
    
    async def process_flogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        F-Logicメッセージ処理（投資価値判定）
        """
        try:
            # レース情報確認
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            venue = race_data.get('venue')
            race_number = race_data.get('race_number')
            
            # F-Logicの説明要求かどうか判定
            explanation_keywords = ['って何', 'とは', '説明', 'どういう', '何ですか', '教えて']
            is_explanation = any(keyword in message for keyword in explanation_keywords)
            
            if is_explanation:
                explanation = """🎯 F-Logic（Fair Value Logic）について

F-Logicは、競馬における理論的な「フェア値（適正オッズ）」を計算し、市場オッズとの乖離から投資価値を判定するAIシステムです。

【主な機能】
• I-Logicスコアを基にした理論的勝率計算
• フェア値（理論オッズ）の算出
• 市場オッズとの乖離率分析
• 期待値とROI（投資収益率）の計算
• Kelly基準による最適投資比率提案

【投資判定の仕組み】
フェア値 < 市場オッズ → 割安（買い推奨）
フェア値 > 市場オッズ → 割高（見送り推奨）

例：フェア値5.0倍の馬が市場で10.0倍
→ オッズ乖離率2.0倍 = 強い投資価値あり

F-Logic分析をご希望の場合は「F-Logic分析して」とお聞きください。"""
                return (explanation, None)
            
            if not horses:
                return ("F-Logic分析にはレース情報が必要です。", None)
            
            # 分析要求かどうか判定
            analyze_keywords = ['分析', '計算', '判定', '価値', 'オッズ', 'フェア', '期待値']
            should_analyze = any(keyword in message for keyword in analyze_keywords)
            
            if should_analyze:
                # レースデータからオッズを取得
                odds_values = race_data.get('odds', [])
                market_odds = {}
                

                
                # オッズが存在する場合はマッピング
                if odds_values and horses:
                    for i, horse_name in enumerate(horses):
                        if i < len(odds_values):
                            odds_value = odds_values[i]
                            # オッズ値が有効な場合のみ追加
                            if odds_value and odds_value > 0:
                                market_odds[horse_name] = float(odds_value)
                    logger.info(f"F-Logic: market_odds from race_data: {list(market_odds.items())[:3]}")
                    logger.info(f"F-Logic: Total odds mapped: {len(market_odds)}")
                
                # オッズがない場合はodds_managerから取得を試みる（デバッグのため一時的に無効化）
                # if not market_odds:
                #     logger.info("F-Logic: No odds in race_data, trying odds_manager")
                #     from services.odds_manager import odds_manager
                #     market_odds = odds_manager.get_real_time_odds(
                #         venue=venue,
                #         race_number=race_number,
                #         horses=horses
                #     )
                
                # オッズが取得できない場合はエラーメッセージを返す
                if not market_odds:
                    return ("オッズデータが取得できないため、F-Logic分析を実行できません。\n\nF-Logicは市場オッズとフェア値の比較が必要なため、オッズデータがない場合は分析できません。", None)
                
                # F-Logic分析実行
                from services.flogic_engine import flogic_engine
                result = flogic_engine.analyze_race(race_data, market_odds)
                
                if result.get('status') == 'success':
                    content = self._format_flogic_result(result, race_data)
                    
                    # 分析データも返す
                    analysis_data = {
                        'type': 'flogic',
                        'rankings': result.get('rankings', []),
                        'has_market_odds': result.get('has_market_odds', False)
                    }
                    
                    return (content, analysis_data)
                else:
                    return (f"F-Logic分析エラー: {result.get('message', '不明なエラー')}", None)
            else:
                # F-Logicの説明（Claude API不要、直接返答）
                race_context = f"現在選択中: {venue}{race_number}R"
                if horses:
                    race_context += f"（{len(horses)}頭）"
                    
                explanation = f"""🎯 {race_context}

F-Logic（Fair Value Logic）は、理論的な公正オッズと市場オッズを比較して投資価値を判定するシステムです。

【主な機能】
🎯 公正価値計算: I-Logicスコアから理論的な適正オッズを算出
💰 投資価値判定: 市場オッズとの乖離から割安・割高を判定
📊 期待値計算: 投資リターンの期待値とROIを推定

【投資判断基準】
・フェア値 < 市場オッズ = 割安（買い）
・フェア値 > 市場オッズ = 割高（見送り）

分析をご希望の場合は「F-Logic分析して」「投資価値を判定」などとお聞きください。"""
                
                return (explanation, None)
                
        except Exception as e:
            logger.error(f"F-Logic処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return (f"F-Logic分析中にエラーが発生しました: {str(e)}", None)
    
    def _format_flogic_result(self, result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """
        F-Logic分析結果をフォーマット
        """
        try:
            rankings = result.get('rankings', [])
            if not rankings:
                return "F-Logic分析結果が取得できませんでした。"
            
            lines = []
            lines.append(f"🎯 F-Logic 投資価値分析結果")
            lines.append("=" * 40)
            
            # 全馬を投資価値順に出力
            for i, horse in enumerate(rankings, 1):
                # 順位と馬名
                lines.append(f"\n【{i}位】 {horse['horse']}")
                lines.append("-" * 30)
                
                # フェア値と市場オッズ
                lines.append(f"フェア値: {horse['fair_odds']}倍")
                if 'market_odds' in horse:
                    lines.append(f"市場オッズ: {horse['market_odds']}倍")
                    divergence = horse.get('odds_divergence', 0)
                    lines.append(f"オッズ乖離率: {divergence:.2f}倍")
                
                # 投資判断
                signal = horse.get('investment_signal', '評価なし')
                lines.append(f"投資判断: {signal}")
                
                # 期待値とROI
                if 'expected_value' in horse:
                    lines.append(f"期待値: {horse['expected_value']}")
                if 'roi_estimate' in horse:
                    lines.append(f"推定ROI: {horse['roi_estimate']}%")
                
                # I-Logicスコア
                if 'ilogic_score' in horse:
                    # I-Logicスコアは非表示（I-Logicエンジンと重複するため）
                    pass
                
                # 投資価値評価
                if horse.get('odds_divergence', 0) >= 2.0:
                    lines.append("⭐ 【非常に割安】投資価値が高い")
                elif horse.get('odds_divergence', 0) >= 1.5:
                    lines.append("✨ 【割安】良い投資機会")
                elif horse.get('odds_divergence', 0) >= 1.2:
                    lines.append("📊 【やや割安】検討価値あり")
                elif horse.get('odds_divergence', 0) >= 0.8:
                    lines.append("➖ 【適正】投資価値は普通")
                else:
                    lines.append("⚠️ 【割高】投資は見送り推奨")
            
            # 注意事項
            lines.append("\n\n※F-Logicは理論値と市場価格の乖離を分析するものです")
            lines.append("※投資は自己責任でお願いします")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"F-Logic結果フォーマットエラー: {e}")
            return "F-Logic分析結果の表示中にエラーが発生しました。"
    
    async def process_ilogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict]]:
        """
        I-Logicメッセージ処理（地方競馬対応版）
        """
        try:
            # I-Logic分析を実行する場合
            if self._should_analyze(message):
                venue = race_data.get('venue', '')
                
                # 地方競馬場の場合は地方競馬版エンジンを使用
                if self._is_local_racing(venue):
                    from services.local_race_analysis_engine_v2 import local_race_analysis_engine_v2 as local_ilogic_engine_v2
                    logger.info(f"🏇 地方競馬版I-Logicエンジンを使用: {venue}")
                    
                    # レース情報を準備
                    horses = race_data.get('horses', [])
                    jockeys = race_data.get('jockeys', [])
                    
                    if not horses:
                        return ("分析対象の馬が指定されていません。", None)
                    
                    if not jockeys:
                        return ("I-Logic分析には騎手情報が必要です。", None)
                    
                    # 地方競馬版I-Logic計算
                    logger.info(f"地方I-Logic分析開始: horses={horses}, jockeys={jockeys}")
                    result = local_ilogic_engine_v2.analyze_race(race_data)
                    logger.info(f"地方I-Logic分析結果: status={result.get('status')}, scores数={len(result.get('scores', []))}")
                    
                    if result.get('status') == 'success':
                        scores = result.get('scores', [])
                        content = self._format_ilogic_scores_local(scores, race_data)
                        
                        analysis_data = {
                            'type': 'ilogic',
                            'scores': scores,
                            'top_horses': [s['horse'] for s in scores[:5]]
                        }
                        
                        return (content, analysis_data)
                    else:
                        return (f"I-Logic分析に失敗しました: {result.get('message', '不明なエラー')}", None)
                else:
                    # JRA版（既存の処理）
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
            import traceback
            logger.error(f"I-Logic処理エラー: {e}")
            logger.error(f"I-Logicスタックトレース: {traceback.format_exc()}")
            logger.error(f"I-Logicエラー時のrace_data: {race_data}")
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
    
    def _format_betting_recommendations(self, result: Dict[str, Any]) -> str:
        """
        ViewLogic馬券推奨結果をフォーマット（展開予想ベース）
        """
        try:
            lines = []
            lines.append("🎯 ViewLogic推奨馬券")
            lines.append("")
            
            venue = result.get('venue', '不明')
            total_horses = result.get('total_horses', 0)
            top_5_horses = result.get('top_5_horses', [])
            recommendations = result.get('recommendations', [])
            
            lines.append(f"**開催場**: {venue}")
            lines.append(f"**出走頭数**: {total_horses}頭")
            
            # 展開予想の上位5頭を表示
            if top_5_horses:
                lines.append("")
                lines.append("**🏇 ViewLogic展開予想 上位5頭**:")
                for i, horse in enumerate(top_5_horses[:5], 1):
                    lines.append(f"  {i}. {horse}")
            
            lines.append("")
            
            if not recommendations:
                lines.append("⚠️ 推奨馬券を生成できませんでした。")
                return "\n".join(lines)
            
            lines.append("### 📋 推奨馬券")
            lines.append("")
            
            for rec in recommendations:
                rec_type = rec.get('type', '不明')
                ticket_type = rec.get('ticket_type', '馬券')
                horses = rec.get('horses', [])
                confidence = rec.get('confidence', 0)
                investment = rec.get('investment', 0)
                reason = rec.get('reason', '')
                buy_type = rec.get('buy_type', '')
                combinations = rec.get('combinations', 0)
                
                # 推奨馬券のアイコン
                icon_map = {
                    '単勝': '🥇',
                    '馬連BOX': '📦',
                    '3連単流し': '🎯',
                    'ワイド': '🌟',
                    '3連複BOX': '💰'
                }
                icon = icon_map.get(rec_type, '🎪')
                
                lines.append(f"{icon} **{rec_type}**")
                
                # 馬名の表示（複雑な形式に対応）
                if isinstance(horses, dict):
                    # 流し買いの場合（3連単など）
                    if '1着' in horses:
                        lines.append(f"  【{ticket_type}】")
                        lines.append(f"   1着: {', '.join(horses['1着'])}")
                        lines.append(f"   2着: {', '.join(horses['2着'])}")  
                        lines.append(f"   3着: {', '.join(horses['3着'])}")
                    elif '軸' in horses:
                        # ワイドの場合
                        lines.append(f"  【{ticket_type}】 {horses['軸']} 軸")
                        lines.append(f"   相手: {', '.join(horses['相手'])}")
                elif isinstance(horses, list):
                    # 通常のBOX買いまたは単勝
                    if buy_type == 'BOX':
                        lines.append(f"  【{ticket_type}BOX】 {' - '.join(horses)}")
                    else:
                        lines.append(f"  【{ticket_type}】 {' → '.join(horses)}")
                
                # 買い方詳細
                if buy_type and combinations > 0:
                    lines.append(f"   買い方: {buy_type} ({combinations}点買い)")
                
                lines.append(f"   💰 投資額: **{investment:,}円**")
                lines.append(f"   📊 信頼度: {confidence}%")
                if reason:
                    lines.append(f"   💭 {reason}")
                lines.append("")
            
            # 総投資額
            total_investment = sum(rec.get('investment', 0) for rec in recommendations)
            lines.append("---")
            lines.append(f"💵 **総投資額**: {total_investment:,}円")
            
            lines.append("")
            lines.append("※ ViewLogic展開予想の上位馬を基にした推奨馬券です")
            lines.append("※ 投資は自己責任でお願いします")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"馬券推奨フォーマットエラー: {e}")
            import traceback
            traceback.print_exc()
            return "馬券推奨結果の表示中にエラーが発生しました。"
    
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
            lines.append("")
            
            # 全頭を順位付きで表示（I-Logic形式）
            emojis = ['🥇', '🥈', '🥉']
            for i, (horse_name, data) in enumerate(valid_horses):
                # 上位3位まで絵文字、4位以降は数字表示
                if i < 3:
                    rank_display = f"{emojis[i]} {i+1}位:"
                else:
                    rank_display = f"{i+1}位:"
                
                score = data.get('score', 0)
                lines.append(f"{rank_display} {horse_name}: {score:.1f}点")
                
                # 詳細スコアがあれば表示（上位5頭のみ）
                if i < 5 and data.get('details'):
                    details = data['details']
                    # 主要な項目を表示
                    if 'distance_aptitude' in details:
                        lines.append(f"   距離適性: {details['distance_aptitude']:.1f}")
                    if 'bloodline_evaluation' in details:
                        lines.append(f"   血統評価: {details['bloodline_evaluation']:.1f}")
                
                # 次の馬との間に空行を追加（最後の馬以外）
                if i < len(valid_horses) - 1:
                    lines.append("")
                
                # 6位目に区切り線を追加
                if i == 5:
                    lines.append("【6位以下】")
            
            # データがない馬がいる場合の注記
            no_data_horses = [name for name, data in dlogic_result.items() 
                            if not data.get('data_available', False)]
            if no_data_horses:
                lines.append("")
                lines.append("【データ不足】")
                lines.append(f"以下の馬はデータベースにデータがありません:")
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
    
    def _format_ilogic_scores_local(self, scores: List[Dict[str, Any]], race_data: Dict[str, Any]) -> str:
        """地方競馬版I-Logicスコアのフォーマット"""
        venue = race_data.get('venue', '不明')
        race_number = race_data.get('race_number', '不明')
        
        content = f"🎯 I-Logic分析結果\n"
        content += f"{venue} {race_number}R\n\n"
        
        if not scores:
            return content + "分析データがありません。"
        
        # スコア順にソート
        scores.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        # 上位5頭を表示
        for i, score in enumerate(scores[:5], 1):
            horse = score.get('horse', '不明')
            jockey = score.get('jockey', '不明')
            total = score.get('total_score', 0)
            horse_score = score.get('horse_score', 0)
            jockey_score = score.get('jockey_score', 0)
            
            if i == 1:
                content += f"🥇 {i}位: {horse}: {total:.1f}点\n"
            elif i == 2:
                content += f"🥈 {i}位: {horse}: {total:.1f}点\n"
            elif i == 3:
                content += f"🥉 {i}位: {horse}: {total:.1f}点\n"
            else:
                content += f"{i}位: {horse}: {total:.1f}点\n"
            
            content += f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点\n\n"
        
        # 6位以下
        if len(scores) > 5:
            content += "【6位以下】\n"
            for i, score in enumerate(scores[5:], 6):
                horse = score.get('horse', '不明')
                total = score.get('total_score', 0)
                horse_score = score.get('horse_score', 0)
                jockey_score = score.get('jockey_score', 0)
                
                content += f"{i}位: {horse}: {total:.1f}点\n"
                content += f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点\n"
                
                # 次の馬との間に空行を追加（最後の馬以外）
                if i < len(scores) - 1:
                    content += "\n"
        
        return content
    
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
    
    def _format_betting_recommendations(self, result: Dict[str, Any]) -> str:
        """
        ViewLogic馬券推奨結果をフォーマット（展開予想ベース）
        """
        try:
            lines = []
            lines.append("🎯 ViewLogic推奨馬券")
            lines.append("")
            
            venue = result.get('venue', '不明')
            total_horses = result.get('total_horses', 0)
            top_5_horses = result.get('top_5_horses', [])
            recommendations = result.get('recommendations', [])
            
            lines.append(f"**開催場**: {venue}")
            lines.append(f"**出走頭数**: {total_horses}頭")
            
            # 展開予想の上位5頭を表示
            if top_5_horses:
                lines.append("")
                lines.append("**🏇 ViewLogic展開予想 上位5頭**:")
                for i, horse in enumerate(top_5_horses[:5], 1):
                    lines.append(f"  {i}. {horse}")
            
            lines.append("")
            
            if not recommendations:
                lines.append("⚠️ 推奨馬券を生成できませんでした。")
                return "\n".join(lines)
            
            lines.append("### 📋 推奨馬券")
            lines.append("")
            
            for rec in recommendations:
                rec_type = rec.get('type', '不明')
                ticket_type = rec.get('ticket_type', '馬券')
                horses = rec.get('horses', [])
                confidence = rec.get('confidence', 0)
                investment = rec.get('investment', 0)
                reason = rec.get('reason', '')
                buy_type = rec.get('buy_type', '')
                combinations = rec.get('combinations', 0)
                
                # 推奨馬券のアイコン
                icon_map = {
                    '単勝': '🥇',
                    '馬連BOX': '📦',
                    '3連単流し': '🎯',
                    'ワイド': '🌟',
                    '3連複BOX': '💰'
                }
                icon = icon_map.get(rec_type, '🎪')
                
                lines.append(f"{icon} **{rec_type}**")
                
                # 馬名の表示（複雑な形式に対応）
                if isinstance(horses, dict):
                    # 流し買いの場合（3連単など）
                    if '1着' in horses:
                        lines.append(f"  【{ticket_type}】")
                        lines.append(f"   1着: {', '.join(horses['1着'])}")
                        lines.append(f"   2着: {', '.join(horses['2着'])}")  
                        lines.append(f"   3着: {', '.join(horses['3着'])}")
                    elif '軸' in horses:
                        # ワイドの場合
                        lines.append(f"  【{ticket_type}】 {horses['軸']} 軸")
                        lines.append(f"   相手: {', '.join(horses['相手'])}")
                elif isinstance(horses, list):
                    # 通常のBOX買いまたは単勝
                    if buy_type == 'BOX':
                        lines.append(f"  【{ticket_type}BOX】 {' - '.join(horses)}")
                    else:
                        lines.append(f"  【{ticket_type}】 {' → '.join(horses)}")
                
                # 買い方詳細
                if buy_type and combinations > 0:
                    lines.append(f"   買い方: {buy_type} ({combinations}点買い)")
                
                lines.append(f"   💰 投資額: **{investment:,}円**")
                lines.append(f"   📊 信頼度: {confidence}%")
                if reason:
                    lines.append(f"   💭 {reason}")
                lines.append("")
            
            # 総投資額
            total_investment = sum(rec.get('investment', 0) for rec in recommendations)
            lines.append("---")
            lines.append(f"💵 **総投資額**: {total_investment:,}円")
            
            lines.append("")
            lines.append("※ ViewLogic展開予想の上位馬を基にした推奨馬券です")
            lines.append("※ 投資は自己責任でお願いします")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"馬券推奨フォーマットエラー: {e}")
            import traceback
            traceback.print_exc()
            return "馬券推奨結果の表示中にエラーが発生しました。"
    
    def _format_horse_history(self, result: Dict[str, Any], horse_name: str) -> str:
        """馬の過去データをモバイル最適化フォーマットで表示"""
        lines = []
        lines.append(f"🏇 **{horse_name} 過去戦績**")
        lines.append("")
        
        if result["status"] == "success" and result["races"]:
            races = result["races"]
            lines.append(f"📊 **直近{len(races)}戦のデータ**")
            lines.append("")
            
            for i, race in enumerate(races, 1):
                # レース基本情報（新しい絵文字付きキーと旧キーの両方に対応）
                race_date = race.get("📅 開催日", race.get("開催日", "不明"))
                venue = race.get("🏟️ 競馬場", race.get("競馬場", "不明"))
                race_name = race.get("🏁 レース", race.get("レース", ""))
                class_name = race.get("🏆 クラス", race.get("クラス", ""))
                distance = race.get("📏 距離", race.get("距離", "不明"))
                track = race.get("🌤️ 馬場", race.get("馬場", ""))
                
                # 血統情報の取得
                sire = race.get("🐴 父", race.get("父", ""))
                broodmare_sire = race.get("🐎 母父", race.get("母父", ""))
                
                # 日付フォーマットの改善（例: 2025/0608 → 2025/06/08）
                if race_date != "不明" and len(race_date) == 9 and "/" in race_date:
                    parts = race_date.split("/")
                    if len(parts) == 2 and len(parts[1]) == 4:
                        year = parts[0]
                        month = parts[1][:2]
                        day = parts[1][2:]
                        race_date = f"{year}/{month}/{day}"
                
                # レース名とクラス名の表示（どちらか一方でも表示）
                if race_name or class_name:
                    # レース名とクラス名の組み合わせを適切に処理
                    if race_name and class_name:
                        race_display = f"{race_name}（{class_name}）"
                    elif race_name:
                        race_display = race_name
                    else:  # class_nameのみの場合
                        race_display = class_name
                    lines.append(f"**{i}. {race_date} {venue} {race_display}**")
                else:
                    # レース名もクラス名もない場合はレース番号のみ
                    race_num = race.get("🏁 レース", race.get("レース", ""))
                    if race_num:
                        lines.append(f"**{i}. {race_date} {venue} {race_num}**")
                    else:
                        lines.append(f"**{i}. {race_date} {venue}**")
                
                # 距離と馬場（馬場が空の場合は「-」を表示）
                track_display = track if track else "-"
                lines.append(f"　📏 距離: {distance} / 馬場: {track_display}")
                
                # 成績情報（新しい絵文字付きキーと旧キーの両方に対応）
                chakujun = race.get("🥇 着順", race.get("着順", ""))
                # "11着" のような形式から数字部分を抽出
                if chakujun and "着" in str(chakujun):
                    chakujun = str(chakujun).replace("着", "")
                # 先頭の0を削除（"02" → "2"）
                if chakujun and str(chakujun).startswith("0") and len(str(chakujun)) > 1:
                    chakujun = str(chakujun).lstrip("0")
                
                if chakujun and str(chakujun) != "":
                    # 1-3着は強調表示
                    if str(chakujun) in ["1", "2", "3"]:
                        chakujun_display = f"**🏆 {chakujun}着**"
                    else:
                        chakujun_display = f"{chakujun}着"
                else:
                    chakujun_display = "-"
                
                popularity = race.get("📊 人気", race.get("人気", ""))
                # "10番人気" のような形式から数字部分を抽出
                if popularity and "番人気" in str(popularity):
                    popularity = str(popularity).replace("番人気", "")
                if popularity and str(popularity) != "":
                    popularity_display = f"{popularity}番人気"
                else:
                    popularity_display = "-"
                
                lines.append(f"　📊 着順: {chakujun_display} / 人気: {popularity_display}")
                
                # タイムと上り（新しい絵文字付きキーと旧キーの両方に対応）
                time_result = race.get("⏱️ タイム", race.get("タイム", ""))
                agari = race.get("🏃 上り", race.get("上り", ""))
                
                # タイムの表示改善（例: 1588 → 1:58.8）
                time_display = "-"
                if time_result and str(time_result).isdigit():
                    time_str = str(time_result)
                    if len(time_str) == 4:  # 1588のような形式
                        time_display = f"{time_str[0]}:{time_str[1:3]}.{time_str[3]}"
                    elif len(time_str) == 3:  # 589のような形式（1分未満）
                        time_display = f"0:{time_str[0:2]}.{time_str[2]}"
                    else:
                        time_display = time_result
                elif time_result:
                    time_display = time_result
                
                # 上りの表示改善（例: 334 → 33.4）
                agari_display = "-"
                if agari and str(agari) != "":
                    agari_str = str(agari).replace("秒", "")  # "334秒"から"秒"を削除
                    try:
                        if agari_str.isdigit():
                            agari_int = int(agari_str)
                            if agari_int > 100:  # 334のような形式の場合
                                agari_display = f"{agari_int/10:.1f}秒"
                            else:
                                agari_display = f"{agari_int:.1f}秒"
                        else:
                            agari_float = float(agari_str)
                            if agari_float > 100:  # 343.0のような形式の場合
                                agari_display = f"{agari_float/10:.1f}秒"
                            else:
                                agari_display = f"{agari_float:.1f}秒"
                    except:
                        agari_display = str(agari) if agari else "-"
                
                lines.append(f"　⏱ タイム: {time_display} / 上り: {agari_display}")
                
                # 血統情報を表示
                if sire or broodmare_sire:
                    bloodline_parts = []
                    if sire and sire != "不明":
                        bloodline_parts.append(f"父: {sire}")
                    if broodmare_sire and broodmare_sire != "不明":
                        bloodline_parts.append(f"母父: {broodmare_sire}")
                    if bloodline_parts:
                        lines.append(f"　🧬 血統: {' / '.join(bloodline_parts)}")
                
                # レース名があれば追加（注：これは別のレース名フィールド）
                extra_race_name = race.get("レース名", "")
                if extra_race_name and extra_race_name != race_name:  # 重複を避ける
                    lines.append(f"　📋 {extra_race_name}")
                
                # 騎手名があれば追加  
                jockey = race.get("🏇 騎手", race.get("騎手", ""))
                if jockey:
                    lines.append(f"　🏇 騎手: {jockey}")
                
                lines.append("")
            
            # 統計情報
            # 2024-09-11: 地方競馬版の勝率・複勝率計算にバグがあるため一時的にコメントアウト
            # TODO: 計算ロジック修正後に復活させる
            """
            total_races = result.get("total_races", len(races))
            if total_races > 0:
                lines.append("📈 **戦績サマリー**")
                lines.append(f"　総戦数: {total_races}戦")
                
                # 着順分析（整数型と文字列型、絵文字付きキーの両方に対応）
                win_count = 0
                place_count = 0
                valid_races = []
                
                for r in races:
                    # 着順データを取得（新旧両方のキーに対応）
                    chakujun = r.get("🥇 着順", r.get("着順", ""))
                    # "11着" のような形式から数字部分を抽出
                    if chakujun and "着" in str(chakujun):
                        chakujun = str(chakujun).replace("着", "")
                    
                    # 有効な着順データかチェック
                    if chakujun and str(chakujun).isdigit():
                        valid_races.append({"着順": int(chakujun)})
                        if str(chakujun) == "1":
                            win_count += 1
                        if str(chakujun) in ["1", "2", "3"]:
                            place_count += 1
                if valid_races:
                    win_rate = (win_count / len(valid_races)) * 100
                    place_rate = (place_count / len(valid_races)) * 100
                    lines.append(f"　🥇 勝率: {win_rate:.1f}% ({win_count}/{len(valid_races)})")
                    lines.append(f"　🏅 複勝率: {place_rate:.1f}% ({place_count}/{len(valid_races)})")
                    
                    # 平均着順
                    avg_position = sum(int(r.get("着順")) for r in valid_races) / len(valid_races)
                    lines.append(f"　📊 平均着順: {avg_position:.1f}着")
                else:
                    lines.append("　※ 着順データが不足しています")
            """
        
        else:
            lines.append("❌ **データが見つかりません**")
            lines.append(f"　{horse_name}の過去戦績データが存在しないか、")
            lines.append("　データベースから取得できませんでした。")
        
        return "\n".join(lines)
    
    def _format_jockey_history(self, result: Dict[str, Any], jockey_name: str) -> str:
        """騎手の過去データをモバイル最適化フォーマットで表示"""
        lines = []
        lines.append(f"👤 **{jockey_name}騎手 データ**")
        lines.append("")
        
        if result["status"] == "success" and result.get("statistics"):
            stats = result["statistics"]
            
            # 総合成績を表示
            lines.append("📈 **総合成績（直近データ）**")
            total_races = stats.get('total_races', 0)
            place_rate = stats.get('place_rate', 0)
            
            if total_races > 0:
                lines.append(f"　分析対象: {total_races}戦")
                lines.append(f"　複勝率: {place_rate:.1f}%")
            else:
                lines.append("　分析対象: 0戦")
            lines.append("")
            
            # 場所別成績（地方競馬版の特徴）
            if stats.get('top_venues'):
                lines.append("🏟️ **主な競馬場別成績**")
                for venue_stat in stats['top_venues']:
                    lines.append(f"　{venue_stat}")
                lines.append("")
            
            # recent_ridesからデータ表示（出走数が0でない場合のみ表示）
            if result.get("recent_rides"):
                lines.append("🏟️ **競馬場・距離別成績（直近データ）**")
                displayed_any = False
                
                for ride in result["recent_rides"]:
                    venue = ride.get("競馬場", "不明")
                    distance = ride.get("距離", "不明")
                    runs = ride.get("出走数", 0)
                    fukusho_rate = ride.get("複勝率", "0.0%")
                    
                    # 出走数が0でない場合のみ表示
                    if runs > 0:
                        # 騎手ナレッジファイルは直近5戦のみ保持
                        display_runs = f"直近{runs}戦" if runs <= 5 else f"{runs}戦"
                        lines.append(f"　{venue}{distance}: {display_runs} 複勝率{fukusho_rate}")
                        displayed_any = True
                
                if not displayed_any:
                    lines.append("　データなし")
                lines.append("")
            
            # 統計情報から馬場状態別成績
            if stats.get("馬場別成績"):
                lines.append("🌧️ **馬場状態別成績（直近データ）**")
                track_stats = stats["馬場別成績"]
                
                # 重複を除去して表示
                seen_conditions = set()
                for track_data in track_stats:
                    condition = track_data.get("馬場", "不明")
                    rate = track_data.get("複勝率", "0.0%")
                    
                    # 「平地・芝」など同じ条件は1回だけ表示
                    if condition not in seen_conditions:
                        lines.append(f"　{condition}: 複勝率{rate}")
                        seen_conditions.add(condition)
                
                lines.append("")
            
            # 枠順別成績
            if stats.get("枠順別成績"):
                lines.append("🎯 **枠順別成績（直近データ）**")
                post_stats = stats["枠順別成績"]
                
                for post_data in post_stats:
                    post = post_data.get("枠", "不明")
                    rate = post_data.get("複勝率", "0.0%")
                    lines.append(f"　{post}: 複勝率{rate}")
                
                lines.append("")
            
            # 総合統計は既に上部で表示済みのため、ここでは表示しない

        
        else:
            lines.append("❌ **データが見つかりません**")
            lines.append(f"　{jockey_name}騎手のデータが存在しないか、")
            lines.append("　データベースから取得できませんでした。")
        
        return "\n".join(lines)
    
    def _get_viewlogic_5race_guide(self, race_data: Dict[str, Any]) -> str:
        """ViewLogic５走の使い方案内メッセージ"""
        venue = race_data.get('venue', '')
        race_number = race_data.get('race_number', '')
        
        lines = []
        lines.append("🏇 **ViewLogic５走の使い方**")
        lines.append("")
        lines.append(f"**{venue}{race_number}R**に出走する**馬名**または**騎手名**を1つだけ入力してください。")
        lines.append("")
        lines.append("📊 **出力データ**")
        lines.append("• ナレッジデータベースから**直近5走**の詳細データを表示")
        lines.append("• レース結果、着順、タイム、条件等の履歴情報")
        lines.append("• 成績分析（勝率、複勝率、平均着順）")
        lines.append("")
        lines.append("💡 **入力例**")
        lines.append("• 馬名のみ：「ドウデュース」")
        lines.append("• 騎手名のみ：「武豊」")
        lines.append("• フルネーム：「北村友一の過去5走」")
        lines.append("")
        lines.append("⚠️ **注意事項**")
        lines.append("• **1回の入力で1つの対象のみ**分析可能")
        lines.append("• 複数の馬名や騎手名を同時に入力すると反応しません")
        lines.append("• このレースに出走しない馬・騎手は分析できません")
        lines.append("")
        lines.append("🔄 **データ更新**")
        lines.append("• ナレッジデータベースは**毎月第一月曜日**に更新")
        lines.append("• 最新の競走結果が反映されています")
        lines.append("")
        lines.append("✨ さっそく馬名または騎手名を1つ入力して試してみてください！")

        return "\n".join(lines)

    def _generate_sire_analysis(self, race_data: Dict[str, Any]) -> Tuple[str, Optional[Dict]]:
        """
        種牡馬分析を生成
        出走馬の父、母、母父を表示 + 産駒成績を追加

        Returns:
            (content, analysis_data) のタプル
        """
        try:
            venue = race_data.get('venue', '')
            race_number = race_data.get('race_number', '')
            horses = race_data.get('horses', [])
            distance = race_data.get('distance', '')

            # 地方競馬かどうかを判定
            is_local = self._is_local_racing(venue)

            # 統合ナレッジファイルからデータを取得
            # 初期化済みのDLogicマネージャーを使用（高速化）
            dlogic_manager = self.dlogic_manager

            lines = []
            lines.append("**血統分析**")
            lines.append(f"【{venue} {race_number}R】")
            lines.append("")

            # SirePerformanceAnalyzerから産駒成績を取得する準備
            venue_code = None
            if not is_local and distance:  # JRAの場合のみ産駒成績を表示
                # 会場コードマッピング
                venue_codes = {
                    '札幌': '01', '函館': '02', '福島': '03', '新潟': '04',
                    '東京': '05', '中山': '06', '中京': '07', '京都': '08',
                    '阪神': '09', '小倉': '10'
                }
                venue_code = venue_codes.get(venue, '')
                # 距離を文字列に変換（例: 2400m → '2400'）
                if isinstance(distance, str) and distance.endswith('m'):
                    distance = distance[:-1]
                distance = str(distance)

            # 各馬の血統データを取得
            for i, horse in enumerate(horses):
                horse_number = i + 1

                # 馬名を取得（辞書形式と文字列形式の両方に対応）
                if isinstance(horse, dict):
                    horse_name = horse.get('馬名', horse.get('name', ''))
                else:
                    horse_name = str(horse)

                if not horse_name:
                    continue

                # 血統データを取得
                pedigree_data = self._get_horse_pedigree(dlogic_manager, horse_name)

                # 馬番をシンプルな数字表記に

                # フォーマット出力
                lines.append(f"【{horse_number}番】 **{horse_name}**")

                if pedigree_data:
                    sire = pedigree_data.get('sire', 'データなし')
                    dam = pedigree_data.get('dam', None)
                    broodmare_sire = pedigree_data.get('broodmare_sire', 'データなし')

                    lines.append(f"  ◆ 父　：{sire}")
                    if dam and dam != '':
                        lines.append(f"  ◆ 母　：{dam}")
                    lines.append(f"  ◆ 母父：{broodmare_sire}")

                    # 血統情報と産駒成績を見やすく分離
                    lines.append("")

                    # 産駒成績を追加（SirePerformanceAnalyzerを使用）
                    if venue_code and distance and self.sire_analyzer:
                        try:
                            # 父の産駒成績を取得
                            if sire and sire != 'データなし':
                                sire_perf = self.sire_analyzer.analyze_sire_performance(
                                    sire, venue_code, distance
                                )
                                if 'message' not in sire_perf:
                                    lines.append(f"    └ 父 {venue}{distance}m成績: {sire_perf['total_races']}戦{sire_perf['wins']}勝 複勝率{sire_perf['place_rate']:.1f}%")
                                    # 馬場状態別を追加（0戦のデータは表示しない）
                                    if sire_perf.get('by_condition'):
                                        for cond in sire_perf['by_condition']:
                                            # 0戦のデータは表示しない
                                            if cond['races'] > 0:
                                                lines.append(f"      {cond['condition']}: {cond['races']}戦{cond['wins']}勝 複勝率{cond['place_rate']:.1f}%")

                            # 空行を追加（父と母父の成績を見やすく分離）
                            lines.append("")

                            # 母父の産駒成績を取得
                            if broodmare_sire and broodmare_sire != 'データなし':
                                bm_perf = self.sire_analyzer.analyze_broodmare_sire_performance(
                                    broodmare_sire, venue_code, distance
                                )
                                if 'message' not in bm_perf:
                                    lines.append(f"    └ 母父 {venue}{distance}m成績: {bm_perf['total_races']}戦{bm_perf['wins']}勝 複勝率{bm_perf['place_rate']:.1f}%")
                                    # 馬場状態別を追加（0戦のデータは表示しない）
                                    if bm_perf.get('by_condition'):
                                        for cond in bm_perf['by_condition']:
                                            # 0戦のデータは表示しない
                                            if cond['races'] > 0:
                                                lines.append(f"      {cond['condition']}: {cond['races']}戦{cond['wins']}勝 複勝率{cond['place_rate']:.1f}%")

                        except Exception as e:
                            logger.debug(f"産駒成績取得エラー（{horse_name}）: {e}")
                            # エラーは無視（基本の血統表示は維持）

                else:
                    lines.append("  － 血統データなし")

                lines.append("")  # 1行空ける

            content = "\n".join(lines)

            # 分析データも返す（将来的な拡張用）
            analysis_data = {
                'venue': venue,
                'race_number': race_number,
                'type': 'sire_analysis',
                'horses_count': len(horses)
            }

            return (content, analysis_data)

        except Exception as e:
            logger.error(f"種牡馬分析エラー: {e}")
            return (f"種牡馬分析中にエラーが発生しました: {str(e)}", None)

    def _get_horse_pedigree(self, dlogic_manager, horse_name: str) -> Optional[Dict[str, str]]:
        """
        統合ナレッジファイルから馬の血統データを取得

        Args:
            dlogic_manager: DLogicRawDataManager インスタンス
            horse_name: 馬名

        Returns:
            血統データの辞書 {'sire': 父名, 'dam': 母名, 'broodmare_sire': 母父名}
        """
        try:
            # 馬の過去データを取得
            horse_data = dlogic_manager.get_horse_raw_data(horse_name)

            if not horse_data or 'races' not in horse_data:
                logger.warning(f"馬データが見つかりません: {horse_name}")
                return None

            # 最新のレースから血統データを取得
            races = horse_data.get('races', [])
            if not races:
                return None

            # 最新レースのデータを使用
            latest_race = races[0]

            # フィールド29, 30, 31から血統データを取得
            pedigree = {
                'sire': latest_race.get('sire', latest_race.get('29', 'データなし')),
                'dam': latest_race.get('dam', latest_race.get('30', '')),
                'broodmare_sire': latest_race.get('broodmare_sire', latest_race.get('31', 'データなし'))
            }

            # 空文字の場合はNoneに変換
            if pedigree['dam'] == '':
                pedigree['dam'] = None

            return pedigree

        except Exception as e:
            logger.error(f"血統データ取得エラー ({horse_name}): {e}")
            return None
