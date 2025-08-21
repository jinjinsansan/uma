#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
9レース版騎手ナレッジファイル作成プロセスの監視エージェント
エラー発生時やプロセス停止時に自動的に報告
"""

import os
import time
import subprocess
import logging
from datetime import datetime, timedelta
import json

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor_jockey_process.log'),
        logging.StreamHandler()
    ]
)

class ProcessMonitor:
    def __init__(self):
        self.process_name = "create_9races_jockey_knowledge.py"
        self.log_file = "jockey_9races_process.log"
        self.output_file = "data/jockey_knowledge_9races.json"
        self.last_line_count = 0
        self.last_check_time = datetime.now()
        self.error_count = 0
        self.max_idle_time = 300  # 5分間進捗がない場合は警告
        self.check_interval = 60   # 60秒ごとにチェック
        
    def check_process_running(self):
        """プロセスが実行中かチェック"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', self.process_name],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except:
            return False
    
    def get_log_line_count(self):
        """ログファイルの行数を取得"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0
    
    def get_latest_logs(self, n=10):
        """最新のログを取得"""
        try:
            result = subprocess.run(
                ['tail', f'-{n}', self.log_file],
                capture_output=True,
                text=True
            )
            return result.stdout
        except:
            return ""
    
    def count_errors_in_log(self):
        """エラーの数をカウント"""
        try:
            result = subprocess.run(
                ['grep', '-c', 'ERROR', self.log_file],
                capture_output=True,
                text=True
            )
            return int(result.stdout.strip())
        except:
            return 0
    
    def get_progress(self):
        """進捗状況を取得"""
        try:
            # 処理済み騎手数を取得
            result = subprocess.run(
                ['grep', '-c', '処理中:', self.log_file],
                capture_output=True,
                text=True
            )
            processed = int(result.stdout.strip())
            
            # 総騎手数（810）
            total = 810
            
            # 進捗率
            progress_rate = (processed / total) * 100 if total > 0 else 0
            
            # 推定残り時間（1騎手約1.5分）
            remaining = total - processed
            remaining_minutes = remaining * 1.5
            remaining_hours = remaining_minutes / 60
            
            return {
                'processed': processed,
                'total': total,
                'progress_rate': progress_rate,
                'remaining_hours': remaining_hours
            }
        except:
            return None
    
    def create_status_report(self):
        """ステータスレポートを作成"""
        is_running = self.check_process_running()
        current_line_count = self.get_log_line_count()
        current_errors = self.count_errors_in_log()
        progress = self.get_progress()
        latest_logs = self.get_latest_logs(5)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'process_running': is_running,
            'log_lines': current_line_count,
            'total_errors': current_errors,
            'new_errors': current_errors - self.error_count,
            'progress': progress,
            'latest_logs': latest_logs,
            'idle_time': None
        }
        
        # アイドル時間の計算
        if current_line_count == self.last_line_count:
            idle_time = datetime.now() - self.last_check_time
            report['idle_time'] = str(idle_time)
        else:
            self.last_check_time = datetime.now()
            self.last_line_count = current_line_count
        
        self.error_count = current_errors
        
        return report
    
    def save_report(self, report):
        """レポートを保存"""
        report_file = f"monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return report_file
    
    def monitor(self):
        """監視ループ"""
        logging.info("監視エージェント起動")
        logging.info(f"監視対象プロセス: {self.process_name}")
        logging.info(f"チェック間隔: {self.check_interval}秒")
        
        while True:
            try:
                report = self.create_status_report()
                
                # 重要なイベントのログ出力
                if not report['process_running']:
                    logging.error("⚠️ プロセスが停止しています！")
                    report_file = self.save_report(report)
                    logging.error(f"詳細レポート: {report_file}")
                    break
                
                if report['new_errors'] > 0:
                    logging.warning(f"⚠️ 新しいエラーが{report['new_errors']}件発生しました")
                
                if report['idle_time'] and report['idle_time'] > str(timedelta(seconds=self.max_idle_time)):
                    logging.warning(f"⚠️ {report['idle_time']}間進捗がありません")
                
                if report['progress']:
                    logging.info(
                        f"進捗: {report['progress']['processed']}/{report['progress']['total']} "
                        f"({report['progress']['progress_rate']:.1f}%) "
                        f"残り約{report['progress']['remaining_hours']:.1f}時間"
                    )
                
                # 定期的なステータス保存（1時間ごと）
                if datetime.now().minute == 0:
                    report_file = self.save_report(report)
                    logging.info(f"定期レポート保存: {report_file}")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logging.info("監視を終了します")
                break
            except Exception as e:
                logging.error(f"監視中にエラー発生: {e}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    monitor = ProcessMonitor()
    monitor.monitor()