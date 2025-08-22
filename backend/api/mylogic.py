"""
MyLogicAI API エンドポイント
ユーザーカスタマイズのD-Logic分析を提供
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv
import requests
import json

# MyLogic計算エンジンをインポート
from services.mylogic_calculator import MyLogicCalculator
from services.openai_service import openai_service

load_dotenv()

# ロガー設定
logger = logging.getLogger(__name__)

# APIルーター
router = APIRouter(prefix="/api/my-logic", tags=["MyLogicAI"])

# MyLogic計算エンジンのグローバルインスタンス
mylogic_calculator = MyLogicCalculator()

# Supabase設定
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# MyLogic用システムプロンプト
MYLOGIC_SYSTEM_PROMPT = """
あなたはMyLogic AI（カスタマイズ可能な競馬分析AI）のアシスタントです。

【MyLogic AIの特徴】
- ユーザーが12項目の重み付けを自由にカスタマイズできる独自の分析システム
- 100ポイントを12項目に配分することで、あなただけの評価基準を作成
- 距離適性、血統評価、騎手相性など12項目を自由に調整
- 無料会員は初回作成後変更不可、プレミアム会員は月1回変更可能

【他のAIシステムの紹介】
- D-Logic AI: 独自基準による標準的な分析。単頭・複数頭比較・レース全体の分析が可能です。総合的なバランスを求める方にお勧めです。
- I-Logic AI: 馬と騎手の総合評価（馬70%・騎手30%）による新しい分析手法。騎手の影響を重視したい方にお勧めです。

【使い方】
1. まず「設定」ボタンから12項目の重み付けを設定してください
2. 馬名を入力すると、あなたの設定に基づいた独自スコアが表示されます
3. 標準D-Logicスコアとの比較で、どれだけカスタマイズが反映されているか確認できます

【よくある質問】
Q: 重み付けをどう設定すればいいですか？
A: 重視したい項目に多くのポイントを割り当ててください。例えば血統重視なら血統評価に20-30ポイント、他の項目を5-8ポイントずつにするなど。

Q: D-LogicとMyLogicの違いは？
A: D-Logicは標準的なバランス型評価、MyLogicはあなたの好みに特化した評価です。

Q: どの項目を重視すべきですか？
A: 競馬場や距離によって変わりますが、一般的には距離適性、血統評価、騎手相性が重要とされています。

親しみやすく、分かりやすい説明を心がけてください。
"""

# リクエスト/レスポンスモデル
class WeightConfig(BaseModel):
    distance_aptitude: int          # 距離適性
    bloodline_evaluation: int       # 血統評価
    jockey_compatibility: int       # 騎手相性
    trainer_evaluation: int         # 調教師評価
    track_aptitude: int            # トラック適性
    weather_aptitude: int          # 天候適性
    popularity_factor: int         # 人気要因
    weight_impact: int             # 斤量影響
    horse_weight_impact: int       # 馬体重影響
    corner_specialist_degree: int  # コーナー巧者度
    margin_analysis: int           # 着差分析
    time_index: int                # タイム指数

class SavePreferenceRequest(BaseModel):
    weights: WeightConfig

class AnalyzeRequest(BaseModel):
    horse_names: List[str]
    weights: Optional[WeightConfig] = None
    user_id: Optional[str] = None

class PreviewRequest(BaseModel):
    weights: WeightConfig
    horse_names: List[str]

class MyLogicPreference(BaseModel):
    id: str
    user_id: str
    weights: WeightConfig
    is_active: bool
    created_at: datetime
    updated_at: datetime
    version: int

class MyLogicPermission(BaseModel):
    can_edit: bool
    has_preference: bool
    last_edit_date: Optional[datetime]
    next_edit_date: Optional[datetime]
    subscription_type: str

# 簡易的な認証チェック（フロントエンドからのuser_idを信頼）
def get_user_id_from_auth(authorization: Optional[str] = Header(None)) -> str:
    """認証ヘッダーからユーザーIDを取得（簡易実装）"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    # 実際の認証は省略（フロントエンドを信頼）
    return "mock-user-id"

@router.get("/preferences")
async def get_preference(user_id: str = Depends(get_user_id_from_auth)):
    """ユーザーのMyLogic設定を取得"""
    try:
        # 現在はモック実装
        logger.info(f"Getting preference for user: {user_id}")
        
        # モックデータを返す（実際にはSupabaseから取得）
        # デフォルトの重み付けを返す
        default_preference = {
            "id": "default",
            "user_id": user_id,
            "weights": {
                "distance_aptitude": 8,
                "bloodline_evaluation": 8,
                "jockey_compatibility": 8,
                "trainer_evaluation": 8,
                "track_aptitude": 8,
                "weather_aptitude": 9,
                "popularity_factor": 9,
                "weight_impact": 9,
                "horse_weight_impact": 9,
                "corner_specialist_degree": 8,
                "margin_analysis": 8,
                "time_index": 8
            },
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "version": 1
        }
        return {"preference": default_preference}
            
    except Exception as e:
        logger.error(f"Error fetching preference: {str(e)}")
        return {"preference": None}

