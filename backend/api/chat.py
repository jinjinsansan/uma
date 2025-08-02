from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from services.openai_service import openai_service
from services.today_race_fetcher import today_race_fetcher
from services.knowledge_base import d_logic_calculator

router = APIRouter(prefix="/api/chat", tags=["Chat"])

logger = logging.getLogger(__name__)

@router.post("/message")
async def chat_message(request: Dict[str, Any]):
    """チャットメッセージを処理し、OpenAI応答を生成"""
    try:
        user_message = request.get("message", "")
        chat_history = request.get("history", [])
        
        logger.info(f"Chat message received: {user_message}")
        
        # レース関連のキーワードをチェック
        if any(keyword in user_message for keyword in ["指数", "Dロジック", "レース", "東京", "京都", "阪神"]):
            return await handle_race_related_message(user_message, chat_history)
        else:
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

async def calculate_d_logic(race_detail: Dict[str, Any]) -> Dict[str, Any]:
    """Dロジック計算を実行"""
    try:
        if not race_detail or "horses" not in race_detail:
            return {"error": "レース詳細情報が不足しています"}
        
        # Dロジック計算エンジンを初期化
        await d_logic_calculator.initialize()
        
        # 各馬のDロジック指数計算
        horses_results = []
        
        for horse in race_detail.get("horses", []):
            horse_result = d_logic_calculator.calculate_d_logic_score(horse)
            horses_results.append({
                "horse_id": horse.get("horse_id"),
                "horse_name": horse.get("horse_name"),
                "d_logic_score": horse_result.get("total_score", 0),
                "detailed_analysis": horse_result
            })
        
        # 結果をスコア順にソート
        horses_results.sort(key=lambda x: x["d_logic_score"], reverse=True)
        
        return {
            "status": "success",
            "race_code": race_detail.get("race_code"),
            "calculation_method": "多次元Dロジック計算エンジン",
            "base_horse": "ダンスインザダーク",
            "base_score": 100,
            "sql_data_utilization": "12項目の多角的評価",
            "horses": horses_results,
            "calculation_summary": {
                "total_horses": len(horses_results),
                "average_score": sum(h["d_logic_score"] for h in horses_results) / len(horses_results) if horses_results else 0,
                "top_score": horses_results[0]["d_logic_score"] if horses_results else 0,
                "bottom_score": horses_results[-1]["d_logic_score"] if horses_results else 0
            }
        }
        
    except Exception as e:
        logger.error(f"D-logic calculation error: {e}")
        return {"error": f"Dロジック計算中にエラーが発生しました: {str(e)}"} 