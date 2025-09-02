"""
V2 LINE OAuth認証処理
V1システムから独立した新しい実装
"""
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
import os
import logging
import secrets
import hashlib
import base64
import json
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode
from supabase import create_client, Client
from dotenv import load_dotenv

from api.v2.config import v2_config
from services.v2.points_service import V2PointsService

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/line/oauth", tags=["v2-line-oauth"])

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# LINE OAuth設定
LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_OAUTH_BASE_URL = "https://access.line.me/oauth2/v2.1/authorize"
LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_PROFILE_URL = "https://api.line.me/v2/profile"

# リダイレクトURL（本番環境）
REDIRECT_URI = "https://uma-i30n.onrender.com/api/v2/line/oauth/callback"
FRONTEND_SUCCESS_URL = "https://www.dlogicai.in/v2/my-account?line_connected=true"
FRONTEND_ERROR_URL = "https://www.dlogicai.in/v2/my-account?line_error=true"

# 開発環境の場合は環境変数で上書き可能
if os.getenv("ENVIRONMENT") == "development":
    REDIRECT_URI = os.getenv("LINE_REDIRECT_URI_DEV", REDIRECT_URI)
    FRONTEND_SUCCESS_URL = os.getenv("FRONTEND_SUCCESS_URL_DEV", FRONTEND_SUCCESS_URL)
    FRONTEND_ERROR_URL = os.getenv("FRONTEND_ERROR_URL_DEV", FRONTEND_ERROR_URL)

@router.get("/redirect")
async def line_oauth_redirect(request: Request, user_id: str = Query(None)):
    """
    LINE OAuth認証へリダイレクト
    フロントエンドから呼ばれるエンドポイント
    """
    try:
        if not LINE_CHANNEL_ID:
            logger.error("LINE_CHANNEL_ID is not configured")
            raise HTTPException(status_code=500, detail="LINE認証が設定されていません")
        
        # stateパラメータを生成（CSRF対策）
        state = secrets.token_urlsafe(32)
        
        # セッション情報を保存（5分間有効）
        session_data = {
            "state": state,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat()
        }
        
        # Supabaseにセッション情報を保存
        supabase.table("v2_line_oauth_sessions").insert(session_data).execute()
        
        # LINE OAuth URLを構築
        params = {
            "response_type": "code",
            "client_id": LINE_CHANNEL_ID,
            "redirect_uri": REDIRECT_URI,
            "state": state,
            "scope": "profile openid",
            "nonce": secrets.token_urlsafe(16),  # OpenID Connect用
        }
        
        auth_url = f"{LINE_OAUTH_BASE_URL}?{urlencode(params)}"
        
        logger.info(f"Redirecting to LINE OAuth: user_id={user_id}")
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"LINE OAuth redirect error: {e}")
        return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=oauth_setup_failed")