@router.post("/preferences")
async def save_preference(
    request: SavePreferenceRequest,
    user_id: str = Depends(get_user_id_from_auth)
):
    """MyLogic設定を保存"""
    try:
        logger.info(f"Saving preference for user: {user_id}")
        
        # 重み付けの合計を検証（浮動小数点誤差を考慮）
        total = sum(dict(request.weights).values())
        if abs(total - 100) > 0.1:  # 浮動小数点誤差を考慮
            raise HTTPException(
                status_code=400,
                detail=f"重み付けの合計は100でなければなりません。現在: {total}"
            )
        
        # モック実装（実際にはSupabaseに保存）
        logger.info(f"Weights to save: {dict(request.weights)}")
        return {"success": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving preference: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="設定の保存中にエラーが発生しました"
        )

@router.get("/can-edit")
async def check_edit_permission(user_id: str = Depends(get_user_id_from_auth)):
    """編集権限を確認"""
    try:
        # モック実装
        logger.info(f"Checking permission for user: {user_id}")
        
        # モックデータ（実際にはSupabaseから取得）
        subscription_type = 'free_trial'
        has_preference = False
        last_edit_date = None
        can_edit = True  # 初回は誰でも作成可能
        next_edit_date = None
        
        return MyLogicPermission(
            can_edit=can_edit,
            has_preference=has_preference,
            last_edit_date=last_edit_date,
            next_edit_date=next_edit_date,
            subscription_type=subscription_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking permission: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="権限の確認中にエラーが発生しました"
        )

@router.post("/analyze")
async def analyze_with_mylogic(
    request: AnalyzeRequest,
    user_id: str = Depends(get_user_id_from_auth)
):
    """MyLogic設定で馬を分析"""
    try:
        # リクエストから重み付けとuser_idを取得
        weights = request.weights if hasattr(request, 'weights') else None
        actual_user_id = request.user_id if hasattr(request, 'user_id') else user_id
        
        # 重み付けがリクエストに含まれていない場合は、Supabaseから取得
        if not weights and SUPABASE_URL and SUPABASE_SERVICE_KEY:
            try:
                headers = {
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json"
                }
                
                # ユーザーのMyLogic設定を取得
                url = f"{SUPABASE_URL}/rest/v1/user_my_logic_preferences"
                params = {
                    "user_id": f"eq.{actual_user_id}",
                    "is_active": "eq.true",
                    "select": "weights"
                }
                
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        weights = data[0].get('weights')
            except Exception as e:
                logger.warning(f"Supabase fetch failed: {str(e)}")
        
        # デフォルトの重み付け（均等配分）
        if not weights:
            weights = {
                "distance_aptitude": 8,
                "bloodline_evaluation": 8,
                "jockey_compatibility": 8,
                "trainer_evaluation": 8,
                "track_aptitude": 8,
                "weather_aptitude": 9,
                "popularity_factor": 9,
                "weight_impact": 9,
                "horse_weight_impact": 9,
                "corner_specialist_degree": 8,
                "margin_analysis": 8,
                "time_index": 8
            }
        
        # MyLogic計算エンジンで分析
        # WeightConfigオブジェクトを辞書に変換
        weights_dict = dict(weights) if hasattr(weights, '__dict__') else weights
        results = mylogic_calculator.analyze_multiple_horses(
            request.horse_names,
            weights_dict
        )
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        return {
            "success": False,
            "error": "分析中にエラーが発生しました"
        }

