#!/usr/bin/env python3
"""
Render向けD-Logicデータマネージャー
分割されたJSONファイルを効率的に読み込み・キャッシュ
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional, List
import aiofiles
from functools import lru_cache
import logging

class RenderDataManager:
    """
    Render環境で分割されたD-Logicデータを効率的に管理するクラス
    """
    
    def __init__(self, data_dir: str = 'data/chunks', max_cache_chunks: int = 3):
        self.data_dir = data_dir
        self.max_cache_chunks = max_cache_chunks
        self.index_file = os.path.join(data_dir, 'dlogic_index.json')
        self._index = None
        self._chunk_cache = {}
        self._cache_order = []
        
        # ロガーの設定
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    async def load_index(self) -> Dict[str, Any]:
        """インデックスファイルを非同期で読み込み"""
        if self._index is None:
            try:
                async with aiofiles.open(self.index_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    self._index = json.loads(content)
                self.logger.info(f"Loaded index with {self._index['meta']['total_chunks']} chunks")
            except Exception as e:
                self.logger.error(f"Failed to load index: {e}")
                raise
        
        return self._index
    
    async def load_chunk(self, chunk_id: int) -> Dict[str, Any]:
        """指定したチャンクを非同期で読み込み（LRUキャッシュ付き）"""
        if chunk_id in self._chunk_cache:
            # キャッシュヒット時は順序を更新
            self._cache_order.remove(chunk_id)
            self._cache_order.append(chunk_id)
            return self._chunk_cache[chunk_id]
        
        # インデックスから該当チャンクの情報を取得
        index = await self.load_index()
        chunk_info = next((c for c in index['chunks'] if c['chunk_id'] == chunk_id), None)
        
        if not chunk_info:
            raise ValueError(f"Chunk {chunk_id} not found in index")
        
        # ファイルを非同期で読み込み
        filepath = os.path.join(self.data_dir, chunk_info['filename'])
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
                chunk_data = json.loads(content)
        except Exception as e:
            self.logger.error(f"Failed to load chunk {chunk_id}: {e}")
            raise
        
        # キャッシュ管理（LRU）
        if len(self._chunk_cache) >= self.max_cache_chunks:
            # 最古のチャンクを削除
            oldest_chunk = self._cache_order.pop(0)
            del self._chunk_cache[oldest_chunk]
            self.logger.debug(f"Evicted chunk {oldest_chunk} from cache")
        
        # 新しいチャンクをキャッシュに追加
        self._chunk_cache[chunk_id] = chunk_data
        self._cache_order.append(chunk_id)
        
        self.logger.debug(f"Loaded chunk {chunk_id} with {len(chunk_data['horses'])} horses")
        return chunk_data
    
    async def find_horse(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """特定の馬のデータを非同期で検索"""
        index = await self.load_index()
        split_method = index['meta']['split_method']
        
        try:
            if split_method == 'alphabetical':
                # アルファベット分割の場合は効率的に検索
                for chunk_info in index['chunks']:
                    if ('first_horse' in chunk_info and 
                        chunk_info['first_horse'] <= horse_name <= chunk_info['last_horse']):
                        chunk = await self.load_chunk(chunk_info['chunk_id'])
                        return chunk['horses'].get(horse_name)
            
            elif split_method == 'hash':
                # ハッシュ分割の場合は該当チャンクを直接計算
                chunk_id = (hash(horse_name) % index['meta']['total_chunks']) + 1
                chunk = await self.load_chunk(chunk_id)
                return chunk['horses'].get(horse_name)
        
        except Exception as e:
            self.logger.error(f"Error finding horse {horse_name}: {e}")
            return None
        
        return None
    
    async def find_horses_batch(self, horse_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """複数の馬を一括検索（並列処理）"""
        tasks = [self.find_horse(name) for name in horse_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            name: result if not isinstance(result, Exception) else None
            for name, result in zip(horse_names, results)
        }
    
    async def get_chunk_horses(self, chunk_id: int) -> Dict[str, Any]:
        """指定したチャンクの全馬データを取得"""
        chunk = await self.load_chunk(chunk_id)
        return chunk['horses']
    
    async def get_stats(self) -> Dict[str, Any]:
        """データ統計を非同期で取得"""
        index = await self.load_index()
        total_horses = sum(chunk['horses_count'] for chunk in index['chunks'])
        
        return {
            'total_chunks': index['meta']['total_chunks'],
            'total_horses': total_horses,
            'split_method': index['meta']['split_method'],
            'cached_chunks': len(self._chunk_cache),
            'cache_order': self._cache_order.copy(),
            'chunks': index['chunks']
        }
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._chunk_cache.clear()
        self._cache_order.clear()
        self.logger.info("Cache cleared")
    
    async def preload_popular_chunks(self, chunk_ids: List[int]):
        """よく使用されるチャンクを事前に読み込み"""
        tasks = [self.load_chunk(chunk_id) for chunk_id in chunk_ids[:self.max_cache_chunks]]
        await asyncio.gather(*tasks, return_exceptions=True)
        self.logger.info(f"Preloaded chunks: {chunk_ids[:self.max_cache_chunks]}")

# FastAPI用のヘルパー関数
class FastAPIDataManager:
    """FastAPI専用のデータマネージャー"""
    
    def __init__(self, data_dir: str = 'data/chunks'):
        self.manager = RenderDataManager(data_dir)
        self._initialized = False
    
    async def initialize(self):
        """初期化処理"""
        if not self._initialized:
            await self.manager.load_index()
            self._initialized = True
    
    async def get_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬データを取得（APIエンドポイント用）"""
        await self.initialize()
        return await self.manager.find_horse(horse_name)
    
    async def get_multiple_horses(self, horse_names: List[str]) -> Dict[str, Any]:
        """複数馬データを一括取得（APIエンドポイント用）"""
        await self.initialize()
        results = await self.manager.find_horses_batch(horse_names)
        
        return {
            'success': True,
            'total_requested': len(horse_names),
            'found_count': sum(1 for v in results.values() if v is not None),
            'data': results
        }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """システム統計を取得（APIエンドポイント用）"""
        await self.initialize()
        return await self.manager.get_stats()

# 使用例とテスト
async def test_performance():
    """パフォーマンステスト"""
    import time
    
    manager = RenderDataManager()
    
    # 統計取得のテスト
    start_time = time.time()
    stats = await manager.get_stats()
    print(f"Stats loaded in {time.time() - start_time:.3f}s")
    print(f"Total horses: {stats['total_horses']}")
    print(f"Total chunks: {stats['total_chunks']}")
    
    # 単体検索のテスト
    test_horses = ['ヴァランセカズマ', 'カップッチョ', '存在しない馬']
    
    for horse_name in test_horses:
        start_time = time.time()
        horse_data = await manager.find_horse(horse_name)
        elapsed = time.time() - start_time
        
        if horse_data:
            print(f"Found {horse_name} in {elapsed:.3f}s ({horse_data['race_count']} races)")
        else:
            print(f"Horse {horse_name} not found in {elapsed:.3f}s")
    
    # バッチ検索のテスト
    start_time = time.time()
    batch_results = await manager.find_horses_batch(test_horses)
    batch_elapsed = time.time() - start_time
    
    found_count = sum(1 for v in batch_results.values() if v is not None)
    print(f"Batch search: {found_count}/{len(test_horses)} found in {batch_elapsed:.3f}s")
    
    # キャッシュ統計
    cache_stats = await manager.get_stats()
    print(f"Cached chunks: {cache_stats['cached_chunks']}")

if __name__ == '__main__':
    asyncio.run(test_performance())