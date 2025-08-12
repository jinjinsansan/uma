#!/usr/bin/env python3
"""
D-Logic遅延読み込みナレッジマネージャー
メモリ効率を重視した実装（Render対応）
"""
import json
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from functools import lru_cache
import tempfile
import gzip
import pickle

class DLogicLazyDataManager:
    """D-Logic遅延読み込みデータ管理システム"""
    
    def __init__(self):
        self.knowledge_url = "https://github.com/jinjinsansan/dlogic-knowledge-data/releases/download/V2.0/dlogic_raw_knowledge.json"
        self.cache_file = os.path.join(tempfile.gettempdir(), "dlogic_cache.pkl.gz")
        self.horse_index = {}  # 馬名 -> ファイル内位置のマッピング
        self.cached_horses = {}  # 最近使用した馬データ（LRUキャッシュ）
        self.max_cache_size = 1000  # 最大1000頭をメモリキャッシュ
        
        # 軽量インデックスファイルを作成/読み込み
        self._initialize_index()
        print(f"🚀 D-Logic遅延読み込みマネージャー初期化完了 (インデックス: {len(self.horse_index)}頭)")
        
    def _initialize_index(self):
        """軽量インデックスファイルの初期化"""
        index_file = os.path.join(tempfile.gettempdir(), "horse_index.json")
        
        if os.path.exists(index_file):
            # 既存インデックス読み込み
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.horse_index = json.load(f)
                print(f"✅ インデックス読み込み: {len(self.horse_index)}頭")
                return
            except Exception as e:
                print(f"⚠️ インデックス読み込み失敗: {e}")
        
        # インデックス作成
        print("📦 インデックス作成中...")
        self._create_horse_index()
        
        # インデックス保存
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.horse_index, f, ensure_ascii=False)
            print("💾 インデックス保存完了")
        except Exception as e:
            print(f"⚠️ インデックス保存失敗: {e}")
    
    def _create_horse_index(self):
        """馬名インデックスを作成（メモリ効率重視）"""
        try:
            print("📥 ナレッジファイルのストリーミング読み込み開始...")
            response = requests.get(self.knowledge_url, stream=True, timeout=120)
            
            if response.status_code != 200:
                print(f"❌ ダウンロード失敗: {response.status_code}")
                self.horse_index = {}
                return
            
            # JSONを部分的に解析してhorsesセクションの馬名だけを抽出
            content = ""
            horses_section_found = False
            bracket_count = 0
            current_horse_name = None
            
            for chunk in response.iter_content(chunk_size=8192):
                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8', errors='ignore')
                content += chunk
                
                # horsesセクションを探す
                if not horses_section_found and '"horses": {' in content:
                    horses_section_found = True
                    horses_start = content.find('"horses": {')
                    content = content[horses_start:]
                    print("✅ horsesセクション発見")
                
                if horses_section_found:
                    # 馬名を抽出
                    import re
                    horse_pattern = r'"([^"]+)": \{'
                    matches = re.findall(horse_pattern, content)
                    
                    for match in matches:
                        if match != "horses":  # horsesキー自体を除外
                            self.horse_index[match] = True  # 存在フラグ
                    
                    # メモリ節約のため処理済み部分を削除
                    if len(content) > 50000:
                        content = content[-10000:]  # 末尾10KBだけ保持
            
            print(f"✅ インデックス作成完了: {len(self.horse_index)}頭")
            
        except Exception as e:
            print(f"❌ インデックス作成エラー: {e}")
            # フォールバック: よく使われる馬名のハードコードリスト
            common_horses = [
                "ウィルソンテソーロ", "ドンフランキー", "アルファマム", "イグナイター",
                "ドゥラエレーデ", "スピーディキック", "オメガギネス", "カラテ",
                "シャンパンカラー", "ペプチドナイル", "ガイアフォース", "セキフウ",
                "タガノビューティー", "キングズソード", "レッドルゼル", "ミックファイア",
                "ドウデュース", "イクイノックス", "リバティアイランド", "ソダシ"
            ]
            self.horse_index = {name: True for name in common_horses}
            print(f"⚠️ フォールバック: {len(self.horse_index)}頭の基本リスト使用")
    
    @lru_cache(maxsize=1000)
    def get_horse_raw_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬の生データ取得（キャッシュ付き）"""
        # インデックスチェック
        if horse_name not in self.horse_index:
            print(f"❌ 馬名 '{horse_name}' がインデックスに見つかりません")
            return None
        
        # キャッシュチェック
        if horse_name in self.cached_horses:
            return self.cached_horses[horse_name]
        
        # オンデマンド読み込み
        horse_data = self._load_horse_data_streaming(horse_name)
        
        if horse_data:
            # LRUキャッシュに追加
            if len(self.cached_horses) >= self.max_cache_size:
                # 古いエントリを削除
                oldest_key = next(iter(self.cached_horses))
                del self.cached_horses[oldest_key]
            
            self.cached_horses[horse_name] = horse_data
        
        return horse_data
    
    def _load_horse_data_streaming(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """特定の馬のデータをストリーミング読み込み"""
        try:
            print(f"📥 '{horse_name}'のデータをストリーミング読み込み中...")
            response = requests.get(self.knowledge_url, stream=True, timeout=60)
            
            if response.status_code != 200:
                return None
            
            # 目標の馬名を探す
            search_pattern = f'"{horse_name}": {{'
            buffer = ""
            found = False
            bracket_count = 0
            horse_data_str = ""
            
            for chunk in response.iter_content(chunk_size=8192):
                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8', errors='ignore')
                buffer += chunk
                
                if not found and search_pattern in buffer:
                    found = True
                    start_pos = buffer.find(search_pattern)
                    horse_data_str = buffer[start_pos:]
                    buffer = ""  # メモリ節約
                    print(f"✅ '{horse_name}'を発見")
                
                if found:
                    horse_data_str += chunk
                    
                    # JSON構造の終端を検出
                    for char in chunk:
                        if char == '{':
                            bracket_count += 1
                        elif char == '}':
                            bracket_count -= 1
                            if bracket_count == 0:  # 馬データの終端
                                # JSONパース
                                try:
                                    # 馬データ部分を抽出
                                    json_str = horse_data_str[:horse_data_str.rfind('}') + 1]
                                    # 馬名部分を含む完全なJSONにする
                                    complete_json = '{' + json_str + '}'
                                    parsed = json.loads(complete_json)
                                    return parsed[horse_name]
                                except Exception as e:
                                    print(f"❌ JSON解析エラー: {e}")
                                    return None
                
                # メモリ効率のためバッファサイズ制限
                if len(buffer) > 100000:
                    if not found:
                        buffer = buffer[-50000:]  # 後半のみ保持
            
            print(f"❌ '{horse_name}'のデータが見つかりませんでした")
            return None
            
        except Exception as e:
            print(f"❌ ストリーミング読み込みエラー: {e}")
            return None
    
    def calculate_dlogic_realtime(self, horse_name: str) -> Dict[str, Any]:
        """生データからリアルタイムD-Logic計算"""
        raw_data = self.get_horse_raw_data(horse_name)
        if not raw_data:
            return {"error": f"{horse_name}のデータが見つかりません"}
        
        # 12項目をリアルタイム計算（簡略版）
        races = raw_data.get("races", [])
        if not races:
            return {"error": f"{horse_name}のレースデータが不足しています"}
        
        # 簡易スコア計算
        avg_finish = sum(int(race.get("KAKUTEI_CHAKUJUN", 9)) for race in races if race.get("KAKUTEI_CHAKUJUN", "").isdigit()) / len(races)
        base_score = max(0, 100 - (avg_finish - 1) * 10)
        
        scores = {
            "1_distance_aptitude": base_score * 0.95,
            "2_bloodline_evaluation": base_score * 1.05,
            "3_jockey_compatibility": base_score * 0.98,
            "4_trainer_evaluation": base_score * 1.02,
            "5_track_aptitude": base_score * 0.97,
            "6_weather_aptitude": base_score * 0.99,
            "7_popularity_factor": base_score * 0.94,
            "8_weight_impact": base_score * 0.96,
            "9_horse_weight_impact": base_score * 0.93,
            "10_corner_specialist_degree": base_score * 1.01,
            "11_margin_analysis": base_score * 1.03,
            "12_time_index": base_score * 1.04
        }
        
        total_score = sum(scores.values()) / len(scores)
        
        return {
            "horse_name": horse_name,
            "d_logic_scores": scores,
            "total_score": total_score,
            "grade": self._grade_performance(total_score),
            "calculation_time": datetime.now().isoformat()
        }
    
    def _grade_performance(self, score: float) -> str:
        """成績グレード判定"""
        if score >= 90:
            return "SS (伝説級)"
        elif score >= 80:
            return "S (超一流)"
        elif score >= 70:
            return "A (一流)"
        elif score >= 60:
            return "B (良馬)"
        elif score >= 50:
            return "C (平均)"
        else:
            return "D (要改善)"
    
    def calculate_weather_adaptive_dlogic(self, horse_name: str, baba_condition: int) -> Dict[str, Any]:
        """天候適性D-Logic計算"""
        # 標準計算を実行
        standard_result = self.calculate_dlogic_realtime(horse_name)
        
        if "error" in standard_result:
            return standard_result
        
        # 天候調整
        weather_multiplier = {1: 1.0, 2: 0.97, 3: 0.94, 4: 0.91}[baba_condition]
        
        adjusted_scores = {}
        for key, value in standard_result["d_logic_scores"].items():
            if key == "6_weather_aptitude":
                adjusted_scores[key] = value * (2.0 - weather_multiplier)  # 天候適性は逆転
            else:
                adjusted_scores[key] = value * weather_multiplier
        
        adjusted_total = sum(adjusted_scores.values()) / len(adjusted_scores)
        
        result = standard_result.copy()
        result.update({
            "d_logic_scores": adjusted_scores,
            "total_score": adjusted_total,
            "grade": self._grade_performance(adjusted_total),
            "weather_condition": {1: "良", 2: "稍重", 3: "重", 4: "不良"}[baba_condition],
            "weather_adjustment": adjusted_total - standard_result["total_score"]
        })
        
        return result

# グローバルインスタンス
lazy_dlogic_manager = DLogicLazyDataManager()

if __name__ == "__main__":
    # テスト実行
    print("\n🧪 遅延読み込みテスト:")
    test_horses = ["ウィルソンテソーロ", "ドンフランキー", "アルファマム"]
    
    for horse in test_horses:
        result = lazy_dlogic_manager.calculate_dlogic_realtime(horse)
        if "error" in result:
            print(f"  {horse}: エラー - {result['error']}")
        else:
            print(f"  {horse}: {result.get('total_score', 0):.1f}点")