"""
LINE Messaging API連携（修正版）
友達追加・メッセージ送受信・延長チケット配布機能
"""

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional, List
import hashlib
import hmac
import base64
import json
import os
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv
import logging
import time
from collections import defaultdict

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()

# レート制限のためのグローバル変数
rate_limiter = defaultdict(list)

# LINE設定
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'your-channel-secret')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'your-access-token')
LINE_ACCOUNT_ID = os.getenv('LINE_ACCOUNT_ID', '@082thmrq')

# データベース接続
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'mykeibadb'),
        charset='utf8mb4'
    )

# Pydanticモデル
class LineWebhookEvent(BaseModel):
    type: str
    source: dict
    timestamp: int
    message: Optional[dict] = None
    replyToken: Optional[str] = None

class LineWebhookRequest(BaseModel):
    events: List[LineWebhookEvent]
    destination: str

class LineTicketRequest(BaseModel):
    user_email: str
    line_user_id: str
    verification_code: str

def verify_line_signature(body: bytes, signature: str) -> bool:
    """LINE署名検証"""
    hash = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash).decode('utf-8')
    return hmac.compare_digest(signature, expected_signature)

async def check_line_id_duplicate(line_user_id: str, current_user_id: str, cursor) -> dict:
    """LINE ID重複チェック"""
    try:
        # 既に同じLINE IDを使用しているユーザーがいるかチェック
        cursor.execute("""
            SELECT lu.user_id, u.email, lu.friend_added_at 
            FROM line_users lu
            JOIN users u ON lu.user_id = u.id
            WHERE lu.line_user_id = %s AND lu.user_id != %s
            ORDER BY lu.friend_added_at ASC
            LIMIT 1
        """, (line_user_id, current_user_id))
        
        existing = cursor.fetchone()
        
        if existing:
            return {
                'is_duplicate': True,
                'existing_user_id': existing['user_id'],
                'existing_email': existing['email'],
                'existing_date': existing['friend_added_at'].strftime('%Y-%m-%d') if existing['friend_added_at'] else '不明'
            }
        else:
            return {
                'is_duplicate': False
            }
    except Exception as e:
        logger.error(f"LINE ID duplicate check error: {e}")
        # エラーが発生した場合は重複なしとして処理を続行
        return {
            'is_duplicate': False
        }

