#!/usr/bin/env python3
"""
D-Logic生データナレッジマネージャー
12項目分析に必要な生データのみを保存（計算はリアルタイム）
"""
import json
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import mysql.connector

class DLogicRawDataManager:
    """D-Logic生データ管理システム"""
    
    def __init__(self):
        self.knowledge_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'dlogic_raw_knowledge.json'
        )
        self.knowledge_data = self._load_knowledge()
        print("🚀 D-Logic生データマネージャー初期化完了")
        
    def _load_knowledge(self) -> Dict[str, Any]:
        """ナレッジファイル読み込み"""
        # まずローカルファイルを試す
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Git LFS ポインタファイルかチェック
                    if content.startswith('version https://git-lfs.github.com'):
                        print("⚠️ Git LFS ポインタファイル検出。GitHub Releasesからダウンロード...")
                        return self._download_from_github()
                    
                    data = json.loads(content)
                    print(f"✅ ナレッジファイル読み込み: {len(data.get('horses', {}))}頭")
                    return data
            except json.JSONDecodeError as e:
                print(f"⚠️ JSONデコードエラー: {e}")
                print("GitHub Releasesからダウンロードを試行...")
                return self._download_from_github()
            except Exception as e:
                print(f"⚠️ ナレッジファイル読み込みエラー: {e}")
        
        # ファイルが存在しない場合はGitHubからダウンロード
        return self._download_from_github()
    
    def _download_from_github(self) -> Dict[str, Any]:
        """GitHub Releasesからナレッジファイルをダウンロード"""
        # GitHub Releases URL（環境変数から取得、またはデフォルト）
        github_url = os.environ.get('KNOWLEDGE_FILE_URL', 
            'https://raw.githubusercontent.com/jinjinsansan/uma/main/backend/data/dlogic_raw_knowledge.json')
        
        try:
            print(f"📥 GitHub Releasesからダウンロード中: {github_url}")
            response = requests.get(github_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # ローカルに保存
                os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
                with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ ダウンロード完了: {len(data.get('horses', {}))}頭")
                return data
            else:
                print(f"❌ ダウンロード失敗: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ ダウンロードエラー: {e}")
        
        # フォールバック：新規作成
        return {
            "meta": {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "target_years": "2020-2025",
                "data_type": "raw_data_only",
                "calculation_method": "realtime"
            },
            "horses": {}
        }
    
    def _save_knowledge(self):
        """ナレッジファイル保存"""
        self.knowledge_data["meta"]["last_updated"] = datetime.now().isoformat()
        
        os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_data, f, ensure_ascii=False, indent=2)
    
    def add_horse_raw_data(self, horse_name: str, raw_data: Dict[str, Any]):
        """馬の生データを追加"""
        self.knowledge_data["horses"][horse_name] = {
            "basic_info": raw_data.get("basic_info", {}),
            "race_history": raw_data.get("race_history", []),
            "aggregated_stats": raw_data.get("aggregated_stats", {}),
            "last_updated": datetime.now().isoformat()
        }
        
    def get_horse_raw_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬の生データ取得"""
        return self.knowledge_data["horses"].get(horse_name)
    
    def calculate_dlogic_realtime(self, horse_name: str) -> Dict[str, Any]:
        """生データからリアルタイムD-Logic計算"""
        raw_data = self.get_horse_raw_data(horse_name)
        if not raw_data:
            return {"error": f"{horse_name}のデータが見つかりません"}
        
        # 12項目をリアルタイム計算
        scores = {
            "1_distance_aptitude": self._calc_distance_aptitude(raw_data),
            "2_bloodline_evaluation": self._calc_bloodline_evaluation(raw_data),
            "3_jockey_compatibility": self._calc_jockey_compatibility(raw_data),
            "4_trainer_evaluation": self._calc_trainer_evaluation(raw_data),
            "5_track_aptitude": self._calc_track_aptitude(raw_data),
            "6_weather_aptitude": self._calc_weather_aptitude(raw_data),
            "7_popularity_factor": self._calc_popularity_factor(raw_data),
            "8_weight_impact": self._calc_weight_impact(raw_data),
            "9_horse_weight_impact": self._calc_horse_weight_impact(raw_data),
            "10_corner_specialist_degree": self._calc_corner_specialist(raw_data),
            "11_margin_analysis": self._calc_margin_analysis(raw_data),
            "12_time_index": self._calc_time_index(raw_data)
        }
        
        # 総合スコア計算（ダンスインザダーク基準）
        total_score = self._calculate_total_score(scores)
        
        return {
            "horse_name": horse_name,
            "d_logic_scores": scores,
            "total_score": total_score,
            "grade": self._grade_performance(total_score),
            "calculation_time": datetime.now().isoformat()
        }
    
    def _calc_distance_aptitude(self, raw_data: Dict) -> float:
        """距離適性計算"""
        distance_perf = raw_data.get("aggregated_stats", {}).get("distance_performance", {})
        if not distance_perf:
            return 50.0
        
        scores = []
        for distance, finishes in distance_perf.items():
            if finishes:
                avg_finish = sum(finishes) / len(finishes)
                score = max(0, 100 - (avg_finish - 1) * 10)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _calc_bloodline_evaluation(self, raw_data: Dict) -> float:
        """血統評価計算"""
        stats = raw_data.get("aggregated_stats", {})
        wins = stats.get("wins", 0)
        total = stats.get("total_races", 1)
        
        win_rate = wins / total if total > 0 else 0
        return min(100, win_rate * 200)
    
    def _calc_jockey_compatibility(self, raw_data: Dict) -> float:
        """騎手相性計算"""
        jockey_perf = raw_data.get("aggregated_stats", {}).get("jockey_performance", {})
        if not jockey_perf:
            return 50.0
        
        scores = []
        for jockey, finishes in jockey_perf.items():
            if finishes:
                avg_finish = sum(finishes) / len(finishes)
                score = max(0, 100 - (avg_finish - 1) * 8)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _calc_trainer_evaluation(self, raw_data: Dict) -> float:
        """調教師評価計算"""
        trainer_perf = raw_data.get("aggregated_stats", {}).get("trainer_performance", {})
        if not trainer_perf:
            return 50.0
        
        scores = []
        for trainer, finishes in trainer_perf.items():
            if finishes:
                avg_finish = sum(finishes) / len(finishes)
                score = max(0, 100 - (avg_finish - 1) * 8)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _calc_track_aptitude(self, raw_data: Dict) -> float:
        """トラック適性計算"""
        races = raw_data.get("race_history", [])
        track_perf = {}
        
        for race in races:
            track = race.get("track", "")
            finish = race.get("finish")
            if track and finish:
                if track not in track_perf:
                    track_perf[track] = []
                track_perf[track].append(finish)
        
        if not track_perf:
            return 50.0
        
        scores = []
        for track, finishes in track_perf.items():
            avg_finish = sum(finishes) / len(finishes)
            score = max(0, 100 - (avg_finish - 1) * 8)
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _calc_weather_aptitude(self, raw_data: Dict) -> float:
        """天候適性計算（簡略版）"""
        # 実装は省略（デフォルト値返却）
        return 50.0
    
    def _calc_popularity_factor(self, raw_data: Dict) -> float:
        """人気度要因計算"""
        races = raw_data.get("race_history", [])
        if not races:
            return 50.0
        
        performance_scores = []
        for race in races:
            odds = race.get("odds", 10.0)
            finish = race.get("finish", 10)
            expected_finish = min(18, odds / 2)
            if finish > 0:
                ratio = expected_finish / finish
                performance_scores.append(ratio)
        
        if performance_scores:
            avg_ratio = sum(performance_scores) / len(performance_scores)
            return min(100, avg_ratio * 50)
        
        return 50.0
    
    def _calc_weight_impact(self, raw_data: Dict) -> float:
        """重量影響度計算"""
        races = raw_data.get("race_history", [])
        weight_scores = []
        
        for race in races:
            weight = race.get("weight", 550)
            finish = race.get("finish", 10)
            
            weight_score = max(0, (600 - weight) / 100 * 20 + 50)
            finish_score = max(0, 100 - (finish - 1) * 8)
            
            combined = (weight_score + finish_score) / 2
            weight_scores.append(combined)
        
        return sum(weight_scores) / len(weight_scores) if weight_scores else 50.0
    
    def _calc_horse_weight_impact(self, raw_data: Dict) -> float:
        """馬体重影響度計算"""
        races = raw_data.get("race_history", [])
        weight_scores = []
        
        for race in races:
            horse_weight = race.get("horse_weight", 480)
            finish = race.get("finish", 10)
            
            optimal_weight = 480
            weight_diff = abs(horse_weight - optimal_weight)
            weight_score = max(0, 100 - weight_diff / 2)
            
            finish_score = max(0, 100 - (finish - 1) * 8)
            combined = (weight_score + finish_score) / 2
            weight_scores.append(combined)
        
        return sum(weight_scores) / len(weight_scores) if weight_scores else 50.0
    
    def _calc_corner_specialist(self, raw_data: Dict) -> float:
        """コーナー専門度計算"""
        races = raw_data.get("race_history", [])
        improvements = []
        
        for race in races:
            corners = race.get("corner_positions", [])
            finish = race.get("finish")
            
            if len(corners) >= 2 and finish:
                first_corner = corners[0]
                improvement = first_corner - finish
                improvements.append(improvement)
        
        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            return min(100, max(0, 50 + avg_improvement * 5))
        
        return 50.0
    
    def _calc_margin_analysis(self, raw_data: Dict) -> float:
        """着差分析計算"""
        races = raw_data.get("race_history", [])
        finish_scores = []
        
        for race in races:
            finish = race.get("finish", 10)
            score = max(0, 100 - (finish - 1) * 6)
            finish_scores.append(score)
        
        return sum(finish_scores) / len(finish_scores) if finish_scores else 50.0
    
    def _calc_time_index(self, raw_data: Dict) -> float:
        """タイム指数計算（簡略版）"""
        races = raw_data.get("race_history", [])
        time_scores = []
        
        for race in races:
            time = race.get("time", 150.0)
            finish = race.get("finish", 10)
            
            time_score = max(0, 100 - time / 2)
            finish_score = max(0, 100 - (finish - 1) * 8)
            combined = (time_score + finish_score) / 2
            time_scores.append(combined)
        
        return sum(time_scores) / len(time_scores) if time_scores else 50.0
    
    def _calculate_total_score(self, scores: Dict[str, float]) -> float:
        """総合スコア計算（ダンスインザダーク基準）"""
        weights = [1.2, 1.1, 1.0, 1.0, 1.1, 0.9, 0.8, 0.9, 0.8, 1.0, 1.1, 1.2]
        
        # スコア項目を正しい順序で取得
        ordered_keys = [
            "1_distance_aptitude",
            "2_bloodline_evaluation", 
            "3_jockey_compatibility",
            "4_trainer_evaluation",
            "5_track_aptitude",
            "6_weather_aptitude",
            "7_popularity_factor",
            "8_weight_impact",
            "9_horse_weight_impact",
            "10_corner_specialist_degree",
            "11_margin_analysis",
            "12_time_index"
        ]
        
        weighted_sum = 0
        for i, key in enumerate(ordered_keys):
            if key in scores:
                weighted_sum += scores[key] * weights[i]
            else:
                weighted_sum += 50.0 * weights[i]  # デフォルト値
        
        return weighted_sum / sum(weights)
    
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

# グローバルインスタンス
dlogic_manager = DLogicRawDataManager()

if __name__ == "__main__":
    # テスト実行
    manager = DLogicRawDataManager()
    print(f"📊 ナレッジ統計: {len(manager.knowledge_data['horses'])}頭登録済み")