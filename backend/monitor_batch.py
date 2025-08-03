#!/usr/bin/env python3
"""
フルバッチ処理の進捗監視スクリプト
"""
import time
import os
import subprocess
from services.dlogic_raw_data_manager import DLogicRawDataManager
from datetime import datetime

def monitor_batch_progress():
    """バッチ進捗監視"""
    print("📊 D-Logic フルバッチ処理監視開始")
    print("=" * 50)
    
    start_time = time.time()
    last_horse_count = 0
    
    while True:
        try:
            # ナレッジファイル状況確認
            manager = DLogicRawDataManager()
            horse_count = len(manager.knowledge_data.get('horses', {}))
            file_size = os.path.getsize(manager.knowledge_file) if os.path.exists(manager.knowledge_file) else 0
            last_updated = manager.knowledge_data.get('meta', {}).get('last_updated', 'N/A')
            
            # プロセス確認
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                process_running = 'auto_full_batch' in result.stdout
            except:
                process_running = False
            
            # 進捗計算
            progress_horses = horse_count - 20  # 初期20頭を除く
            progress_rate = progress_horses / 9980 * 100 if progress_horses > 0 else 0
            
            # 処理速度計算
            elapsed = time.time() - start_time
            if progress_horses > 0:
                rate = progress_horses / elapsed
                eta_hours = (9980 - progress_horses) / rate / 3600 if rate > 0 else 0
            else:
                rate = 0
                eta_hours = 0
            
            # 新規追加馬数
            new_horses = horse_count - last_horse_count
            last_horse_count = horse_count
            
            # レポート出力
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - 進捗レポート")
            print(f"📊 登録済み馬数: {horse_count:,}頭 (+{new_horses})")
            print(f"📈 進捗率: {progress_rate:.1f}% ({progress_horses}/9,980頭)")
            print(f"📁 ファイルサイズ: {file_size/1024/1024:.1f}MB")
            print(f"⚡ 処理速度: {rate:.1f}頭/秒")
            print(f"⏳ 推定残り時間: {eta_hours:.1f}時間")
            print(f"🔄 プロセス状況: {'実行中' if process_running else '停止'}") 
            print(f"📅 最終更新: {last_updated}")
            
            # 処理完了チェック
            if horse_count >= 10000 or not process_running:
                if horse_count >= 10000:
                    print(f"\n🎉 フルバッチ処理完了! 最終馬数: {horse_count}頭")
                elif not process_running:
                    print(f"\n⚠️ プロセス停止検出。現在の馬数: {horse_count}頭")
                break
            
            # 5分間隔で監視
            time.sleep(300)
            
        except KeyboardInterrupt:
            print(f"\n⏹️ 監視を停止しました。現在の馬数: {horse_count}頭")
            break
        except Exception as e:
            print(f"❌ 監視エラー: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_batch_progress()