async def update_referral_status(user_email: str):
    """Supabaseの紹介記録を更新する共通関数"""
    try:
        from supabase import create_client, Client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found")
            return False
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # メールアドレスからSupabaseユーザーIDを取得
        user_result = supabase.table('users').select('id, referral_code').eq('email', user_email).execute()
        
        if not user_result.data or len(user_result.data) == 0:
            logger.warning(f"Supabase user not found for email: {user_email}")
            return False
        
        supabase_user_id = user_result.data[0]['id']
        user_referral_code = user_result.data[0].get('referral_code')
        logger.info(f"Found Supabase user: {supabase_user_id} for email: {user_email}, referral_code: {user_referral_code}")
        
        # アプローチ1: referred_idで検索
        logger.info(f"Approach 1: Searching for pending referral with referred_id: {supabase_user_id}")
        referral_result = supabase.table('line_referrals').select('*').eq('referred_id', supabase_user_id).eq('status', 'pending').execute()
        
        # アプローチ2: 紹介コードで検索（ユーザーが再作成された場合）
        if not referral_result.data and user_referral_code:
            logger.info(f"Approach 2: Searching by referral_code: {user_referral_code}")
            # 紹介コードで紹介記録を検索
            code_referral_result = supabase.table('line_referrals').select('*').eq('referral_code', user_referral_code).eq('status', 'pending').execute()
            
            if code_referral_result.data and len(code_referral_result.data) > 0:
                # referred_idを更新
                referral_id = code_referral_result.data[0]['id']
                logger.info(f"Found referral by code, updating referred_id to {supabase_user_id}")
                supabase.table('line_referrals').update({
                    'referred_id': supabase_user_id
                }).eq('id', referral_id).execute()
                
                referral_result = code_referral_result
        
        logger.info(f"Referral query result: {referral_result.data}")
        
        if not referral_result.data or len(referral_result.data) == 0:
            # 全ての紹介記録を確認（デバッグ用）
            all_referrals = supabase.table('line_referrals').select('*').eq('referred_id', supabase_user_id).execute()
            logger.info(f"All referrals for this user: {all_referrals.data}")
            logger.info(f"No pending referral found for user {user_email} (ID: {supabase_user_id})")
            return False
        
        referral = referral_result.data[0]
        referral_id = referral['id']
        referrer_id = referral['referrer_id']
        
        logger.info(f"Found pending referral: {referral_id} for user {user_email}")
        
        # 紹介記録をcompletedに更新
        update_result = supabase.table('line_referrals').update({
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }).eq('id', referral_id).execute()
        
        if not update_result.data:
            logger.error(f"Failed to update referral status for {referral_id}")
            return False
        
        logger.info(f"Successfully updated referral status to completed for {referral_id}")
        
        # 紹介者のreferral_countを更新
        referrer_result = supabase.table('users').select('referral_count').eq('id', referrer_id).execute()
        
        if referrer_result.data and len(referrer_result.data) > 0:
            current_count = referrer_result.data[0].get('referral_count', 0) or 0
            new_count = current_count + 1
            
            count_update_result = supabase.table('users').update({
                'referral_count': new_count
            }).eq('id', referrer_id).execute()
            
            if count_update_result.data:
                logger.info(f"Successfully updated referral_count to {new_count} for referrer {referrer_id}")
            else:
                logger.error(f"Failed to update referral_count for referrer {referrer_id}")
        
        # 紹介通知フラグをセット（エラーハンドリング付き）
        try:
            referrer_code_result = supabase.table('users').select('referral_code').eq('id', referrer_id).execute()
            if referrer_code_result.data and len(referrer_code_result.data) > 0:
                referrer_code = referrer_code_result.data[0]['referral_code']
                
                # pending_referral_notificationフィールドが存在しない場合はスキップ
                supabase.table('users').update({
                    'pending_referral_notification': json.dumps({
                        'type': 'referred',
                        'referral_code': referrer_code,
                        'created_at': datetime.now().isoformat()
                    })
                }).eq('id', supabase_user_id).execute()
        except Exception as e:
            logger.warning(f"Failed to set pending_referral_notification: {e}")
            # このエラーは無視して処理を続行
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating referral status: {str(e)}")
        return False

