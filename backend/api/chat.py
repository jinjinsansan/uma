from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import logging
import re
from services.openai_service import openai_service
from services.today_race_fetcher import today_race_fetcher
from services.integrated_d_logic_calculator import d_logic_calculator
from services.dlogic_raw_data_manager import dlogic_manager
from services.fast_dlogic_engine import FastDLogicEngine

router = APIRouter(prefix="/api/chat", tags=["Chat"])

logger = logging.getLogger(__name__)

def extract_horse_name(text: str) -> Optional[str]:
    """テキストから馬名を抽出（100点満点・インジケーター優先版）"""
    if not text or len(text.strip()) < 3:
        return None
    
    text_clean = text.strip()
    text_lower = text_clean.lower()
    
    # 【第1段階】馬名インジケーター最優先チェック
    horse_indicators = [
        "の指数", "の分析", "を分析", "の成績", "のスコア", 
        "のD-Logic", "の予想", "の評価", "はどう", "について",
        "を教えて", "について教えて", "の情報", "のデータ",
        "の結果", "はどんな", "を調べて", "を見て", "をお願い"
    ]
    
    # インジケーターがある場合は優先的に馬名を探す
    has_clear_indicator = any(indicator in text_clean for indicator in horse_indicators)
    
    if has_clear_indicator:
        # カタカナ検出
        katakana_pattern = r'[ァ-ヴー]{3,}'
        katakana_matches = re.findall(katakana_pattern, text_clean)
        
        if katakana_matches:
            longest_katakana = max(katakana_matches, key=len)
            if len(longest_katakana) >= 3:
                return longest_katakana
    
    # 【第2段階】明確な除外対象チェック
    immediate_exclude = [
        "こんにちは", "こんにちわ", "おはよう", "おはようございます", 
        "こんばんは", "こんばんわ", "お疲れ様", "お疲れさま", "お疲れ",
        "ありがとう", "ありがとうございます", "よろしく", "はじめまして",
        "さようなら", "またね", "お元気", "元気",
        "何ですか", "誰ですか", "どうですか", "なんですか", "だれですか",
        "教えて", "説明して", "わからない", "知りたい",
        "D-Logicとは", "使い方", "やり方", "方法", "テスト", "test",
        "あなたは", "君は", "きみは",
        "今日の天気", "天気", "時間", "日付", "曜日", "今日", "明日", "昨日",
        "暑い", "寒い", "雨", "晴れ", "面白い", "楽しい", "すごい"
    ]
    
    if text_lower in immediate_exclude:
        return None
    
    # 【第3段階】一般的な除外パターン（馬名が含まれない場合のみ）
    exclude_if_contains = [
        "です", "ます", "でしょう", "ですか", "ますか", "でした", "ました",
        "なに", "なん", "だれ", "いつ", "どこ", "なぜ", "なんで",
        "って", "という", "といえば", "に関して",
        "hello", "hi", "good", "nice", "wow", "ok", "yes", "no"
    ]
    
    # カタカナがない場合のみ除外パターンを適用
    katakana_pattern = r'[ァ-ヴー]{3,}'
    katakana_matches = re.findall(katakana_pattern, text_clean)
    
    if not katakana_matches:
        for exclude in exclude_if_contains:
            if exclude in text_lower:
                return None
        return None
    
    # 【第4段階】長いカタカナ単独入力
    longest_katakana = max(katakana_matches, key=len)
    
    if (len(longest_katakana) >= 8 and 
        len(text_clean) <= len(longest_katakana) + 2 and
        not any(char in text_clean for char in ['？', '?', '！', '!', '。', '、'])):
        return longest_katakana
    
    # その他は除外
    return None

async def get_horse_d_logic_analysis(horse_name: str) -> Dict[str, Any]:
    """馬のD-Logic分析結果を取得"""
    try:
        # FastDLogicEngineを使用
        fast_engine = FastDLogicEngine()
        result = fast_engine.analyze_single_horse(horse_name)
        
        # FastDLogicEngineが正常な結果を返したかチェック（errorフィールドがなく、total_scoreがある場合）
        if result and "error" not in result and "total_score" in result:
            return {
                "status": "success",
                "calculation_method": "Phase D統合・独自基準100点・12項目D-Logic",
                "horses": [{
                    "name": horse_name,
                    "total_score": result.get("total_score", 0),
                    "grade": result.get("grade", "未評価"),
                    "detailed_scores": result.get("d_logic_scores", {}),
                    "analysis_source": result.get("data_source", "高速分析エンジン")
                }]
            }
        else:
            return {
                "status": "error", 
                "message": "分析結果が取得できませんでした"
            }
        
    except Exception as e:
        logger.error(f"D-Logic analysis error for {horse_name}: {e}")
        return {
            "status": "error",
            "message": f"分析エラーが発生しました: {str(e)}"
        }

