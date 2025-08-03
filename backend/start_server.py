#!/usr/bin/env python3
"""
FastAPIサーバー起動スクリプト
馬名直接入力D-Logic分析テスト用
"""
import uvicorn
import sys
import os

# パス設定
sys.path.append(os.path.dirname(__file__))

if __name__ == "__main__":
    print("🚀 D-Logic競馬予想AI サーバー起動")
    print("Phase D統合版 - 馬名直接入力対応")
    print("=" * 50)
    print("🌐 サーバーURL: http://127.0.0.1:8001")
    print("📖 API ドキュメント: http://127.0.0.1:8001/docs") 
    print("🐎 チャットエンドポイント: http://127.0.0.1:8001/api/chat/message")
    print()
    print("📝 馬名直接入力テスト例:")
    print("POST /api/chat/message")
    print('{"message": "エフワンライデンの指数を教えて"}')
    print('{"message": "ディープインパクトはどう？"}')
    print()
    print("サーバーを停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "main:app", 
            host="127.0.0.1", 
            port=8001, 
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しました")
    except Exception as e:
        print(f"❌ サーバー起動エラー: {e}")
        sys.exit(1)