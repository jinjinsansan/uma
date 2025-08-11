#!/usr/bin/env python3
"""18頭立てパフォーマンステスト"""

import asyncio
import time
from api.chat import get_multiple_horses_analysis, extract_multiple_horse_names
from services.fast_dlogic_engine import FastDLogicEngine

# 実在の有名馬18頭（2024年有馬記念風）
test_horses_18 = [
    "ドウデュース", "イクイノックス", "タイトルホルダー", 
    "ソダシ", "スターズオンアース", "ジャスティンパレス",
    "プログノーシス", "ボルドグフーシュ", "サリオス",
    "シャフリヤール", "ディープボンド", "エフフォーリア",
    "グランアレグリア", "コントレイル", "アーモンドアイ",
    "レガレイラ", "ヤマニンバロネス", "サツキノジョウ"
]

async def test_18_horses_performance():
    """18頭のパフォーマンステスト"""
    
    print("=" * 60)
    print("18頭立てパフォーマンステスト")
    print("=" * 60)
    
    # 直接エンジンでのテスト
    print("\n【FastDLogicEngine直接テスト】")
    engine = FastDLogicEngine()
    
    start_time = time.time()
    result = engine.analyze_race_horses(test_horses_18)
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"総計算時間: {elapsed:.3f}秒")
    print(f"1頭あたり: {elapsed/18:.3f}秒")
    print(f"分析成功: {result['race_analysis']['analyzed_horses']}/{result['race_analysis']['total_horses']}頭")
    print(f"ナレッジヒット: {result['race_analysis']['knowledge_hits']}頭")
    print(f"MySQLフォールバック: {result['race_analysis']['mysql_fallbacks']}頭")
    
    # TOP5を表示
    print("\n【TOP5】")
    for i, horse in enumerate(result['horses'][:5]):
        total_score = horse.get('total_score', 0)
        if total_score is not None:
            print(f"{i+1}位: {horse.get('horse_name', 'Unknown')} - {total_score:.2f}点")
        else:
            print(f"{i+1}位: {horse.get('horse_name', 'Unknown')} - データなし")
    
    # API経由でのテスト
    print("\n【API経由テスト】")
    race_text = "2024年有馬記念 " + " ".join(test_horses_18)
    
    start_time = time.time()
    api_result = await get_multiple_horses_analysis(test_horses_18, "2024年有馬記念")
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"API総計算時間: {elapsed:.3f}秒")
    
    if api_result.get('status') == 'success':
        horses = api_result.get('analysis_result', {}).get('horses', [])
        print(f"API分析成功: {len(horses)}頭")
        
        # TOP5を表示
        print("\n【API TOP5】")
        for i, horse in enumerate(horses[:5]):
            total_score = horse.get('total_score', 0)
            if total_score is not None:
                print(f"{i+1}位: {horse.get('horse_name', 'Unknown')} - {total_score:.2f}点")
            else:
                print(f"{i+1}位: {horse.get('horse_name', 'Unknown')} - データなし")
    else:
        print(f"APIエラー: {api_result.get('message')}")
    
    # メモリ使用量の確認
    import psutil
    import os
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"\n【メモリ使用量】")
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    asyncio.run(test_18_horses_performance())