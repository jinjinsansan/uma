from fastapi import APIRouter
import logging
from services.dlogic_raw_data_manager import dlogic_manager
from services.fast_dlogic_engine import FastDLogicEngine

router = APIRouter(prefix="/api/debug", tags=["Debug"])
logger = logging.getLogger(__name__)

# グローバルインスタンスを使用
fast_engine_instance = FastDLogicEngine()

@router.get("/knowledge-status")
async def get_knowledge_status():
    """ナレッジファイルの状態を確認"""
    try:
        horses_dict = dlogic_manager.knowledge_data.get('horses', {})
        total_horses = len(horses_dict)
        
        # 最初と最後の10頭を取得
        horse_names = list(horses_dict.keys())
        first_10 = horse_names[:10] if len(horse_names) >= 10 else horse_names
        last_10 = horse_names[-10:] if len(horse_names) >= 10 else []
        
        # ロカヒを含む特定の馬を検索
        search_horses = ["ロカヒ", "アイク", "カラテ", "ドウデュース", "イクイノックス"]
        found_horses = {}
        
        for search_name in search_horses:
            # 直接検索
            if search_name in horses_dict:
                found_horses[search_name] = "Found (exact match)"
            else:
                # 部分一致検索
                partial_matches = [name for name in horse_names if search_name in name]
                if partial_matches:
                    found_horses[search_name] = f"Found (partial): {partial_matches[:3]}"
                else:
                    # 類似名検索（カタカナの違いなど）
                    similar = [name for name in horse_names if len(name) == len(search_name)]
                    found_horses[search_name] = f"Not found. Similar length names: {similar[:5]}"
        
        # メタ情報
        meta_info = dlogic_manager.knowledge_data.get('meta', {})
        
        return {
            "status": "success",
            "total_horses": total_horses,
            "first_10_horses": first_10,
            "last_10_horses": last_10,
            "search_results": found_horses,
            "meta_info": meta_info,
            "file_path": dlogic_manager.knowledge_file,
            "engine_horses": len(fast_engine_instance.raw_manager.knowledge_data.get('horses', {}))
        }
        
    except Exception as e:
        logger.error(f"Knowledge status error: {e}")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/search-horse/{horse_name}")
async def search_horse(horse_name: str):
    """特定の馬名を詳細検索"""
    try:
        # 直接検索
        raw_data = dlogic_manager.get_horse_raw_data(horse_name)
        
        # すべての馬名から類似検索
        horses_dict = dlogic_manager.knowledge_data.get('horses', {})
        all_names = list(horses_dict.keys())
        
        # 完全一致
        exact_matches = [name for name in all_names if name == horse_name]
        
        # 部分一致
        partial_matches = [name for name in all_names if horse_name in name or name in horse_name]
        
        # 同じ長さ
        same_length = [name for name in all_names if len(name) == len(horse_name)][:20]
        
        # カタカナのみで同じ文字数
        if all(char in 'ァ-ヴー' for char in horse_name):
            similar_katakana = [name for name in all_names 
                               if len(name) == len(horse_name) 
                               and all(char in 'ァ-ヴー' for char in name)][:10]
        else:
            similar_katakana = []
        
        return {
            "search_term": horse_name,
            "found": raw_data is not None,
            "raw_data_preview": str(raw_data)[:500] if raw_data else None,
            "exact_matches": exact_matches,
            "partial_matches": partial_matches[:20],
            "same_length_count": len([n for n in all_names if len(n) == len(horse_name)]),
            "same_length_sample": same_length,
            "similar_katakana": similar_katakana,
            "total_horses_in_knowledge": len(all_names)
        }
        
    except Exception as e:
        logger.error(f"Horse search error: {e}")
        import traceback
        return {
            "status": "error",
            "search_term": horse_name,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/test-analysis/{horse_name}")
async def test_analysis(horse_name: str):
    """特定の馬のD-Logic分析をテスト"""
    try:
        result = fast_engine_instance.analyze_single_horse(horse_name)
        
        return {
            "horse_name": horse_name,
            "analysis_result": result,
            "data_source": result.get('data_source'),
            "total_score": result.get('total_score'),
            "has_error": 'error' in result
        }
        
    except Exception as e:
        logger.error(f"Test analysis error: {e}")
        import traceback
        return {
            "status": "error",
            "horse_name": horse_name,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/test-weather-analysis/{horse_name}/{baba_condition}")
async def test_weather_analysis(horse_name: str, baba_condition: int):
    """天候適性D-Logic分析をテスト
    
    Args:
        horse_name: 馬名
        baba_condition: 馬場状態 (1=良, 2=稍重, 3=重, 4=不良)
    """
    try:
        # 入力検証
        if baba_condition not in [1, 2, 3, 4]:
            return {
                "status": "error",
                "message": "baba_condition must be 1, 2, 3, or 4"
            }
        
        # 標準分析
        standard_result = fast_engine_instance.analyze_single_horse(horse_name)
        
        # 天候適性分析
        weather_result = fast_engine_instance.analyze_single_horse_weather(horse_name, baba_condition)
        
        # 比較結果
        comparison = {
            "horse_name": horse_name,
            "baba_condition": baba_condition,
            "weather_name": {1: "良", 2: "稍重", 3: "重", 4: "不良"}[baba_condition],
            "standard": {
                "total_score": standard_result.get('total_score', 0),
                "grade": standard_result.get('grade', ''),
                "calculation_time": standard_result.get('calculation_time_seconds', 0)
            },
            "weather_adaptive": {
                "total_score": weather_result.get('total_score', 0),
                "grade": weather_result.get('grade', ''),
                "weather_adjustment": weather_result.get('weather_adjustment', 0),
                "calculation_time": weather_result.get('calculation_time_seconds', 0),
                "weather_details": weather_result.get('weather_details', {})
            },
            "score_difference": weather_result.get('total_score', 0) - standard_result.get('total_score', 0)
        }
        
        return comparison
        
    except Exception as e:
        logger.error(f"Weather analysis test error: {e}")
        import traceback
        return {
            "status": "error",
            "horse_name": horse_name,
            "baba_condition": baba_condition,
            "error": str(e),
            "traceback": traceback.format_exc()
        }