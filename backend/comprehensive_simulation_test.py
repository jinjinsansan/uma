#!/usr/bin/env python3
"""
🎯 D-Logic AI 包括的シミュレーションテスト
日本全国の自然言語パターンによる200頭馬名テスト
"""
import json
import random
import asyncio
import aiohttp
import time
from typing import List, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(__file__))

class ComprehensiveSimulationTest:
    def __init__(self):
        self.knowledge_file = "data/dlogic_raw_knowledge.json"
        self.api_base_url = "http://localhost:8000"
        self.test_results = []
        self.failed_tests = []
        self.success_count = 0
        self.total_tests = 0
        self.horse_list = []
        
    def load_knowledge_base(self) -> List[str]:
        """ナレッジファイルから馬のリストを読み込み"""
        try:
            print("🐎 ナレッジファイル読み込み開始...")
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                knowledge_data = json.load(f)
            
            horses = list(knowledge_data.keys())
            print(f"✅ 総馬数: {len(horses):,}頭")
            return horses
            
        except FileNotFoundError:
            print(f"❌ ナレッジファイルが見つかりません: {self.knowledge_file}")
            return []
        except Exception as e:
            print(f"❌ ナレッジファイル読み込みエラー: {e}")
            return []
    
    def select_random_horses(self, horses: List[str], count: int = 200) -> List[str]:
        """ランダムに馬を抽出"""
        if len(horses) < count:
            print(f"⚠️ 要求数({count})が総馬数({len(horses)})より多いため、全頭を選択")
            return horses
        
        selected = random.sample(horses, count)
        print(f"🎯 {count}頭をランダム抽出完了")
        return selected
    
    def generate_natural_language_patterns(self) -> Dict[str, List[str]]:
        """日本全国の自然言語パターンを生成"""
        patterns = {
            # 標準語・関東
            "standard": [
                "{horse}の指数を教えて",
                "{horse}はどう？",
                "{horse}について分析して",
                "{horse}の成績を見せて",
                "{horse}のスコアをお願いします",
                "{horse}を調べてください",
                "{horse}の評価は？"
            ],
            
            # 関西弁
            "kansai": [
                "{horse}の指数教えて〜",
                "{horse}はどうやん？",
                "{horse}について分析してや",
                "{horse}の成績見せてもらえる？",
                "{horse}のスコアお願いしまっせ",
                "{horse}調べてくれる？",
                "{horse}の評価どうなん？"
            ],
            
            # 東北弁
            "tohoku": [
                "{horse}の指数教えでけろ",
                "{horse}はどうだべ？",
                "{horse}について分析してけろ",
                "{horse}の成績見せでけろ",
                "{horse}のスコアお願いしますだ",
                "{horse}調べでもらえる？",
                "{horse}の評価どうだべ？"
            ],
            
            # 九州弁
            "kyushu": [
                "{horse}の指数教えてくれんね",
                "{horse}はどうと？",
                "{horse}について分析してくれん？",
                "{horse}の成績見せてもらえんね",
                "{horse}のスコアお願いしますたい",
                "{horse}調べてもらえる？",
                "{horse}の評価どうと？"
            ],
            
            # 北海道弁
            "hokkaido": [
                "{horse}の指数教えてくれる？",
                "{horse}はどうだべさ？",
                "{horse}について分析してくれるべ",
                "{horse}の成績見せてもらえるっしょ",
                "{horse}のスコアお願いします",
                "{horse}調べてくれるべさ",
                "{horse}の評価どうだべ？"
            ],
            
            # 沖縄弁
            "okinawa": [
                "{horse}の指数教えてくれんね〜",
                "{horse}はどうね〜？",
                "{horse}について分析してくれる？",
                "{horse}の成績見せてくれんね",
                "{horse}のスコアお願いしますさ〜",
                "{horse}調べてくれる？",
                "{horse}の評価どうね？"
            ],
            
            # 丁寧語（女性的）
            "polite_female": [
                "{horse}の指数を教えていただけませんか？",
                "{horse}はいかがでしょうか？",
                "{horse}について分析していただけますか？",
                "{horse}の成績を拝見させていただけますか？",
                "{horse}のスコアをお願いいたします",
                "{horse}をお調べいただけませんか？",
                "{horse}の評価はいかがですか？"
            ],
            
            # カジュアル（男性的）
            "casual_male": [
                "{horse}の指数頼む",
                "{horse}どうだ？",
                "{horse}分析してくれ",
                "{horse}の成績見せろ",
                "{horse}のスコア教えて",
                "{horse}調べてくれ",
                "{horse}の評価どう？"
            ]
        }
        
        return patterns
    
    def generate_test_queries(self, horses: List[str]) -> List[Dict[str, Any]]:
        """テスト用クエリを生成"""
        patterns = self.generate_natural_language_patterns()
        test_queries = []
        
        print("🗣️ 自然言語クエリ生成中...")
        
        for horse in horses:
            # 各馬に対して複数の方言・語調パターンでテスト
            for dialect, pattern_list in patterns.items():
                # 各方言から1-2パターンをランダム選択
                selected_patterns = random.sample(pattern_list, min(2, len(pattern_list)))
                
                for pattern in selected_patterns:
                    query = pattern.format(horse=horse)
                    test_queries.append({
                        "horse": horse,
                        "query": query,
                        "dialect": dialect,
                        "pattern": pattern
                    })
        
        # テスト数を調整（多すぎる場合は一部をサンプル）
        if len(test_queries) > 1000:  # 最大1000テストに制限
            test_queries = random.sample(test_queries, 1000)
            print(f"⚡ テスト数を1000に制限")
        
        print(f"✅ 生成完了: {len(test_queries)}個のテストクエリ")
        return test_queries
    
    async def test_single_query(self, session: aiohttp.ClientSession, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """単一クエリをテスト"""
        query = test_data["query"]
        horse = test_data["horse"]
        dialect = test_data["dialect"]
        
        start_time = time.time()
        
        try:
            # バックエンドAPIにリクエスト送信
            async with session.post(
                f"{self.api_base_url}/api/chat/message",
                json={"message": query, "history": []},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    # 結果の検証
                    has_d_logic = result.get("has_d_logic", False)
                    horse_name = result.get("horse_name", "")
                    message = result.get("message", "")
                    d_logic_result = result.get("d_logic_result", {})
                    
                    # 12項目チェック
                    detailed_scores = {}
                    if d_logic_result and "horses" in d_logic_result:
                        horses_data = d_logic_result["horses"]
                        if horses_data and len(horses_data) > 0:
                            detailed_scores = horses_data[0].get("detailed_scores", {})
                    
                    twelve_items_count = len(detailed_scores)
                    
                    test_result = {
                        "query": query,
                        "horse": horse,
                        "dialect": dialect,
                        "success": True,
                        "response_time": response_time,
                        "has_d_logic": has_d_logic,
                        "detected_horse": horse_name,
                        "twelve_items_count": twelve_items_count,
                        "message_length": len(message),
                        "status": "✅"
                    }
                    
                    return test_result
                    
                else:
                    return {
                        "query": query,
                        "horse": horse,
                        "dialect": dialect,
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response_time": time.time() - start_time,
                        "status": "❌"
                    }
                    
        except asyncio.TimeoutError:
            return {
                "query": query,
                "horse": horse,
                "dialect": dialect,
                "success": False,
                "error": "タイムアウト",
                "response_time": time.time() - start_time,
                "status": "⏰"
            }
        except Exception as e:
            return {
                "query": query,
                "horse": horse,
                "dialect": dialect,
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "status": "💥"
            }
    
    async def run_comprehensive_test(self):
        """包括的テストを実行"""
        print("🚀 D-Logic AI 包括的シミュレーションテスト開始")
        print("=" * 80)
        
        # 1. ナレッジベース読み込み
        horses = self.load_knowledge_base()
        if not horses:
            print("❌ テスト中止: ナレッジファイルが読み込めません")
            return
        
        # 2. 200頭ランダム抽出
        selected_horses = self.select_random_horses(horses, 200)
        self.horse_list = selected_horses
        
        # 3. テストクエリ生成
        test_queries = self.generate_test_queries(selected_horses)
        self.total_tests = len(test_queries)
        
        print(f"🎯 テスト対象: {len(selected_horses)}頭")
        print(f"🗣️ テストクエリ: {self.total_tests}個")
        print("=" * 80)
        
        # 4. 並行テスト実行
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            print("⚡ 並行テスト実行中...")
            
            # バッチサイズを設定（一度に処理するテスト数）
            batch_size = 20
            completed_tests = 0
            
            for i in range(0, len(test_queries), batch_size):
                batch = test_queries[i:i + batch_size]
                
                # バッチを並行実行
                tasks = [self.test_single_query(session, test_data) for test_data in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 結果を処理
                for result in batch_results:
                    if isinstance(result, dict):
                        self.test_results.append(result)
                        if result["success"]:
                            self.success_count += 1
                        else:
                            self.failed_tests.append(result)
                    
                    completed_tests += 1
                
                # 進捗表示
                progress = (completed_tests / self.total_tests) * 100
                print(f"📊 進捗: {completed_tests}/{self.total_tests} ({progress:.1f}%)")
                
                # 少し待機（APIへの負荷軽減）
                await asyncio.sleep(0.1)
        
        # 5. 結果分析
        await self.analyze_results()
    
    async def analyze_results(self):
        """テスト結果を分析"""
        print("\n" + "=" * 80)
        print("📊 テスト結果分析")
        print("=" * 80)
        
        success_rate = (self.success_count / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"🎯 総テスト数: {self.total_tests}")
        print(f"✅ 成功: {self.success_count}")
        print(f"❌ 失敗: {len(self.failed_tests)}")
        print(f"🏆 成功率: {success_rate:.2f}%")
        print()
        
        # 応答速度分析
        successful_tests = [t for t in self.test_results if t["success"]]
        if successful_tests:
            response_times = [t["response_time"] for t in successful_tests]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print("⚡ 応答速度分析:")
            print(f"   平均: {avg_response_time:.2f}秒")
            print(f"   最高: {max_response_time:.2f}秒") 
            print(f"   最低: {min_response_time:.2f}秒")
            
            # 速度別分類
            fast_responses = len([t for t in response_times if t <= 3])
            medium_responses = len([t for t in response_times if 3 < t <= 10])
            slow_responses = len([t for t in response_times if t > 10])
            
            print(f"   高速（3秒以下）: {fast_responses}個 ({fast_responses/len(successful_tests)*100:.1f}%)")
            print(f"   中速（3-10秒）: {medium_responses}個 ({medium_responses/len(successful_tests)*100:.1f}%)")
            print(f"   低速（10秒超）: {slow_responses}個 ({slow_responses/len(successful_tests)*100:.1f}%)")
        
        print()
        
        # 12項目分析
        twelve_items_tests = [t for t in successful_tests if t.get("twelve_items_count", 0) >= 12]
        twelve_items_rate = (len(twelve_items_tests) / len(successful_tests) * 100) if successful_tests else 0
        print(f"🐎 12項目完全計算率: {twelve_items_rate:.1f}%")
        
        # 方言別分析
        dialect_stats = {}
        for test in successful_tests:
            dialect = test.get("dialect", "unknown")
            if dialect not in dialect_stats:
                dialect_stats[dialect] = {"count": 0, "total_time": 0}
            dialect_stats[dialect]["count"] += 1
            dialect_stats[dialect]["total_time"] += test["response_time"]
        
        print("\n🗣️ 方言別パフォーマンス:")
        for dialect, stats in dialect_stats.items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            print(f"   {dialect}: {stats['count']}テスト, 平均{avg_time:.2f}秒")
        
        # 失敗ケース分析
        if self.failed_tests:
            print(f"\n❌ 失敗ケース分析 (上位10件):")
            for i, failed in enumerate(self.failed_tests[:10], 1):
                print(f"   {i}. {failed['query']} → {failed['error']}")
        
        print("\n" + "=" * 80)
        if success_rate >= 95:
            print("🎉 優秀！システムは高い信頼性で動作しています")
        elif success_rate >= 90:
            print("👍 良好！実用的なレベルで動作しています")
        elif success_rate >= 80:
            print("⚠️ 普通：改善の余地があります")
        else:
            print("🚨 要改善：重大な問題があります")
        
        print("=" * 80)

# メイン実行
if __name__ == "__main__":
    print("🎯 D-Logic AI 包括的シミュレーションテスト")
    print("🗾 日本全国の自然言語パターンによる徹底検証")
    print("🐎 200頭ランダム抽出 × 多様な方言・語調")
    print("=" * 80)
    
    test = ComprehensiveSimulationTest()
    asyncio.run(test.run_comprehensive_test())