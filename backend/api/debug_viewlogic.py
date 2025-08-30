#!/usr/bin/env python3
"""
Render上でViewLogicエラーを直接デバッグするAPIエンドポイント
"""

from fastapi import APIRouter, HTTPException
import traceback
import sys
import json
from typing import Dict, Any, List

router = APIRouter()

@router.get("/debug-viewlogic-error")
async def debug_viewlogic_error():
    """ViewLogicエラーをRender上で直接デバッグ"""
    
    debug_result = {
        "timestamp": None,
        "python_version": sys.version,
        "tests": {},
        "error_details": None,
        "success": False
    }
    
    try:
        import datetime
        debug_result["timestamp"] = datetime.datetime.now().isoformat()
        
        # 1. JockeyKnowledgeManager基本テスト
        debug_result["tests"]["jockey_manager_import"] = "attempting"
        
        from services.jockey_knowledge_manager import JockeyKnowledgeManager
        debug_result["tests"]["jockey_manager_import"] = "success"
        
        # 2. マネージャー初期化テスト
        debug_result["tests"]["jockey_manager_init"] = "attempting"
        manager = JockeyKnowledgeManager()
        debug_result["tests"]["jockey_manager_init"] = "success"
        debug_result["tests"]["jockey_count"] = len(manager.jockey_data) if hasattr(manager, 'jockey_data') else 0
        
        # 3. 基本メソッドテスト
        debug_result["tests"]["get_jockey_data"] = "attempting"
        test_result = manager.get_jockey_data('武豊')
        debug_result["tests"]["get_jockey_data"] = "success" if test_result is None else f"found_data_type_{type(test_result).__name__}"
        
        # 4. 問題のメソッドテスト
        debug_result["tests"]["get_jockey_post_position_fukusho_rates"] = "attempting"
        test_jockeys = ['武豊', '川田']
        result = manager.get_jockey_post_position_fukusho_rates(test_jockeys)
        debug_result["tests"]["get_jockey_post_position_fukusho_rates"] = f"success_with_{len(result)}_jockeys"
        
        # 5. ViewLogicEngineテスト
        debug_result["tests"]["viewlogic_engine"] = "attempting"
        from services.viewlogic_engine import ViewLogicEngine
        engine = ViewLogicEngine()
        
        test_race_data = {
            'venue': '新潟',
            'distance': 1200,
            'track_type': '芝',
            'horses': ['テストホース1', 'テストホース2'],
            'jockeys': ['武豊', '川田'],
            'posts': [1, 2]
        }
        
        analysis_result = engine.analyze_course_trend(test_race_data)
        debug_result["tests"]["viewlogic_engine"] = "success"
        debug_result["tests"]["viewlogic_result_keys"] = list(analysis_result.keys()) if isinstance(analysis_result, dict) else "not_dict"
        
        # 6. データ詳細検査
        debug_result["data_inspection"] = {}
        
        # 武豊のデータを詳細調査
        takeshi_patterns = ['武豊', '武豊　', '武豊　　']
        for pattern in takeshi_patterns:
            if pattern in manager.jockey_data:
                jockey_data = manager.jockey_data[pattern]
                post_stats = jockey_data.get('post_position_stats', {})
                debug_result["data_inspection"][f"takeshi_pattern_{len(pattern)}"] = {
                    "found": True,
                    "post_stats_type": type(post_stats).__name__,
                    "post_stats_keys": list(post_stats.keys()) if isinstance(post_stats, dict) else "not_dict"
                }
                
                # 最初の枠のstatsを詳細調査
                if isinstance(post_stats, dict) and post_stats:
                    first_waku = next(iter(post_stats.keys()))
                    first_stats = post_stats[first_waku]
                    debug_result["data_inspection"][f"takeshi_first_waku_{first_waku}"] = {
                        "stats_type": type(first_stats).__name__,
                        "stats_value": str(first_stats)[:100] if not isinstance(first_stats, dict) else "dict_with_keys_" + str(list(first_stats.keys()))
                    }
                break
        else:
            debug_result["data_inspection"]["takeshi_not_found"] = True
        
        debug_result["success"] = True
        
    except Exception as e:
        debug_result["success"] = False
        debug_result["error_details"] = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        
        # エラーが'get'関連かチェック
        if "'int' object has no attribute 'get'" in str(e):
            debug_result["target_error_reproduced"] = True
            
            # スタックトレースから詳細な発生場所を特定
            tb_lines = traceback.format_exc().split('\n')
            for i, line in enumerate(tb_lines):
                if 'get' in line and ('race_count' in line or 'fukusho_rate' in line):
                    debug_result["error_location"] = {
                        "line": line.strip(),
                        "context": tb_lines[max(0, i-2):i+3]
                    }
                    break
        
    return debug_result

@router.post("/debug-viewlogic-specific")
async def debug_viewlogic_specific(request: Dict[str, Any]):
    """特定のデータでViewLogicエラーをデバッグ"""
    
    try:
        jockeys = request.get('jockeys', ['武豊', '川田'])
        
        from services.jockey_knowledge_manager import JockeyKnowledgeManager
        manager = JockeyKnowledgeManager()
        
        result = manager.get_jockey_post_position_fukusho_rates(jockeys)
        
        return {
            "success": True,
            "jockeys_requested": jockeys,
            "jockeys_found": len(result),
            "result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "jockeys_requested": request.get('jockeys', []),
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            },
            "target_error_reproduced": "'int' object has no attribute 'get'" in str(e)
        }