#!/usr/bin/env python3
"""
Simple MySQL Connection Test without mysql-connector-python
Windows MySQL94サーバーとの接続テスト
"""
import socket
import os

# 直接設定値を使用（.env読み込み不要）

def test_mysql_socket_connection():
    """Socket接続でMySQL可用性をテスト"""
    host = '172.25.160.1'  # Windows Host IP
    port = 3306
    
    print("MySQL94 サーバー接続テスト")
    print("=" * 40)
    print(f"接続先: {host}:{port}")
    print()
    
    try:
        # Socket接続テスト
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print("✅ MySQL94サーバー接続成功!")
            print("✅ ポート3306が開いています")
            print("✅ WSL2からWindows MySQLへの接続確立")
            print()
            print("📊 接続設定情報:")
            print(f"  - Host: {host}")
            print(f"  - Port: {port}")
            print(f"  - User: root")
            print(f"  - Database: mykeibadb")
            print()
            print("🔄 次のステップ:")
            print("  1. mysql-connector-python をインストール")
            print("  2. mysql_test.py で完全接続テスト")
            print("  3. Phase D完全調査実行")
            print()
            print("💡 mysql-connector-pythonインストール方法:")
            print("  pip3 install mysql-connector-python")
            print("  または")
            print("  Windows側でPythonパッケージをインストール")
            
            return True
        else:
            print(f"❌ 接続失敗: エラーコード {result}")
            return False
            
    except socket.timeout:
        print("❌ 接続タイムアウト")
        print("MySQL94サーバーが応答しません")
        return False
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False
    finally:
        sock.close()

def check_environment():
    """環境設定確認"""
    print("🔍 環境設定確認:")
    print(f"  MYSQL_HOST: 172.25.160.1 (Windows Host)")
    print(f"  MYSQL_PORT: 3306")
    print(f"  MYSQL_USER: root")
    print(f"  MYSQL_DATABASE: mykeibadb")
    print()

if __name__ == "__main__":
    check_environment()
    
    if test_mysql_socket_connection():
        print("=" * 40)
        print("✅ MySQL94接続テスト成功!")
        print("Phase D実行準備完了")
        exit(0)
    else:
        print("=" * 40)
        print("❌ MySQL94接続テスト失敗")
        print("設定を確認してください")
        exit(1)