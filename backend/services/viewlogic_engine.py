"""
ViewLogic展開予想エンジン

レースの展開（ペース）を予想するシステム。
各馬の脚質（逃げ/先行/中団/後方）を分析して、レース全体の展開をシミュレーション。
"""

import json
import gzip
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RunningStyle:
    """脚質分析結果"""
    style: str  # 逃げ/先行/中団/後方
    confidence: float  # 信頼度 (0-1)
    avg_position: float  # 平均通過順位
    position_stability: float  # 位置安定性
    sample_size: int  # データ数

@dataclass
class HorseViewLogic:
    """馬のViewLogic分析結果"""
    horse_name: str
    running_style: RunningStyle
    pace_preference: str  # slow/average/high
    decisive_power: float  # 決め手（上がり3Fの評価）
    experience: int  # 分析対象レース数

@dataclass
class RacePaceAnalysis:
    """レースのペース分析結果"""
    expected_pace: str  # slow/average/high
    confidence: float  # 確信度
    front_horses_count: int  # 前に行く馬の数
    competition_level: str  # 激しさ（low/medium/high）

class ViewLogicEngine:
    """ViewLogic展開予想エンジン"""
    
    def __init__(self):
        self.knowledge_data = {}
        self.loaded = False
        
    def load_knowledge(self, data_dir: str = None):
        """ViewLogicナレッジファイルを読み込み"""
        if data_dir is None:
            data_dir = "/mnt/c/Users/USER/OneDrive/デスクトップ/Cusor/data/viewlogic/phase3"
            
        try:
            logger.info("ViewLogicナレッジファイル読み込み開始")
            
            # Phase 3のすべてのファイルを読み込み
            phase3_files = [f for f in os.listdir(data_dir) if f.endswith('.json.gz')]
            
            total_horses = 0
            for filename in sorted(phase3_files):
                filepath = os.path.join(data_dir, filename)
                
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    
                for horse_data in batch_data:
                    horse_name = horse_data.get('horse_name')
                    if horse_name:
                        self.knowledge_data[horse_name] = horse_data
                        total_horses += 1
            
            self.loaded = True
            logger.info(f"ViewLogicナレッジファイル読み込み完了: {total_horses:,}頭")
            
        except Exception as e:
            logger.error(f"ViewLogicナレッジファイル読み込みエラー: {e}")
            raise RuntimeError(f"ViewLogicナレッジファイルの読み込みに失敗: {e}")
    
    def analyze_horse_running_style(self, horse_name: str) -> Optional[HorseViewLogic]:
        """馬の脚質を分析"""
        if not self.loaded:
            self.load_knowledge()
            
        horse_data = self.knowledge_data.get(horse_name)
        if not horse_data:
            return None
            
        races = horse_data.get('races', [])
        if not races:
            return None
            
        # コーナー通過順位分析
        running_style = self._analyze_running_style(races)
        
        # ペース適性分析
        pace_preference = self._analyze_pace_preference(races)
        
        # 決め手分析
        decisive_power = self._analyze_decisive_power(races)
        
        return HorseViewLogic(
            horse_name=horse_name,
            running_style=running_style,
            pace_preference=pace_preference,
            decisive_power=decisive_power,
            experience=len(races)
        )
    
    def _analyze_running_style(self, races: List[Dict]) -> RunningStyle:
        """脚質を詳細分析"""
        corner1_positions = []
        position_changes = []
        
        for race in races:
            corner1 = race.get('CORNER1_JUNI')
            corner4 = race.get('CORNER4_JUNI')
            tosu = race.get('TOSU', 18)  # デフォルト18頭
            
            if corner1 and corner1 > 0 and tosu and tosu > 1:
                # 相対位置に変換 (0-1)
                relative_pos = (corner1 - 1) / (tosu - 1)
                corner1_positions.append(relative_pos)
                
                # 位置変動を分析
                if corner4 and corner4 > 0:
                    position_change = corner4 - corner1
                    position_changes.append(position_change)
        
        if not corner1_positions:
            return RunningStyle("不明", 0.0, 0.0, 0.0, 0)
        
        avg_position = statistics.mean(corner1_positions)
        
        # 脚質判定
        if avg_position <= 0.15:
            style = "逃げ"
        elif avg_position <= 0.35:
            style = "先行"
        elif avg_position <= 0.65:
            style = "中団"
        else:
            style = "後方"
        
        # 信頼度計算
        confidence = min(len(corner1_positions) / 9.0, 1.0)
        
        # 位置安定性
        stability = 0.0
        if len(corner1_positions) > 1:
            std_dev = statistics.stdev(corner1_positions)
            stability = max(0.0, 1.0 - std_dev * 2)  # 変動が小さいほど高い
        
        return RunningStyle(
            style=style,
            confidence=confidence,
            avg_position=avg_position,
            position_stability=stability,
            sample_size=len(corner1_positions)
        )
    
    def _analyze_pace_preference(self, races: List[Dict]) -> str:
        """ペース適性を分析"""
        pace_results = {"slow": 0, "average": 0, "high": 0}
        
        for race in races:
            corner1 = race.get('CORNER1_JUNI')
            corner4 = race.get('CORNER4_JUNI')
            result = race.get('KAKUTEI_CHAKUJUN')
            
            if corner1 and corner4 and result:
                position_change = corner4 - corner1
                
                # ペース推定（簡易版）
                if position_change > 2:
                    pace = "high"  # ハイペース（前が崩れた）
                elif position_change < -2:
                    pace = "slow"  # スローペース（後方から差した）
                else:
                    pace = "average"
                
                # 好成績での重み付け
                if result <= 3:
                    pace_results[pace] += 2
                else:
                    pace_results[pace] += 1
        
        # 最適ペースを判定
        best_pace = max(pace_results, key=pace_results.get)
        return best_pace
    
    def _analyze_decisive_power(self, races: List[Dict]) -> float:
        """決め手を分析（上がり3F）"""
        kohan_times = []
        
        for race in races:
            kohan = race.get('KOHAN_3F')
            if kohan and kohan > 0:
                # 秒単位に変換（データが10倍されている可能性）
                if kohan > 100:
                    kohan = kohan / 10.0
                kohan_times.append(kohan)
        
        if not kohan_times:
            return 50.0  # デフォルト値
        
        # 平均上がり3Fから決め手度を算出
        avg_kohan = statistics.mean(kohan_times)
        
        # 33秒台前半=優秀、35秒台=平凡として100点満点で評価
        if avg_kohan <= 33.0:
            return 100.0
        elif avg_kohan >= 36.0:
            return 30.0
        else:
            # 線形補間
            return 100 - (avg_kohan - 33.0) * 23.3
    
    def analyze_race_pace(self, horses: List[str]) -> RacePaceAnalysis:
        """レース全体のペース分析"""
        if not self.loaded:
            self.load_knowledge()
        
        # 各馬の脚質を分析
        horse_styles = []
        for horse_name in horses:
            horse_analysis = self.analyze_horse_running_style(horse_name)
            if horse_analysis:
                horse_styles.append(horse_analysis.running_style.style)
            else:
                horse_styles.append("不明")
        
        # 脚質分布を集計
        style_counts = {
            "逃げ": horse_styles.count("逃げ"),
            "先行": horse_styles.count("先行"),
            "中団": horse_styles.count("中団"),
            "後方": horse_styles.count("後方")
        }
        
        front_horses = style_counts["逃げ"] + style_counts["先行"]
        
        # ペース予想
        if style_counts["逃げ"] >= 2:
            expected_pace = "high"  # 複数逃げでハイペース
            confidence = 0.8
            competition_level = "high"
        elif front_horses >= len(horses) * 0.4:
            expected_pace = "average"  # 前に行く馬が多い
            confidence = 0.6
            competition_level = "medium"
        else:
            expected_pace = "slow"  # 前に行く馬が少ない
            confidence = 0.7
            competition_level = "low"
        
        return RacePaceAnalysis(
            expected_pace=expected_pace,
            confidence=confidence,
            front_horses_count=front_horses,
            competition_level=competition_level
        )
    
    def predict_race_development(self, horses: List[str], jockeys: List[str] = None) -> Dict:
        """レース展開を予想"""
        if not self.loaded:
            self.load_knowledge()
        
        # ペース分析
        pace_analysis = self.analyze_race_pace(horses)
        
        # 各馬の分析
        horse_analyses = []
        for i, horse_name in enumerate(horses):
            horse_analysis = self.analyze_horse_running_style(horse_name)
            if horse_analysis:
                jockey = jockeys[i] if jockeys and i < len(jockeys) else "騎手不明"
                horse_analyses.append({
                    "horse": horse_name,
                    "jockey": jockey,
                    "style": horse_analysis.running_style.style,
                    "confidence": horse_analysis.running_style.confidence,
                    "pace_preference": horse_analysis.pace_preference,
                    "decisive_power": horse_analysis.decisive_power
                })
        
        # 脚質別にグループ化
        style_groups = {
            "逃げ": [],
            "先行": [],
            "中団": [],
            "後方": []
        }
        
        for horse in horse_analyses:
            style = horse.get("style", "不明")
            if style in style_groups:
                style_groups[style].append(horse)
        
        # 展開シミュレーション文章を生成
        simulation_text = self._generate_race_simulation(pace_analysis, style_groups)
        
        # 有利・不利な馬を選出
        favorable_horses = self._select_favorable_horses(horse_analyses, pace_analysis)
        unfavorable_horses = self._select_unfavorable_horses(horse_analyses, pace_analysis)
        
        return {
            "pace_prediction": {
                "expected_pace": pace_analysis.expected_pace,
                "confidence": pace_analysis.confidence,
                "competition_level": pace_analysis.competition_level
            },
            "style_distribution": {
                style: len(horses_list) for style, horses_list in style_groups.items()
            },
            "simulation_text": simulation_text,
            "favorable_horses": favorable_horses,
            "unfavorable_horses": unfavorable_horses,
            "detailed_analysis": horse_analyses
        }
    
    def _generate_race_simulation(self, pace_analysis: RacePaceAnalysis, style_groups: Dict) -> str:
        """展開シミュレーション文章を生成"""
        pace_desc = {
            "slow": "スローペース",
            "average": "平均的なペース", 
            "high": "ハイペース"
        }
        
        confidence_desc = f"確信度{pace_analysis.confidence*100:.0f}%"
        
        text = f"【ペース予想】{pace_desc[pace_analysis.expected_pace]}（{confidence_desc}）\n\n"
        
        # 脚質分布
        text += "【脚質分布】\n"
        for style, horses_list in style_groups.items():
            if horses_list:
                count = len(horses_list)
                if count == 1:
                    text += f"{style}：{count}頭（{horses_list[0]['horse']}）\n"
                else:
                    text += f"{style}：{count}頭\n"
        
        text += "\n【展開シミュレーション】\n"
        
        # ペース別のシミュレーション
        if pace_analysis.expected_pace == "high":
            if style_groups["逃げ"]:
                escape_horses = [h["horse"] for h in style_groups["逃げ"]]
                text += f"スタート直後は{escape_horses[0]}が積極的にハナを主張。"
                if len(escape_horses) > 1:
                    text += f"{escape_horses[1]}も譲らず、激しい先行争いが予想されます。"
                text += "前半は速いペースとなりそうです。\n"
        elif pace_analysis.expected_pace == "slow":
            text += "前に行く馬が少なく、スローペースが予想されます。直線での瞬発力勝負となりそうです。\n"
        else:
            text += "標準的な流れが予想されます。道中のポジション取りが重要になりそうです。\n"
        
        return text
    
    def _select_favorable_horses(self, horse_analyses: List[Dict], pace_analysis: RacePaceAnalysis) -> List[Dict]:
        """有利な馬を選出"""
        favorable = []
        
        for horse in horse_analyses:
            style = horse.get("style")
            pace_preference = horse.get("pace_preference")
            decisive_power = horse.get("decisive_power", 50)
            
            # ペースとの適性
            is_favorable = False
            reason = ""
            
            if pace_analysis.expected_pace == "high" and style in ["中団", "後方"]:
                is_favorable = True
                reason = f"{style}・差し - ハイペース適性"
            elif pace_analysis.expected_pace == "slow" and style in ["先行", "中団"]:
                is_favorable = True
                reason = f"{style}・捲り - スローペース適性"
            elif decisive_power >= 80:
                is_favorable = True
                reason = "上がり最速級"
            
            if is_favorable:
                favorable.append({
                    "horse": horse["horse"],
                    "jockey": horse["jockey"], 
                    "reason": reason
                })
        
        return favorable[:5]  # 最大5頭
    
    def _select_unfavorable_horses(self, horse_analyses: List[Dict], pace_analysis: RacePaceAnalysis) -> List[Dict]:
        """不利な馬を選出"""
        unfavorable = []
        
        for horse in horse_analyses:
            style = horse.get("style")
            decisive_power = horse.get("decisive_power", 50)
            
            # ペースでの不利
            is_unfavorable = False
            reason = ""
            
            if pace_analysis.expected_pace == "high" and style == "逃げ":
                is_unfavorable = True
                reason = "競り合いで消耗"
            elif pace_analysis.expected_pace == "high" and style == "先行":
                is_unfavorable = True
                reason = "ハイペース巻き込まれ"
            elif pace_analysis.expected_pace == "slow" and style == "後方" and decisive_power < 60:
                is_unfavorable = True
                reason = "決め手不足"
            
            if is_unfavorable:
                unfavorable.append({
                    "horse": horse["horse"],
                    "jockey": horse["jockey"],
                    "reason": reason
                })
        
        return unfavorable[:5]  # 最大5頭


# グローバルインスタンス
viewlogic_engine = ViewLogicEngine()