from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import json
import os
from datetime import datetime
from services.dlogic_calculator import FastDLogicEngine
from services.mylogic_calculator import MyLogicCalculator

router = APIRouter()

# グローバルインスタンス（メモリ効率化）
fast_engine = FastDLogicEngine()

class BatchDLogicAnalyzer:
    def __init__(self):
        self.fast_engine = fast_engine
        
    async def analyze_race(self, venue: str, race_number: int, horses: List[str]) -> Dict[str, Any]:
        """単一レースのD-Logic分析を実行"""
        try:
            # 各馬のD-Logicスコアを計算
            horse_scores = []
            
            for horse_name in horses:
                # D-Logic計算
                d_logic_results = self.fast_engine.calculate_single(
                    horse_name=horse_name,
                    race_date=datetime.now().strftime('%Y-%m-%d'),
                    jyo=venue,
                    race_num=str(race_number)
                )
                
                if d_logic_results and 'results' in d_logic_results and len(d_logic_results['results']) > 0:
                    result = d_logic_results['results'][0]
                    total_score = result.get('dLogicTotal', 50)
                    horse_scores.append({
                        'horse_name': horse_name,
                        'score': total_score,
                        'details': result
                    })
                else:
                    horse_scores.append({
                        'horse_name': horse_name,
                        'score': 50,  # デフォルトスコア
                        'details': None
                    })
            
            # スコア順にソート
            horse_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # 上位5頭を抽出
            dlogic_top5 = [h['horse_name'] for h in horse_scores[:5]]
            
            return {
                'venue': venue,
                'race_number': race_number,
                'horses': horses,
                'dlogic_top5': dlogic_top5,
                'all_scores': horse_scores,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"エラー: {venue} {race_number}R - {str(e)}")
            return None

    async def analyze_all_races(self, races: List[Dict[str, Any]]) -> Dict[str, Any]:
        """全レースを一括分析"""
        results = {}
        success_count = 0
        
        for race in races:
            print(f"分析中: {race['venue']} {race['race_number']}R...")
            
            result = await self.analyze_race(
                venue=race['venue'],
                race_number=race['race_number'],
                horses=race['horses']
            )
            
            if result:
                key = f"{race['venue']}_{race['race_number']}"
                results[key] = result
                success_count += 1
        
        return {
            'results': results,
            'total_races': len(races),
            'success_count': success_count,
            'analyzed_at': datetime.now().isoformat()
        }

@router.post("/api/admin/batch-dlogic-analyze")
async def batch_dlogic_analyze(data: Dict[str, str]):
    """指定日のアーカイブレースを一括D-Logic分析"""
    archive_date = data.get('archive_date')
    
    try:
        # アーカイブデータファイルを読み込み
        archive_file = f"data/archive_races/{archive_date.replace('-', '')}.json"
        
        if not os.path.exists(archive_file):
            # ファイルがない場合は、フロントエンドから送信されたデータを期待
            raise HTTPException(
                status_code=404, 
                detail="アーカイブデータファイルが見つかりません。フロントエンドからデータを送信してください。"
            )
        
        # バッチ分析実行
        analyzer = BatchDLogicAnalyzer()
        results = await analyzer.analyze_all_races(races)
        
        # 結果を保存
        os.makedirs('data/dlogic_results', exist_ok=True)
        filename = f"data/dlogic_results/batch_{archive_date.replace('-', '')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "message": f"{results['success_count']}/{results['total_races']}レースの分析が完了しました",
            "results_file": filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/admin/batch-dlogic-status/{archive_date}")
async def get_batch_status(archive_date: str):
    """バッチ分析結果の確認"""
    filename = f"data/dlogic_results/batch_{archive_date.replace('-', '')}.json"
    
    if not os.path.exists(filename):
        return {"status": "not_found", "message": "分析結果が見つかりません"}
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return {
        "status": "completed",
        "total_races": data['total_races'],
        "success_count": data['success_count'],
        "analyzed_at": data['analyzed_at']
    }