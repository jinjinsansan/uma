#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合スクリプト：レース結果取得とアーカイブページ更新を一括実行
毎週月曜日に手動実行
"""

import os
import sys
import json
from datetime import datetime
from get_weekend_race_results import WeekendRaceResultsFetcher
from update_archive_with_results import ArchiveUpdater

def main():
    """メイン処理"""
    print("=== D-Logic AI レース結果統合処理 ===")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: 直近土日のレース結果を取得
    print("\n[1] MySQLから直近土日のレース結果を取得中...")
    fetcher = WeekendRaceResultsFetcher()
    results_file = fetcher.run()
    
    if not results_file:
        print("エラー: レース結果の取得に失敗しました")
        return 1
    
    print(f"\n結果ファイル: {results_file}")
    
    # Step 2: アーカイブページの日付を確認
    print("\n[2] 更新対象のアーカイブページを選択")
    print("更新可能な日付:")
    
    # アーカイブディレクトリを確認
    archive_base = "front/d-logic-ai-frontend/src/app/archive"
    if os.path.exists(archive_base):
        dates = [d for d in os.listdir(archive_base) if os.path.isdir(os.path.join(archive_base, d))]
        dates.sort(reverse=True)
        
        for i, date in enumerate(dates[:7]):  # 直近7日分を表示
            print(f"  {i+1}. {date}")
    
    # ユーザーに選択させる
    choice = input("\n更新する日付を選択してください (番号または日付 例: 2025-08-17): ")
    
    if choice.isdigit() and 1 <= int(choice) <= len(dates):
        archive_date = dates[int(choice) - 1]
    else:
        archive_date = choice
    
    # Step 3: アーカイブページを更新
    print(f"\n[3] アーカイブページ ({archive_date}) を更新中...")
    updater = ArchiveUpdater(results_file, archive_date)
    updater.load_results()
    
    if updater.update_archive_file():
        print("\n✅ アーカイブページの更新が完了しました！")
        
        # Step 4: 分析用データの保存
        print("\n[4] 分析用データを保存中...")
        save_analysis_data(results_file, archive_date)
        
        print("\n=== 処理完了 ===")
        print("\n次のステップ:")
        print("1. フロントエンドをデプロイ")
        print("2. 本番環境で確認")
        print("3. 3ヶ月後にデータ分析")
        
        return 0
    else:
        print("\n❌ アーカイブページの更新に失敗しました")
        return 1

def save_analysis_data(results_file, archive_date):
    """分析用データを保存"""
    # 結果ファイルを読み込み
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # 分析用ディレクトリ作成
    analysis_dir = "data/dlogic_analysis"
    os.makedirs(analysis_dir, exist_ok=True)
    
    # 週ごとのファイルとして保存
    week_file = f"{analysis_dir}/week_{archive_date}.json"
    
    analysis_data = {
        'week_ending': archive_date,
        'created_at': datetime.now().isoformat(),
        'results': results,
        'dlogic_predictions': {},  # アーカイブページから抽出予定
        'hit_analysis': {}  # 的中分析結果
    }
    
    with open(week_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
    
    print(f"分析用データを保存: {week_file}")
    
    # 全体の集計ファイルも更新
    summary_file = f"{analysis_dir}/summary.json"
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
    else:
        summary = {
            'total_races': 0,
            'hit_count': 0,
            'hit_rate': 0,
            'weeks': []
        }
    
    summary['weeks'].append(archive_date)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    sys.exit(main())