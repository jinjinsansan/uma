"""
V2チャット管理API
IMLogicとViewLogic（将来）を統合
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, List, Optional
from datetime import datetime
import logging
from pydantic import BaseModel
import uuid
import os
import json
from supabase import create_client, Client

from api.v2.auth import get_current_user, verify_email_token
from api.v2.config import v2_config
from services.v2.points_service import V2PointsService
from services.v2.chat_service import V2ChatService
from services.v2.ai_handler import V2AIHandler
from services.v2.race_scores_service import V2RaceScoresService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/chat", tags=["v2-chat"])

async def get_user_from_email_header(
    x_user_email: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
) -> dict:
    """X-User-EmailヘッダーまたはAuthorizationヘッダーから簡易的にユーザー情報を取得"""
    # X-User-Emailヘッダーがあればそれを使用
    email = x_user_email
    
    # なければAuthorizationヘッダーから取得
    if not email and authorization:
        # "Bearer email@example.com" 形式から email を抽出
        if authorization.startswith("Bearer "):
            email = authorization[7:]  # "Bearer " の7文字をスキップ
    
    if not email:
        raise HTTPException(status_code=403, detail="Not authenticated")
    
    # verify_email_tokenと同じようにユーザー情報を取得
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error(f"Supabase設定エラー: URL={bool(supabase_url)}, KEY={bool(supabase_key)}")
        raise HTTPException(status_code=500, detail="サーバー設定エラー")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # V2専用テーブルでユーザーを検索
        user_result = supabase.table("v2_users").select("*").eq("email", email).execute()
    except Exception as e:
        logger.error(f"Supabase接続エラー: {e}")
        raise HTTPException(status_code=500, detail=f"データベース接続エラー: {str(e)}")
    
    if user_result.data:
        user = user_result.data[0]
        return {
            "user_id": user["id"],
            "email": user["email"],
            "name": user.get("name", "")
        }
    else:
        # ユーザーが見つからない場合は作成
        try:
            create_result = supabase.table("v2_users").insert({
                "email": email,
                "name": email.split("@")[0],
                "google_id": f"v2-{email}",
                "avatar_url": ""
            }).execute()
        except Exception as e:
            logger.error(f"V2ユーザー作成エラー: {e}")
            raise HTTPException(status_code=500, detail=f"ユーザー作成エラー: {str(e)}")
        
        if create_result.data:
            user = create_result.data[0]
            
            # 初期ポイント付与
            try:
                initial_points = v2_config.POINTS_GOOGLE_AUTH
                
                supabase.table("v2_user_points").insert({
                    "user_id": user["id"],
                    "current_points": initial_points,
                    "total_earned": initial_points,
                    "total_spent": 0
                }).execute()
                
                supabase.table("v2_point_transactions").insert({
                    "user_id": user["id"],
                    "amount": initial_points,
                    "transaction_type": "initial_grant",
                    "description": f"初期ポイント付与（{initial_points}ポイント）",
                    "balance_after": initial_points
                }).execute()
                
            except Exception as e:
                logger.warning(f"Failed to grant initial points: {e}")
            
            return {
                "user_id": user["id"],
                "email": user["email"],
                "name": user.get("name", "")
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")

class CreateChatRequest(BaseModel):
    """チャット作成リクエスト"""
    race_id: str
    race_date: str
    venue: str
    race_number: int
    race_name: str
    horses: List[str]
    jockeys: Optional[List[str]] = []
    posts: Optional[List[int]] = []
    horse_numbers: Optional[List[int]] = []
    # V2フィールド（2025-08-28追加）
    sex_ages: Optional[List[str]] = []        # 性齢
    weights: Optional[List[float]] = []       # 斤量
    trainers: Optional[List[str]] = []        # 調教師
    odds: Optional[List[float]] = []          # オッズ
    popularities: Optional[List[int]] = []    # 人気
    distance: Optional[int] = None
    course_type: Optional[str] = None
    weather: Optional[str] = None
    track_condition: Optional[str] = None
    # レース結果データ（着順と払戻）
    raceResults: Optional[Dict] = None  # {"first": 1, "second": 3, "third": 5, "payouts": {...}}
    imlogic_settings_id: Optional[str] = None
    is_test_mode: Optional[bool] = False  # 管理者テストモード

class ChatMessageRequest(BaseModel):
    """チャットメッセージリクエスト"""
    message: str
    ai_type: Optional[str] = None  # 'imlogic', 'dlogic', 'ilogic', 'viewlogic', 'metalogic', or None for auto-detect
    imlogic_settings: Optional[Dict] = None  # IMLogic設定（オプション）

@router.post("/create")
async def create_chat(
    request: CreateChatRequest,
    user_info: dict = Depends(verify_email_token)
):
    """
    新しいチャットセッションを作成（1ポイント消費）
    管理者テストモードの場合はポイント消費なし
    初回作成時はD-Logic/I-Logicバッチ計算を実行してv2_race_scoresに保存
    """
    try:
        user_id = user_info["user_id"]
        user_email = user_info.get("email", "")
        
        # 管理者チェック（テストモードの場合はポイントチェックをスキップ）
        is_admin_test = request.is_test_mode and (user_email == "goldbenchan@gmail.com" or user_email == "kusanokiyoshi1@gmail.com")
        
        # ポイント確認（管理者テストモード以外）
        if not is_admin_test:
            points_service = V2PointsService()
            points_data = await points_service.get_user_points(user_id)
            
            required_points = v2_config.POINTS_PER_CHAT
            if required_points > 0 and points_data["current_points"] < required_points:
                raise HTTPException(status_code=400, detail=f"チャット作成には{required_points}ポイントが必要です")
        
        # v2_race_scoresテーブルをチェック（パフォーマンス最適化のため無効化）
        # # from services.v2.race_scores_service import V2RaceScoresService  # パフォーマンス最適化のため無効化
        # # race_scores_service = V2RaceScoresService()  # パフォーマンス最適化のため無効化
        # existing_scores = await race_scores_service.get_race_scores(request.race_id)
        
        # バッチ計算を常にスキップ（パフォーマンス最適化）
        if False:  # not existing_scores:
            logger.info(f"初回チャット作成: {request.race_id}")
            
            # D-Logic/I-Logicバッチ計算をスキップ（出走表で表示しないため）
            # 将来的に再度表示する場合はコメントを外す
            dlogic_scores = None
            ilogic_scores = None
            
            # # D-Logicバッチ計算
            # try:
            #     from api.v2.dlogic import calculate_dlogic_batch
            #     dlogic_scores = await calculate_dlogic_batch(request.horses)
            #     logger.info(f"D-Logicバッチ計算完了: {len(dlogic_scores)}頭")
            # except Exception as e:
            #     logger.warning(f"D-Logicバッチ計算失敗: {e}")
            #     dlogic_scores = None
            
            # # I-Logicバッチ計算（騎手データがある場合のみ）
            # ilogic_scores = None
            # if request.jockeys and request.posts:
            #     try:
            #         from api.v2.ilogic import calculate_ilogic_batch
            #         ilogic_scores = await calculate_ilogic_batch(
            #             horses=request.horses,
            #             jockeys=request.jockeys,
            #             posts=request.posts,
            #             horse_numbers=request.horse_numbers or [],
            #             venue=request.venue
            #         )
            #         logger.info(f"I-Logicバッチ計算完了: {len(ilogic_scores)}頭")
            #     except Exception as e:
            #         logger.warning(f"I-Logicバッチ計算失敗: {e}")
            #         ilogic_scores = None
            
            # v2_race_scoresへの保存をスキップ（パフォーマンス最適化）
            # 注意: D-Logic/I-Logicの計算を無効化したため、スコア保存も不要
            logger.info(f"[SKIP] v2_race_scoresへの保存をスキップ（パフォーマンス最適化）: {request.race_id}")
            
            # # 元のコード（無効化）
            # await race_scores_service.save_race_scores(
            #     race_id=request.race_id,
            #     race_date=request.race_date,
            #     venue=request.venue,
            #     race_number=request.race_number,
            #     race_name=request.race_name,
            #     horses=request.horses,
            #     jockeys=request.jockeys,
            #     posts=request.posts,
            #     horse_numbers=request.horse_numbers,
            #     sex_ages=request.sex_ages,
            #     weights=request.weights,
            #     trainers=request.trainers,
            #     odds=request.odds,
            #     popularities=request.popularities,
            #     dlogic_scores=dlogic_scores,
            #     ilogic_scores=ilogic_scores
            # )
            # logger.info(f"v2_race_scoresに保存完了: {request.race_id}")
        
        # チャット作成
        chat_service = V2ChatService()
        chat_session = await chat_service.create_session(
            user_id=user_id,
            race_data={
                "race_id": request.race_id,
                "race_date": request.race_date,
                "venue": request.venue,
                "race_number": request.race_number,
                "race_name": request.race_name,
                "horses": request.horses,
                "jockeys": request.jockeys,
                "posts": request.posts,
                "horse_numbers": request.horse_numbers,
                "sex_ages": request.sex_ages,          # V2フィールド追加
                "weights": request.weights,            # V2フィールド追加
                "trainers": request.trainers,          # V2フィールド追加
                "odds": request.odds,                  # V2フィールド追加
                "popularities": request.popularities,  # V2フィールド追加
                "distance": request.distance,
                "course_type": request.course_type,
                "weather": request.weather,
                "track_condition": request.track_condition,
                "raceResults": request.raceResults     # レース結果追加
            },
            imlogic_settings_id=request.imlogic_settings_id,
            user_email=user_email
        )

        # レーススコアを保存（軽量メタデータのみ）
        try:
            race_scores_service = V2RaceScoresService()
            await race_scores_service.save_race_scores(
                race_id=request.race_id,
                race_date=request.race_date,
                venue=request.venue,
                race_number=request.race_number,
                race_name=request.race_name,
                horses=request.horses,
                jockeys=request.jockeys or [],
                posts=request.posts or [],
                horse_numbers=request.horse_numbers or [],
                sex_ages=request.sex_ages or [],
                weights=request.weights or [],
                trainers=request.trainers or [],
                odds=request.odds or [],
                popularities=request.popularities or [],
                race_results=request.raceResults
            )
        except Exception as e:
            logger.warning(f"v2_race_scores保存スキップ: {e}")
        
        # ポイント消費（管理者テストモード以外）
        if not is_admin_test:
            required_points = v2_config.POINTS_PER_CHAT
            if required_points > 0:
                await points_service.use_points(
                    user_id=user_id,
                    amount=required_points,
                transaction_type="chat_create",
                description=f"{request.venue}{request.race_number}Rのチャット作成",
                related_entity_id=chat_session["id"]
            )
            remaining_points = points_data["current_points"] - required_points
        else:
            # 管理者テストモードの場合はポイント変更なし
            points_service = V2PointsService()
            points_data = await points_service.get_user_points(user_id)
            remaining_points = points_data["current_points"]
        
        return {
            "success": True,
            "chat_id": chat_session["id"],
            "remaining_points": remaining_points,
            "test_mode": is_admin_test
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チャット作成エラー: {e}")
        raise HTTPException(status_code=500, detail="チャットの作成に失敗しました")

@router.get("/sessions")
async def get_chat_sessions(
    limit: int = 20,
    offset: int = 0,
    user_info: dict = Depends(verify_email_token)
):
    """
    ユーザーのチャットセッション一覧を取得
    """
    try:
        user_id = user_info["user_id"]
        logger.info(f"Getting sessions for user: {user_info.get('email', 'unknown')}, user_id: {user_id}")
        
        chat_service = V2ChatService()
        sessions = await chat_service.get_user_sessions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Returning {len(sessions)} sessions")
        
        return {
            "sessions": sessions,
            "limit": limit,
            "offset": offset,
            "total": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"セッション一覧取得エラー: {e}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="セッション一覧の取得に失敗しました")

@router.get("/session/{session_id}")
async def get_chat_session(
    session_id: str,
    user_info: dict = Depends(verify_email_token)
):
    """
    特定のチャットセッションを取得
    """
    try:
        user_id = user_info["user_id"]
        chat_service = V2ChatService()
        session = await chat_service.get_session(session_id, user_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="チャットセッションが見つかりません")
        
        # 最終アクセス日時を更新
        await chat_service.update_last_accessed(session_id)
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セッション取得エラー: {e}")
        raise HTTPException(status_code=500, detail="セッションの取得に失敗しました")

@router.post("/session/{session_id}/message")
async def send_message(
    session_id: str,
    request: ChatMessageRequest,
    user_info: dict = Depends(get_user_from_email_header)
):
    """
    チャットにメッセージを送信
    """
    try:
        # レート制限チェック
        from api.v2.rate_limiter import check_rate_limit
        user_id = user_info["user_id"]
        is_allowed, retry_after = check_rate_limit(user_id, 'chat_message')
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail=f"リクエスト制限を超えました。{retry_after}秒後に再試行してください。",
                headers={"Retry-After": str(retry_after)}
            )
        logger.info(f"=== send_message開始 ===")
        logger.info(f"session_id: {session_id}")
        logger.info(f"user_info: {user_info}")
        logger.info(f"request: {request}")
        
        user_id = user_info["user_id"]
        user_email = user_info.get("email", "")
        chat_service = V2ChatService()

        # セッション確認
        session = await chat_service.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="チャットセッションが見つかりません")
        
        # AIタイプ確認（Noneの場合は自然言語判定するため許可）
        if request.ai_type is not None and request.ai_type not in ["imlogic", "viewlogic", "dlogic", "ilogic", "flogic", "metalogic"]:
            raise HTTPException(status_code=400, detail="無効なAIタイプです")
        
        # V2 AIハンドラーで処理（グローバルインスタンスを使用してメモリ節約）
        logger.info(f"AIハンドラー取得開始")
        from services.v2.ai_handler_singleton import get_ai_handler
        ai_handler = get_ai_handler()
        logger.info(f"AIハンドラー取得完了")
        
        # レースデータを構築
        # race_snapshotからデータを優先的に取得
        race_snapshot = session.get("race_snapshot", {})
        if isinstance(race_snapshot, str):
            try:
                race_snapshot = json.loads(race_snapshot)
            except:
                race_snapshot = {}
        
        # デバッグ: セッションデータの構造を確認
        logger.info(f"=== セッションデータ確認 ===")
        logger.info(f"session keys: {session.keys()}")
        logger.info(f"race_snapshot type: {type(race_snapshot)}")
        if isinstance(race_snapshot, dict):
            logger.info(f"race_snapshot horses: {race_snapshot.get('horses', [])}")
            logger.info(f"race_snapshot jockeys: {race_snapshot.get('jockeys', [])}")
        
        race_data = {
            "race_id": session.get("race_id"),
            "race_date": session.get("race_date"),
            "venue": session.get("venue"),
            "race_id": session.get("race_id"),
            "race_number": session.get("race_number"),
            "race_name": session.get("race_name"),
            "horses": race_snapshot.get("horses") or session.get("horses", []),
            "jockeys": race_snapshot.get("jockeys") or session.get("jockeys"),
            "posts": race_snapshot.get("posts") or session.get("posts"),
            "horse_numbers": race_snapshot.get("horse_numbers") or session.get("horse_numbers"),
            "distance": race_snapshot.get("distance") or session.get("distance"),
            "course_type": race_snapshot.get("course_type") or session.get("course_type"),  # 血統分析で使用
            "track_condition": race_snapshot.get("track_condition") or session.get("track_condition"),
            # V2フィールド追加（F-Logic等で必要）
            "sex_ages": race_snapshot.get("sex_ages") or session.get("sex_ages"),
            "weights": race_snapshot.get("weights") or session.get("weights"),
            "trainers": race_snapshot.get("trainers") or session.get("trainers"),
            "odds": race_snapshot.get("odds") or session.get("odds"),
            "popularities": race_snapshot.get("popularities") or session.get("popularities")
        }
        
        # IMLogic設定を取得（リクエストから渡されるか、Supabaseから取得）
        imlogic_settings = request.imlogic_settings
        
        # horse_weightとjockey_weightが含まれていない場合もSupabaseから取得
        if (not imlogic_settings or imlogic_settings == {} or 
            'horse_weight' not in imlogic_settings or 'jockey_weight' not in imlogic_settings):
            # ユーザーのIMLogic設定をSupabaseから取得
            try:
                from supabase import create_client, Client
                import os
                
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
                supabase: Client = create_client(supabase_url, supabase_key)
                
                # v2_usersテーブルからユーザーIDを取得
                user_result = supabase.table("v2_users").select("id").eq("email", user_email).execute()
                if user_result.data:
                    v2_user_id = user_result.data[0]['id']
                    
                    # v2_imlogic_settingsから最新の設定を取得
                    settings_result = supabase.table("v2_imlogic_settings").select("*").eq(
                        "user_id", v2_user_id
                    ).eq("is_active", True).order("created_at", desc=True).limit(1).execute()
                    
                    if settings_result.data:
                        settings_data = settings_result.data[0]
                        imlogic_settings = {
                            "horse_weight": settings_data.get("horse_weight", 70),
                            "jockey_weight": settings_data.get("jockey_weight", 30),
                            "item_weights": settings_data.get("item_weights", {})
                        }
            except Exception as e:
                logger.warning(f"IMLogic設定取得エラー: {e}")
                pass
        
        # AIハンドラーで処理
        logger.info(f"process_message開始")
        logger.info(f"race_data: {race_data}")
        logger.info(f"imlogic_settings: {imlogic_settings}")
        
        # ai_typeがNoneの場合は自然言語判定させる
        ai_response = await ai_handler.process_message(
            message=request.message,
            race_data=race_data,
            ai_type=request.ai_type,  # Noneの場合、ai_handler内で自然言語判定
            settings=imlogic_settings,
            user_email=user_email
        )
        
        logger.info(f"process_message完了: {ai_response}")

        response_payload = dict(ai_response)
        response_payload['remaining_points'] = None
        if not session.get('test_mode'):
            try:
                points_service = V2PointsService()
                points_data = await points_service.get_user_points(user_id)
                response_payload['remaining_points'] = points_data.get('current_points')
                if response_payload.get('analysis_data') and isinstance(response_payload['analysis_data'], dict):
                    response_payload['analysis_data']['remaining_points'] = points_data.get('current_points')
            except Exception as points_error:
                logger.warning(f"ポイント残高取得エラー: {points_error}")
        
        # チャットサービスに保存
        # ユーザーメッセージにもデフォルトのai_typeを設定
        user_ai_type = request.ai_type or "imlogic"
        response = await chat_service.save_message(
            session_id=session_id,
            role="user",
            content=request.message,
            ai_type=user_ai_type
        )
        
        # ai_typeがNoneの場合はデフォルトで"imlogic"を使用
        final_ai_type = ai_response.get("ai_type") or request.ai_type or "imlogic"
        
        assistant_response = await chat_service.save_message(
            session_id=session_id,
            role="assistant",
            content=ai_response.get("content", ""),  # 辞書からcontentを取得
            ai_type=final_ai_type,
            analysis_data=ai_response.get("analysis_data")
        )
        
        # アシスタントの応答を返す
        return {
            "message": assistant_response,
            "remaining_points": response_payload.get('remaining_points')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"エラー: {str(e)}\n\nトレース: {traceback.format_exc()}"
        logger.error(f"メッセージ送信エラー: {error_detail}")
        raise HTTPException(status_code=500, detail=f"メッセージの送信に失敗しました: {str(e)}")

@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    user_info: dict = Depends(get_user_from_email_header)
):
    """
    チャットセッションを削除
    """
    try:
        user_id = user_info["user_id"]
        logger.info(f"Deleting session: {session_id} for user: {user_id}")
        
        chat_service = V2ChatService()
        
        # セッションの所有権確認
        session = await chat_service.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="チャットセッションが見つかりません")
        
        # セッションとメッセージを削除
        await chat_service.delete_session(session_id, user_id)
        
        logger.info(f"Successfully deleted session: {session_id}")
        return {"success": True, "message": "チャット履歴を削除しました"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セッション削除エラー: {e}")
        raise HTTPException(status_code=500, detail="チャット履歴の削除に失敗しました")

@router.get("/race-scores/{race_id}")
async def get_race_scores(race_id: str):
    """
    レースのD-Logic/I-Logicスコアを取得
    v2_race_scoresテーブルから取得
    """
    try:
        service = V2RaceScoresService()
        scores = await service.get_race_scores(race_id)

        if not scores:
            return {}

        # JSON文字列を辞書に変換
        for key in ("dlogic_scores", "ilogic_scores"):
            if scores.get(key) and isinstance(scores[key], str):
                try:
                    scores[key] = json.loads(scores[key])
                except json.JSONDecodeError:
                    logger.warning(f"{key} のJSON変換に失敗: {scores[key]}")

        return scores

    except Exception as e:
        logger.error(f"レーススコア取得エラー: {e}")
        return {}

@router.post("/race-scores/batch")
async def get_race_scores_batch(race_ids: list[str]):
    """
    複数レースの全エンジンスコアを一括取得（パフォーマンス最適化）

    Args:
        race_ids: レースIDのリスト (例: ["20250921-中山-7", "20250921-中山-8"])

    Returns:
        {
            "20250921-中山-7": {
                "dlogic": null,
                "ilogic": null,
                "flogic": null,
                "metalogic": null,
                "viewlogic": null,
                "imlogic": null
            },
            ...
        }
    """
    try:
        # パフォーマンス最適化: 現在は全て空のスコアを返す
        # 将来的にはここでDBから一括取得する
        result = {}
        for race_id in race_ids:
            result[race_id] = {
                "dlogic": None,
                "ilogic": None,
                "flogic": None,
                "metalogic": None,
                "viewlogic": None,
                "imlogic": None
            }

        logger.info(f"バッチ取得: {len(race_ids)}レース分のスコアを返却")
        return result

    except Exception as e:
        logger.error(f"バッチスコア取得エラー: {e}")
        return {}