@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None)
):
    """LINE Webhook エンドポイント"""
    try:
        body = await request.body()
        
        # 署名検証（開発環境では省略可能）
        if x_line_signature and not verify_line_signature(body, x_line_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        data = json.loads(body.decode('utf-8'))
        webhook_request = LineWebhookRequest(**data)
        
        for event in webhook_request.events:
            await handle_line_event(event)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"LINE Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_line_event(event: LineWebhookEvent):
    """LINEイベント処理"""
    if event.type == "follow":
        # 友達追加イベント
        await handle_friend_added(event)
    elif event.type == "message" and event.message:
        # メッセージイベント
        await handle_message(event)
    elif event.type == "unfollow":
        # 友達解除イベント
        await handle_friend_removed(event)

async def handle_friend_added(event: LineWebhookEvent):
    """友達追加時の処理"""
    line_user_id = event.source.get('userId')
    if not line_user_id:
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 友達追加記録（まだユーザー連携前）
        cursor.execute("""
            INSERT INTO line_pending_friends (line_user_id, added_at)
            VALUES (%s, NOW())
            ON DUPLICATE KEY UPDATE added_at = NOW()
        """, (line_user_id,))
        conn.commit()
        
        # ウェルカムメッセージ送信
        welcome_message = """🎉 D-Logic AI公式LINEへようこそ！

🎁 1日の分析回数を増やすには：
1. D-Logic AIサイトでGoogleログイン
2. マイページで認証コードを取得
3. このLINEに認証コードを送信

📱 サイト: https://www.dlogicai.in/?openExternalBrowser=1

競馬予想の新時代をお楽しみください！"""
        
        await send_line_message(line_user_id, welcome_message)
        
    except Exception as e:
        logger.error(f"Friend added error: {e}")
    finally:
        if conn:
            conn.close()

async def handle_message(event: LineWebhookEvent):
    """メッセージ受信時の処理"""
    line_user_id = event.source.get('userId')
    message_text = event.message.get('text', '').strip().upper()
    
    if not line_user_id or not message_text:
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 認証コードかチェック（6文字の英数字）
        if len(message_text) == 6 and message_text.isalnum():
            # 認証コード処理
            cursor.execute("""
                SELECT * FROM line_verification_codes 
                WHERE code = %s AND used = FALSE 
                AND created_at > DATE_SUB(NOW(), INTERVAL 10 MINUTE)
            """, (message_text,))
            verification = cursor.fetchone()
            
            if verification:
                # ユーザーと連携
                user_id = verification['user_id']
                
                # 既に連携済みかチェック
                cursor.execute("""
                    SELECT * FROM line_users WHERE user_id = %s
                """, (user_id,))
                existing = cursor.fetchone()
                
                if not existing:
                    # LINE ID重複チェック
                    duplicate_check_result = await check_line_id_duplicate(line_user_id, user_id, cursor)
                    
                    if duplicate_check_result['is_duplicate']:
                        # 重複が検出された場合
                        warning_message = f"""⚠️ 警告: LINE ID重複検出
                        
このLINE IDは既に他のアカウントで使用されています。

既存のアカウント: {duplicate_check_result['existing_email']}
登録日: {duplicate_check_result['existing_date']}

不正利用の可能性があるため、管理者に報告されました。
正当な理由がある場合は、サポートまでお問い合わせください。

サポート: https://www.dlogicai.in/?openExternalBrowser=1"""
                        
                        await send_line_message(line_user_id, warning_message)
                        
                        # 管理者に通知（ログ記録）
                        logger.warning(f"LINE ID duplicate detected: {line_user_id} - User: {user_id}, Existing: {duplicate_check_result['existing_user_id']}")
                        return
                    
                    # LINE連携記録
                    cursor.execute("""
                        INSERT INTO line_users (user_id, line_user_id, tickets_received, friend_added_at)
                        VALUES (%s, %s, 1, NOW())
                    """, (user_id, line_user_id))
                    
                    # 無料期間延長（旧仕様、現在は使用回数増加）
                    cursor.execute("""
                        UPDATE users 
                        SET free_trial_end_date = DATE_ADD(
                            COALESCE(free_trial_end_date, NOW()), 
                            INTERVAL 3 DAY
                        )
                        WHERE id = %s
                    """, (user_id,))
                    
                    # 認証コードを使用済みに
                    cursor.execute("""
                        UPDATE line_verification_codes 
                        SET used = TRUE WHERE id = %s
                    """, (verification['id'],))
                    
                    conn.commit()
                    
                    # メールアドレスを取得
                    cursor.execute("""
                        SELECT email FROM users WHERE id = %s
                    """, (user_id,))
                    user_data = cursor.fetchone()
                    
                    if user_data and user_data['email']:
                        user_email = user_data['email']
                        logger.info(f"LINE integration completed for user: {user_email}")
                        
                        # Supabaseの紹介記録を更新
                        referral_updated = await update_referral_status(user_email)
                        
                        if referral_updated:
                            success_message = """✅ 認証完了！

🎉 LINE連携で1日4回分析可能になりました！
🎁 さらに、あなたは友達紹介経由で登録されました

📊 紹介者の分析回数も12回/日に増加しました！

引き続きD-Logic AIをお楽しみください！"""
                        else:
                            success_message = """✅ 認証完了！

🎁 LINE連携で1日4回分析可能になりました！
📊 分析回数が増加しました（1回 → 4回）

👥 友達を紹介すると1日12回に！
紹介URLはマイページで確認できます。

引き続きD-Logic AIをお楽しみください！"""
                    else:
                        success_message = """✅ 認証完了！

🎁 LINE連携で1日4回分析可能になりました！

引き続きD-Logic AIをお楽しみください！"""
                    
                    await send_line_message(line_user_id, success_message)
                else:
                    await send_line_message(line_user_id, "既に連携済みです。")
            else:
                await send_line_message(line_user_id, "認証コードが無効または期限切れです。")
        else:
            # その他のメッセージに対する自動応答
            help_message = """🤖 D-Logic AI公式LINEです

📝 利用可能なコマンド：
・認証コード（6文字）: アカウント連携
・「ヘルプ」: このメッセージを表示
・「サイト」: D-Logic AIサイトURL

🏇 最新の競馬情報やキャンペーン情報をお届けします！"""
            
            if message_text in ['ヘルプ', 'HELP']:
                await send_line_message(line_user_id, help_message)
            elif message_text in ['サイト', 'SITE']:
                await send_line_message(line_user_id, "🌐 D-Logic AI: https://www.dlogicai.in/?openExternalBrowser=1")
            else:
                await send_line_message(line_user_id, help_message)
                
    except Exception as e:
        logger.error(f"Message handling error: {e}")
    finally:
        if conn:
            conn.close()

async def handle_friend_removed(event: LineWebhookEvent):
    """友達解除時の処理"""
    line_user_id = event.source.get('userId')
    if not line_user_id:
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 友達解除記録
        cursor.execute("""
            UPDATE line_users 
            SET unfriend_at = NOW() 
            WHERE line_user_id = %s
        """, (line_user_id,))
        conn.commit()
        
    except Exception as e:
        logger.error(f"Friend removed error: {e}")
    finally:
        if conn:
            conn.close()

async def send_line_message(line_user_id: str, message: str):
    """LINEメッセージ送信"""
    import aiohttp
    
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'to': line_user_id,
        'messages': [{
            'type': 'text',
            'text': message
        }]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    logger.error(f"LINE API error: {response.status}")
    except Exception as e:
        logger.error(f"Send message error: {e}")

@router.post("/generate-verification-code")
async def generate_verification_code(user_email: str):
    """認証コード生成"""
    import random
    import string
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # ユーザー情報取得
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 認証コード生成
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # 既存の未使用コードを無効化
        cursor.execute("""
            UPDATE line_verification_codes 
            SET used = TRUE 
            WHERE user_id = %s AND used = FALSE
        """, (user['id'],))
        
        # 新しい認証コード保存
        cursor.execute("""
            INSERT INTO line_verification_codes (user_id, code, created_at)
            VALUES (%s, %s, NOW())
        """, (user['id'], code))
        
        conn.commit()
        
        return {"verification_code": code}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.get("/qr-code/{user_email}")
async def get_line_qr_code(user_email: str):
    """LINE QRコード情報取得"""
    line_add_url = f"https://line.me/R/ti/p/{LINE_ACCOUNT_ID}"
    
    return {
        "line_id": LINE_ACCOUNT_ID,
        "add_url": line_add_url,
        "qr_code_url": f"https://qr-server.com/api/v1/create-qr-code/?size=200x200&data={line_add_url}"
    }

# 紹介記録更新用のエンドポイント（フロントエンドから呼び出される）
@router.post("/complete-referral")
async def complete_referral(request: Request):
    """LINE連携完了時の紹介記録更新"""
    try:
        # ボディまたはクエリパラメータからuser_emailを取得
        body = await request.body()
        if body:
            data = json.loads(body.decode('utf-8'))
            user_email = data.get('user_email')
        else:
            # クエリパラメータから取得
            user_email = request.query_params.get('user_email')
        
        if not user_email:
            raise HTTPException(status_code=400, detail="user_email is required")
        
        # 特定の問題ユーザーを完全ブロック
        if user_email == "miraiakajiproject@gmail.com":
            logger.warning(f"Blocked problematic user: {user_email}")
            return {"status": "blocked", "message": "Account temporarily suspended due to abnormal activity"}
        
        # レート制限チェック（1分間に3回まで）
        now = time.time()
        recent_calls = rate_limiter[user_email]
        recent_calls = [t for t in recent_calls if now - t < 60]
        
        if len(recent_calls) >= 3:
            logger.warning(f"Rate limit exceeded for user: {user_email}")
            return {"status": "rate_limited", "message": "Too many requests, please wait"}
        
        recent_calls.append(now)
        rate_limiter[user_email] = recent_calls
        
        logger.info(f"Complete referral called for: {user_email}")
        result = await update_referral_status(user_email)
        if result:
            return {"status": "success", "message": "Referral updated successfully"}
        else:
            return {"status": "no_referral", "message": "No pending referral found"}
    except Exception as e:
        logger.error(f"Complete referral error: {e}")
        raise HTTPException(status_code=500, detail=str(e))