@router.get("/callback")
async def line_oauth_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None)
):
    """
    LINE OAuth認証のコールバック処理
    LINEから認証後にリダイレクトされるエンドポイント
    """
    try:
        # エラーチェック
        if error:
            logger.error(f"LINE OAuth error: {error} - {error_description}")
            return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message={error}")
        
        if not code or not state:
            logger.error("Missing code or state parameter")
            return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=invalid_parameters")
        
        # セッション情報を取得
        session_result = supabase.table("v2_line_oauth_sessions")\
            .select("*")\
            .eq("state", state)\
            .gte("expires_at", datetime.now().isoformat())\
            .execute()
        
        if not session_result.data:
            logger.error(f"Invalid or expired state: {state}")
            return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=session_expired")
        
        session = session_result.data[0]
        user_id = session.get("user_id")
        
        # セッションを削除（使い回し防止）
        supabase.table("v2_line_oauth_sessions").delete().eq("state", state).execute()
        
        # アクセストークンを取得
        token_data = await get_access_token(code)
        if not token_data:
            logger.error("Failed to get access token")
            return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=token_failed")
        
        access_token = token_data.get("access_token")
        id_token = token_data.get("id_token")  # OpenID Connect
        
        # LINEプロフィールを取得
        profile = await get_line_profile(access_token)
        if not profile:
            logger.error("Failed to get LINE profile")
            return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=profile_failed")
        
        line_user_id = profile.get("userId")
        line_display_name = profile.get("displayName", "")
        line_picture_url = profile.get("pictureUrl", "")
        
        # ユーザー情報を取得
        user_result = supabase.table("v2_users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            logger.error(f"User not found: {user_id}")
            return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=user_not_found")
        
        user = user_result.data[0]
        
        # 初回LINE連携かチェック
        is_first_connection = not user.get("line_user_id")
        
        # 既存のLINE連携をチェック（同じLINE IDが既に使われていないか）
        if is_first_connection:
            existing_line = supabase.table("v2_users")\
                .select("id")\
                .eq("line_user_id", line_user_id)\
                .neq("id", user_id)\
                .execute()
            
            if existing_line.data:
                logger.warning(f"LINE ID {line_user_id} is already linked to another account")
                # 不正利用記録
                supabase.table("v2_line_duplicate_attempts").insert({
                    "line_user_id": line_user_id,
                    "attempted_by_user_id": user_id,
                    "existing_user_ids": [u["id"] for u in existing_line.data],
                    "attempted_at": datetime.now().isoformat()
                }).execute()
                return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=line_already_linked")
        
        # ユーザー情報を更新
        update_data = {
            "line_user_id": line_user_id,
            "line_display_name": line_display_name,
            "line_picture_url": line_picture_url,
            "line_connected_at": datetime.now().isoformat(),
            "line_access_token": access_token,  # 必要に応じて暗号化
            "updated_at": datetime.now().isoformat()
        }
        
        update_result = supabase.table("v2_users")\
            .update(update_data)\
            .eq("id", user_id)\
            .execute()
        
        if not update_result.data:
            logger.error(f"Failed to update user: {user_id}")
            return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=update_failed")
        
        # 初回連携の場合はポイント付与と紹介ボーナス処理
        points_granted = 0
        referral_bonus_info = None
        if is_first_connection:
            points_to_grant = v2_config.POINTS_LINE_CONNECT
            service = V2PointsService()
            try:
                transaction = await service.grant_points(
                    user_id=user_id,
                    amount=points_to_grant,
                    transaction_type="line_connection",
                    description=f"LINE連携によるポイント付与（{points_to_grant}ポイント）"
                )
                points_granted = points_to_grant
                logger.info(f"Granted {points_to_grant} points to user {user_id} for LINE connection")
                
                # 紹介ボーナス処理（LINE連携完了時）
                if user.get("referred_by") and not user.get("referral_bonus_granted"):
                    # 紹介者情報を取得
                    referrer_result = supabase.table("v2_users").select("*").eq("id", user["referred_by"]).execute()
                    if referrer_result.data:
                        referrer = referrer_result.data[0]
                        
                        # 紹介者のLINE連携済み紹介人数をカウント
                        referred_users_result = supabase.table("v2_referral_history").select(
                            "referred_id"
                        ).eq("referrer_id", referrer["id"]).eq("status", "line_connected").execute()
                        
                        line_connected_count = len(referred_users_result.data) if referred_users_result.data else 0
                        new_line_connected_count = line_connected_count + 1
                        
                        # 紹介者に段階的ポイント付与
                        points_for_referrer = v2_config.get_referral_points_for_count(new_line_connected_count)
                        if points_for_referrer > 0:
                            referrer_transaction = await service.grant_points(
                                user_id=referrer["id"],
                                amount=points_for_referrer,
                                transaction_type="referral_line_bonus",
                                description=f"{new_line_connected_count}人目の友達がLINE連携完了（{points_for_referrer}ポイント）",
                                related_entity_id=user_id
                            )
                            
                            # 紹介履歴のステータスを更新
                            supabase.table("v2_referral_history").update({
                                "status": "line_connected",
                                "line_connected_at": datetime.now().isoformat()
                            }).eq("referrer_id", referrer["id"]).eq("referred_id", user_id).execute()
                            
                            # ユーザーのボーナス付与フラグを更新
                            supabase.table("v2_users").update({
                                "referral_bonus_granted": True
                            }).eq("id", user_id).execute()
                            
                            # 紹介者のLINE連携済み紹介人数を更新
                            supabase.table("v2_users").update({
                                "line_connected_referral_count": new_line_connected_count
                            }).eq("id", referrer["id"]).execute()
                            
                            referral_bonus_info = {
                                "referrer_bonus": points_for_referrer,
                                "referrer_name": referrer.get("name", "友達")
                            }
                            logger.info(f"Granted {points_for_referrer} points to referrer {referrer['id']} for LINE connection")
                
            except Exception as e:
                logger.error(f"Failed to grant points: {e}")
                # ポイント付与に失敗してもLINE連携は成功とする
        
        # 成功URLにリダイレクト
        success_params = {
            "line_connected": "true",
            "points_granted": str(points_granted) if points_granted > 0 else None,
            "line_name": line_display_name
        }
        
        # 紹介ボーナス情報があれば追加
        if referral_bonus_info:
            success_params["referral_bonus"] = str(referral_bonus_info["referrer_bonus"])
            success_params["referrer_name"] = referral_bonus_info["referrer_name"]
        
        success_params = {k: v for k, v in success_params.items() if v is not None}
        success_url = f"{FRONTEND_SUCCESS_URL}&{urlencode(success_params)}"
        
        logger.info(f"LINE OAuth successful for user {user_id}")
        return RedirectResponse(url=success_url)
        
    except Exception as e:
        logger.error(f"LINE OAuth callback error: {e}")
        return RedirectResponse(url=f"{FRONTEND_ERROR_URL}&message=unexpected_error")

async def get_access_token(code: str) -> dict:
    """認証コードからアクセストークンを取得"""
    try:
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": LINE_CHANNEL_ID,
                "client_secret": LINE_CHANNEL_SECRET
            }
            
            response = await client.post(
                LINE_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token request failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Failed to get access token: {e}")
        return None

async def get_line_profile(access_token: str) -> dict:
    """アクセストークンからLINEプロフィールを取得"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                LINE_PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Profile request failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Failed to get LINE profile: {e}")
        return None

@router.delete("/disconnect")
async def disconnect_line_account(user_id: str):
    """
    LINE連携を解除（管理者用）
    """
    try:
        # ユーザー情報をクリア
        update_result = supabase.table("v2_users")\
            .update({
                "line_user_id": None,
                "line_display_name": None,
                "line_picture_url": None,
                "line_connected_at": None,
                "line_access_token": None,
                "updated_at": datetime.now().isoformat()
            })\
            .eq("id", user_id)\
            .execute()
        
        if not update_result.data:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        logger.info(f"LINE disconnected for user {user_id}")
        return {"success": True, "message": "LINE連携を解除しました"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect LINE: {e}")
        raise HTTPException(status_code=500, detail="LINE連携の解除に失敗しました")