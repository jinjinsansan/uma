from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from services.openai_service import openai_service
from services.today_race_fetcher import today_race_fetcher
from services.integrated_d_logic_calculator import d_logic_calculator

router = APIRouter(prefix="/api/chat", tags=["Chat"])

logger = logging.getLogger(__name__)

@router.post("/message")
async def chat_message(request: Dict[str, Any]):
    """チャットメッセージを処理し、OpenAI応答を生成"""
    try:
        user_message = request.get("message", "")
        chat_history = request.get("history", [])
        
        logger.info(f"Chat message received: {user_message}")
        
        # 馬名直接入力を最優先でチェック
        horse_name = extract_horse_name(user_message)
        if horse_name:
            return await handle_horse_analysis_message(user_message, horse_name, chat_history)
        
        # レース関連のキーワードをチェック
        if any(keyword in user_message for keyword in ["Dロジック", "レース", "東京", "京都", "阪神"]):
            return await handle_race_related_message(user_message, chat_history)
        
        return await handle_general_message(user_message, chat_history)
            
    except Exception as e:
        logger.error(f"Chat message processing error: {e}")
        raise HTTPException(status_code=500, detail="チャット処理中にエラーが発生しました")

async def handle_race_related_message(user_message: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """レース関連メッセージの処理"""
    try:
        # レース検索
        race_keyword = extract_race_keyword(user_message)
        if race_keyword:
            matching_races = await today_race_fetcher.search_race_by_keyword(race_keyword)
            
            if matching_races:
                if len(matching_races) == 1:
                    # 単一レースの場合、Dロジック計算を提案
                    race = matching_races[0]
                    race_detail = await today_race_fetcher.get_race_detail(race["race_code"])
                    
                    # Dロジック計算
                    d_logic_result = await calculate_d_logic(race_detail)
                    
                    # OpenAIで自然言語説明を生成
                    explanation = await openai_service.generate_d_logic_explanation(d_logic_result)
                    
                    return {
                        "status": "success",
                        "message": explanation,
                        "race_info": race,
                        "d_logic_result": d_logic_result,
                        "has_d_logic": True
                    }
                else:
                    # 複数レースの場合、選択を促す
                    races_info = "\n".join([f"- {r['keibajo_name']}{r['race_bango']} {r['kyosomei_hondai']}" for r in matching_races])
                    response = f"以下のレースが見つかりました。どのレースの指数をお求めでしょうか？\n{races_info}"
                    
                    return {
                        "status": "success",
                        "message": response,
                        "matching_races": matching_races,
                        "has_d_logic": False
                    }
            else:
                # レースが見つからない場合
                response = await openai_service.chat_completion([
                    {"role": "user", "content": f"「{race_keyword}」に該当するレースが見つかりませんでした。本日の開催レースをご確認ください。"}
                ])
                
                return {
                    "status": "success",
                    "message": response,
                    "has_d_logic": False
                }
        else:
            # 一般的なレース関連の質問
            response = await openai_service.chat_completion([
                {"role": "user", "content": user_message}
            ])
            
            return {
                "status": "success",
                "message": response,
                "has_d_logic": False
            }
            
    except Exception as e:
        logger.error(f"Race related message handling error: {e}")
        return {
            "status": "error",
            "message": "レース情報の処理中にエラーが発生しました。もう一度お試しください。",
            "has_d_logic": False
        }

async def handle_general_message(user_message: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """一般的なメッセージの処理"""
    try:
        # チャット履歴をOpenAI形式に変換
        messages = []
        for msg in chat_history[-5:]:  # 最新5件のみ使用
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # 現在のメッセージを追加
        messages.append({"role": "user", "content": user_message})
        
        # OpenAI応答を生成
        response = await openai_service.chat_completion(messages)
        
        return {
            "status": "success",
            "message": response,
            "has_d_logic": False
        }
        
    except Exception as e:
        logger.error(f"General message handling error: {e}")
        return {
            "status": "error",
            "message": "メッセージの処理中にエラーが発生しました。",
            "has_d_logic": False
        }

async def handle_horse_analysis_message(user_message: str, horse_name: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """馬名直接入力による分析メッセージの処理"""
    try:
        logger.info(f"Horse analysis requested for: {horse_name}")
        
        # Phase D統合D-Logic計算エンジンを初期化
        await d_logic_calculator.initialize()
        
        # 馬データ作成
        horse_data = {"horse_name": horse_name}
        
        # D-Logic分析実行
        analysis_result = d_logic_calculator.calculate_d_logic_score(horse_data)
        
        # 分析結果をチャット用に整形
        d_logic_result = {
            "status": "success",
            "calculation_method": "Phase D統合・ダンスインザダーク基準100点・12項目D-Logic",
            "base_horse": "ダンスインザダーク",
            "base_score": 100,
            "sql_data_utilization": "959,620レコード・109,426頭・71年間完全データベース",
            "horses": [analysis_result],
            "horse_name": horse_name,
            "analysis_type": "単体馬分析"
        }
        
        # OpenAIで自然言語説明を生成
        explanation = await openai_service.generate_d_logic_explanation(d_logic_result)
        
        return {
            "status": "success",
            "message": explanation,
            "horse_name": horse_name,
            "d_logic_result": d_logic_result,
            "has_d_logic": True,
            "analysis_type": "horse_direct_analysis"
        }
        
    except Exception as e:
        logger.error(f"Horse analysis message handling error: {e}")
        return {
            "status": "error", 
            "message": f"馬「{horse_name}」の分析中にエラーが発生しました。もう一度お試しください。",
            "has_d_logic": False
        }

def extract_race_keyword(message: str) -> str:
    """メッセージからレースキーワードを抽出"""
    import re
    
    # 数字+Rのパターン
    race_pattern = re.search(r'(\d+R)', message)
    if race_pattern:
        return race_pattern.group(1)
    
    # 数字のみの場合
    number_pattern = re.search(r'(\d+)', message)
    if number_pattern:
        return number_pattern.group(1) + "R"
    
    return None

def extract_horse_name(message: str) -> str:
    """メッセージから馬名を抽出"""
    import re
    
    # 馬名を示すキーワードパターン
    horse_indicators = ["の指数", "はどう", "について", "を分析", "の分析", "の成績", "のスコア"]
    
    for indicator in horse_indicators:
        if indicator in message:
            # インジケーターの前の部分を馬名として抽出
            parts = message.split(indicator)
            if len(parts) > 0:
                potential_horse_name = parts[0].strip()
                # 不要な文字を除去
                potential_horse_name = re.sub(r'^[「『]', '', potential_horse_name)
                potential_horse_name = re.sub(r'[」』]$', '', potential_horse_name)
                
                # 3文字以上の場合のみ馬名とみなす
                if len(potential_horse_name) >= 3:
                    return potential_horse_name
    
    # カタカナの連続（馬名の可能性が高い）
    katakana_pattern = re.search(r'[ア-ヴー]{3,}', message)
    if katakana_pattern:
        return katakana_pattern.group(0)
    
    # ひらがな+カタカナの混合馬名
    mixed_pattern = re.search(r'[あ-んア-ヴー]{3,}', message)
    if mixed_pattern:
        potential_name = mixed_pattern.group(0)
        # 一般的でない組み合わせのみ馬名とする
        if not any(common in potential_name for common in ["です", "ます", "でしょう", "ですか", "どう"]):
            return potential_name
    
    return None

async def calculate_d_logic(race_detail: Dict[str, Any]) -> Dict[str, Any]:
    """Dロジック計算を実行"""
    try:
        if not race_detail or "horses" not in race_detail:
            return {"error": "レース詳細情報が不足しています"}
        
        # Phase D統合D-Logic計算エンジンを初期化
        await d_logic_calculator.initialize()
        
        # レース全馬一括計算（Phase D最新エンジン使用）
        horses_results = await d_logic_calculator.batch_calculate_race(race_detail.get("horses", []))
        
        # 計算サマリー作成
        calculation_summary = d_logic_calculator.get_calculation_summary(horses_results)
        
        return {
            "status": "success",
            "race_code": race_detail.get("race_code"),
            "calculation_method": "Phase D統合・ダンスインザダーク基準100点・12項目D-Logic",
            "base_horse": "ダンスインザダーク",
            "base_score": 100,
            "sql_data_utilization": "959,620レコード・109,426頭・71年間完全データベース",
            "horses": horses_results,
            "calculation_summary": calculation_summary,
            "phase_d_features": {
                "legendary_horses_analyzed": calculation_summary.get("legendary_horses_count", 0),
                "mysql_complete_analysis": calculation_summary.get("mysql_analysis_count", 0),
                "database_scale": "日本競馬史上最大規模",
                "analysis_accuracy": "最高精度"
            }
        }
        
    except Exception as e:
        logger.error(f"D-logic calculation error: {e}")
        return {"error": f"Dロジック計算中にエラーが発生しました: {str(e)}"} 