"""
LINE Messaging API連携
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

load_dotenv()

router = APIRouter()

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
        print(f"LINE Webhook error: {e}")
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

🎁 3日間延長チケットを受け取るには：
1. D-Logic AIサイトでGoogleログイン
2. ポップアップに表示される認証コードをこのLINEに送信

📱 サイト: https://www.dlogicai.in

競馬予想の新時代をお楽しみください！"""
        
        await send_line_message(line_user_id, welcome_message)
        
    except Exception as e:
        print(f"Friend added error: {e}")
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
                    # LINE連携記録
                    cursor.execute("""
                        INSERT INTO line_users (user_id, line_user_id, tickets_received, friend_added_at)
                        VALUES (%s, %s, 1, NOW())
                    """, (user_id, line_user_id))
                    
                    # 無料期間延長
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
                    
                    # Supabaseの紹介記録を更新（もし紹介経由の場合）
                    try:
                        from supabase import create_client, Client
                        import os
                        
                        supabase_url = os.getenv('SUPABASE_URL')
                        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
                        
                        if supabase_url and supabase_key:
                            supabase: Client = create_client(supabase_url, supabase_key)
                            
                            # このユーザーが紹介経由で登録されているか確認
                            result = supabase.table('line_referrals').select('*').eq('referred_id', user_id).eq('status', 'pending').execute()
                            
                            if result.data and len(result.data) > 0:
                                # 紹介記録を completed に更新
                                referral_id = result.data[0]['id']
                                from datetime import datetime
                                update_result = supabase.table('line_referrals').update({
                                    'status': 'completed',
                                    'completed_at': datetime.now().isoformat()
                                }).eq('id', referral_id).execute()
                                
                                if update_result:
                                    print(f"Referral completed for user {user_id}")
                                    # トリガーが自動的に referral_count を更新する
                    except Exception as e:
                        print(f"Supabase referral update error: {e}")
                        # エラーでもLINE連携自体は成功しているので続行
                    
                    success_message = """✅ 認証完了！

🎁 LINE連携で1日4回になりました
📊 分析回数が増加しました（1回 → 4回）

引き続きD-Logic AIをお楽しみください！
最新の競馬予想情報もLINEでお届けします。"""
                    
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
                await send_line_message(line_user_id, "🌐 D-Logic AI: https://www.dlogicai.in")
            else:
                await send_line_message(line_user_id, help_message)
                
    except Exception as e:
        print(f"Message handling error: {e}")
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
        print(f"Friend removed error: {e}")
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
                    print(f"LINE API error: {response.status}")
    except Exception as e:
        print(f"Send message error: {e}")

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