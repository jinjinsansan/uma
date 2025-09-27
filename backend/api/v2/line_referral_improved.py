"""
V2 LINE連携・友達紹介API（改善版）
LINE連携完了時に紹介ボーナスを付与する仕組み
同一LINEアカウントの使い回し防止機能付き
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
router = APIRouter(prefix="/api/v2/line", tags=["v2-line-referral-improved"])

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

async def check_line_id_duplicate(line_user_id: str, current_user_id: str) -> bool:
    """
    LINE IDの重複チェック
    同じLINE IDが他のユーザーで既に使用されていないかチェック
    """
    try:
        # 同じLINE IDを持つ他のユーザーを検索
        existing_users = supabase.table("v2_users").select("id, email, created_at").eq("line_user_id", line_user_id).neq("id", current_user_id).execute()
        
        if existing_users.data and len(existing_users.data) > 0:
            # 重複が見つかった場合、ログに記録
            logger.warning(f"LINE ID重複検出: {line_user_id} - 既存ユーザー: {existing_users.data}")
            
            # 不正利用履歴を記録
            supabase.table("v2_line_duplicate_attempts").insert({
                "line_user_id": line_user_id,
                "attempted_by_user_id": current_user_id,
                "existing_user_ids": [user["id"] for user in existing_users.data],
                "attempted_at": datetime.now().isoformat()
            }).execute()
            
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"LINE ID重複チェックエラー: {e}")
        return False

async def process_referral_bonus_on_line_connect(user_id: str):
    """
    LINE連携完了時に紹介ボーナスを処理
    紹介コードを使用していて、まだボーナスが付与されていない場合に実行
    """
    try:
        # ユーザー情報を取得
        user_result = supabase.table("v2_users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            return None
        
        user = user_result.data[0]
        
        # 紹介者がいて、まだボーナスを受け取っていない場合
        if user.get("referred_by") and not user.get("referral_bonus_granted"):
            # 紹介者情報を取得
            referrer_result = supabase.table("v2_users").select("*").eq("id", user["referred_by"]).execute()
            if not referrer_result.data:
                return None
            
            referrer = referrer_result.data[0]

            # 紹介履歴が存在しない場合は整備
            history_record = None
            try:
                history_record = supabase.table("v2_referral_history") \
                    .select("id, status") \
                    .eq("referrer_id", referrer["id"]) \
                    .eq("referred_id", user_id) \
                    .single() \
                    .execute()
            except Exception as history_error:
                history_record = None
                if getattr(history_error, "code", None) != "PGRST116":
                    logger.warning(f"紹介履歴取得エラー: {history_error}")

            if history_record and history_record.data:
                existing = history_record.data
                if existing.get("status") != "line_connected":
                    supabase.table("v2_referral_history").update({
                        "referral_code": existing.get("referral_code"),
                        "status": "pending",
                        "line_connected_at": None
                    }).eq("id", existing["id"]).execute()
            else:
                supabase.table("v2_referral_history").insert({
                    "referrer_id": referrer["id"],
                    "referred_id": user_id,
                    "referral_code": referrer.get("referral_code"),
                    "status": "pending"
                }).execute()
            
            # 紹介者のLINE連携済み紹介人数をカウント
            # v2_referral_historyテーブルから、紹介者が紹介した人でLINE連携済みの人数を取得
            referred_users_result = supabase.table("v2_referral_history").select(
                "referred_id"
            ).eq("referrer_id", referrer["id"]).eq("status", "line_connected").execute()
            
            line_connected_count = len(referred_users_result.data) if referred_users_result.data else 0
            new_line_connected_count = line_connected_count + 1
            
            # 紹介者に段階的ポイント付与
            points_for_referrer = v2_config.get_referral_points_for_count(new_line_connected_count)
            if points_for_referrer > 0:
                service = V2PointsService()
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
                
                logger.info(f"紹介者{referrer['id']}に{points_for_referrer}ポイント付与（LINE連携{new_line_connected_count}人目）")
                return {
                    "referrer_bonus": points_for_referrer,
                    "referrer_name": referrer.get("name", "友達"),
                    "line_connected_count": new_line_connected_count
                }
        
        return None
        
    except Exception as e:
        logger.error(f"紹介ボーナス処理エラー: {e}")
        return None

@router.post("/connect")
async def connect_line_account(
    request: LineConnectRequest,
    user_id: str = Depends(get_current_user)
):
    """
    LINE連携（環境変数で設定されたポイント付与 + 紹介ボーナス処理）
    同一LINE IDの使い回し防止機能付き
    """
    try:
        # 既にLINE連携済みかチェック
        existing = supabase.table("v2_users").select("line_user_id").eq("id", user_id).execute()
        
        if existing.data and existing.data[0].get("line_user_id"):
            raise HTTPException(status_code=400, detail="既にLINE連携済みです")
        
        # LINE IDの重複チェック（同じLINE IDが他のユーザーで使われていないか）
        is_duplicate = await check_line_id_duplicate(request.line_user_id, user_id)
        if is_duplicate:
            raise HTTPException(
                status_code=400, 
                detail="このLINEアカウントは既に他のユーザーと連携されています。別のLINEアカウントをご使用ください。"
            )
        
        # LINE user_idを更新
        update_result = supabase.table("v2_users").update({
            "line_user_id": request.line_user_id,
            "line_connected_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="LINE連携の更新に失敗しました")
        
        # LINE連携履歴を記録（監査用）
        supabase.table("v2_line_connection_history").insert({
            "user_id": user_id,
            "line_user_id": request.line_user_id,
            "connected_at": datetime.now().isoformat(),
            "status": "success"
        }).execute()
        
        # LINE連携ポイント付与
        points_to_grant = v2_config.POINTS_LINE_CONNECT
        service = V2PointsService()
        transaction = await service.grant_points(
            user_id=user_id,
            amount=points_to_grant,
            transaction_type="line_connection",
            description=f"LINE連携によるポイント付与（{points_to_grant}ポイント）"
        )
        
        # 紹介ボーナス処理（LINE連携完了時）
        referral_bonus_result = await process_referral_bonus_on_line_connect(user_id)
        
        response_data = {
            "success": True,
            "message": "LINE連携が完了しました",
            "points_granted": points_to_grant,
            "new_balance": transaction["balance_after"]
        }
        
        # 紹介ボーナスがあった場合は情報を追加
        if referral_bonus_result:
            response_data["referral_bonus_info"] = {
                "referrer_received": referral_bonus_result["referrer_bonus"],
                "referrer_name": referral_bonus_result["referrer_name"],
                "message": f"{referral_bonus_result['referrer_name']}さんに{referral_bonus_result['referrer_bonus']}ポイントが付与されました"
            }
        
        return response_data
        
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
    友達紹介コード適用（被紹介者のポイントのみ付与、紹介者ボーナスはLINE連携時）
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
        
        # IPアドレスチェック（同一IPから大量の紹介を防ぐ）
        # これは別途実装が必要（リクエストからIPを取得する処理）
        
        # 被紹介者の情報を更新
        update_result = supabase.table("v2_users").update({
            "referred_by": referrer["id"],
            "referred_at": datetime.now().isoformat(),
            "referral_bonus_granted": False  # まだ紹介ボーナスは付与されていない
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="紹介情報の更新に失敗しました")
        
        # 被紹介者にポイント付与
        points_for_referred = v2_config.POINTS_REFERRAL_RECEIVED
        service = V2PointsService()
        referred_transaction = await service.grant_points(
            user_id=user_id,
            amount=points_for_referred,
            transaction_type="referral_applied",
            description=f"友達紹介コード使用によるポイント付与（{points_for_referred}ポイント）",
            related_entity_id=referrer["id"]
        )
        
        # 紹介履歴を記録（既存のレコードがあれば更新）
        history_record = None
        try:
            history_record = supabase.table("v2_referral_history") \
                .select("id, status") \
                .eq("referrer_id", referrer["id"]) \
                .eq("referred_id", user_id) \
                .single() \
                .execute()
        except Exception as history_error:
            if getattr(history_error, "code", None) != "PGRST116":
                logger.warning(f"紹介履歴取得エラー: {history_error}")

        if history_record and history_record.data:
            existing = history_record.data
            supabase.table("v2_referral_history").update({
                "referral_code": request.referral_code.upper(),
                "status": "pending",
                "line_connected_at": None
            }).eq("id", existing["id"]).execute()
        else:
            supabase.table("v2_referral_history").insert({
                "referrer_id": referrer["id"],
                "referred_id": user_id,
                "referral_code": request.referral_code.upper(),
                "status": "pending"
            }).execute()
        
        return {
            "success": True,
            "message": "紹介コードが適用されました",
            "points_granted": points_for_referred,
            "new_balance": referred_transaction["balance_after"],
            "referrer_name": referrer.get("name", "友達"),
            "note": "LINE連携を完了すると、紹介者にもボーナスポイントが付与されます"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"紹介コード適用エラー: {e}")
        raise HTTPException(status_code=500, detail="紹介コードの適用に失敗しました")

def generate_referral_code(email: str) -> str:
    """メールアドレスから6文字の紹介コードを生成（フロントエンドと同じアルゴリズム）"""
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    hash_value = 0
    for i in range(len(email)):
        hash_value = ((hash_value << 5) - hash_value) + ord(email[i])
        hash_value = hash_value & 0x7FFFFFFF  # 32bit integer
    hash_value = abs(hash_value)
    code = ''
    for _ in range(6):
        code += chars[hash_value % len(chars)]
        hash_value = hash_value // len(chars)
    return code

@router.get("/referral/status")
async def get_referral_status(user_id: str = Depends(get_current_user)):
    """
    友達紹介の状態を取得（LINE連携済み人数を含む）
    """
    try:
        # ユーザー情報を取得
        user_result = supabase.table("v2_users").select("*").eq("id", user_id).execute()
        
        if not user_result.data:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        user = user_result.data[0]
        
        # referral_codeがない場合は生成して保存
        if not user.get("referral_code") and user.get("email"):
            referral_code = generate_referral_code(user["email"])
            supabase.table("v2_users").update({
                "referral_code": referral_code
            }).eq("id", user_id).execute()
            user["referral_code"] = referral_code
            logger.info(f"Generated referral code for user {user_id}: {referral_code}")
        
        # 紹介した人のうちLINE連携済みの人数を取得
        line_connected_result = supabase.table("v2_referral_history").select(
            "id"
        ).eq("referrer_id", user_id).eq("status", "line_connected").execute()
        
        line_connected_count = len(line_connected_result.data) if line_connected_result.data else 0
        
        # 紹介待ちの人数を取得
        pending_result = supabase.table("v2_referral_history").select(
            "id"
        ).eq("referrer_id", user_id).eq("status", "pending").execute()
        
        pending_count = len(pending_result.data) if pending_result.data else 0
        
        # 次の紹介ボーナス
        next_bonus = v2_config.get_referral_points_for_count(line_connected_count + 1)
        
        return {
            "referral_code": user.get("referral_code"),
            "line_connected_referral_count": line_connected_count,
            "pending_referral_count": pending_count,
            "total_referral_count": line_connected_count + pending_count,
            "next_bonus_points": next_bonus,
            "referral_url": f"https://www.dlogicai.in/v2?ref={user.get('referral_code')}" if user.get("referral_code") else None,
            "bonus_structure": {
                "1人目": v2_config.POINTS_REFERRAL_1,
                "2人目": v2_config.POINTS_REFERRAL_2,
                "3人目": v2_config.POINTS_REFERRAL_3,
                "4人目": v2_config.POINTS_REFERRAL_4,
                "5人目以降": v2_config.POINTS_REFERRAL_5
            }
        }
        
    except Exception as e:
        logger.error(f"紹介状態取得エラー: {e}")
        raise HTTPException(status_code=500, detail="紹介状態の取得に失敗しました")

@router.post("/disconnect")
async def disconnect_line_account(user_id: str = Depends(get_current_user)):
    """
    LINE連携を解除（ユーザー自身が解除する場合）
    """
    try:
        # ユーザー情報を取得
        user_result = supabase.table("v2_users").select("line_user_id").eq("id", user_id).execute()
        
        if not user_result.data or not user_result.data[0].get("line_user_id"):
            raise HTTPException(status_code=400, detail="LINE連携されていません")
        
        old_line_id = user_result.data[0].get("line_user_id")
        
        # LINE連携を解除
        update_result = supabase.table("v2_users").update({
            "line_user_id": None,
            "line_connected_at": None
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="LINE連携の解除に失敗しました")
        
        # 解除履歴を記録
        supabase.table("v2_line_connection_history").insert({
            "user_id": user_id,
            "line_user_id": old_line_id,
            "connected_at": datetime.now().isoformat(),
            "status": "disconnected"
        }).execute()
        
        return {
            "success": True,
            "message": "LINE連携を解除しました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LINE連携解除エラー: {e}")
        raise HTTPException(status_code=500, detail="LINE連携の解除に失敗しました")

# 既存のエンドポイントもそのまま残す（互換性のため）
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
        
        # ログインボーナスを付与
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

@router.get("/status")
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
        
        # LINE連携済み紹介人数を取得
        line_connected_result = supabase.table("v2_referral_history").select(
            "id"
        ).eq("referrer_id", user_id).eq("status", "line_connected").execute()
        line_connected_count = len(line_connected_result.data) if line_connected_result.data else 0
        
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
            "line_connected_referral_count": line_connected_count,
            "has_claimed_daily_login": has_claimed_daily_login,
            "total_bonus_points": {
                "google_auth": points_config["google_auth"],
                "line_connection": points_config["line_connect"] if user.get("line_user_id") else 0,
                "referral_used": points_config["referral_received"] if user.get("referred_by") else 0,
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