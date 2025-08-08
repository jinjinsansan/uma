#!/usr/bin/env python3
"""
dlogic_raw_knowledge.jsonを分割するスクリプト
GitHub 100MB制限に対応
"""

import json
import os
import sys
from typing import Dict, List, Any
import math

def get_file_size_mb(filepath: str) -> float:
    """ファイルサイズをMBで取得"""
    return os.path.getsize(filepath) / (1024 * 1024)

def estimate_chunk_size(data: Dict[str, Any], target_size_mb: float = 90) -> int:
    """目標サイズに基づいて分割数を推定"""
    total_horses = len(data['horses'])
    current_size_mb = get_file_size_mb('data/dlogic_raw_knowledge.json')
    
    # 90MBを目標サイズとして分割数を計算（余裕をもって）
    estimated_chunks = math.ceil(current_size_mb / target_size_mb)
    horses_per_chunk = math.ceil(total_horses / estimated_chunks)
    
    return horses_per_chunk, estimated_chunks

def split_by_alphabetical(data: Dict[str, Any], horses_per_chunk: int) -> List[Dict[str, Any]]:
    """アルファベット順で分割"""
    horses = data['horses']
    horse_names = sorted(horses.keys())
    
    chunks = []
    for i in range(0, len(horse_names), horses_per_chunk):
        chunk_names = horse_names[i:i + horses_per_chunk]
        chunk_data = {
            'meta': {
                **data['meta'],
                'chunk_info': {
                    'chunk_id': len(chunks) + 1,
                    'total_chunks': math.ceil(len(horse_names) / horses_per_chunk),
                    'horses_in_chunk': len(chunk_names),
                    'first_horse': chunk_names[0] if chunk_names else '',
                    'last_horse': chunk_names[-1] if chunk_names else ''
                }
            },
            'horses': {name: horses[name] for name in chunk_names}
        }
        chunks.append(chunk_data)
    
    return chunks

def split_by_hash(data: Dict[str, Any], num_chunks: int) -> List[Dict[str, Any]]:
    """ハッシュベースで均等に分割（ランダム性を保ちつつ一貫性がある）"""
    horses = data['horses']
    
    # 各チャンクの初期化
    chunks = []
    for i in range(num_chunks):
        chunks.append({
            'meta': {
                **data['meta'],
                'chunk_info': {
                    'chunk_id': i + 1,
                    'total_chunks': num_chunks,
                    'horses_in_chunk': 0
                }
            },
            'horses': {}
        })
    
    # ハッシュベースで分散
    for horse_name, horse_data in horses.items():
        chunk_index = hash(horse_name) % num_chunks
        chunks[chunk_index]['horses'][horse_name] = horse_data
        chunks[chunk_index]['meta']['chunk_info']['horses_in_chunk'] += 1
    
    return chunks

def create_index_file(chunks: List[Dict[str, Any]], split_method: str) -> Dict[str, Any]:
    """インデックスファイルを作成"""
    index_data = {
        'meta': {
            'version': '3.1',
            'split_method': split_method,
            'total_chunks': len(chunks),
            'created': chunks[0]['meta']['created'],
            'split_date': chunks[0]['meta']['last_updated']
        },
        'chunks': []
    }
    
    for i, chunk in enumerate(chunks):
        chunk_info = {
            'chunk_id': i + 1,
            'filename': f'dlogic_raw_knowledge_chunk_{i+1:02d}.json',
            'horses_count': chunk['meta']['chunk_info']['horses_in_chunk']
        }
        
        if split_method == 'alphabetical':
            chunk_info['first_horse'] = chunk['meta']['chunk_info']['first_horse']
            chunk_info['last_horse'] = chunk['meta']['chunk_info']['last_horse']
        
        index_data['chunks'].append(chunk_info)
    
    return index_data

def save_chunks(chunks: List[Dict[str, Any]], output_dir: str, prefix: str):
    """チャンクファイルを保存"""
    os.makedirs(output_dir, exist_ok=True)
    
    for i, chunk in enumerate(chunks):
        filename = f'{prefix}_chunk_{i+1:02d}.json'
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        
        size_mb = get_file_size_mb(filepath)
        print(f'Created {filename}: {size_mb:.1f}MB, {len(chunk["horses"])} horses')

def create_loader_script(output_dir: str):
    """データローダースクリプトを作成"""
    loader_content = '''#!/usr/bin/env python3
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
'''
    
    with open(os.path.join(output_dir, 'dlogic_loader.py'), 'w', encoding='utf-8') as f:
        f.write(loader_content)
    
    print(f'Created data loader script: {os.path.join(output_dir, "dlogic_loader.py")}')

def main():
    input_file = 'data/dlogic_raw_knowledge.json'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        sys.exit(1)
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    current_size = get_file_size_mb(input_file)
    total_horses = len(data['horses'])
    
    print(f"Current file size: {current_size:.1f}MB")
    print(f"Total horses: {total_horses}")
    
    horses_per_chunk, estimated_chunks = estimate_chunk_size(data)
    print(f"Estimated chunks needed: {estimated_chunks}")
    print(f"Horses per chunk: {horses_per_chunk}")
    
    # デフォルトでアルファベット順分割を使用（検索に最適）
    print("\\nUsing alphabetical split method (recommended for searches)")
    chunks = split_by_alphabetical(data, horses_per_chunk)
    split_method = 'alphabetical'
    
    # 出力ディレクトリを作成
    output_dir = 'data/chunks'
    save_chunks(chunks, output_dir, 'dlogic_raw_knowledge')
    
    # インデックスファイルを作成
    index_data = create_index_file(chunks, split_method)
    index_path = os.path.join(output_dir, 'dlogic_index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    index_size = get_file_size_mb(index_path)
    print(f'\\nCreated index file: {index_size:.2f}MB')
    
    # ローダースクリプトを作成
    create_loader_script(output_dir)
    
    print(f'\\nSplit completed successfully!')
    print(f'Total chunks: {len(chunks)}')
    print(f'Output directory: {output_dir}')

if __name__ == '__main__':
    main()