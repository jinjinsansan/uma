"""
V2 レーススコアサービス
v2_race_scoresテーブルの管理
"""
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class V2RaceScoresService:
    def __init__(self):
        """Supabaseクライアントを初期化"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase設定が不足しています")
            raise ValueError("Supabase設定が不足しています")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self._race_results_enabled = os.getenv("ENABLE_V2_RACE_RESULTS_COLUMN", "0") == "1"
    
    async def get_race_scores(self, race_id: str) -> Optional[Dict[str, Any]]:
        """
        レースのスコアを取得
        """
        try:
            response = self.supabase.table("v2_race_scores").select("*").eq("race_id", race_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"レーススコア取得エラー: {e}")
            return None
    
    async def save_race_scores(
        self,
        race_id: str,
        race_date: str,
        venue: str,
        race_number: int,
        race_name: str,
        horses: List[str],
        jockeys: Optional[List[str]] = None,
        posts: Optional[List[int]] = None,
        horse_numbers: Optional[List[int]] = None,
        sex_ages: Optional[List[str]] = None,
        weights: Optional[List[float]] = None,
        trainers: Optional[List[str]] = None,
        odds: Optional[List[float]] = None,
        popularities: Optional[List[int]] = None,
        dlogic_scores: Optional[Dict[str, Any]] = None,
        ilogic_scores: Optional[Dict[str, Any]] = None,
        race_results: Optional[Dict[str, Any]] = None
    ):
        """
        レーススコアを保存
        """
        try:
            # 既存データがあるか確認
            existing = await self.get_race_scores(race_id)
            
            # データ準備
            data = {
                "race_id": race_id,
                "race_date": race_date,
                "venue": venue,
                "race_number": race_number,
                "race_name": race_name,
                "horses": horses,
                "jockeys": jockeys or [],
                "posts": posts or [],
                "horse_numbers": horse_numbers or [],
                "sex_ages": sex_ages or [],
                "weights": weights or [],
                "trainers": trainers or [],
                "odds": odds or [],
                "popularities": popularities or [],
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # D-Logicスコアがある場合
            if dlogic_scores:
                data["dlogic_scores"] = json.dumps(dlogic_scores) if isinstance(dlogic_scores, dict) else dlogic_scores
                data["dlogic_calculated_at"] = datetime.utcnow().isoformat()
            
            # I-Logicスコアがある場合
            if ilogic_scores:
                data["ilogic_scores"] = json.dumps(ilogic_scores) if isinstance(ilogic_scores, dict) else ilogic_scores
                data["ilogic_calculated_at"] = datetime.utcnow().isoformat()

            if race_results and self._race_results_enabled:
                data["race_results"] = json.dumps(race_results) if isinstance(race_results, dict) else race_results
            elif race_results and not self._race_results_enabled:
                logger.debug("race_results column disabled; skipping storage for race_id=%s", race_id)
            
            if existing:
                # 更新
                response = self.supabase.table("v2_race_scores").update(data).eq("race_id", race_id).execute()
                logger.info(f"レーススコア更新: {race_id}")
            else:
                # 新規作成
                data["created_at"] = datetime.utcnow().isoformat()
                response = self.supabase.table("v2_race_scores").insert(data).execute()
                logger.info(f"レーススコア作成: {race_id}")
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"レーススコア保存エラー: {e}")
            raise
    
    async def get_batch_race_scores(self, race_ids: List[str]) -> Dict[str, Any]:
        """
        複数レースのスコアを一括取得
        """
        try:
            response = self.supabase.table("v2_race_scores").select("*").in_("race_id", race_ids).execute()
            
            # race_id をキーにした辞書に変換
            result = {}
            for item in response.data:
                result[item["race_id"]] = item
            
            return result
            
        except Exception as e:
            logger.error(f"バッチレーススコア取得エラー: {e}")
            return {}