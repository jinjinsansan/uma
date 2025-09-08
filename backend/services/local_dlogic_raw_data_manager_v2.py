#!/usr/bin/env python3
"""
地方競馬版D-Logic生データナレッジマネージャー V2
完全に独立した実装（親クラスを継承しない）
"""
import json
import os
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LocalDLogicRawDataManagerV2:
    """地方競馬版D-Logic生データ管理システム（独立版）"""
    
    def __init__(self):
        """初期化：地方競馬版専用"""
        # キャッシュファイルパス
        if os.environ.get('RENDER'):
            self.knowledge_file = '/var/data/local_dlogic_raw_knowledge_v2.json'
        else:
            self.knowledge_file = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'local_dlogic_raw_knowledge_v2.json'
            )
        
        # CDN URL
        self.cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_unified_knowledge_20250907.json"
        
        print(f"🏇 地方競馬版マネージャーV2初期化")
        print(f"   キャッシュ: {self.knowledge_file}")
        
        # ナレッジデータを読み込み
        self.knowledge_data = self._load_knowledge()
        
        horse_count = len(self.knowledge_data.get('horses', {}))
        print(f"✅ 地方競馬版マネージャーV2初期化完了: {horse_count}頭")
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """ナレッジファイルの読み込み"""
        # キャッシュファイルが存在する場合
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # データ構造を確認
                    if isinstance(data, dict) and 'horses' in data:
                        horse_count = len(data['horses'])
                        print(f"📂 キャッシュから読み込み: {horse_count}頭")
                        return data
                    else:
                        print("⚠️ キャッシュのデータ構造が不正")
            except Exception as e:
                print(f"⚠️ キャッシュ読み込みエラー: {e}")
        
        # CDNからダウンロード
        return self._download_from_cdn()
    
    def _download_from_cdn(self) -> Dict[str, Any]:
        """CDNからダウンロード"""
        try:
            print(f"📥 CDNからダウンロード中: {self.cdn_url}")
            response = requests.get(self.cdn_url, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                # データ構造を確認（馬名が直接キーになっている）
                if isinstance(data, dict) and 'horses' not in data:
                    horse_count = len(data)
                    print(f"✅ ダウンロード完了: {horse_count}頭")
                    
                    # horsesキーでラップ
                    wrapped_data = {
                        "meta": {
                            "version": "2.0",
                            "type": "local_racing",
                            "created_at": datetime.now().isoformat()
                        },
                        "horses": data
                    }
                    
                    # キャッシュに保存
                    self._save_cache(wrapped_data)
                    return wrapped_data
                else:
                    # 既にラップされている
                    horse_count = len(data.get('horses', {}))
                    print(f"✅ ダウンロード完了: {horse_count}頭")
                    self._save_cache(data)
                    return data
            else:
                print(f"❌ ダウンロード失敗: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ ダウンロードエラー: {e}")
        
        # フォールバック
        return {"horses": {}}
    
    def _save_cache(self, data: Dict[str, Any]):
        """キャッシュに保存"""
        try:
            os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            print(f"💾 キャッシュ保存完了")
        except Exception as e:
            print(f"⚠️ キャッシュ保存失敗: {e}")
    
    def get_raw_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬の生データを取得"""
        races = self.knowledge_data.get('horses', {}).get(horse_name)
        if races is None:
            return None
        
        # 地方競馬版は配列形式なので、JRA版と同じ形式に変換
        if isinstance(races, list):
            return {
                "horse_name": horse_name,
                "races": races,
                "race_count": len(races)
            }
        # 既にJRA形式の場合はそのまま返す
        return races
    
    def get_horse_raw_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬の生データを取得（互換性のため別名も提供）"""
        return self.get_raw_horse_data(horse_name)
    
    def get_all_horse_names(self) -> list:
        """全馬名リストを取得"""
        return list(self.knowledge_data.get('horses', {}).keys())
    
    def get_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬データを取得（ViewLogicとの互換性のため）"""
        return self.get_horse_raw_data(horse_name)
    
    def is_loaded(self) -> bool:
        """データがロードされているか確認"""
        return bool(self.knowledge_data and self.knowledge_data.get('horses'))
    
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
                except (ValueError, TypeError):
                    continue
        
        if not distance_perf:
            return 50.0
        
        # 平均着順から適性スコアを計算
        best_score = 0
        for distance, finishes in distance_perf.items():
            avg_finish = sum(finishes) / len(finishes)
            score = max(0, 100 - (avg_finish - 1) * 10)
            best_score = max(best_score, score)
        
        return min(100, best_score)
    
    def _calc_bloodline_evaluation(self, raw_data: Dict) -> float:
        """血統評価計算"""
        stats = raw_data.get("aggregated_stats", {})
        wins = stats.get("wins", 0)
        total = stats.get("total_races", 0)
        
        if total == 0:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                total = len(races)
                wins = sum(1 for race in races if str(race.get("KAKUTEI_CHAKUJUN", race.get("finish", "99"))).strip() == "01" or race.get("KAKUTEI_CHAKUJUN", race.get("finish", 99)) == 1)
        
        win_rate = wins / total if total > 0 else 0
        return min(100, win_rate * 200)
    
    def _calc_jockey_compatibility(self, raw_data: Dict) -> float:
        """騎手相性計算"""
        jockey_perf = raw_data.get("aggregated_stats", {}).get("jockey_performance", {})
        
        if not jockey_perf:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                jockey_perf = {}
                for race in races:
                    jockey = race.get("KISHUMEI_RYAKUSHO", race.get("KISYURYAKUSYO", race.get("jockey", "")))
                    finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
                    if jockey and finish:
                        if jockey not in jockey_perf:
                            jockey_perf[jockey] = []
                        try:
                            jockey_perf[jockey].append(int(finish))
                        except (ValueError, TypeError):
                            continue
        
        if not jockey_perf:
            return 50.0
        
        best_avg = 999
        for jockey, finishes in jockey_perf.items():
            if len(finishes) >= 1:
                avg = sum(finishes) / len(finishes)
                best_avg = min(best_avg, avg)
        
        if best_avg == 999:
            return 50.0
        
        return max(0, min(100, 100 - (best_avg - 1) * 10))
    
    def _calc_trainer_evaluation(self, raw_data: Dict) -> float:
        """調教師評価計算"""
        trainer_perf = raw_data.get("aggregated_stats", {}).get("trainer_performance", {})
        
        if not trainer_perf:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                trainer_perf = {}
                for race in races:
                    trainer = race.get("CHOKYOSHIMEI_RYAKUSHO", race.get("CHOUKYOUSIRYAKUSYO", race.get("trainer", "")))
                    finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
                    if trainer and finish:
                        if trainer not in trainer_perf:
                            trainer_perf[trainer] = []
                        try:
                            trainer_perf[trainer].append(int(finish))
                        except (ValueError, TypeError):
                            continue
        
        if not trainer_perf:
            return 50.0
        
        best_avg = 999
        for trainer, finishes in trainer_perf.items():
            if len(finishes) >= 1:
                avg = sum(finishes) / len(finishes)
                best_avg = min(best_avg, avg)
        
        if best_avg == 999:
            return 50.0
        
        return max(0, min(100, 100 - (best_avg - 1) * 10))
    
    def _calc_track_aptitude(self, raw_data: Dict) -> float:
        """トラック適性計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        track_perf = {}
        
        for race in races:
            track_code = race.get("TRACK_CODE", race.get("TRACKCD", race.get("track", "")))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
            
            if track_code and finish:
                if track_code in ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]:
                    track = "芝"
                elif track_code in ["20", "21", "22", "23", "24", "25", "26", "27", "28", "29"]:
                    track = "ダート"
                else:
                    track = str(track_code)
                
                if track not in track_perf:
                    track_perf[track] = []
                try:
                    track_perf[track].append(int(finish))
                except (ValueError, TypeError):
                    continue
        
        if not track_perf:
            return 50.0
        
        best_score = 0
        for track, finishes in track_perf.items():
            avg_finish = sum(finishes) / len(finishes)
            score = max(0, 100 - (avg_finish - 1) * 10)
            best_score = max(best_score, score)
        
        return min(100, best_score)
    
    def _calc_weather_aptitude(self, raw_data: Dict) -> float:
        """天候適性計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        if not races:
            return 50.0
        
        weather_perf = {}
        
        for race in races:
            tenko = race.get("TENKO_CODE", race.get("weather", 0))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            track_code = race.get("TRACK_CODE", "")
            
            if str(track_code).startswith("1"):  # 芝
                baba = race.get("SHIBA_BABAJOTAI_CODE", 1)
            else:  # ダート
                baba = race.get("DIRT_BABAJOTAI_CODE", 1)
            
            if tenko and finish:
                weather_key = f"{tenko}_{baba}"
                if weather_key not in weather_perf:
                    weather_perf[weather_key] = []
                try:
                    weather_perf[weather_key].append(int(finish))
                except (ValueError, TypeError):
                    continue
        
        if not weather_perf:
            return 50.0
        
        total_races = sum(len(finishes) for finishes in weather_perf.values())
        weighted_score = 0
        
        for weather_key, finishes in weather_perf.items():
            avg_finish = sum(finishes) / len(finishes)
            score = max(0, 100 - (avg_finish - 1) * 10)
            weight = len(finishes) / total_races
            weighted_score += score * weight
        
        return min(100, weighted_score)
    
    def _calc_popularity_factor(self, raw_data: Dict) -> float:
        """人気度要因計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        if not races:
            return 50.0
        
        performance_scores = []
        for race in races:
            popularity = race.get("TANSHO_NINKIJUN", race.get("NINKIJUN", race.get("popularity", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if popularity and finish:
                try:
                    pop_int = int(popularity)
                    fin_int = int(finish)
                    
                    if pop_int <= fin_int:
                        score = 100 - (fin_int - pop_int) * 10
                    else:
                        score = 100 - (pop_int - fin_int) * 5
                    
                    performance_scores.append(max(0, min(100, score)))
                except (ValueError, TypeError):
                    continue
        
        if not performance_scores:
            return 50.0
        
        return sum(performance_scores) / len(performance_scores)
    
    def _calc_weight_impact(self, raw_data: Dict) -> float:
        """重量影響度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        weight_scores = []
        
        for race in races:
            weight = race.get("FUTAN_JURYO", race.get("FUTAN", race.get("weight", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if weight and finish:
                try:
                    weight_int = int(weight)
                    finish_int = int(finish)
                    
                    weight_score = max(0, 100 - abs(weight_int - 550) / 10 * 5)
                    
                    if finish_int <= 3:
                        weight_score *= 1.1
                    
                    weight_scores.append(min(100, weight_score))
                except (ValueError, TypeError):
                    continue
        
        return sum(weight_scores) / len(weight_scores) if weight_scores else 50.0
    
    def _calc_horse_weight_impact(self, raw_data: Dict) -> float:
        """馬体重影響度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        weight_scores = []
        
        for race in races:
            horse_weight = race.get("BATAIJU", race.get("BATAI", race.get("horse_weight", 0)))
            weight_change = race.get("ZOGEN_SA", race.get("ZOUGEN", race.get("weight_change", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if horse_weight and finish:
                try:
                    weight_int = int(horse_weight)
                    finish_int = int(finish)
                    change_int = int(weight_change) if weight_change else 0
                    
                    base_score = 75
                    if 460 <= weight_int <= 500:
                        base_score = 100
                    elif weight_int < 440 or weight_int > 520:
                        base_score = 50
                    
                    if abs(change_int) > 10:
                        base_score *= 0.9
                    
                    weight_scores.append(base_score)
                except (ValueError, TypeError):
                    continue
        
        return sum(weight_scores) / len(weight_scores) if weight_scores else 50.0
    
    def _calc_corner_specialist(self, raw_data: Dict) -> float:
        """コーナー専門度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        improvements = []
        
        for race in races:
            corner1 = race.get("CORNER1_JUNI", race.get("CORNER1JUN", race.get("corner1", 0)))
            corner2 = race.get("CORNER2_JUNI", race.get("CORNER2JUN", race.get("corner2", 0)))
            corner3 = race.get("CORNER3_JUNI", race.get("CORNER3JUN", race.get("corner3", 0)))
            corner4 = race.get("CORNER4_JUNI", race.get("CORNER4JUN", race.get("corner4", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if finish:
                try:
                    finish_int = int(finish)
                    corners = [c for c in [corner1, corner2, corner3, corner4] if c]
                    
                    if corners:
                        last_corner = int(corners[-1])
                        improvement = last_corner - finish_int
                        
                        if improvement > 0:
                            score = 50 + improvement * 10
                        else:
                            score = 50 + improvement * 5
                        
                        improvements.append(max(0, min(100, score)))
                except (ValueError, TypeError):
                    continue
        
        return sum(improvements) / len(improvements) if improvements else 50.0
    
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
                    
                    if finish_int == 1 and margin:
                        try:
                            if "大差" in str(margin):
                                base_score = 100
                            elif margin and float(margin) >= 0.5:
                                base_score = min(100, base_score * 1.1)
                        except:
                            pass
                    
                    finish_scores.append(base_score)
                except (ValueError, TypeError):
                    continue
        
        return sum(finish_scores) / len(finish_scores) if finish_scores else 50.0
    
    def _calc_time_index(self, raw_data: Dict) -> float:
        """タイム指数計算（簡略版）"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        time_scores = []
        
        for race in races:
            time = race.get("SOHA_TIME", race.get("TIME", race.get("time", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            distance = race.get("KYORI", race.get("distance", 0))
            
            if time and finish and distance:
                try:
                    time_float = float(time) / 10.0 if time else 0
                    finish_int = int(finish)
                    distance_int = int(distance)
                    
                    if time_float > 0 and distance_int > 0:
                        speed = distance_int / time_float
                        
                        base_score = 50
                        if speed > 16:
                            base_score = 90
                        elif speed > 15:
                            base_score = 75
                        elif speed > 14:
                            base_score = 60
                        
                        if finish_int <= 3:
                            base_score = min(100, base_score * 1.1)
                        
                        time_scores.append(base_score)
                except (ValueError, TypeError):
                    continue
        
        return sum(time_scores) / len(time_scores) if time_scores else 50.0
    
    def _calculate_total_score(self, scores: Dict[str, float]) -> float:
        """総合スコア計算（ダンスインザダーク基準）"""
        weights = [1.2, 1.1, 1.0, 1.0, 1.1, 0.9, 0.8, 0.9, 0.8, 1.0, 1.1, 1.2]
        
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
        
        total_weighted_score = 0
        total_weight = 0
        
        for i, key in enumerate(ordered_keys):
            if key in scores:
                total_weighted_score += scores[key] * weights[i]
                total_weight += weights[i]
        
        if total_weight == 0:
            return 50.0
        
        return total_weighted_score / total_weight
    
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

# グローバルインスタンス（シングルトン）
local_dlogic_manager_v2 = LocalDLogicRawDataManagerV2()
print(f"🏇 地方競馬版マネージャーV2準備完了")