#!/usr/bin/env python3
"""
馬名直接入力チャット機能テストクライアント
"""
import requests
import json
import sys

def test_horse_name_chat():
    """馬名直接入力チャット機能をテスト"""
    print("🐎 馬名直接入力チャット機能テスト")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8001"
    chat_endpoint = f"{base_url}/api/chat/message"
    
    # テストメッセージ
    test_messages = [
        "エフワンライデンの指数を教えて",
        "ディープインパクトはどう？",
        "ダンスインザダークの分析をお願いします",
        "ブライアンズロマンについて知りたい"
    ]
    
    print(f"🌐 接続先: {chat_endpoint}")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"📤 テスト {i}: {message}")
        
        try:
            # POSTリクエスト送信
            response = requests.post(
                chat_endpoint,
                json={"message": message, "history": []},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ ステータス: {result.get('status')}")
                print(f"📋 分析タイプ: {result.get('analysis_type', 'N/A')}")
                print(f"🏇 馬名: {result.get('horse_name', 'N/A')}")
                
                if result.get('has_d_logic'):
                    d_logic_result = result.get('d_logic_result', {})
                    if d_logic_result.get('horses'):
                        horse_analysis = d_logic_result['horses'][0]
                        print(f"📊 スコア: {horse_analysis.get('total_score', 0)}")
                        print(f"🏆 グレード: {horse_analysis.get('grade', 'N/A')}")
                        print(f"🔍 分析元: {horse_analysis.get('analysis_source', 'N/A')}")
                
                message_preview = result.get('message', '')[:200]
                print(f"💬 LLM応答: {message_preview}...")
                
            else:
                print(f"❌ エラー: HTTP {response.status_code}")
                print(f"📝 レスポンス: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 接続エラー: サーバーが起動していません")
            print("まず start_server.py を実行してください")
            return False
        except requests.exceptions.Timeout:
            print("❌ タイムアウト: レスポンスが遅すぎます")
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        print("-" * 30)
    
    return True

def test_server_status():
    """サーバー状態確認"""
    print("\n🔍 サーバー状態確認")
    print("=" * 30)
    
    try:
        response = requests.get("http://127.0.0.1:8001/", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ サーバー稼働中: {result.get('message')}")
            return True
        else:
            print(f"❌ サーバー応答エラー: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ サーバー接続失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 D-Logic競馬予想AI テストクライアント")
    print("Phase D統合版 - 馬名直接入力機能テスト")
    print("=" * 60)
    
    # サーバー状態確認
    if not test_server_status():
        print("\n⚠️  サーバーが起動していません")
        print("先に以下のコマンドでサーバーを起動してください:")
        print("python3 start_server.py")
        sys.exit(1)
    
    # 馬名直接入力テスト
    success = test_horse_name_chat()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 馬名直接入力チャット機能テスト完了!")
        print("\n🐎 テスト成功パターン:")
        print("  • 馬名抽出 → D-Logic分析 → LLM説明生成")
        print("  • Phase D伝説馬データベース活用")
        print("  • MySQL完全分析エンジン連携")
    else:
        print("❌ テストに問題がありました")
    
    print("\n💡 手動テスト方法:")
    print("curl -X POST http://127.0.0.1:8001/api/chat/message \\")
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"message": "エフワンライデンの指数を教えて", "history": []}\'')