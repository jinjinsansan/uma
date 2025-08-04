"""
ユーザー管理API
Google OAuth認証から取得したユーザー情報の保存・管理
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import mysql.connector
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# データベース接続設定
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'mykeibadb'),
        charset='utf8mb4'
    )

# Pydanticモデル
class UserCreate(BaseModel):
    google_id: str
    email: str
    name: str
    image_url: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    google_id: str
    email: str
    name: str
    image_url: Optional[str]
    subscription_type: str
    total_queries_used: int
    Free_trial_end_date: Optional[datetime]
    premium_end_date: Optional[datetime]
    daily_queries_remaining: int

class QueryCreate(BaseModel):
    user_id: int
    query_type: str  # 'horse_analysis', 'race_analysis', 'general_chat'
    query_text: str
    response_text: str
    processing_time_ms: int

# ユーザー登録/取得
@router.post("/register", response_model=UserResponse)
async def register_or_get_user(user_data: UserCreate):
    """Google OAuth認証後のユーザー登録/取得"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 既存ユーザーチェック
        cursor.execute(
            "SELECT * FROM users WHERE google_id = %s OR email = %s",
            (user_data.google_id, user_data.email)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            # 既存ユーザーの情報を更新
            cursor.execute("""
                UPDATE users 
                SET name = %s, image_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_data.name, user_data.image_url, existing_user['id']))
            conn.commit()
            user_id = existing_user['id']
        else:
            # 新規ユーザー作成（7日間無料トライアル）
            free_trial_start = datetime.now()
            free_trial_end = free_trial_start + timedelta(days=7)
            
            cursor.execute("""
                INSERT INTO users (google_id, email, name, image_url, 
                                 subscription_type, free_trial_start_date, free_trial_end_date)
                VALUES (%s, %s, %s, %s, 'free', %s, %s)
            """, (user_data.google_id, user_data.email, user_data.name, 
                  user_data.image_url, free_trial_start, free_trial_end))
            conn.commit()
            user_id = cursor.lastrowid
        
        # ユーザー情報を取得して返す
        return await get_user_info(user_id)
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        if conn:
            conn.close()

@router.get("/info/{user_id}", response_model=UserResponse)
async def get_user_info(user_id: int):
    """ユーザー情報取得"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 今日の使用回数を計算
        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(*) as today_queries
            FROM user_queries 
            WHERE user_id = %s AND DATE(created_at) = %s
        """, (user_id, today))
        today_usage = cursor.fetchone()['today_queries']
        
        # 無料会員の1日制限
        daily_limit = 5 if user['subscription_type'] == 'free' else 999999
        daily_remaining = max(0, daily_limit - today_usage)
        
        return UserResponse(
            id=user['id'],
            google_id=user['google_id'],
            email=user['email'],
            name=user['name'],
            image_url=user['image_url'],
            subscription_type=user['subscription_type'],
            total_queries_used=user['total_queries_used'],
            free_trial_end_date=user['free_trial_end_date'],
            premium_end_date=user['premium_end_date'],
            daily_queries_remaining=daily_remaining
        )
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        if conn:
            conn.close()

@router.get("/quota/{user_id}")
async def check_user_quota(user_id: int):
    """使用制限チェック"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # ユーザー情報取得
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 無料期間チェック
        now = datetime.now()
        is_trial_active = (user['free_trial_end_date'] and 
                         now <= user['free_trial_end_date'])
        is_premium_active = (user['premium_end_date'] and 
                           now <= user['premium_end_date'])
        
        # 今日の使用回数
        today = now.date()
        cursor.execute("""
            SELECT COUNT(*) as today_queries
            FROM user_queries 
            WHERE user_id = %s AND DATE(created_at) = %s
        """, (user_id, today))
        today_usage = cursor.fetchone()['today_queries']
        
        # 制限チェック
        if is_premium_active:
            can_use = True
            daily_remaining = 999999
            subscription_status = "premium"
        elif is_trial_active:
            daily_limit = 5
            can_use = today_usage < daily_limit
            daily_remaining = max(0, daily_limit - today_usage)
            subscription_status = "free_trial"
        else:
            can_use = False
            daily_remaining = 0
            subscription_status = "expired"
        
        return {
            "can_use": can_use,
            "subscription_status": subscription_status,
            "daily_remaining": daily_remaining,
            "today_usage": today_usage,
            "free_trial_end": user['free_trial_end_date'],
            "premium_end": user['premium_end_date']
        }
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        if conn:
            conn.close()

@router.post("/use-quota")
async def use_quota(query_data: QueryCreate):
    """使用回数消費"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 使用履歴を記録
        cursor.execute("""
            INSERT INTO user_queries (user_id, query_type, query_text, 
                                    response_text, processing_time_ms)
            VALUES (%s, %s, %s, %s, %s)
        """, (query_data.user_id, query_data.query_type, query_data.query_text,
              query_data.response_text, query_data.processing_time_ms))
        
        # 総使用回数を更新
        cursor.execute("""
            UPDATE users 
            SET total_queries_used = total_queries_used + 1
            WHERE id = %s
        """, (query_data.user_id,))
        
        conn.commit()
        
        return {"success": True, "message": "Usage recorded"}
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        if conn:
            conn.close()

@router.post("/line/add-ticket/{user_id}")
async def add_line_ticket(user_id: int, line_user_id: str):
    """LINE友達追加で3日間延長チケット付与"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # LINE連携チェック
        cursor.execute("""
            SELECT * FROM line_users WHERE user_id = %s AND line_user_id = %s
        """, (user_id, line_user_id))
        line_user = cursor.fetchone()
        
        if line_user:
            raise HTTPException(status_code=400, detail="Ticket already claimed")
        
        # LINE連携記録
        cursor.execute("""
            INSERT INTO line_users (user_id, line_user_id, tickets_received)
            VALUES (%s, %s, 1)
        """, (user_id, line_user_id))
        
        # 無料期間を3日延長
        cursor.execute("""
            UPDATE users 
            SET free_trial_end_date = DATE_ADD(COALESCE(free_trial_end_date, NOW()), INTERVAL 3 DAY)
            WHERE id = %s
        """, (user_id,))
        
        conn.commit()
        
        return {"success": True, "message": "3-day extension added"}
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        if conn:
            conn.close()