"""
V2ポイント管理サービス
Supabaseのv2_user_pointsテーブルを使用
楽観的ロック機能付き（2025-09-04追加）
"""
import os
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class InsufficientPointsError(Exception):
    """ポイント不足エラー"""
    pass

class ConcurrencyError(Exception):
    """同時実行制御エラー"""
    pass

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
    
    async def use_points_with_lock(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None,
        related_entity_id: Optional[str] = None
    ) -> Dict:
        """ポイントを使用（楽観的ロック付き）"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 現在のポイントとversionを取得
                points_response = self.supabase.table("v2_user_points")\
                    .select("current_points, total_spent, version")\
                    .eq("user_id", user_id)\
                    .execute()
                
                if not points_response.data:
                    # ユーザーのポイントデータが存在しない場合は作成
                    points_data = await self._create_initial_points(user_id)
                    current_points = 0
                    total_spent = 0
                    current_version = 0
                else:
                    points_data = points_response.data[0]
                    current_points = points_data["current_points"]
                    total_spent = points_data["total_spent"]
                    current_version = points_data.get("version", 0)
                
                # ポイント不足チェック
                if current_points < amount:
                    raise InsufficientPointsError(f"ポイントが不足しています。現在: {current_points}, 必要: {amount}")
                
                new_balance = current_points - amount
                new_total_spent = total_spent + amount
                
                # 楽観的ロックを使用した更新
                update_response = self.supabase.table("v2_user_points")\
                    .update({
                        "current_points": new_balance,
                        "total_spent": new_total_spent,
                        "version": current_version + 1,
                        "updated_at": datetime.now().isoformat()
                    })\
                    .eq("user_id", user_id)\
                    .eq("version", current_version)\
                    .execute()
                
                if not update_response.data:
                    # versionが一致しない = 他で更新された
                    if attempt < max_retries - 1:
                        logger.warning(f"楽観的ロック競合検出 (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(0.1 * (attempt + 1))  # 指数バックオフ
                        continue
                    else:
                        raise ConcurrencyError("ポイント更新が競合しました。もう一度お試しください。")
                
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
                
                logger.info(f"ポイント使用成功: user={user_id}, amount={amount}, new_balance={new_balance}")
                return transaction_response.data[0]
                
            except (InsufficientPointsError, ConcurrencyError) as e:
                # 既知のエラーはそのまま再スロー
                raise
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"ポイント使用エラー（最終試行）: {e}")
                    raise
                else:
                    logger.warning(f"ポイント使用エラー（リトライ {attempt + 1}/{max_retries}）: {e}")
                    await asyncio.sleep(0.1 * (attempt + 1))
        
        # ここには到達しないはず
        raise Exception("予期しないエラーが発生しました")
    
    async def use_points(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None,
        related_entity_id: Optional[str] = None
    ) -> Dict:
        """ポイントを使用（楽観的ロック版を使用）"""
        # 既存のコードとの互換性を保つため、新しいメソッドを呼び出す
        return await self.use_points_with_lock(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            related_entity_id=related_entity_id
        )
    
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
    
    async def check_daily_login_exists(self, user_id: str, date) -> bool:
        """指定日のデイリーログインボーナスが既に取得されているかチェック"""
        try:
            from datetime import datetime
            
            # 日付を文字列形式に変換（YYYY-MM-DD）
            if isinstance(date, datetime):
                date_str = date.strftime('%Y-%m-%d')
            else:
                date_str = str(date)
            
            # 指定日のデイリーログイン取引をチェック
            response = self.supabase.table("v2_point_transactions")\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("transaction_type", "daily_login")\
                .gte("created_at", f"{date_str}T00:00:00")\
                .lte("created_at", f"{date_str}T23:59:59")\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"デイリーログインチェックエラー: {e}")
            return False  # エラー時は安全側に倒して false を返す