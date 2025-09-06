"""
V2 LINE連携・友達紹介API
環境変数で柔軟にポイント設定可能
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from datetime import datetime, date
import logging
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv

from api.v2.auth import get_current_user
from api.v2.config import v2_config
from services.v2.points_service import V2PointsService

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/line", tags=["v2-line-referral"])

# Supabaseクライアント
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

class LineConnectRequest(BaseModel):
    """LINE連携リクエスト"""
    line_user_id: str

class ReferralRequest(BaseModel):
    """友達紹介リクエスト"""
    referral_code: str

@router.post("/connect")
async def connect_line_account(
    request: LineConnectRequest,
    user_id: str = Depends(get_current_user)
):
    """
    LINE連携（環境変数で設定されたポイント付与）
    """
    try:
        # 既にLINE連携済みかチェック
        existing = supabase.table("v2_users").select("line_user_id").eq("id", user_id).execute()
        
        if existing.data and existing.data[0].get("line_user_id"):
            raise HTTPException(status_code=400, detail="既にLINE連携済みです")
        
        # LINE user_idを更新
        update_result = supabase.table("v2_users").update({
            "line_user_id": request.line_user_id,
            "line_connected_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="LINE連携の更新に失敗しました")
        
        # ポイント付与（環境変数から読み込み）
        points_to_grant = v2_config.POINTS_LINE_CONNECT
        service = V2PointsService()
        transaction = await service.grant_points(
            user_id=user_id,
            amount=points_to_grant,
            transaction_type="line_connection",
            description=f"LINE連携によるポイント付与（{points_to_grant}ポイント）"
        )
        
        return {
            "success": True,
            "message": "LINE連携が完了しました",
            "points_granted": points_to_grant,
            "new_balance": transaction["balance_after"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LINE連携エラー: {e}")
        raise HTTPException(status_code=500, detail="LINE連携に失敗しました")

@router.post("/referral")
async def apply_referral_code(
    request: ReferralRequest,
    user_id: str = Depends(get_current_user)
):
    """
    友達紹介コード適用（環境変数で設定されたポイント付与）
    """
    try:
        # 自分のユーザー情報を取得
        user_result = supabase.table("v2_users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        user = user_result.data[0]
        
        # 既に紹介コードを使用済みかチェック
        if user.get("referred_by"):
            raise HTTPException(status_code=400, detail="既に紹介コードを使用済みです")
        
        # 紹介コードからユーザーを検索
        referrer_result = supabase.table("v2_users").select("*").eq("referral_code", request.referral_code.upper()).execute()
        if not referrer_result.data:
            raise HTTPException(status_code=404, detail="無効な紹介コードです")
        
        referrer = referrer_result.data[0]
        
        # 自己紹介はNG
        if referrer["id"] == user_id:
            raise HTTPException(status_code=400, detail="自分の紹介コードは使用できません")
        
        # 被紹介者の情報を更新
        update_result = supabase.table("v2_users").update({
            "referred_by": referrer["id"],
            "referred_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="紹介情報の更新に失敗しました")
        
        # 被紹介者にポイント付与（10ポイント固定）
        points_for_referred = v2_config.POINTS_REFERRAL_RECEIVED
        service = V2PointsService()
        referred_transaction = await service.grant_points(
            user_id=user_id,
            amount=points_for_referred,
            transaction_type="referral_applied",
            description=f"友達紹介コード使用によるポイント付与（{points_for_referred}ポイント）",
            related_entity_id=referrer["id"]
        )
        
        # 紹介者の紹介回数を増やす
        old_referral_count = referrer.get("referral_count") or 0
        new_referral_count = old_referral_count + 1
        supabase.table("v2_users").update({
            "referral_count": new_referral_count
        }).eq("id", referrer["id"]).execute()
        
        # 紹介者に段階的ポイント付与
        points_for_referrer = v2_config.get_referral_points_for_count(new_referral_count)
        if points_for_referrer > 0:
            referrer_transaction = await service.grant_points(
                user_id=referrer["id"],
                amount=points_for_referrer,
                transaction_type="referral_bonus",
                description=f"{new_referral_count}人目の友達紹介ボーナス（{points_for_referrer}ポイント）",
                related_entity_id=user_id
            )
            logger.info(f"紹介者{referrer['id']}に{points_for_referrer}ポイント付与（{new_referral_count}人目）")
        
        # 紹介履歴を記録
        supabase.table("v2_referral_history").insert({
            "referrer_id": referrer["id"],
            "referred_id": user_id,
            "referral_code": request.referral_code.upper(),
            "status": "completed"
        }).execute()
        
        return {
            "success": True,
            "message": "紹介コードが適用されました",
            "points_granted": points_for_referred,
            "new_balance": referred_transaction["balance_after"],
            "referrer_name": referrer.get("name", "友達"),
            "referrer_bonus": points_for_referrer if points_for_referrer > 0 else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"紹介コード適用エラー: {e}")
        raise HTTPException(status_code=500, detail="紹介コードの適用に失敗しました")

@router.get("/status")
async def get_line_status(user_id: str = Depends(get_current_user)):
    """
    LINE連携と友達紹介の状態を取得
    """
    try:
        # v2_usersテーブルからユーザー情報を取得（タイムアウト設定）
        import time
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                user_result = supabase.table("v2_users").select("*").eq("id", user_id).execute()
                break  # 成功したらループを抜ける
            except (ConnectionResetError, ConnectionError) as conn_err:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.warning(f"Connection failed after {max_retries} retries: {conn_err}")
                    # 接続エラーの場合はデフォルト値を返す
                    return {
                        "line_connected": False,
                        "line_connected_at": None,
                        "has_used_referral": False,
                        "referral_code": None,
                        "referral_count": 0,
                        "has_claimed_daily_login": False,
                        "points_config": v2_config.get_points_summary()
                    }
                time.sleep(0.5)  # 500ms待機してリトライ
        
        if not user_result.data:
            # ユーザーが存在しない場合はデフォルト値を返す
            return {
                "line_connected": False,
                "line_connected_at": None,
                "has_used_referral": False,
                "referral_code": None,
                "referral_count": 0,
                "has_claimed_daily_login": False,
                "points_config": v2_config.get_points_summary()
            }
        
        user = user_result.data[0]
        
        # 今日のデイリーログインボーナスを取得したか確認
        today = date.today().isoformat()
        daily_login_result = supabase.table("v2_point_transactions").select("id").eq("user_id", user_id).eq("transaction_type", "daily_login").gte("created_at", f"{today}T00:00:00").execute()
        has_claimed_daily_login = bool(daily_login_result.data)
        
        return {
            "line_connected": bool(user.get("line_user_id")),
            "line_connected_at": user.get("line_connected_at"),
            "has_used_referral": bool(user.get("referred_by")),
            "referral_code": user.get("referral_code"),
            "referral_count": user.get("referral_count", 0),
            "has_claimed_daily_login": has_claimed_daily_login,
            "points_config": v2_config.get_points_summary()
        }
        
    except ConnectionResetError as e:
        logger.warning(f"Connection reset during LINE status check: {e}")
        # 接続リセットの場合はデフォルト値を返す
        return {
            "line_connected": False,
            "line_connected_at": None,
            "has_used_referral": False,
            "referral_code": None,
            "referral_count": 0,
            "has_claimed_daily_login": False,
            "points_config": v2_config.get_points_summary()
        }
    except Exception as e:
        logger.error(f"LINE状態取得エラー: {e}")
        # その他のエラーでもデフォルト値を返してシステムを止めない
        return {
            "line_connected": False,
            "line_connected_at": None,
            "has_used_referral": False,
            "referral_code": None,
            "referral_count": 0,
            "has_claimed_daily_login": False,
            "points_config": v2_config.get_points_summary()
        }

@router.post("/daily-login")
async def claim_daily_login_bonus(user_id: str = Depends(get_current_user)):
    """
    デイリーログインボーナス（1日1回、環境変数で設定されたポイント付与）
    """
    try:
        today = date.today().isoformat()
        
        # 今日既にログインボーナスを受け取ったかチェック
        existing = supabase.table("v2_point_transactions").select("id").eq("user_id", user_id).eq("transaction_type", "daily_login").gte("created_at", f"{today}T00:00:00").execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail="本日のログインボーナスは既に受け取り済みです")
        
        # ログインボーナスを付与（2ポイント）
        points_to_grant = v2_config.POINTS_DAILY_LOGIN
        service = V2PointsService()
        transaction = await service.grant_points(
            user_id=user_id,
            amount=points_to_grant,
            transaction_type="daily_login",
            description=f"デイリーログインボーナス（{points_to_grant}ポイント）"
        )
        
        # ユーザーの最終ログイン日時を更新
        supabase.table("v2_users").update({
            "last_login_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        return {
            "success": True,
            "message": "ログインボーナスを受け取りました",
            "points_granted": points_to_grant,
            "new_balance": transaction["balance_after"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ログインボーナスエラー: {e}")
        raise HTTPException(status_code=500, detail="ログインボーナスの受け取りに失敗しました")

@router.get("/referral/code")
async def get_my_referral_code(user_id: str = Depends(get_current_user)):
    """
    自分の紹介コードを取得（なければ生成）
    """
    try:
        # ユーザー情報を取得
        user_result = supabase.table("v2_users").select("referral_code").eq("id", user_id).execute()
        
        if not user_result.data:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        referral_code = user_result.data[0].get("referral_code")
        
        # 紹介コードがなければ生成
        if not referral_code:
            import random
            import string
            
            # 6文字の英数字コードを生成
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                # 重複チェック
                existing = supabase.table("v2_users").select("id").eq("referral_code", code).execute()
                if not existing.data:
                    # コードを保存
                    update_result = supabase.table("v2_users").update({
                        "referral_code": code
                    }).eq("id", user_id).execute()
                    
                    if update_result.data:
                        referral_code = code
                        break
        
        return {
            "referral_code": referral_code,
            "referral_url": f"https://www.dlogicai.in/v2?ref={referral_code}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"紹介コード取得エラー: {e}")
        raise HTTPException(status_code=500, detail="紹介コードの取得に失敗しました")

@router.get("/full-status")
async def get_line_referral_status(user_id: str = Depends(get_current_user)):
    """
    LINE連携・紹介状態・ログインボーナス状態を取得
    """
    try:
        # ユーザー情報を取得
        user_result = supabase.table("v2_users").select("*").eq("id", user_id).execute()
        
        if not user_result.data:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        user = user_result.data[0]
        
        # 紹介した人数を取得
        referral_count_result = supabase.table("v2_referral_history").select("id").eq("referrer_id", user_id).eq("status", "completed").execute()
        referral_count = len(referral_count_result.data) if referral_count_result.data else 0
        
        # 今日のログインボーナス受け取り状況
        today = date.today().isoformat()
        daily_login_result = supabase.table("v2_point_transactions").select("id").eq("user_id", user_id).eq("transaction_type", "daily_login").gte("created_at", f"{today}T00:00:00").execute()
        has_claimed_daily_login = bool(daily_login_result.data)
        
        # 現在のポイント設定を含める
        points_config = v2_config.get_points_summary()
        
        return {
            "line_connected": bool(user.get("line_user_id")),
            "line_connected_at": user.get("line_connected_at"),
            "has_used_referral": bool(user.get("referred_by")),
            "referral_code": user.get("referral_code"),
            "referral_count": referral_count,
            "has_claimed_daily_login": has_claimed_daily_login,
            "total_bonus_points": {
                "google_auth": points_config["google_auth"],
                "line_connection": points_config["line_connect"] if user.get("line_user_id") else 0,
                "referral_used": points_config["referral"] if user.get("referred_by") else 0,
                "daily_login": points_config["daily_login"] if has_claimed_daily_login else 0
            },
            "points_config": points_config
        }
        
    except Exception as e:
        logger.error(f"ステータス取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ステータスの取得に失敗しました")

@router.get("/config")
async def get_points_config():
    """
    現在のポイント設定を取得（公開情報）
    """
    return {
        "points_config": v2_config.get_points_summary(),
        "message": "現在のポイント設定"
    }