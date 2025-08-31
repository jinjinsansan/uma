#!/usr/bin/env python3
"""
ViewLogic新機能の修正版APIテスト
"""

import asyncio
import json
from services.v2.ai_handler import V2AIHandler

async def test_viewlogic_history_fixed():
    """ViewLogic過去データ機能を修正版でテスト"""
    
    print("🔧 ViewLogic新機能（過去データ表示）修正版テスト開始")
    print("=" * 60)
    
    # AIハンドラー初期化
    handler = V2AIHandler()
    
    # テストデータ（実際のV2レースを模擬）
    race_data = {
        'horses': ['ドウデュース', 'エフフォーリア', 'レイパパレ', 'ジェラルディナ'],
        'jockeys': ['川田将雅', '横山武史', 'C.ルメール', '福永祐一'],
        'venue': '阪神',
        'race_name': '阪神大賞典（G2）'
    }
    
    # テストケース一覧
    test_cases = [
        {
            'name': '馬の過去データ取得',
            'message': 'ドウデュースの過去データを教えて',
        },
        {
            'name': '騎手の戦績取得',
            'message': '川田将雅騎手の戦績を見せて',
        },
        {
            'name': '馬の直近レース',
            'message': 'エフフォーリアの直近のレース',
        },
        {
            'name': 'レース制限テスト',
            'message': 'アーモンドアイの過去データ',
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【テスト{i}】{test_case['name']}")
        print(f"入力メッセージ: 「{test_case['message']}」")
        print("-" * 40)
        
        try:
            # レースデータを設定
            handler.current_race_data = race_data
            
            # AI判定テスト
            ai_type, sub_type = handler.determine_ai_type(test_case['message'])
            print(f"🔍 AI判定: {ai_type} / {sub_type}")
            
            # メッセージ処理テスト（辞書形式の戻り値）
            result = await handler.process_message(
                message=test_case['message'],
                race_data=race_data
            )
            
            # 結果から値を取得
            response = result.get('content', '')
            ai_type_result = result.get('ai_type', '')
            sub_type_result = result.get('sub_type', '')
            data = result.get('analysis_data')
            
            print(f"📋 実行AI: {ai_type_result}/{sub_type_result}")
            
            # レスポンスチェック
            if response and len(response) > 0:
                print("✅ レスポンス: 生成成功")
                print(f"📄 レスポンス長: {len(response)}文字")
                print(f"📋 内容（抜粋）: {response[:150]}...")
                response_score = 100
            else:
                print("❌ レスポンス: 生成失敗")
                response_score = 0
            
            # ViewLogic historyが正しく動作しているかチェック
            if ai_type_result == 'viewlogic' and ('過去' in response or '戦績' in response or '直近' in response):
                print("✅ ViewLogic過去データ: 正常動作")
                functionality_score = 100
            else:
                print("⚠️ ViewLogic過去データ: 期待した動作と異なる")
                functionality_score = 50
            
            # 総合評価
            total_score = (response_score + functionality_score) / 2
            results.append({
                'test_name': test_case['name'],
                'score': total_score,
                'ai_type': ai_type_result,
                'sub_type': sub_type_result,
                'response_length': len(response) if response else 0
            })
            
            print(f"🎯 テスト{i}評価: {total_score:.1f}/100点")
            
        except Exception as e:
            print(f"❌ テスト{i}エラー: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'test_name': test_case['name'],
                'score': 0,
                'error': str(e)
            })
    
    # 総合診断レポート
    print("\n" + "=" * 60)
    print("🏆 ViewLogic新機能 総合診断レポート")
    print("=" * 60)
    
    total_tests = len(results)
    total_score = sum(r['score'] for r in results) / total_tests if total_tests > 0 else 0
    
    for i, result in enumerate(results, 1):
        status = "✅" if result['score'] >= 80 else "⚠️" if result['score'] >= 60 else "❌"
        print(f"{status} テスト{i}: {result['test_name']} - {result['score']:.1f}点")
        if 'ai_type' in result:
            print(f"   実行AI: {result['ai_type']}/{result['sub_type']}, レスポンス: {result['response_length']}文字")
    
    print("-" * 60)
    print(f"🎯 **総合評価: {total_score:.1f}/100点**")
    
    if total_score >= 90:
        grade = "S級 - 完璧！"
    elif total_score >= 80:
        grade = "A級 - 優秀"
    elif total_score >= 70:
        grade = "B級 - 良好"
    elif total_score >= 60:
        grade = "C級 - 要改善"
    else:
        grade = "D級 - 重大な問題"
    
    print(f"📊 品質グレード: {grade}")
    
    # 詳細分析
    print("\n📈 詳細分析:")
    viewlogic_count = sum(1 for r in results if r.get('ai_type') == 'viewlogic')
    history_count = sum(1 for r in results if r.get('sub_type') == 'history')
    
    print(f"  • ViewLogic実行率: {viewlogic_count}/{total_tests} ({viewlogic_count/total_tests*100:.1f}%)")
    print(f"  • History機能実行: {history_count}/{total_tests} ({history_count/total_tests*100:.1f}%)")
    print(f"  • エラー件数: {sum(1 for r in results if 'error' in r)}/{total_tests}")
    
    print("=" * 60)
    
    return total_score, results

if __name__ == "__main__":
    asyncio.run(test_viewlogic_history_fixed())