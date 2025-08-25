"""
V2ポイント管理サービス
Supabaseのv2_user_pointsテーブルを使用
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class V2PointsService:
    """V2ポイント管理サービス"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase環境変数が設定されていません")
            
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # ポイントルール（環境変数から取得、デフォルト値あり）
        self.point_rules = {
            "google_auth": int(os.getenv("V2_POINTS_GOOGLE_AUTH", "2")),
            "line_link": int(os.getenv("V2_POINTS_LINE_LINK", "18")),
            "referral": int(os.getenv("V2_POINTS_REFERRAL", "30")),
            "chat_create": int(os.getenv("V2_POINTS_CHAT_CREATE", "1"))
        }
    
    async def get_user_points(self, user_id: str) -> Dict:
        """ユーザーのポイント情報を取得"""
        try:
            
            # ポイント情報を取得
            points_response = self.supabase.table("v2_user_points").select("*").eq("user_id", user_id).execute()
            
            if not points_response.data or len(points_response.data) == 0:
                # 初回アクセス時は作成
                return await self._create_initial_points(user_id)
            
            return points_response.data[0]
            
        except Exception as e:
            logger.error(f"ポイント情報取得エラー: {e}")
            raise
    
    async def _create_initial_points(self, user_id: str) -> Dict:
        """初回ポイント作成"""
        try:
            initial_data = {
                "user_id": user_id,
                "current_points": 0,
                "total_earned": 0,
                "total_spent": 0
            }
            
            response = self.supabase.table("v2_user_points").insert(initial_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"初回ポイント作成エラー: {e}")
            raise
    
    async def grant_points(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None,
        related_entity_id: Optional[str] = None
    ) -> Dict:
        """ポイントを付与"""
        try:
            # 現在のポイント取得
            points_data = await self.get_user_points(user_id)
            new_balance = points_data["current_points"] + amount
            
            # ポイント更新
            update_response = self.supabase.table("v2_user_points").update({
                "current_points": new_balance,
                "total_earned": points_data["total_earned"] + amount
            }).eq("user_id", user_id).execute()
            
            # 取引履歴作成
            transaction_data = {
                "user_id": user_id,
                "amount": amount,
                "transaction_type": transaction_type,
                "description": description,
                "related_entity_id": related_entity_id,
                "balance_after": new_balance
            }
            
            transaction_response = self.supabase.table("v2_point_transactions").insert(transaction_data).execute()
            
            return transaction_response.data[0]
            
        except Exception as e:
            logger.error(f"ポイント付与エラー: {e}")
            raise
    
    async def use_points(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None,
        related_entity_id: Optional[str] = None
    ) -> Dict:
        """ポイントを使用"""
        try:
            # 現在のポイント取得
            points_data = await self.get_user_points(user_id)
            
            if points_data["current_points"] < amount:
                raise ValueError("ポイントが不足しています")
            
            new_balance = points_data["current_points"] - amount
            
            # ポイント更新
            update_response = self.supabase.table("v2_user_points").update({
                "current_points": new_balance,
                "total_spent": points_data["total_spent"] + amount
            }).eq("user_id", user_id).execute()
            
            # 取引履歴作成
            transaction_data = {
                "user_id": user_id,
                "amount": -amount,  # 使用は負の値
                "transaction_type": transaction_type,
                "description": description,
                "related_entity_id": related_entity_id,
                "balance_after": new_balance
            }
            
            transaction_response = self.supabase.table("v2_point_transactions").insert(transaction_data).execute()
            
            return transaction_response.data[0]
            
        except Exception as e:
            logger.error(f"ポイント使用エラー: {e}")
            raise
    
    async def get_transactions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """取引履歴を取得"""
        try:
            
            # 取引履歴取得
            transactions_response = self.supabase.table("v2_point_transactions")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            return transactions_response.data
            
        except Exception as e:
            logger.error(f"取引履歴取得エラー: {e}")
            raise