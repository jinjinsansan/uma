#!/usr/bin/env python3
"""
V2 ViewLogic傾向分析のテストスクリプト
V2のチャットAPIを通じて動作確認
"""

import requests
import json

def test_v2_viewlogic_trend():
    """V2 APIでViewLogic傾向分析をテスト"""
    
    # まずセッション作成
    create_url = "http://localhost:8000/api/v2/chat/create"
    
    # セッション作成リクエスト
    session_data = {
        "race_id": "test-race-001",
        "race_name": "新潟6R テストレース",
        "race_data": {
            "venue": "新潟",
            "distance": 1200,
            "course_type": "芝",
            "horses": [
                "ケアンズトーラス",
                "カバーガール",
                "リメイク",
                "マンハッタンロック",
                "レオアスク",
                "トミケンカラバティ",
                "テオリア",
                "テネレッツァ",
                "ファクトベース",
                "トランセンデンス",
                "クリノセレブ",
                "タケルアムール",
                "ホープウィッシュ",
                "カイアワセ",
                "アイラナンバーワン",
                "オールマイワーズ",
                "スラージュ",
                "フロスティグレイ"
            ],
            "jockeys": [
                "船橋",
                "森裕",
                "横山和",
                "武豊",
                "川田",
                "横山武",
                "C.ルメール",
                "R.ムーア",
                "福永",
                "松山",
                "戸崎",
                "岩田康",
                "西村淳",
                "鮫島克",
                "菱田",
                "荻野極",
                "小沢",
                "石田"
            ]
        }
    }
    
    print("=== V2 ViewLogic傾向分析テスト ===")
    print(f"レース: {session_data['race_name']}")
    print(f"出走頭数: {len(session_data['race_data']['horses'])}頭")
    print("")
    
    # まずセッション作成
    print("セッション作成中...")
    response = requests.post(
        create_url,
        json=session_data,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ セッション作成エラー: {response.status_code}")
        print(f"エラー内容: {response.text}")
        return
    
    session_result = response.json()
    session_id = session_result.get('session_id')
    print(f"✅ セッション作成成功: {session_id}")
    
    # ViewLogic傾向分析メッセージを送信
    chat_url = f"http://localhost:8000/api/v2/chat/{session_id}/message"
    test_message = "このレースの傾向分析して"
    request_data = {
        "message": test_message,
        "analysis_type": "viewlogic"
    }
    
    try:
        # APIリクエスト送信
        print(f"\nテストメッセージ: {test_message}")
        print("APIリクエスト送信中...")
        response = requests.post(
            chat_url,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # AI応答を表示
            if 'response' in result:
                print("\n=== AI応答 ===")
                print(result['response'])
                
                # 騎手データの確認
                if "騎手の当コース成績" in result['response']:
                    print("\n✅ 騎手の当コース成績が含まれています")
                    
                    # 騎手数をカウント
                    import re
                    jockey_matches = re.findall(r'\d+\.\s+\*\*([^*]+)\*\*:', result['response'])
                    print(f"検出された騎手数: {len(jockey_matches)}名")
                    if jockey_matches:
                        print(f"騎手リスト: {', '.join(jockey_matches[:5])}...")
                
                # 枠順データの確認
                if "騎手の枠順別" in result['response']:
                    print("\n✅ 騎手の枠順別成績が含まれています")
                    
                    # データなしかどうか確認
                    if "データなし" not in result['response'].split("騎手の枠順別")[1].split("【")[0]:
                        print("✅ 枠順データが正常に取得されています")
                    else:
                        print("⚠️ 枠順データが「データなし」になっています")
            else:
                print("❌ レスポンスにAI応答が含まれていません")
                print(f"レスポンス全体: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
        else:
            print(f"❌ APIエラー: {response.status_code}")
            print(f"エラー内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ APIサーバーに接続できません。サーバーが起動していることを確認してください。")
    except requests.exceptions.Timeout:
        print("❌ リクエストがタイムアウトしました。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    test_v2_viewlogic_trend()