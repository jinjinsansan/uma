#!/usr/bin/env python3
"""
分割されたD-Logicデータを統合して読み込むローダー
"""

import json
import os
from typing import Dict, Any

class DLogicDataLoader:
    def __init__(self, data_dir: str = 'data/chunks'):
        self.data_dir = data_dir
        self.index_file = os.path.join(data_dir, 'dlogic_index.json')
        self._index = None
        self._cache = {}
    
    def load_index(self) -> Dict[str, Any]:
        """インデックスファイルを読み込み"""
        if self._index is None:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self._index = json.load(f)
        return self._index
    
    def load_chunk(self, chunk_id: int) -> Dict[str, Any]:
        """指定したチャンクを読み込み"""
        if chunk_id in self._cache:
            return self._cache[chunk_id]
        
        index = self.load_index()
        chunk_info = next(c for c in index['chunks'] if c['chunk_id'] == chunk_id)
        
        filepath = os.path.join(self.data_dir, chunk_info['filename'])
        with open(filepath, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
        
        self._cache[chunk_id] = chunk_data
        return chunk_data
    
    def load_all_horses(self) -> Dict[str, Any]:
        """全馬データを統合して読み込み"""
        index = self.load_index()
        all_horses = {}
        
        for chunk_info in index['chunks']:
            chunk = self.load_chunk(chunk_info['chunk_id'])
            all_horses.update(chunk['horses'])
        
        return all_horses
    
    def find_horse(self, horse_name: str) -> Dict[str, Any]:
        """特定の馬のデータを検索"""
        index = self.load_index()
        
        # アルファベット分割の場合は効率的に検索
        if index['meta']['split_method'] == 'alphabetical':
            for chunk_info in index['chunks']:
                if ('first_horse' in chunk_info and 
                    chunk_info['first_horse'] <= horse_name <= chunk_info['last_horse']):
                    chunk = self.load_chunk(chunk_info['chunk_id'])
                    return chunk['horses'].get(horse_name)
        
        # ハッシュ分割の場合は該当チャンクを直接計算
        elif index['meta']['split_method'] == 'hash':
            chunk_id = (hash(horse_name) % index['meta']['total_chunks']) + 1
            chunk = self.load_chunk(chunk_id)
            return chunk['horses'].get(horse_name)
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """データ統計を取得"""
        index = self.load_index()
        total_horses = sum(chunk['horses_count'] for chunk in index['chunks'])
        
        return {
            'total_chunks': index['meta']['total_chunks'],
            'total_horses': total_horses,
            'split_method': index['meta']['split_method'],
            'chunks': index['chunks']
        }

# 使用例
if __name__ == '__main__':
    loader = DLogicDataLoader()
    
    # 統計表示
    stats = loader.get_stats()
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Total horses: {stats['total_horses']}")
    print(f"Split method: {stats['split_method']}")
    
    # 特定の馬を検索
    horse_data = loader.find_horse('ヴァランセカズマ')
    if horse_data:
        print(f"Found horse with {horse_data['race_count']} races")
