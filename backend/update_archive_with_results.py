#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アーカイブページ更新スクリプト
レース結果とD-Logic予想を照合して的中判定を行う
"""

import json
import os
from datetime import datetime
import re

class ArchiveUpdater:
    def __init__(self, results_file, archive_date):
        self.results_file = results_file
        self.archive_date = archive_date
        self.archive_path = f"front/d-logic-ai-frontend/src/app/archive/{archive_date}/page.tsx"
        self.results = None
        self.archive_content = None
        
    def load_results(self):
        """レース結果JSONを読み込み"""
        with open(self.results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.results = {
                'saturday': {f"{r['venue']}_{r['race_number']}": r for r in data['saturday']},
                'sunday': {f"{r['venue']}_{r['race_number']}": r for r in data['sunday']}
            }
        print(f"結果読み込み完了: 土曜{len(self.results['saturday'])}レース, 日曜{len(self.results['sunday'])}レース")
    
    def extract_dlogic_predictions(self, race_content):
        """レース内容からD-Logic予想を抽出"""
        # TypeScriptのhorses配列から馬名を抽出
        horses_match = re.search(r'horses:\s*\[(.*?)\]', race_content, re.DOTALL)
        if not horses_match:
            return []
        
        horses_str = horses_match.group(1)
        # 馬名を抽出（シングルクォートまたはダブルクォートで囲まれた文字列）
        horses = re.findall(r'[\'"]([^\'",]+)[\'"]', horses_str)
        
        # D-Logic分析では通常上位5頭が重要
        return horses[:5] if len(horses) >= 5 else horses
    
    def calculate_hit_result(self, result, dlogic_top5):
        """的中判定を行う"""
        if not result or not dlogic_top5:
            return None
        
        first = result.get('first', '')
        second = result.get('second', '')
        third = result.get('third', '')
        
        # D-Logic上位5頭の的中判定
        hit_info = {
            'dlogic_top5': dlogic_top5,
            'hit_type': '',
            'hit_description': '',
            'hit_rate': 0
        }
        
        # 上位3頭での的中判定
        top3 = dlogic_top5[:3]
        
        # 1着的中
        if first in top3:
            if first == dlogic_top5[0]:
                hit_info['hit_type'] = '◎ 1位が1着'
                hit_info['hit_description'] = 'D-Logic1位が見事に1着！'
                hit_info['hit_rate'] = 100
            else:
                hit_info['hit_type'] = '○ 上位3頭内から1着'
                hit_info['hit_description'] = f'D-Logic{top3.index(first)+1}位が1着'
                hit_info['hit_rate'] = 80
        # 2着的中
        elif second in top3:
            hit_info['hit_type'] = '△ 上位3頭内から2着'
            hit_info['hit_description'] = f'D-Logic{top3.index(second)+1}位が2着'
            hit_info['hit_rate'] = 60
        # 3着的中
        elif third in top3:
            hit_info['hit_type'] = '▲ 上位3頭内から3着'
            hit_info['hit_description'] = f'D-Logic{top3.index(third)+1}位が3着'
            hit_info['hit_rate'] = 40
        # 上位5頭での的中
        elif first in dlogic_top5 or second in dlogic_top5 or third in dlogic_top5:
            hit_info['hit_type'] = '☆ 上位5頭内から3着内'
            hit_info['hit_description'] = 'D-Logic上位5頭から3着内'
            hit_info['hit_rate'] = 30
        else:
            hit_info['hit_type'] = '× 不的中'
            hit_info['hit_description'] = 'D-Logic上位5頭が3着内に入らず'
            hit_info['hit_rate'] = 0
        
        return hit_info
    
    def create_result_component(self, result, hit_info):
        """結果表示用のReactコンポーネントを生成"""
        if not result or not hit_info:
            return ""
        
        return f'''
              <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm">
                <div className="font-semibold text-gray-700 mb-2">レース結果</div>
                <div className="space-y-1">
                  <div className="flex">
                    <span className="font-medium w-12">1着:</span>
                    <span>{result.get('first', '-')}</span>
                  </div>
                  <div className="flex">
                    <span className="font-medium w-12">2着:</span>
                    <span>{result.get('second', '-')}</span>
                  </div>
                  <div className="flex">
                    <span className="font-medium w-12">3着:</span>
                    <span>{result.get('third', '-')}</span>
                  </div>
                </div>
                
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="font-semibold text-gray-700 mb-2">D-Logic予想結果</div>
                  <div className="space-y-1">
                    <div className="text-blue-600">
                      上位5頭: {', '.join(hit_info['dlogic_top5'])}
                    </div>
                    <div className="flex items-center mt-2">
                      <span className="font-medium">的中:</span>
                      <span className="ml-2 text-lg">{hit_info['hit_type']}</span>
                    </div>
                    <div className="text-gray-600">{hit_info['hit_description']}</div>
                    <div className="mt-2">
                      <span className="font-medium">的中率:</span>
                      <span className="ml-2 text-lg font-bold text-green-600">{hit_info['hit_rate']}%</span>
                    </div>
                  </div>
                </div>
              </div>'''
    
    def update_archive_file(self):
        """アーカイブファイルを更新"""
        if not os.path.exists(self.archive_path):
            print(f"アーカイブファイルが見つかりません: {self.archive_path}")
            return False
        
        with open(self.archive_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 各レースを処理
        races_updated = 0
        
        # レースブロックを検索（race_idから次のrace_idまで）
        race_blocks = re.finditer(
            r'(race_id:\s*[\'"]([^\'",]+)[\'"],.*?)((?=race_id:)|$)',
            content,
            re.DOTALL
        )
        
        new_content = content
        offset = 0
        
        for match in race_blocks:
            race_block = match.group(1)
            race_id = match.group(2)
            
            # race_idから開催場とレース番号を抽出
            # 例: 'archive-niigata-11r-20250817' -> venue='新潟', race_number=11
            id_parts = race_id.split('-')
            if len(id_parts) >= 3:
                venue_en = id_parts[1]
                race_num_str = id_parts[2].replace('r', '')
                
                # 英語->日本語変換
                venue_map = {
                    'sapporo': '札幌', 'hakodate': '函館', 'fukushima': '福島',
                    'niigata': '新潟', 'tokyo': '東京', 'nakayama': '中山',
                    'chukyo': '中京', 'kyoto': '京都', 'hanshin': '阪神',
                    'kokura': '小倉'
                }
                
                venue = venue_map.get(venue_en)
                if venue and race_num_str.isdigit():
                    race_number = int(race_num_str)
                    key = f"{venue}_{race_number}"
                    
                    # 土曜または日曜の結果を検索
                    result = (self.results['saturday'].get(key) or 
                             self.results['sunday'].get(key))
                    
                    if result:
                        # D-Logic予想を抽出
                        dlogic_top5 = self.extract_dlogic_predictions(race_block)
                        
                        # 的中判定
                        hit_info = self.calculate_hit_result(result['result'], dlogic_top5)
                        
                        if hit_info:
                            # 結果コンポーネントを生成
                            result_component = self.create_result_component(result['result'], hit_info)
                            
                            # レースブロックの終了位置を探す（</div>の連続）
                            end_pattern = r'(\s*</div>\s*</div>\s*</div>)'
                            end_match = re.search(end_pattern, race_block)
                            
                            if end_match:
                                # 結果を挿入
                                insert_pos = match.start() + end_match.start() + offset
                                new_content = (new_content[:insert_pos] + 
                                             result_component + 
                                             new_content[insert_pos:])
                                offset += len(result_component)
                                races_updated += 1
                                print(f"更新: {venue} {race_number}R - {hit_info['hit_type']}")
        
        # ファイルを保存
        if races_updated > 0:
            with open(self.archive_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"\n{races_updated}レース更新完了！")
            return True
        else:
            print("更新対象のレースが見つかりませんでした")
            return False

def main():
    """メイン処理"""
    # 最新の結果ファイルを探す
    results_dir = "data/race_results"
    if not os.path.exists(results_dir):
        print("結果ディレクトリが見つかりません")
        return
    
    # 最新のファイルを取得
    files = [f for f in os.listdir(results_dir) if f.startswith('weekend_results_')]
    if not files:
        print("結果ファイルが見つかりません")
        return
    
    latest_file = sorted(files)[-1]
    results_file = os.path.join(results_dir, latest_file)
    
    # アーカイブ日付を入力
    archive_date = input("アーカイブ日付を入力してください (例: 2025-08-17): ")
    
    # 更新実行
    updater = ArchiveUpdater(results_file, archive_date)
    updater.load_results()
    
    if updater.update_archive_file():
        print("\nアーカイブページの更新が完了しました！")
        print(f"更新ファイル: {updater.archive_path}")
    else:
        print("\n更新に失敗しました")

if __name__ == "__main__":
    main()