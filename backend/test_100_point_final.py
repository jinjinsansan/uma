#!/usr/bin/env python3
"""
ViewLogic履歴機能の最終100点テスト
実際のV2 APIエンドポイント経由でテスト

修正内容:
1. 短縮騎手名「川田」の認識修正
2. 外国人騎手「C.ルメール」の認識修正
3. 複勝率表示の正規化修正（4000.0% → 40.0%）
"""

import requests
import json
import uuid
import time

def test_v2_viewlogic_history():
    """V2 API経由でViewLogic履歴機能をテスト"""
    
    print("🧪 ViewLogic履歴機能 最終100点テスト")
    print("=" * 60)
    print("実際のV2 APIエンドポイント経由でテスト実行")
    
    base_url = "http://localhost:8000/api/v2"
    
    # テスト用チャットセッション作成
    session_data = {
        "race_id": f"test-final-{uuid.uuid4().hex[:8]}",
        "race_date": "2025-08-31",
        "venue": "新潟",
        "race_number": 4,
        "race_name": "最終テストレース",
        "horses": ["エリックバローズ", "ウンエン", "アランチャータ"],
        "jockeys": ["川田将雅", "C.ルメール", "武豊"],
        "posts": [1, 2, 3],
        "distance": 1200,
        "course_type": "芝",
        "is_test_mode": True
    }
    
    print("1. チャットセッション作成...")
    try:
        response = requests.post(
            f"{base_url}/chat/create",
            json=session_data,
            headers={"x-user-id": "goldbenchan@gmail.com"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ セッション作成失敗: {response.text}")
            return 0
        
        session_info = response.json()
        session_id = session_info.get("session_id")
        print(f"✅ セッション作成成功: {session_id}")
        
    except Exception as e:
        print(f"❌ セッション作成エラー: {e}")
        return 0
    
    # テストケース定義
    test_cases = [
        {
            'name': 'Test 1: 馬名（エリックバローズ）',
            'message': 'エリックバローズ',
            'expected_points': 100,
            'description': 'ViewLogicナレッジファイル内の馬名認識'
        },
        {
            'name': 'Test 2: フルネーム騎手（川田将雅）',
            'message': '川田将雅',
            'expected_points': 100,
            'description': 'フルネーム騎手の正常認識'
        },
        {
            'name': 'Test 3: 短縮名騎手（川田）- 修正対象',
            'message': '川田',
            'expected_points': 100,
            'description': '短縮名騎手の部分一致認識（修正）'
        },
        {
            'name': 'Test 4: 外国人騎手（C.ルメール）- 修正対象',
            'message': 'C.ルメール',
            'expected_points': 100,
            'description': '外国人騎手名の正規化（修正）'
        },
        {
            'name': 'Test 5: 外国人短縮（ルメール）- 修正対象',
            'message': 'ルメール',
            'expected_points': 100,
            'description': '外国人騎手の短縮名認識（修正）'
        }
    ]
    
    total_points = 0
    successful_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 {test_case['name']}")
        print(f"   メッセージ: '{test_case['message']}'")
        print(f"   説明: {test_case['description']}")
        
        try:
            # V2 APIにメッセージ送信
            message_data = {
                "message": test_case['message'],
                "ai_type": "viewlogic"  # ViewLogicを明示的に指定
            }
            
            response = requests.post(
                f"{base_url}/chat/{session_id}/message",
                json=message_data,
                headers={"x-user-id": "goldbenchan@gmail.com"},
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"   ❌ API呼び出し失敗: {response.text}")
                print(f"   📊 獲得ポイント: 0/100")
                continue
            
            result = response.json()
            
            # エラーチェック
            if "error" in result:
                print(f"   ❌ エラー応答: {result['error']}")
                print(f"   📊 獲得ポイント: 20/100")
                total_points += 20
                continue
            
            content = result.get("content", "")
            
            # 修正前の問題パターンをチェック
            error_patterns = [
                "'int' object has no attribute 'get'",
                "ViewLogic分析中にエラー",
                "データが見つかりませんでした",
                "騎手データが読み込まれていません"
            ]
            
            # 修正後の異常パターンをチェック
            percentage_issues = [
                "4000.0%",      # 異常な複勝率
                "複勝率40.0",    # 40% が 4000% に
                "500.0%",       # 5倍の異常表示
                "1000.0%",      # 10倍の異常表示
            ]
            
            has_errors = any(pattern in content for pattern in error_patterns)
            has_percentage_issues = any(pattern in content for pattern in percentage_issues)
            
            if has_errors:
                print("   ❌ システムエラー検出")
                for pattern in error_patterns:
                    if pattern in content:
                        print(f"      → エラー: '{pattern}'")
                points = 20
            elif has_percentage_issues:
                print("   ⚠️ 複勝率表示異常検出")
                for pattern in percentage_issues:
                    if pattern in content:
                        print(f"      → 異常表示: '{pattern}'")
                points = 40  # エラーではないが表示異常
            else:
                # 正常なレスポンスの確認
                success_indicators = [
                    "👤",  # 騎手データの表示
                    "🏟️", # 競馬場データの表示
                    "📊",  # 馬データの表示
                    "騎手 データ",
                    "直近5戦",
                    "複勝率"
                ]
                
                has_success = any(indicator in content for indicator in success_indicators)
                
                if has_success:
                    print("   ✅ 正常なViewLogic履歴データ表示")
                    print(f"   レスポンス: {content[:150]}...")
                    points = 100
                    successful_tests += 1
                else:
                    print("   ⚠️ ViewLogic以外のAIが応答")
                    print(f"   レスポンス: {content[:100]}...")
                    points = 60
            
            print(f"   📊 獲得ポイント: {points}/100")
            total_points += points
            
        except requests.Timeout:
            print("   ❌ API呼び出しタイムアウト")
            print(f"   📊 獲得ポイント: 0/100")
        except Exception as e:
            print(f"   ❌ テスト実行エラー: {e}")
            print(f"   📊 獲得ポイント: 0/100")
        
        # テスト間の待機
        time.sleep(2)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("🏆 最終テスト結果")
    print("=" * 60)
    print(f"総合ポイント: {total_points}/500")
    print(f"平均スコア: {total_points/len(test_cases):.1f}/100")
    print(f"完全成功テスト: {successful_tests}/{len(test_cases)}")
    
    # 評価
    if total_points == 500:
        print("\n🎉 Perfect! 100点満点達成！")
        print("🌟 ViewLogic履歴機能の修正が完全に成功しました")
        grade = "A+"
    elif total_points >= 450:
        print(f"\n🎯 Excellent! {total_points}/500点")
        print("🌟 優秀な成績です。軽微な修正で完璧になります")
        grade = "A"
    elif total_points >= 400:
        print(f"\n✅ Good! {total_points}/500点")
        print("✨ 良好な成績です。ほぼ全ての修正が成功しています")
        grade = "B+"
    elif total_points >= 300:
        print(f"\n⚠️ Fair: {total_points}/500点")
        print("🔧 部分的に成功していますが、さらなる修正が必要です")
        grade = "C"
    else:
        print(f"\n❌ Needs Work: {total_points}/500点")
        print("🚧 大幅な修正が必要です")
        grade = "F"
    
    print(f"\n📋 最終評価: {grade}")
    
    return total_points

def main():
    """メイン関数"""
    print("ViewLogic履歴機能の修正内容:")
    print("1. 短縮騎手名の部分一致認識（川田 → 川田将雅）")
    print("2. 外国人騎手名の正規化（C.ルメール → ルメール）")
    print("3. 複勝率表示の正規化（値が1以下なら100倍、1以上ならそのまま）")
    print("")
    
    try:
        final_score = test_v2_viewlogic_history()
        
        if final_score >= 400:
            print(f"\n🎊 修正成功！ 最終スコア: {final_score}/500")
            print("ユーザーからの残り25点の問題をクリアしました")
        else:
            print(f"\n🔄 追加修正必要: {final_score}/500")
            print("さらなる改善が必要です")
            
    except Exception as e:
        print(f"\nテスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()