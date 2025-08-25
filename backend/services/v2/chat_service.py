"""
V2チャット管理サービス
Supabaseのv2_chat_sessionsテーブルを使用
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from supabase import create_client, Client
import json

from services.imlogic_engine import IMLogicEngine  # 既存のIMLogicエンジンを使用

logger = logging.getLogger(__name__)

class V2ChatService:
    """V2チャット管理サービス"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase環境変数が設定されていません")
            
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.imlogic_engine = IMLogicEngine()  # 既存のエンジンを使用
    
    async def create_session(
        self,
        user_id: str,
        race_data: Dict,
        imlogic_settings_id: Optional[str] = None
    ) -> Dict:
        """新しいチャットセッションを作成"""
        try:
            
            # チャットセッション作成
            session_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "race_id": race_data["race_id"],
                "race_date": race_data["race_date"],
                "venue": race_data["venue"],
                "race_number": race_data["race_number"],
                "race_name": race_data["race_name"],
                "enabled_chats": {
                    "imlogic": True,
                    "viewlogic": True  # 将来的に有効化
                },
                "imlogic_settings_id": imlogic_settings_id,
                "race_snapshot": json.dumps({
                    "horses": race_data["horses"],
                    "jockeys": race_data.get("jockeys", []),
                    "posts": race_data.get("posts", []),
                    "horse_numbers": race_data.get("horse_numbers", []),
                    "distance": race_data.get("distance"),
                    "course_type": race_data.get("course_type"),
                    "weather": race_data.get("weather"),
                    "track_condition": race_data.get("track_condition")
                })
            }
            
            response = self.supabase.table("v2_chat_sessions").insert(session_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"セッション作成エラー: {e}")
            raise
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """ユーザーのチャットセッション一覧を取得"""
        try:
            
            # セッション一覧取得
            sessions_response = self.supabase.table("v2_chat_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            # race_snapshotをパース
            for session in sessions_response.data:
                if session.get("race_snapshot"):
                    session["race_snapshot"] = json.loads(session["race_snapshot"])
            
            return sessions_response.data
            
        except Exception as e:
            logger.error(f"セッション一覧取得エラー: {e}")
            raise
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[Dict]:
        """特定のチャットセッションを取得"""
        try:
            
            # セッション取得
            session_response = self.supabase.table("v2_chat_sessions")\
                .select("*")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            if not session_response.data:
                return None
            
            session = session_response.data
            
            # race_snapshotをパース
            if session.get("race_snapshot"):
                session["race_snapshot"] = json.loads(session["race_snapshot"])
            
            # メッセージ履歴を取得
            messages_response = self.supabase.table("v2_chat_messages")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at")\
                .execute()
            
            session["messages"] = messages_response.data
            
            # analysis_dataをパース
            for message in session["messages"]:
                if message.get("analysis_data"):
                    message["analysis_data"] = json.loads(message["analysis_data"])
            
            return session
            
        except Exception as e:
            logger.error(f"セッション取得エラー: {e}")
            raise
    
    async def update_last_accessed(self, session_id: str):
        """最終アクセス日時を更新"""
        try:
            self.supabase.table("v2_chat_sessions")\
                .update({"last_accessed_at": datetime.now().isoformat()})\
                .eq("id", session_id)\
                .execute()
        except Exception as e:
            logger.error(f"最終アクセス更新エラー: {e}")
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        ai_type: str,
        session_data: Dict
    ) -> Dict:
        """メッセージを処理してAI応答を生成"""
        try:
            # ユーザーメッセージを保存
            user_message_data = {
                "session_id": session_id,
                "role": "user",
                "content": message,
                "ai_type": ai_type
            }
            
            user_message_response = self.supabase.table("v2_chat_messages").insert(user_message_data).execute()
            user_message = user_message_response.data[0]
            
            # IMLogic処理
            if ai_type == "imlogic":
                # IMLogic設定を取得
                imlogic_settings = None
                if session_data.get("imlogic_settings_id"):
                    settings_response = self.supabase.table("imlogic_user_settings")\
                        .select("*")\
                        .eq("id", session_data["imlogic_settings_id"])\
                        .single()\
                        .execute()
                    if settings_response.data:
                        imlogic_settings = settings_response.data
                
                # IMLogicで分析実行
                race_snapshot = session_data["race_snapshot"]
                
                # IMLogicで分析
                # 注: IMLogicEngineはanalyze_raceメソッドを使用
                race_data = {
                    'horses': race_snapshot["horses"],
                    'jockeys': race_snapshot.get("jockeys", []),
                    'posts': race_snapshot.get("posts", []),
                    'horse_numbers': race_snapshot.get("horse_numbers", []),
                    'venue': session_data["venue"],
                    'race_number': session_data["race_number"],
                    'race_name': session_data["race_name"],
                    'distance': race_snapshot.get("distance"),
                    'track_condition': race_snapshot.get("track_condition", "良")
                }
                
                # IMLogic設定から重み付けを取得
                horse_weight = 70  # デフォルト
                jockey_weight = 30  # デフォルト
                item_weights = {
                    '1_distance_aptitude': 8.3,
                    '2_bloodline_evaluation': 8.3,
                    '3_jockey_compatibility': 8.3,
                    '4_trainer_evaluation': 8.3,
                    '5_track_aptitude': 8.3,
                    '6_weather_aptitude': 8.3,
                    '7_popularity_factor': 8.3,
                    '8_weight_impact': 8.3,
                    '9_horse_weight_impact': 8.3,
                    '10_corner_specialist': 8.3,
                    '11_margin_analysis': 8.3,
                    '12_time_index': 8.7
                }
                
                if imlogic_settings:
                    horse_weight = imlogic_settings.get('horse_weight', 70)
                    jockey_weight = imlogic_settings.get('jockey_weight', 30)
                    if imlogic_settings.get('item_weights'):
                        item_weights = imlogic_settings['item_weights']
                
                analysis_result = self.imlogic_engine.analyze_race(
                    race_data=race_data,
                    horse_weight=horse_weight,
                    jockey_weight=jockey_weight,
                    item_weights=item_weights
                )
                
                # AI応答メッセージを作成
                ai_content = self._format_imlogic_response(analysis_result, session_data)
                
                # AI応答を保存
                ai_message_data = {
                    "session_id": session_id,
                    "role": "assistant",
                    "content": ai_content,
                    "ai_type": ai_type,
                    "analysis_data": json.dumps(analysis_result)
                }
                
                ai_message_response = self.supabase.table("v2_chat_messages").insert(ai_message_data).execute()
                ai_message = ai_message_response.data[0]
                
                # analysis_dataをパース
                if ai_message.get("analysis_data"):
                    ai_message["analysis_data"] = json.loads(ai_message["analysis_data"])
                
                return {"message": ai_message}
            
            # ViewLogicは未実装
            return {
                "message": {
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": "このAIタイプは現在開発中です。",
                    "ai_type": ai_type,
                    "created_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"メッセージ処理エラー: {e}")
            raise
    
    def _format_imlogic_response(self, analysis_result: Dict, session_data: Dict) -> str:
        """IMLogic分析結果をフォーマット"""
        venue = session_data["venue"]
        race_number = session_data["race_number"]
        race_name = session_data["race_name"]
        
        response = f"## {venue}{race_number}R {race_name} IMLogic分析結果\n\n"
        
        # 設定情報を表示
        settings = analysis_result.get("settings", {})
        response += f"**分析設定**: 馬{settings.get('horse_weight', 70)}% / 騎手{settings.get('jockey_weight', 30)}%\n\n"
        
        response += "### 上位5頭\n"
        
        # 結果データを取得
        results = analysis_result.get("results", [])
        data_available = [r for r in results if r.get('data_status') == 'ok']
        
        # 上位5頭を表示
        for i, result in enumerate(data_available[:5]):
            rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
            response += f"{rank_emoji} **{result['horse']}** - {result['total_score']:.1f}点\n"
            response += f"   馬: {result['horse_score']:.1f}点 / 騎手: {result['jockey_score']:.1f}点 ({result['jockey']})\n"
        
        response += "\n### 全馬評価\n"
        
        # 全馬の評価を表示
        for result in results:
            if result.get('data_status') == 'ok':
                response += f"- {result['horse']}: {result['total_score']:.1f}点 (馬{result['horse_score']:.1f}/騎手{result['jockey_score']:.1f})\n"
            else:
                response += f"- {result['horse']}: データなし\n"
        
        return response