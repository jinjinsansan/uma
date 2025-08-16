#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-Logic予想結果保存スクリプト
週末のレース前に実行して、D-Logic分析結果を保存する
"""

import json
import os
from datetime import datetime

class DLogicPredictionSaver:
    def __init__(self):
        self.predictions_file = f"data/dlogic_predictions_{datetime.now().strftime('%Y%m%d')}.json"
        self.predictions = {}
    
    def add_prediction(self, venue, race_number, dlogic_top5):
        """D-Logic予想を追加"""
        key = f"{venue}_{race_number}"
        self.predictions[key] = {
            'venue': venue,
            'race_number': race_number,
            'dlogic_top5': dlogic_top5,
            'analyzed_at': datetime.now().isoformat()
        }
        print(f"追加: {venue} {race_number}R - {dlogic_top5[:3]}...")
    
    def save(self):
        """予想を保存"""
        os.makedirs('data', exist_ok=True)
        with open(self.predictions_file, 'w', encoding='utf-8') as f:
            json.dump(self.predictions, f, ensure_ascii=False, indent=2)
        print(f"\n予想を保存しました: {self.predictions_file}")
    
    def manual_input(self):
        """手動で予想を入力"""
        print("D-Logic予想結果を入力してください")
        print("（終了するには空行を入力）\n")
        
        while True:
            venue = input("開催場（例: 新潟）: ").strip()
            if not venue:
                break
            
            race_num = input("レース番号（例: 11）: ").strip()
            if not race_num.isdigit():
                print("レース番号は数字で入力してください")
                continue
            
            print("D-Logic上位5頭を入力（カンマ区切り）:")
            horses = input("例: イクイノックス,ドウデュース,リバティアイランド,タスティエーラ,ソールオリエンス\n> ")
            
            dlogic_top5 = [h.strip() for h in horses.split(',')][:5]
            
            self.add_prediction(venue, int(race_num), dlogic_top5)
            print()
        
        if self.predictions:
            self.save()

def main():
    """メイン処理"""
    saver = DLogicPredictionSaver()
    
    print("=== D-Logic予想結果保存ツール ===")
    print("\n使い方:")
    print("1. レース前にD-Logic分析を実行")
    print("2. 上位5頭をこのツールに入力")
    print("3. 月曜日の結果取得時に自動的に照合されます\n")
    
    # 手動入力モード
    saver.manual_input()

if __name__ == "__main__":
    main()