@router.post("/message")
async def chat_message(request: Dict[str, Any]):
    """チャットメッセージを処理し、OpenAI応答を生成"""
    try:
        user_message = request.get("message", "")
        chat_history = request.get("history", [])
        
        logger.info(f"Chat message received: {user_message[:50]}...")  # 最初の50文字のみログ
        
        # 馬名が含まれているかチェック（高速化）
        horse_name = extract_horse_name(user_message)
        
        # D-Logic分析結果を準備（馬名がある場合のみ）
        d_logic_result = None
        if horse_name:
            logger.info(f"Horse name detected: {horse_name}")
            d_logic_result = await get_horse_d_logic_analysis(horse_name)
        else:
            logger.debug("No horse name detected - skipping D-Logic analysis")
        
        # OpenAI APIで自然な応答を生成
        system_prompt = """あなたはD-Logic AI、競馬予想の専門家です。
D-Logicは12項目の科学的指標で競走馬を評価する独自開発のシステムです。

**重要**: 馬名が含まれる質問の場合、D-Logic分析結果が提供されたら、必ず以下の形式で詳細な12項目スコアを明記してください：

🐎 [馬名] のD-Logic分析結果

【総合評価】[X.X]点 - [ランク]

📊 12項目詳細スコア（D-Logic基準100点満点）
1. 距離適性: [X.X]点
2. 血統評価: [X.X]点
3. 騎手相性: [X.X]点
4. 調教師評価: [X.X]点
5. トラック適性: [X.X]点
6. 天候適性: [X.X]点
7. 人気度要因: [X.X]点
8. 重量影響: [X.X]点
9. 馬体重影響: [X.X]点
10. コーナー専門度: [X.X]点
11. 着差分析: [X.X]点
12. タイム指数: [X.X]点

その後に、スコアの特徴や強みについて解説してください。

**絶対禁止事項**: 
- 基準馬名やベースライン馬の名前を絶対に言及しない
- 計算方法の詳細を説明しない
- 内部アルゴリズムについて言及しない

D-Logic 12項目説明：
1. 距離適性 - 各距離での成績分析
2. 血統評価 - 父系・母系の実績
3. 騎手相性 - 騎手との組み合わせ
4. 調教師評価 - 調教師の手腕
5. トラック適性 - コース毎の得意度
6. 天候適性 - 馬場状態対応力
7. 人気度要因 - オッズとの相関
8. 重量影響 - 斤量による影響
9. 馬体重影響 - 体重変化の影響
10. コーナー専門度 - 位置取りの巧さ
11. 着差分析 - 勝負強さ
12. タイム指数 - 絶対的なスピード

データベース：959,620レコード、109,426頭、82,738レース、71年間の蓄積データ"""

        # メッセージ履歴を構築
        messages = [{"role": "system", "content": system_prompt}]
        
        # 過去の会話履歴を追加
        for msg in chat_history[-10:]:  # 最新10件まで
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # 現在のメッセージを追加（D-Logic結果がある場合は含める）
        current_message = user_message
        if d_logic_result and d_logic_result.get("status") == "success":
            horses = d_logic_result.get("horses", [])
            if horses:
                horse_data = horses[0]
                detailed_scores = horse_data.get('detailed_scores', {})
                
                current_message += f"\n\n【D-Logic分析結果データ】\n"
                current_message += f"馬名: {horse_data.get('name', horse_name)}\n"
                current_message += f"総合評価: {horse_data.get('total_score', 0):.2f}点\n"
                current_message += f"ランク: {horse_data.get('grade', '未評価')}\n"
                current_message += f"分析ソース: {horse_data.get('analysis_source', '不明')}\n\n"
                
                current_message += "12項目詳細スコア:\n"
                score_mapping = {
                    "1_distance_aptitude": "1. 距離適性",
                    "2_bloodline_evaluation": "2. 血統評価", 
                    "3_jockey_compatibility": "3. 騎手相性",
                    "4_trainer_evaluation": "4. 調教師評価",
                    "5_track_aptitude": "5. トラック適性",
                    "6_weather_aptitude": "6. 天候適性",
                    "7_popularity_factor": "7. 人気度要因",
                    "8_weight_impact": "8. 重量影響",
                    "9_horse_weight_impact": "9. 馬体重影響",
                    "10_corner_specialist_degree": "10. コーナー専門度",
                    "11_margin_analysis": "11. 着差分析",
                    "12_time_index": "12. タイム指数"
                }
                
                for key, label in score_mapping.items():
                    score = detailed_scores.get(key, 0)
                    current_message += f"{label}: {score:.2f}点\n"
                
                current_message += f"\n上記のデータを使って、必ず指定された形式で12項目すべてのスコアを明記した応答を生成してください。"
        
        messages.append({"role": "user", "content": current_message})
        
        # OpenAI APIで応答生成
        ai_response = await openai_service.chat_completion(messages)
        
        # レスポンスを構築
        response_data = {
            "status": "success",
            "message": ai_response,
            "has_d_logic": bool(d_logic_result),
            "analysis_type": "openai_chat"
        }
        
        # D-Logic結果がある場合は追加
        if d_logic_result:
            response_data["horse_name"] = horse_name
            response_data["d_logic_result"] = d_logic_result
        
        return response_data
            
    except Exception as e:
        logger.error(f"Chat message processing error: {e}")
        raise HTTPException(status_code=500, detail="チャット処理中にエラーが発生しました")

# 以下は旧実装（現在未使用）
async def handle_race_related_message_legacy(user_message: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
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

# Old extract_horse_name function removed - using the correct one at line 15

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