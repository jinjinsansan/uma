"""
V2 LINE Webhook エンドポイント
Supabaseのv2_usersテーブルを使用した認証処理
"""

from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import json
from datetime import datetime
import os
from supabase import create_client, Client
import hashlib
import hmac
import base64

logger = logging.getLogger(__name__)

router = APIRouter(tags=["v2-line-webhook"])

# Supabase設定
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing Supabase configuration")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# LINE設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

class LineWebhookRequest(BaseModel):
    """LINE Webhookリクエスト"""
    destination: str
    events: List[Dict[str, Any]]

def verify_line_signature(body: bytes, signature: str) -> bool:
    """LINE署名を検証"""
    if not LINE_CHANNEL_SECRET:
        # 開発環境では署名検証をスキップ
        return True
    
    hash_digest = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    
    calculated_signature = base64.b64encode(hash_digest).decode('utf-8')
    return calculated_signature == signature

@router.post("/api/v2/line/webhook")
async def line_webhook_v2(
    request: Request,
    x_line_signature: str = Header(None)
):
    """V2 LINE Webhook エンドポイント"""
    try:
        body = await request.body()
        
        # 署名検証（本番環境のみ）
        if os.getenv("ENVIRONMENT") == "production" and x_line_signature:
            if not verify_line_signature(body, x_line_signature):
                logger.warning("Invalid LINE signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        data = json.loads(body.decode('utf-8'))
        webhook_request = LineWebhookRequest(**data)
        
        for event in webhook_request.events:
            await handle_line_event_v2(event)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"V2 LINE Webhook error: {e}")
        # LINEには200を返す（再送を防ぐため）
        return {"status": "error", "message": str(e)}

async def handle_line_event_v2(event: Dict[str, Any]):
    """V2 LINEイベント処理"""
    event_type = event.get('type')
    
    if event_type == "message" and event.get('message', {}).get('type') == 'text':
        # テキストメッセージを受信
        await handle_message_v2(event)
    elif event_type == "follow":
        # 友達追加
        logger.info(f"V2 LINE friend added: {event.get('source', {}).get('userId')}")
    elif event_type == "unfollow":
        # 友達削除
        logger.info(f"V2 LINE friend removed: {event.get('source', {}).get('userId')}")

async def handle_message_v2(event: Dict[str, Any]):
    """V2 メッセージ処理（認証コード処理）"""
    try:
        line_user_id = event.get('source', {}).get('userId')
        message_text = event.get('message', {}).get('text', '').strip().upper()
        
        if not line_user_id or not message_text:
            return
        
        logger.info(f"V2 LINE message from {line_user_id}: {message_text}")
        
        # 認証コードかチェック（6-8文字の英数字）
        if 6 <= len(message_text) <= 8 and message_text.isalnum():
            # v2_usersテーブルから認証コードを検索
            user_result = supabase.table("v2_users").select("*").eq(
                "line_verification_code", message_text
            ).eq("is_line_connected", False).execute()
            
            if user_result.data and len(user_result.data) > 0:
                user = user_result.data[0]
                user_id = user.get('id')
                
                # LINE連携を完了
                update_result = supabase.table("v2_users").update({
                    "is_line_connected": True,
                    "line_user_id": line_user_id,
                    "line_connected_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }).eq("id", user_id).execute()
                
                if update_result.data:
                    logger.info(f"V2 LINE connection successful for user {user_id}")
                    print(f"✅ LINE連携成功: ユーザーID={user_id}, LINE_ID={line_user_id}")

                    # ポイント付与設定を取得
                    # 環境変数から取得（デフォルト: 24）
                    line_points = int(os.getenv("LINE_CONNECT_POINTS", "24"))

                    print(f"💰 ポイント設定: {line_points}ポイント (環境変数から取得)")

                    # ポイント付与
                    points_result = supabase.table("v2_user_points").select("*").eq(
                        "user_id", user_id
                    ).execute()
                    
                    if points_result.data and len(points_result.data) > 0:
                        current_points = points_result.data[0]
                        new_points = current_points.get('current_points', 0) + line_points
                        new_earned = current_points.get('total_earned', 0) + line_points
                        
                        # ポイント更新
                        supabase.table("v2_user_points").update({
                            "current_points": new_points,
                            "total_earned": new_earned,
                            "updated_at": datetime.now().isoformat()
                        }).eq("user_id", user_id).execute()
                    else:
                        # ポイントレコード作成
                        supabase.table("v2_user_points").insert({
                            "user_id": user_id,
                            "current_points": line_points,
                            "total_earned": line_points,
                            "total_spent": 0,
                            "created_at": datetime.now().isoformat()
                        }).execute()
                    
                    # ポイント履歴記録
                    transaction_result = supabase.table("v2_point_transactions").insert({
                        "user_id": user_id,
                        "amount": line_points,
                        "transaction_type": "line_connect",
                        "description": "LINE連携ボーナス",
                        "balance_after": new_points if points_result.data else line_points,
                        "created_at": datetime.now().isoformat()
                    }).execute()

                    if transaction_result.data:
                        final_points = new_points if points_result.data else line_points
                        print(f"🎉 LINE連携ポイント付与完了!")
                        print(f"   ユーザー: {user.get('email', 'unknown')}")
                        print(f"   付与ポイント: {line_points}ポイント")
                        print(f"   現在の残高: {final_points}ポイント")
                        print(f"   認証コード: {message_text}")
                        print("="*50)
                    else:
                        print(f"❌ ポイント履歴記録失敗: user_id={user_id}")

                    # TODO: LINE返信メッセージ送信（LINE Messaging APIが必要）
                    # 今は返信なし
                    
                else:
                    logger.error(f"Failed to update LINE connection for user {user_id}")
                    print(f"❌ LINE連携更新失敗: user_id={user_id}")
            else:
                logger.info(f"Invalid or used verification code: {message_text}")
                print(f"⚠️ 無効な認証コード または 使用済み: {message_text}")
                # TODO: エラーメッセージを送信
        
    except Exception as e:
        logger.error(f"V2 message handling error: {e}")
        print(f"🚨 エラー発生: LINE webhook処理失敗")
        print(f"   エラー内容: {e}")
        print(f"   LINE_USER_ID: {line_user_id if 'line_user_id' in locals() else '不明'}")
        print(f"   メッセージ: {message_text if 'message_text' in locals() else '不明'}")
        print("="*50)