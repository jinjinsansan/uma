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

# from services.imlogic_engine import IMLogicEngine  # V2AIHandlerで初期化するため削除

logger = logging.getLogger(__name__)

class V2ChatService:
    """V2チャット管理サービス"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase環境変数が設定されていません")
            
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # IMLogicEngineは遅延初期化（メモリ節約のため）
        self._imlogic_engine = None
    
    @property
    def imlogic_engine(self):
        """IMLogicEngineの遅延初期化"""
        if self._imlogic_engine is None:
            from services.imlogic_engine import IMLogicEngine
            self._imlogic_engine = IMLogicEngine()
        return self._imlogic_engine
    
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
                    "sex_ages": race_data.get("sex_ages", []),
                    "weights": race_data.get("weights", []),
                    "trainers": race_data.get("trainers", []),
                    "odds": race_data.get("odds", []),
                    "popularities": race_data.get("popularities", []),
                    "distance": race_data.get("distance"),
                    "course_type": race_data.get("course_type"),
                    "weather": race_data.get("weather"),
                    "track_condition": race_data.get("track_condition"),
                    "raceResults": race_data.get("raceResults")  # レース結果追加
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
            logger.info(f"Getting sessions for user_id: {user_id}, limit: {limit}, offset: {offset}")
            
            # セッション一覧取得
            sessions_response = self.supabase.table("v2_chat_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            sessions = sessions_response.data if sessions_response.data else []
            logger.info(f"Found {len(sessions)} sessions")
            
            # race_snapshotをパース
            for session in sessions:
                if session.get("race_snapshot"):
                    try:
                        if isinstance(session["race_snapshot"], str):
                            session["race_snapshot"] = json.loads(session["race_snapshot"])
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse race_snapshot for session {session.get('id')}: {e}")
                        session["race_snapshot"] = {}
            
            # メッセージカウントを追加（パフォーマンス最適化: 一括取得）
            session_ids = [session["id"] for session in sessions]
            if session_ids:
                try:
                    # 全セッションのメッセージカウントを一度に取得
                    messages_response = self.supabase.table("v2_chat_messages")\
                        .select("session_id")\
                        .in_("session_id", session_ids)\
                        .execute()
                    
                    # session_idごとにカウント
                    message_counts = {}
                    if messages_response.data:
                        for msg in messages_response.data:
                            session_id = msg["session_id"]
                            message_counts[session_id] = message_counts.get(session_id, 0) + 1
                    
                    # 各セッションにカウントを設定
                    for session in sessions:
                        session["message_count"] = message_counts.get(session["id"], 0)
                    
                    logger.debug(f"Message counts retrieved for {len(sessions)} sessions")
                except Exception as e:
                    logger.warning(f"Failed to get message counts: {e}")
                    # エラー時は全セッションのカウントを0に
                    for session in sessions:
                        session["message_count"] = 0
            
            return sessions
            
        except Exception as e:
            logger.error(f"セッション一覧取得エラー: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"User ID: {user_id}")
            raise
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[Dict]:
        """特定のチャットセッションを取得"""
        try:
            
            # セッション取得
            session_response = self.supabase.table("v2_chat_sessions")\
                .select("*")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not session_response.data or len(session_response.data) == 0:
                return None
            
            session = session_response.data[0]
            
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
        session_data: Dict,
        imlogic_settings: Optional[Dict] = None
    ) -> Dict:
        """メッセージを処理してAI応答を生成"""
        try:
            # レースに出走する馬のチェック
            race_horses = session_data.get("race_snapshot", {}).get("horses", [])
            if race_horses:
                # メッセージ内に馬名が含まれているか確認
                mentioned_horses = []
                for horse in race_horses:
                    if horse in message:
                        mentioned_horses.append(horse)
                
                # レースに出走しない馬名が含まれているかチェック
                import re
                # 「〜の」「〜を」「〜と」などの助詞で区切って馬名候補を抽出
                potential_horses = re.findall(r'[ァ-ヴー]+(?:の|を|と|、|。|\s|$)', message)
                invalid_horses = []
                for potential in potential_horses:
                    # 助詞を除去
                    cleaned = re.sub(r'[のをと、。\s]+$', '', potential)
                    # 3文字以上のカタカナのみの文字列を馬名候補として扱う
                    if len(cleaned) >= 3 and cleaned not in race_horses and re.match(r'^[ァ-ヴー]+$', cleaned):
                        invalid_horses.append(cleaned)
                
                # 無効な馬名が含まれている場合はエラーメッセージを返す
                if invalid_horses:
                    error_content = f"申し訳ございません。以下の馬は{session_data['venue']}{session_data['race_number']}Rに出走していません：\n"
                    error_content += "、".join(invalid_horses) + "\n\n"
                    error_content += f"このレースに出走する馬は以下の{len(race_horses)}頭です：\n"
                    error_content += "、".join(race_horses)
                    
                    # エラーメッセージを保存して返す
                    error_message_data = {
                        "session_id": session_id,
                        "role": "assistant",
                        "content": error_content,
                        "ai_type": ai_type
                    }
                    error_response = self.supabase.table("v2_chat_messages").insert(error_message_data).execute()
                    return {"message": error_response.data[0]}
            
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
                # IMLogic設定を使用（パラメータから取得、またはデータベースから取得）
                if not imlogic_settings and session_data.get("imlogic_settings_id"):
                    settings_response = self.supabase.table("user_imlogic_settings")\
                        .select("*")\
                        .eq("id", session_data["imlogic_settings_id"])\
                        .execute()
                    if settings_response.data and len(settings_response.data) > 0:
                        imlogic_settings = settings_response.data[0]
                
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
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        ai_type: Optional[str],
        analysis_data: Optional[Dict] = None
    ) -> Dict:
        """メッセージを保存"""
        try:
            # ai_typeがNoneの場合はデフォルトで"imlogic"を使用
            final_ai_type = ai_type if ai_type is not None else "imlogic"
            
            message_data = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "role": role,
                "content": content,
                "ai_type": final_ai_type,
                "analysis_data": json.dumps(analysis_data) if analysis_data else None,
                "created_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table("v2_chat_messages").insert(message_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"メッセージ保存エラー: {e}")
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
            rank_emoji = ["🥇", "🥈", "🥉", "4位:", "5位:"][i]
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
    async def delete_session(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """チャットセッションと関連メッセージを削除"""
        try:
            # 削除前にセッションが存在するか確認
            check_session = self.supabase.table("v2_chat_sessions")\
                .select("id")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not check_session.data:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return False
            
            # まずメッセージを削除
            delete_messages = self.supabase.table("v2_chat_messages").delete().eq("session_id", session_id).execute()
            logger.info(f"Deleted messages for session {session_id}")
            
            # セッションを削除
            delete_session = self.supabase.table("v2_chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
            
            # 削除後に確認（削除が成功したか）
            verify_deletion = self.supabase.table("v2_chat_sessions")\
                .select("id")\
                .eq("id", session_id)\
                .execute()
            
            if not verify_deletion.data:
                logger.info(f"Successfully deleted session {session_id}")
                return True
            else:
                logger.error(f"Failed to delete session {session_id} - still exists in database")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
