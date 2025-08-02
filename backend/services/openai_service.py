import os
import logging
from typing import Dict, Any, List
from fastapi import HTTPException
from config import OPENAI_API_KEY, OPENAI_MODEL, DEBUG
from services.enhanced_knowledge_base import enhanced_knowledge_base

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        if not self.api_key or self.api_key == "dummy_key":
            logger.warning("OPENAI_API_KEY not found in environment variables")
            self.api_key = "dummy_key"  # 開発用ダミーキー
        
        self.model = OPENAI_MODEL
    
    async def chat_completion(self, messages: List[Dict[str, str]], system_prompt: str = None) -> str:
        """OpenAI Chat Completions APIを使用してチャット応答を生成"""
        try:
            # システムプロンプトを追加
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
            
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.acreate(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # 開発用フォールバック応答
            return self._get_fallback_response(messages[-1]["content"] if messages else "")
    
    def _get_fallback_response(self, user_message: str) -> str:
        """開発用フォールバック応答"""
        if "指数" in user_message or "Dロジック" in user_message:
            return "Dロジック指数の計算を開始します。レース情報を取得して、12項目の多角的評価を行います。"
        elif "レース" in user_message:
            return "本日のレース情報を確認いたします。どのレースの指数をお求めでしょうか？"
        else:
            return "競馬予想について何でもお聞きください。本日のレースの指数を出したい場合は「本日の東京3Rの指数を出して」のようにお聞きください。"
    
    async def generate_race_analysis(self, race_info: Dict[str, Any], d_logic_result: Dict[str, Any] = None) -> str:
        """レース分析の自然言語説明を生成"""
        try:
            system_prompt = """あなたは競馬予想の専門家です。以下の情報を基に、分かりやすく自然な日本語でレース分析を提供してください。

分析のポイント：
- レースの特徴（距離、馬場状態、出走頭数など）
- 注目馬の紹介
- 予想の根拠
- Dロジック指数がある場合は、その結果を自然に組み込む

回答は親しみやすく、専門的すぎない表現でお願いします。"""

            user_message = f"""
レース情報：
- 競馬場: {race_info.get('keibajo_name', '不明')}
- レース番号: {race_info.get('race_bango', '不明')}
- 距離: {race_info.get('kyori', '不明')}m
- 出走頭数: {race_info.get('shusso_tosu', '不明')}頭
- 馬場状態: {race_info.get('track_condition', '不明')}
- 天候: {race_info.get('weather', '不明')}

Dロジック分析結果: {d_logic_result if d_logic_result else '未計算'}
"""

            messages = [
                {"role": "user", "content": user_message}
            ]
            
            return await self.chat_completion(messages, system_prompt)
            
        except Exception as e:
            logger.error(f"Race analysis generation error: {e}")
            return "レース分析を生成中です。Dロジック指数の計算結果と合わせて詳細な分析をお届けします。"
    
    async def generate_d_logic_explanation(self, d_logic_result: Dict[str, Any]) -> str:
        """Dロジック結果の自然言語説明を生成（Phase D最強馬ナレッジベース活用）"""
        try:
            # Phase D ナレッジベースコンテキスト取得
            knowledge_context = enhanced_knowledge_base.get_context_for_llm_prompt()
            
            system_prompt = f"""あなたは競馬予想の専門家です。以下のPhase D最強馬ナレッジベースを活用して、Dロジック指数の結果を分かりやすく説明してください。

{knowledge_context}

説明のポイント：
- 総合指数の意味（ダンスインザダーク基準100点）
- 上位馬の特徴と類似する伝説馬との比較
- 12項目D-Logic分析結果の詳細解説
- Phase D分析による科学的根拠
- 予想の信頼度と的中可能性

959,620レコード・109,426頭・71年間の日本競馬史上最大規模データベースから導出された結果であることを強調してください。"""

            # Dロジック結果を詳細分析
            horses_info = ""
            legendary_comparison = ""
            
            if 'horses' in d_logic_result:
                legendary_horses = enhanced_knowledge_base.get_legendary_horses()
                
                for i, horse in enumerate(d_logic_result['horses'][:3]):  # 上位3頭
                    horse_name = horse.get('horse_name', '不明')
                    score = horse.get('total_score', 0)
                    grade = horse.get('grade', '')
                    analysis_source = horse.get('analysis_source', '')
                    
                    horses_info += f"\n{i+1}位: {horse_name} - 指数{score:.1f}点 ({grade})"
                    horses_info += f"\n    分析元: {analysis_source}"
                    
                    # 伝説馬との比較
                    if horse_name in legendary_horses:
                        legendary_data = legendary_horses[horse_name]
                        specialties = horse.get('specialties', [])
                        win_rate = horse.get('horse_stats', {}).get('win_rate', 0)
                        
                        legendary_comparison += f"\n📊 {horse_name}は伝説の最強馬データベースに収録済み（勝率{win_rate:.1f}%）"
                        if specialties:
                            legendary_comparison += f"\n   特徴: {', '.join(specialties[:2])}"

            user_message = f"""
Phase D完全分析結果：
- 分析規模: {d_logic_result.get('sql_data_utilization', '959,620レコード・109,426頭・71年間')}
- 計算方法: {d_logic_result.get('calculation_method', 'ダンスインザダーク基準100点・12項目D-Logic')}
- 基準馬: {d_logic_result.get('base_horse', 'ダンスインザダーク')}
- 基準スコア: {d_logic_result.get('base_score', 100)}点

上位馬の詳細指数{horses_info}

伝説馬との比較{legendary_comparison}

この結果を、Phase D最強馬ナレッジベースと照らし合わせて詳しく解説してください。
"""

            messages = [
                {"role": "user", "content": user_message}
            ]
            
            return await self.chat_completion(messages, system_prompt)
            
        except Exception as e:
            logger.error(f"D-logic explanation generation error: {e}")
            return "Dロジック指数の計算が完了しました。詳細な分析結果をご確認ください。"

# グローバルインスタンス
openai_service = OpenAIService() 