@router.post("/preview")
async def preview_analysis(
    request: PreviewRequest,
    user_id: str = Depends(get_user_id_from_auth)
):
    """保存前のプレビュー分析"""
    try:
        # 重み付けの合計を検証（浮動小数点誤差を考慮）
        total = sum(dict(request.weights).values())
        if abs(total - 100) > 0.1:  # 浮動小数点誤差を考慮
            raise HTTPException(
                status_code=400,
                detail=f"重み付けの合計は100でなければなりません。現在: {total}"
            )
        
        # プレビュー用にMyLogic計算エンジンで分析
        # 最大3頭までに制限
        preview_horses = request.horse_names[:3]
        
        # WeightConfigオブジェクトを辞書に変換
        weights_dict = dict(request.weights) if hasattr(request.weights, '__dict__') else request.weights
        results = mylogic_calculator.analyze_multiple_horses(
            preview_horses,
            weights_dict
        )
        
        # プレビュー用に簡略化された結果を返す
        preview_results = []
        for result in results:
            preview_results.append({
                "horse_name": result["horse_name"],
                "total_score": result["mylogic_score"],
                "standard_score": result.get("standard_score", 0),
                "mylogic_score": result["mylogic_score"]
            })
        
        return {
            "success": True,
            "results": preview_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in preview: {str(e)}")
        return {
            "success": False,
            "error": "プレビュー中にエラーが発生しました"
        }

@router.get("/history")
async def get_edit_history(user_id: str = Depends(get_user_id_from_auth)):
    """編集履歴を取得"""
    try:
        # モック実装
        logger.info(f"Getting history for user: {user_id}")
        
        return {
            "success": True,
            "history": []
        }
        
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        return {
            "success": False,
            "history": []
        }

@router.post("/chat")
async def mylogic_chat(request: Dict[str, Any]):
    """MyLogicチャット用エンドポイント - OpenAI統合"""
    try:
        # リクエストからデータ取得
        message = request.get('message', '').strip()
        user_id = request.get('user_id')
        chat_history = request.get('chat_history', [])
        
        logger.info(f"MyLogic chat request: {message[:100]}...")
        
        # 馬名分析かどうかを判定
        # 単純な馬名パターン（カタカナのみ）
        import re
        horse_pattern = r'^[ァ-ヶー]+$'
        is_horse_name = bool(re.match(horse_pattern, message))
        
        # 複数馬の分析（カンマ区切りまたはスペース区切り）
        horse_names = []
        if ',' in message or '、' in message:
            # カンマ区切り
            horse_names = [h.strip() for h in re.split('[,、]', message) if h.strip()]
        elif ' ' in message and all(re.match(horse_pattern, h) for h in message.split()):
            # スペース区切りで全てがカタカナ
            horse_names = message.split()
        elif is_horse_name:
            # 単頭
            horse_names = [message]
        
        # MyLogic分析の場合
        if horse_names:
            # ユーザーの重み付けを取得
            weights = None
            if SUPABASE_URL and SUPABASE_SERVICE_KEY and user_id:
                try:
                    headers = {
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    url = f"{SUPABASE_URL}/rest/v1/user_my_logic_preferences"
                    params = {
                        "user_id": f"eq.{user_id}",
                        "is_active": "eq.true",
                        "select": "weights"
                    }
                    
                    response = requests.get(url, headers=headers, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            weights = data[0].get('weights')
                except Exception as e:
                    logger.warning(f"Failed to fetch user weights: {e}")
            
            # デフォルトの重み付け
            if not weights:
                weights = {
                    "distance_aptitude": 8,
                    "bloodline_evaluation": 8,
                    "jockey_compatibility": 8,
                    "trainer_evaluation": 8,
                    "track_aptitude": 8,
                    "weather_aptitude": 9,
                    "popularity_factor": 9,
                    "weight_impact": 9,
                    "horse_weight_impact": 9,
                    "corner_specialist_degree": 8,
                    "margin_analysis": 8,
                    "time_index": 8
                }
            
            # MyLogic分析実行
            results = mylogic_calculator.analyze_multiple_horses(horse_names, weights)
            
            # 結果を整形
            response_text = f"🎯 MyLogic分析結果\n\n"
            
            if len(results) == 1:
                # 単頭分析
                result = results[0]
                response_text += f"【{result['horse_name']}】\n"
                response_text += f"MyLogicスコア: {result['mylogic_score']:.1f}点\n"
                response_text += f"標準D-Logicスコア: {result.get('standard_score', 0):.1f}点\n"
                response_text += f"差分: {result['mylogic_score'] - result.get('standard_score', 0):+.1f}点\n"
            else:
                # 複数頭分析
                for i, result in enumerate(results):
                    emoji = ['🥇', '🥈', '🥉'][i] if i < 3 else f"{i+1}位"
                    response_text += f"{emoji} {result['horse_name']}: {result['mylogic_score']:.1f}点 "
                    response_text += f"(標準: {result.get('standard_score', 0):.1f}点)\n"
            
            response_text += "\n💡 あなたの重み付けによる独自評価です。"
            response_text += "設定を変更したい場合は「設定」ボタンから調整してください。"
            
            return {
                "status": "success",
                "response": response_text,
                "message": message
            }
        
        # 一般的な会話の場合（OpenAI統合）
        try:
            # チャット履歴をOpenAI形式に変換
            messages = [{"role": "system", "content": MYLOGIC_SYSTEM_PROMPT}]
            
            # 直近5件の履歴を追加
            for msg in chat_history[-5:]:
                if isinstance(msg, dict) and 'content' in msg:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # 現在のメッセージを追加
            messages.append({"role": "user", "content": message})
            
            # OpenAI応答を生成
            response = await openai_service.chat_completion(messages)
            
            return {
                "status": "success",
                "response": response,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            # フォールバック応答
            fallback_response = "申し訳ございません。現在MyLogic AIとの会話機能は利用できません。"
            fallback_response += "\n\n馬名を入力していただければ、MyLogic分析を実行いたします。"
            fallback_response += "\n例: 「ドウデュース」「イクイノックス、ドウデュース」など"
            
            return {
                "status": "success",
                "response": fallback_response,
                "message": message
            }
        
    except Exception as e:
        logger.error(f"MyLogic chat error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "status": "error",
            "response": "エラーが発生しました。もう一度お試しください。",
            "message": request.get('message', ''),
            "error": str(e)
        }