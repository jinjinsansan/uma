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
        github_url = "https://github.com/jinjinsansan/dlogic-knowledge-data/releases/download/V1.0/dlogic_raw_knowledge.json"
        
        try:
            print("📥 GitHub Releasesからナレッジファイルをダウンロード中...")
            response = requests.get(github_url, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                horse_count = len(data.get('horses', {}))
                print(f"✅ ダウンロード完了: {horse_count}頭のデータを取得")
                
                # ローカルに保存（キャッシュとして）
                try:
                    os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
                    with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print("💾 ローカルキャッシュに保存完了")
                except Exception as e:
                    print(f"⚠️ ローカル保存失敗（メモリ上で動作継続）: {e}")
                
                return data
            else:
                print(f"❌ ダウンロード失敗: HTTPステータス {response.status_code}")
                
        except Exception as e:
            print(f"❌ ダウンロードエラー: {e}")
        
        # フォールバック：空のナレッジ構造を返す
        print("⚠️ ナレッジファイルが取得できません。MySQLから動的に取得します。")
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
        races = raw_data.get("races", raw_data.get("race_history", []))
        if not races:
            return 50.0
        
        # 距離別成績を集計
        distance_perf = {}
        for race in races:
            distance = race.get("KYORI") or race.get("distance")
            finish = race.get("KAKUTEI_CHAKUJUN") or race.get("finish")
            if distance and finish:
                if distance not in distance_perf:
                    distance_perf[distance] = []
                try:
                    distance_perf[distance].append(int(finish))
                except:
                    pass
        
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
        # aggregated_statsから取得を試みる
        stats = raw_data.get("aggregated_stats", {})
        wins = stats.get("wins", 0)
        total = stats.get("total_races", 0)
        
        # aggregated_statsがない場合はracesから集計
        if total == 0:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                total = len(races)
                wins = sum(1 for race in races if race.get("KAKUTEI_CHAKUJUN", race.get("finish", 99)) == 1)
        
        win_rate = wins / total if total > 0 else 0
        return min(100, win_rate * 200)
    
    def _calc_jockey_compatibility(self, raw_data: Dict) -> float:
        """騎手相性計算"""
        # まずaggregated_statsから取得を試みる
        jockey_perf = raw_data.get("aggregated_stats", {}).get("jockey_performance", {})
        
        # aggregated_statsがない場合はracesから集計
        if not jockey_perf:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                jockey_perf = {}
                for race in races:
                    jockey = race.get("KISYURYAKUSYO", race.get("jockey", ""))
                    finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
                    if jockey and finish:
                        if jockey not in jockey_perf:
                            jockey_perf[jockey] = []
                        try:
                            jockey_perf[jockey].append(int(finish))
                        except:
                            pass
        
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
        # まずaggregated_statsから取得を試みる
        trainer_perf = raw_data.get("aggregated_stats", {}).get("trainer_performance", {})
        
        # aggregated_statsがない場合はracesから集計
        if not trainer_perf:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                trainer_perf = {}
                for race in races:
                    trainer = race.get("CHOUKYOUSIRYAKUSYO", race.get("trainer", ""))
                    finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
                    if trainer and finish:
                        if trainer not in trainer_perf:
                            trainer_perf[trainer] = []
                        try:
                            trainer_perf[trainer].append(int(finish))
                        except:
                            pass
        
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
        races = raw_data.get("races", raw_data.get("race_history", []))
        track_perf = {}
        
        for race in races:
            # トラックタイプの判定（芝/ダート）
            track_code = race.get("TRACKCD", race.get("track", ""))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
            
            if track_code and finish:
                # TRACKCDを芝/ダートに変換
                if track_code in ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]:
                    track = "芝"
                elif track_code in ["20", "21", "22", "23", "24", "25", "26", "27", "28", "29"]:
                    track = "ダート"
                else:
                    track = track_code
                
                if track not in track_perf:
                    track_perf[track] = []
                try:
                    track_perf[track].append(int(finish))
                except:
                    pass
        
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
        races = raw_data.get("races", raw_data.get("race_history", []))
        if not races:
            return 50.0
        
        performance_scores = []
        for race in races:
            # 人気順位を取得
            popularity = race.get("NINKIJUN", race.get("popularity", 0))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if popularity and finish:
                try:
                    pop_int = int(popularity)
                    fin_int = int(finish)
                    if pop_int > 0 and fin_int > 0:
                        # 人気と着順の差を評価
                        if fin_int <= pop_int:
                            # 人気より上位に来た場合は高評価
                            score = 100 - (fin_int - 1) * 5
                        else:
                            # 人気より下位の場合は低評価
                            score = max(0, 80 - (fin_int - pop_int) * 10)
                        performance_scores.append(score)
                except:
                    pass
        
        if performance_scores:
            return sum(performance_scores) / len(performance_scores)
        
        return 50.0
    
    def _calc_weight_impact(self, raw_data: Dict) -> float:
        """重量影響度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        weight_scores = []
        
        for race in races:
            weight = race.get("FUTAN", race.get("weight", 0))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if weight and finish:
                try:
                    weight_int = int(weight)
                    finish_int = int(finish)
                    
                    # 負担重量の影響を評価（標準的な負担重量を55kgと仮定）
                    weight_score = max(0, 100 - abs(weight_int - 550) / 10 * 5)
                    finish_score = max(0, 100 - (finish_int - 1) * 8)
                    
                    combined = (weight_score + finish_score) / 2
                    weight_scores.append(combined)
                except:
                    pass
        
        return sum(weight_scores) / len(weight_scores) if weight_scores else 50.0
    
    def _calc_horse_weight_impact(self, raw_data: Dict) -> float:
        """馬体重影響度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        weight_scores = []
        
        for race in races:
            horse_weight = race.get("BATAI", race.get("horse_weight", 0))
            weight_change = race.get("ZOUGEN", race.get("weight_change", 0))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if horse_weight and finish:
                try:
                    weight_int = int(horse_weight)
                    finish_int = int(finish)
                    change_int = int(weight_change) if weight_change else 0
                    
                    # 最適体重を480kgと仮定
                    weight_diff = abs(weight_int - 480)
                    weight_score = max(0, 100 - weight_diff / 2)
                    
                    # 体重変化の影響も加味
                    if abs(change_int) > 10:
                        weight_score -= 10
                    
                    finish_score = max(0, 100 - (finish_int - 1) * 8)
                    combined = (weight_score + finish_score) / 2
                    weight_scores.append(combined)
                except:
                    pass
        
        return sum(weight_scores) / len(weight_scores) if weight_scores else 50.0
    
    def _calc_corner_specialist(self, raw_data: Dict) -> float:
        """コーナー専門度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        improvements = []
        
        for race in races:
            # コーナー通過順位
            corner1 = race.get("CORNER1JUN", race.get("corner1", 0))
            corner2 = race.get("CORNER2JUN", race.get("corner2", 0))
            corner3 = race.get("CORNER3JUN", race.get("corner3", 0))
            corner4 = race.get("CORNER4JUN", race.get("corner4", 0))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if finish:
                try:
                    finish_int = int(finish)
                    # 最も早いコーナー通過順位を取得
                    corners = []
                    for c in [corner1, corner2, corner3, corner4]:
                        if c and int(c) > 0:
                            corners.append(int(c))
                    
                    if corners:
                        first_corner = corners[0]
                        # コーナー順位から着順への改善度
                        improvement = first_corner - finish_int
                        improvements.append(improvement)
                except:
                    pass
        
        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            return min(100, max(0, 50 + avg_improvement * 5))
        
        return 50.0
    
    def _calc_margin_analysis(self, raw_data: Dict) -> float:
        """着差分析計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        finish_scores = []
        
        for race in races:
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            margin = race.get("CHAKUSA", race.get("margin", ""))
            
            if finish:
                try:
                    finish_int = int(finish)
                    base_score = max(0, 100 - (finish_int - 1) * 6)
                    
                    # 着差も考慮（勝った場合は着差が大きいほど高評価）
                    if finish_int == 1 and margin:
                        try:
                            # 着差を数値に変換（「1 1/2」→1.5など）
                            margin_val = self._parse_margin(margin)
                            if margin_val > 1:
                                base_score = min(100, base_score + margin_val * 2)
                        except:
                            pass
                    
                    finish_scores.append(base_score)
                except:
                    pass
        
        return sum(finish_scores) / len(finish_scores) if finish_scores else 50.0
    
    def _parse_margin(self, margin: str) -> float:
        """着差文字列を数値に変換"""
        # 「1 1/2」「2」「ハナ」「クビ」などを数値化
        if "ハナ" in margin:
            return 0.1
        elif "クビ" in margin:
            return 0.2
        elif "アタマ" in margin:
            return 0.3
        else:
            # 数値部分を抽出
            import re
            nums = re.findall(r'\d+', margin)
            if nums:
                return float(nums[0])
        return 0.0
    
    def _calc_time_index(self, raw_data: Dict) -> float:
        """タイム指数計算（簡略版）"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        time_scores = []
        
        for race in races:
            # タイムデータ（秒単位）
            time = race.get("TIME", race.get("time", 0))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            distance = race.get("KYORI", race.get("distance", 0))
            
            if time and finish and distance:
                try:
                    time_int = int(time)
                    finish_int = int(finish)
                    distance_int = int(distance)
                    
                    # 距離別の基準タイムを設定（仮の値）
                    if distance_int <= 1200:
                        base_time = 70  # 1200m基準
                    elif distance_int <= 1600:
                        base_time = 95  # 1600m基準
                    elif distance_int <= 2000:
                        base_time = 120  # 2000m基準
                    else:
                        base_time = 150  # 2400m以上基準
                    
                    # タイム指数計算
                    time_score = max(0, 100 - (time_int - base_time) * 2)
                    finish_score = max(0, 100 - (finish_int - 1) * 8)
                    combined = (time_score + finish_score) / 2
                    time_scores.append(combined)
                except:
                    pass
        
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