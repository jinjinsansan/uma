from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Clerk公開鍵取得用のURL
CLERK_JWKS_URL = "https://api.clerk.com/v1/jwks"

# Supabaseクライアント
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase環境変数が設定されていません。SUPABASE_URLとSUPABASE_SERVICE_ROLE_KEYを確認してください。")

supabase: Client = create_client(supabase_url, supabase_key)

security = HTTPBearer()


def get_clerk_public_key():
    """ClerkのJWT検証用の公開鍵を取得"""
    try:
        # 実際の本番環境では、この公開鍵をキャッシュすることを推奨
        response = requests.get(CLERK_JWKS_URL)
        jwks = response.json()
        # 簡略化のため、最初の鍵を使用
        return jwks.get("keys", [])[0] if jwks.get("keys") else None
    except Exception as e:
        print(f"Error fetching Clerk public key: {e}")
        return None


async def verify_email_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """メールベースの簡易認証（既存システムとの互換性）"""
    email = credentials.credentials
    
    try:
        # メールアドレスの簡易検証
        if not email or '@' not in email:
            raise HTTPException(status_code=401, detail="Invalid email format")
        
        # Supabaseが利用可能な場合のみユーザー検索・作成を実行
        if supabase:
            # Supabaseでユーザーを検索または作成
            user_result = supabase.table("users").select("*").eq("email", email).execute()
            
            if user_result.data:
                user = user_result.data[0]
            else:
                # 新規ユーザーの場合は作成
                create_result = supabase.table("users").insert({
                    "email": email,
                    "name": email.split("@")[0],
                    "google_id": "",
                    "avatar_url": ""
                }).execute()
                
                if create_result.data:
                    user = create_result.data[0]
                    
                    # user_quotasも作成
                    supabase.table("user_quotas").insert({
                        "user_id": user["id"],
                        "subscription_type": "free_trial",
                        "daily_uses": 0
                    }).execute()
                else:
                    raise HTTPException(status_code=500, detail="Failed to create user")
            
            return {
                "user_id": user["id"],
                "email": user["email"],
                "name": user["name"]
            }
        else:
            # Supabaseが利用できない場合は簡易的なユーザー情報を返す
            print(f"Using simplified auth for user: {email}")
            return {
                "user_id": email,  # メールアドレスをIDとして使用
                "email": email,
                "name": email.split("@")[0]
            }
        
    except HTTPException:
        # HTTPExceptionはそのまま再スロー
        raise
    except Exception as e:
        print(f"Authentication error: {e}")
        # Supabaseが利用できない場合でも動作するように500ではなく簡易認証を返す
        if not supabase:
            return {
                "user_id": email if email else "anonymous",
                "email": email if email else "anonymous@example.com",
                "name": email.split("@")[0] if email else "Anonymous"
            }
        raise HTTPException(status_code=500, detail=str(e))


def get_current_user(user_info: Dict[str, Any] = Depends(verify_email_token)) -> str:
    """現在のユーザーIDを取得"""
    return user_info["user_id"]


def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[str]:
    """オプショナルな認証（認証なしでもOK）"""
    if not credentials:
        return None
    
    try:
        user_info = verify_email_token(credentials)
        return user_info["user_id"]
    except:
        return None