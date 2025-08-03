#!/usr/bin/env python3
"""
小規模テストバッチ（100頭）
フルバッチ前の動作確認用
"""
import mysql.connector
import time
from services.dlogic_raw_data_manager import DLogicRawDataManager
from services.fast_dlogic_engine import FastDLogicEngine
from batch_create_raw_knowledge import extract_horse_raw_data, get_mysql_connection

def small_batch_test(num_horses: int = 100):
    """小規模バッチテスト"""
    print(f"🧪 小規模バッチテスト開始（{num_horses}頭）")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # 1. MySQL接続テスト
        print("🔌 MySQL接続テスト...")
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 2. テスト対象馬を取得
        print(f"🐎 テスト対象馬抽出（{num_horses}頭）...")
        cursor.execute("""
            SELECT DISTINCT BAMEI, COUNT(*) as race_count
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN >= '2023'
            AND BAMEI IS NOT NULL 
            AND BAMEI != ''
            GROUP BY BAMEI
            HAVING race_count >= 5
            ORDER BY race_count DESC
            LIMIT %s
        """, (num_horses,))
        
        horses = cursor.fetchall()
        print(f"✅ 対象馬: {len(horses)}頭抽出完了")
        
        # 3. ナレッジマネージャー初期化
        print("🚀 ナレッジマネージャー初期化...")
        manager = DLogicRawDataManager()
        
        # 4. 生データ抽出・保存
        print("📊 生データ抽出・保存テスト...")
        processed = 0
        errors = 0
        
        for horse in horses[:20]:  # 最初の20頭でテスト
            horse_name = horse['BAMEI']
            
            try:
                print(f"  🔍 {horse_name} 処理中...")
                
                # 生データ抽出
                raw_data = extract_horse_raw_data(conn, horse_name)
                
                if raw_data["race_history"]:
                    # ナレッジに追加
                    manager.add_horse_raw_data(horse_name, raw_data)
                    processed += 1
                    print(f"    ✅ {horse_name} 完了（レース数: {len(raw_data['race_history'])}）")
                else:
                    print(f"    ⚠️ {horse_name} データなし")
                    
            except Exception as e:
                errors += 1
                print(f"    ❌ {horse_name} エラー: {e}")
        
        # 5. ナレッジ保存
        print("💾 ナレッジ保存...")
        manager._save_knowledge()
        
        # 6. 高速エンジンテスト
        print("\n⚡ 高速D-Logic計算エンジンテスト...")
        engine = FastDLogicEngine()
        
        # テスト馬で計算速度確認
        test_horses = [h['BAMEI'] for h in horses[:5]]
        calc_start = time.time()
        
        for horse_name in test_horses:
            result = engine.analyze_single_horse(horse_name)
            calc_time = result.get('calculation_time_seconds', 0)
            score = result.get('total_score', 0)
            source = result.get('data_source', 'unknown')
            
            print(f"  🐎 {horse_name:15s} {score:6.1f}点 "
                  f"({calc_time:.3f}秒) - {source}")
        
        calc_total = time.time() - calc_start
        print(f"  📊 5頭計算時間: {calc_total:.3f}秒（平均: {calc_total/5:.3f}秒/頭）")
        
        # 7. レース分析テスト
        print("\n🏇 レース分析テスト...")
        race_result = engine.analyze_race_horses(test_horses)
        
        print(f"  総計算時間: {race_result['race_analysis']['total_calculation_time']:.3f}秒")
        print(f"  平均時間/頭: {race_result['race_analysis']['avg_time_per_horse']:.3f}秒")
        print(f"  ナレッジヒット: {race_result['race_analysis']['knowledge_hits']}")
        print(f"  MySQLフォールバック: {race_result['race_analysis']['mysql_fallbacks']}")
        
        # 8. API互換性テスト
        print("\n📡 API互換性テスト...")
        from api.fast_dlogic_api import engine as api_engine
        
        api_result = api_engine.analyze_single_horse("レガレイラ")
        print(f"  APIテスト: レガレイラ {api_result.get('total_score', 0):.1f}点")
        
        total_time = time.time() - start_time
        
        print(f"\n✅ 小規模バッチテスト完了!")
        print(f"📊 処理統計:")
        print(f"  処理成功: {processed}頭")
        print(f"  エラー: {errors}頭")
        print(f"  総時間: {total_time:.1f}秒")
        print(f"  平均処理時間: {total_time/processed:.1f}秒/頭" if processed > 0 else "")
        
        # 9. フルバッチ推定時間
        if processed > 0:
            estimated_full_time = (total_time / processed) * 10000 / 3600
            print(f"📈 10,000頭フルバッチ推定時間: {estimated_full_time:.1f}時間")
        
        # 10. 性能評価
        print(f"\n🎯 性能評価:")
        avg_calc_time = calc_total / 5
        if avg_calc_time <= 0.1:
            print(f"  ✅ 計算速度: EXCELLENT（目標0.1秒 vs 実測{avg_calc_time:.3f}秒）")
        elif avg_calc_time <= 0.5:
            print(f"  🟡 計算速度: GOOD（目標0.1秒 vs 実測{avg_calc_time:.3f}秒）")
        else:
            print(f"  ❌ 計算速度: NEEDS IMPROVEMENT（目標0.1秒 vs 実測{avg_calc_time:.3f}秒）")
        
        return {
            "success": True,
            "processed_horses": processed,
            "errors": errors,
            "total_time": total_time,
            "avg_calc_time": avg_calc_time,
            "estimated_full_batch_hours": estimated_full_time if processed > 0 else None
        }
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return {"success": False, "error": str(e)}
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🧪 小規模バッチテスト実行")
    print("このテストは約5-10分で完了します。")
    print("自動実行開始...")
    
    result = small_batch_test(100)
    
    if result["success"]:
        print(f"\n🎉 テスト成功！フルバッチの準備が整いました。")
        
        if result.get("estimated_full_batch_hours"):
            print(f"推定フルバッチ時間: {result['estimated_full_batch_hours']:.1f}時間")
            print("\n小規模テスト完了。フルバッチは手動で実行してください。")
    else:
        print(f"❌ テスト失敗: {result.get('error')}")