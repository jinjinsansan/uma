#!/usr/bin/env python3
"""
2024年有馬記念出走馬の正確なD-Logic分析
各馬を本物のD-Logic分析システムで分析
"""
import asyncio
import json
import os
from typing import Dict, List, Any
from services.integrated_d_logic_calculator import IntegratedDLogicCalculator

# 有馬記念2024出走馬
ARIMA_HORSES = [
    "レガレイラ",
    "ダノンデサイル", 
    "アーバンシック",
    "ベラジオオペラ",
    "ドウデュース",
    "ジャスティンパレス",
    "シャフリヤール",
    "ローシャムパーク",
    "スターズオンアース",
    "プログノーシス",
    "ブローザホーン",
    "ディープボンド",
    "シュトルーヴェ",
    "スタニングローズ",
    "ダノンベルーガ",
    "ハヤヤッコ"
]

async def analyze_arima_horses():
    """有馬記念出走馬の正確なD-Logic分析"""
    print("🏆 2024年有馬記念出走馬D-Logic分析開始")
    print("=" * 50)
    
    calculator = IntegratedDLogicCalculator()
    results = []
    
    for i, horse_name in enumerate(ARIMA_HORSES, 1):
        print(f"\n🐎 {i:2d}/16 {horse_name} を分析中...")
        
        try:
            # 本物のD-Logic分析実行
            analysis_result = calculator.calculate_d_logic_score({
                'horse_name': horse_name,
                'analysis_type': 'comprehensive'
            })
            
            if 'error' not in analysis_result:
                score = analysis_result.get('total_score', 100)
                print(f"  ✅ D-Logic Score: {score}")
                
                results.append({
                    'name': horse_name,
                    'dLogicScore': int(score),
                    'analysis': analysis_result
                })
            else:
                print(f"  ⚠️ 分析エラー: {analysis_result.get('error')}")
                # エラー時はデフォルトスコア
                results.append({
                    'name': horse_name,
                    'dLogicScore': 100,  # ダンスインザダーク基準
                    'analysis': {'error': analysis_result.get('error')}
                })
                
        except Exception as e:
            print(f"  ❌ 例外エラー: {e}")
            results.append({
                'name': horse_name,
                'dLogicScore': 100,
                'analysis': {'error': str(e)}
            })
    
    # 結果を保存
    output_data = {
        'race': '有馬記念',
        'year': 2024,
        'date': '2024-12-22',
        'horses': results,
        'total_horses': len(results),
        'analysis_completed': True
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "data", "arima_real_dlogic.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 有馬記念D-Logic分析完了!")
    print(f"📁 保存先: {output_path}")
    print("\n📊 分析結果:")
    
    # D-Logic順でソート
    sorted_results = sorted(results, key=lambda x: x['dLogicScore'], reverse=True)
    for rank, horse in enumerate(sorted_results, 1):
        print(f"  {rank:2d}. {horse['name']:12s} D-Logic: {horse['dLogicScore']:3d}")
    
    return output_data

if __name__ == "__main__":
    asyncio.run(analyze_arima_horses())