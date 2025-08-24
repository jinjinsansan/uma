from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel, Field, validator
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()

router = APIRouter(prefix="/api/v2/imlogic", tags=["IMLogic Settings"])

# Supabaseクライアント
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

class ItemWeights(BaseModel):
    distance_aptitude: float = Field(alias="1_distance_aptitude")
    bloodline_evaluation: float = Field(alias="2_bloodline_evaluation")
    jockey_compatibility: float = Field(alias="3_jockey_compatibility")
    trainer_evaluation: float = Field(alias="4_trainer_evaluation")
    track_aptitude: float = Field(alias="5_track_aptitude")
    weather_aptitude: float = Field(alias="6_weather_aptitude")
    popularity_factor: float = Field(alias="7_popularity_factor")
    weight_impact: float = Field(alias="8_weight_impact")
    horse_weight_impact: float = Field(alias="9_horse_weight_impact")
    corner_specialist: float = Field(alias="10_corner_specialist")
    margin_analysis: float = Field(alias="11_margin_analysis")
    time_index: float = Field(alias="12_time_index")
    
    @validator('*')
    def check_positive(cls, v):
        if v < 0:
            raise ValueError('重みは0以上である必要があります')
        return v
    
    class Config:
        allow_population_by_field_name = True

class IMLogicSettingsRequest(BaseModel):
    settings_name: str
    horse_weight: int = Field(..., ge=0, le=100, multiple_of=10)
    jockey_weight: int = Field(..., ge=0, le=100, multiple_of=10)
    item_weights: ItemWeights
    
    @validator('jockey_weight')
    def check_weights_sum(cls, v, values):
        if 'horse_weight' in values:
            if values['horse_weight'] + v != 100:
                raise ValueError('馬と騎手の重みの合計は100である必要があります')
        return v

@router.get("/settings")
async def get_settings():
    """ユーザーのIMLogic設定一覧を取得"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "00000000-0000-0000-0000-000000000000"  # 仮のユーザーID
        
        settings = supabase.table("user_imlogic_settings").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()
        
        # デフォルト設定も含める
        default_settings = {
            "id": "default",
            "settings_name": "IMLogic標準設定",
            "horse_weight": 70,
            "jockey_weight": 30,
            "item_weights": {
                "1_distance_aptitude": 8.33,
                "2_bloodline_evaluation": 8.33,
                "3_jockey_compatibility": 8.33,
                "4_trainer_evaluation": 8.33,
                "5_track_aptitude": 8.33,
                "6_weather_aptitude": 8.33,
                "7_popularity_factor": 8.33,
                "8_weight_impact": 8.33,
                "9_horse_weight_impact": 8.33,
                "10_corner_specialist": 8.33,
                "11_margin_analysis": 8.33,
                "12_time_index": 8.37
            },
            "is_default": True
        }
        
        return {
            "settings": [default_settings] + (settings.data or []),
            "count": len(settings.data or []) + 1
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings")
async def create_settings(request: IMLogicSettingsRequest):
    """新しいIMLogic設定を作成"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "00000000-0000-0000-0000-000000000000"  # 仮のユーザーID
        
        # 12項目の合計をチェック
        weights_sum = sum([
            request.item_weights.distance_aptitude,
            request.item_weights.bloodline_evaluation,
            request.item_weights.jockey_compatibility,
            request.item_weights.trainer_evaluation,
            request.item_weights.track_aptitude,
            request.item_weights.weather_aptitude,
            request.item_weights.popularity_factor,
            request.item_weights.weight_impact,
            request.item_weights.horse_weight_impact,
            request.item_weights.corner_specialist,
            request.item_weights.margin_analysis,
            request.item_weights.time_index
        ])
        
        if not (99.9 <= weights_sum <= 100.1):
            raise HTTPException(
                status_code=400, 
                detail=f"12項目の重みの合計は100である必要があります（現在: {weights_sum:.2f}）"
            )
        
        # JSON形式に変換
        item_weights_json = {
            "1_distance_aptitude": request.item_weights.distance_aptitude,
            "2_bloodline_evaluation": request.item_weights.bloodline_evaluation,
            "3_jockey_compatibility": request.item_weights.jockey_compatibility,
            "4_trainer_evaluation": request.item_weights.trainer_evaluation,
            "5_track_aptitude": request.item_weights.track_aptitude,
            "6_weather_aptitude": request.item_weights.weather_aptitude,
            "7_popularity_factor": request.item_weights.popularity_factor,
            "8_weight_impact": request.item_weights.weight_impact,
            "9_horse_weight_impact": request.item_weights.horse_weight_impact,
            "10_corner_specialist": request.item_weights.corner_specialist,
            "11_margin_analysis": request.item_weights.margin_analysis,
            "12_time_index": request.item_weights.time_index
        }
        
        settings_id = str(uuid.uuid4())
        
        result = supabase.table("user_imlogic_settings").insert({
            "id": settings_id,
            "user_id": user_id,
            "settings_name": request.settings_name,
            "horse_weight": request.horse_weight,
            "jockey_weight": request.jockey_weight,
            "item_weights": item_weights_json
        }).execute()
        
        return {
            "id": settings_id,
            "message": "IMLogic設定を保存しました",
            "settings_name": request.settings_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/settings/{settings_id}")
async def delete_settings(settings_id: str):
    """IMLogic設定を削除"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "00000000-0000-0000-0000-000000000000"  # 仮のユーザーID
        
        if settings_id == "default":
            raise HTTPException(status_code=400, detail="デフォルト設定は削除できません")
        
        result = supabase.table("user_imlogic_settings").delete().eq(
            "id", settings_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="設定が見つかりません")
        
        return {"message": "設定を削除しました"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/{settings_id}")
async def get_single_settings(settings_id: str):
    """特定のIMLogic設定を取得"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "00000000-0000-0000-0000-000000000000"  # 仮のユーザーID
        
        if settings_id == "default":
            return {
                "id": "default",
                "settings_name": "IMLogic標準設定",
                "horse_weight": 70,
                "jockey_weight": 30,
                "item_weights": {
                    "1_distance_aptitude": 8.33,
                    "2_bloodline_evaluation": 8.33,
                    "3_jockey_compatibility": 8.33,
                    "4_trainer_evaluation": 8.33,
                    "5_track_aptitude": 8.33,
                    "6_weather_aptitude": 8.33,
                    "7_popularity_factor": 8.33,
                    "8_weight_impact": 8.33,
                    "9_horse_weight_impact": 8.33,
                    "10_corner_specialist": 8.33,
                    "11_margin_analysis": 8.33,
                    "12_time_index": 8.37
                },
                "is_default": True
            }
        
        result = supabase.table("user_imlogic_settings").select("*").eq(
            "id", settings_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="設定が見つかりません")
        
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))