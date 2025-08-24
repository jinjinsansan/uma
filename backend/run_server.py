#!/usr/bin/env python3
"""
シンプルなサーバー起動スクリプト
"""
import sys
import os

# FastAPIアプリケーションをインポート
from main import app

# uvicornがインストールされているか確認
try:
    import uvicorn
    print("✅ uvicornが見つかりました")
    # uvicornで起動
    uvicorn.run(app, host="127.0.0.1", port=8000)
except ImportError:
    print("⚠️ uvicornが見つかりません。代替方法で起動します...")
    
    # 代替方法：FastAPIのテストクライアントを使用
    from fastapi.testclient import TestClient
    import threading
    import time
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    
    # テストクライアントを作成
    client = TestClient(app)
    
    class ProxyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            # FastAPIアプリケーションにリクエストを転送
            response = client.get(self.path)
            self.send_response(response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.content)
        
        def do_POST(self):
            # POSTデータを読み取り
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # FastAPIアプリケーションにリクエストを転送
            response = client.post(
                self.path,
                content=post_data,
                headers={'Content-Type': 'application/json'}
            )
            self.send_response(response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.content)
        
        def log_message(self, format, *args):
            # ログメッセージをカスタマイズ
            print(f"{self.address_string()} - {format % args}")
    
    # HTTPサーバーを起動
    server = HTTPServer(('127.0.0.1', 8000), ProxyHandler)
    print("🚀 サーバーを http://127.0.0.1:8000 で起動しました")
    print("終了するには Ctrl+C を押してください")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 サーバーを終了します")
        server.shutdown()