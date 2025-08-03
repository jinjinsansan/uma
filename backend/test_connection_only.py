#!/usr/bin/env python3
"""
MySQL接続テスト（接続のみ）
"""
import mysql.connector
import os

def test_mysql_connections():
    """様々な接続設定をテスト"""
    print("🔌 MySQL接続テスト開始")
    
    # 接続設定のパターン
    connection_configs = [
        {
            "name": "localhost:3306",
            "config": {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '',
                'database': 'mykeibadb',
                'charset': 'utf8mb4'
            }
        },
        {
            "name": "127.0.0.1:3306",
            "config": {
                'host': '127.0.0.1',
                'port': 3306,
                'user': 'root',
                'password': '',
                'database': 'mykeibadb',
                'charset': 'utf8mb4'
            }
        },
        {
            "name": "172.25.160.1:3306 (WSL)",
            "config": {
                'host': '172.25.160.1',
                'port': 3306,
                'user': 'root',
                'password': '04050405Aoi-',
                'database': 'mykeibadb',
                'charset': 'utf8mb4'
            }
        }
    ]
    
    for test_case in connection_configs:
        print(f"\n🔍 {test_case['name']} をテスト中...")
        
        try:
            conn = mysql.connector.connect(**test_case['config'])
            cursor = conn.cursor()
            
            # 簡単なクエリ実行
            cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho LIMIT 1")
            result = cursor.fetchone()
            
            print(f"  ✅ 接続成功! レコード数サンプル: {result[0] if result else 'N/A'}")
            
            cursor.close()
            conn.close()
            
            return test_case['config']  # 最初に成功した設定を返す
            
        except mysql.connector.Error as e:
            print(f"  ❌ 接続失敗: {e}")
        except Exception as e:
            print(f"  ❌ エラー: {e}")
    
    print("\n❌ 全ての接続設定が失敗しました")
    return None

def test_without_database():
    """データベース指定なしでの接続テスト"""
    print("\n🔍 データベース指定なしでの接続テスト...")
    
    configs = [
        {'host': 'localhost', 'user': 'root', 'password': ''},
        {'host': '127.0.0.1', 'user': 'root', 'password': ''},
        {'host': '172.25.160.1', 'user': 'root', 'password': '04050405Aoi-'}
    ]
    
    for config in configs:
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            
            # データベース一覧取得
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            
            print(f"  ✅ {config['host']} 接続成功!")
            print(f"    利用可能DB: {[db[0] for db in databases]}")
            
            # mykeibadbの存在確認
            if any('mykeibadb' in str(db) for db in databases):
                print("    ✅ mykeibadb データベース発見!")
            else:
                print("    ⚠️ mykeibadb データベースが見つかりません")
            
            cursor.close()
            conn.close()
            
            return config
            
        except Exception as e:
            print(f"  ❌ {config['host']} 失敗: {e}")
    
    return None

if __name__ == "__main__":
    # データベース指定ありテスト
    working_config = test_mysql_connections()
    
    if not working_config:
        # データベース指定なしテスト
        basic_config = test_without_database()
        
        if basic_config:
            print(f"\n💡 基本接続は成功しました。mykeibadbデータベースの設定を確認してください。")
        else:
            print(f"\n❌ MySQL接続が全て失敗しました。")
            print(f"💡 考えられる原因:")
            print(f"  1. MySQLサービスが起動していない")
            print(f"  2. パスワードが間違っている")
            print(f"  3. ホスト設定が間違っている")
            print(f"  4. ファイアウォールがブロックしている")
    else:
        print(f"\n✅ MySQL接続設定確認完了!")
        print(f"使用する設定: {working_config}")