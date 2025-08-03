#!/usr/bin/env python3
"""
JV-Link接続テスト
既存のJRA-VAN環境での動作確認
"""
import sys
import os

def test_jvlink_connection():
    """JV-Link接続テスト"""
    print("🏇 JV-Link接続テスト開始")
    print("=" * 50)
    
    try:
        # Windows COM接続のテスト
        import win32com.client
        print("✅ win32com.client インポート成功")
        
        # JV-Linkオブジェクト作成
        jv = win32com.client.Dispatch("JVDTLab.JVLink")
        print("✅ JV-Linkオブジェクト作成成功")
        
        # JV-Link初期化
        result = jv.JVInit("UNKNOWN")  # 非登録ソフト用SID
        print(f"🔧 JV-Link初期化結果: {result}")
        
        if result == 0:
            print("✅ JV-Link初期化成功")
            
            # 今週データ取得テスト
            print("\n📊 今週データ取得テスト:")
            
            # データ種別"RACE"で今週データを取得
            fromtime = "00000000000000"  # 初回取得
            
            result = jv.JVOpen("RACE", fromtime, 4)  # option=4は今週データ
            print(f"📥 JVOpen結果: {result}")
            
            if result == 0:
                print("✅ 今週データ取得要求成功")
                
                # データ読み取りテスト
                read_count = 0
                while True:
                    result = jv.JVRead()
                    if result == -1:  # 終了
                        break
                    elif result == 0:  # 正常
                        data = jv.GetLastReadData()
                        if data:
                            read_count += 1
                            if read_count <= 3:  # 最初の3件を表示
                                print(f"📄 データ例 {read_count}: {data[:50]}...")
                    elif result == -3:  # ダウンロード中
                        print("⏳ ダウンロード中...")
                        import time
                        time.sleep(1)
                        continue
                    else:
                        print(f"⚠️  読み取りエラー: {result}")
                        break
                
                print(f"📊 読み取りデータ件数: {read_count}")
                
                # クローズ
                jv.JVClose()
                print("✅ JV-Link正常終了")
                
            else:
                print(f"❌ データ取得エラー: {result}")
                
        else:
            print(f"❌ JV-Link初期化エラー: {result}")
        
        print("\n🎯 結論:")
        if result == 0:
            print("✅ JRA-VAN統合準備完了！")
            print("   Python → JV-Link → JRA-VAN接続成功")
            print("   Phase I実装開始可能")
        else:
            print("⚠️  JRA-VAN接続に問題があります")
            print("   利用キー・認証状況を確認してください")
            
    except ImportError:
        print("❌ win32com.client が見つかりません")
        print("   インストール: pip install pywin32")
        return False
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("   JV-Linkが正しくインストールされているか確認してください")
        return False
        
    return True

if __name__ == "__main__":
    test_jvlink_connection()