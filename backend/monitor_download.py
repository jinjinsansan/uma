#!/usr/bin/env python3
"""
mykeibadbダウンロード完了監視スクリプト
ダウンロード完了を検知したら自動でバッチ処理開始
"""
import mysql.connector
import time
import subprocess
from datetime import datetime

def monitor_download_completion():
    """ダウンロード完了監視"""
    print("🔍 mykeibadbダウンロード完了監視開始")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    last_count = 0
    stable_count = 0
    check_interval = 300  # 5分間隔
    
    while True:
        try:
            # 軽量な接続テスト
            conn = mysql.connector.connect(
                host='172.25.160.1',
                port=3306,
                user='root',
                password='04050405Aoi-',
                database='mykeibadb',
                charset='utf8mb4',
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            
            # シンプルなクエリでダウンロード状況確認
            start_time = time.time()
            cursor.execute('SELECT 1')
            query_time = time.time() - start_time
            
            if query_time < 1.0:  # 1秒以内なら高速化
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - クエリ高速化検知: {query_time:.3f}秒")
                
                # レコード数確認
                cursor.execute('SELECT COUNT(*) FROM umagoto_race_joho LIMIT 1')
                current_count = cursor.fetchone()[0]
                
                if current_count == last_count:
                    stable_count += 1
                    print(f"📊 安定状態: {stable_count}/3, レコード数: {current_count:,}件")
                    
                    if stable_count >= 3:  # 3回連続で変化なし
                        print("\n🎉 ダウンロード完了検知!")
                        print(f"📊 最終レコード数: {current_count:,}件")
                        cursor.close()
                        conn.close()
                        
                        # バッチ処理自動開始
                        print("🚀 年度別戦略バッチ処理自動開始...")
                        subprocess.run(['python3', 'batch_yearly_strategic.py'])
                        break
                else:
                    stable_count = 0
                    growth = current_count - last_count
                    print(f"📈 増加中: +{growth:,}件 (総計: {current_count:,}件)")
                
                last_count = current_count
            else:
                print(f"⏳ {datetime.now().strftime('%H:%M:%S')} - まだダウンロード中: {query_time:.1f}秒")
                stable_count = 0
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - 接続エラー: {e}")
            stable_count = 0
        
        print(f"💤 {check_interval//60}分待機...")
        time.sleep(check_interval)

if __name__ == "__main__":
    monitor_download_completion()