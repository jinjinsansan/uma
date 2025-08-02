#!/usr/bin/env python3
"""
Phase D統合: 究極ナレッジベース・LLM統合システム
959,620レコード・50頭完全分析データをLLMに注入
"""
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

class EnhancedKnowledgeBase:
    """Phase D究極ナレッジベース統合クラス"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.reports_dir = Path(__file__).parent.parent / "reports"
        
        # Phase D究極ナレッジベース読み込み
        self.ultimate_knowledge = self._load_ultimate_knowledge_base()
        
        # 従来のナレッジベース
        self.legacy_knowledge = self._load_legacy_knowledge_base()
        
        # 統合ナレッジベース構築
        self.integrated_knowledge = self._integrate_knowledge_bases()
        
        print("🚀 Phase D究極ナレッジベース統合完了")
        print(f"📊 最強馬データ: {len(self.get_legendary_horses())}頭")
        print(f"🎯 勝利パターン: {len(self.get_winning_patterns())}種類")
    
    def _load_ultimate_knowledge_base(self) -> Dict[str, Any]:
        """Phase D究極ナレッジベース読み込み"""
        try:
            # 最新のultimate_knowledge_baseファイルを検索
            pattern = "ultimate_knowledge_base_*.json"
            files = list(self.reports_dir.glob(pattern))
            
            if files:
                # 最新ファイルを取得
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                print(f"✅ 究極ナレッジベース読み込み: {latest_file.name}")
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print("⚠️  究極ナレッジベースファイルが見つかりません")
                return {}
                
        except Exception as e:
            print(f"❌ 究極ナレッジベース読み込みエラー: {e}")
            return {}
    
    def _load_legacy_knowledge_base(self) -> Dict[str, Any]:
        """従来のナレッジベース読み込み"""
        try:
            knowledge_file = self.data_dir / "knowledgeBase.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"従来ナレッジベース読み込みエラー: {e}")
        
        # デフォルトデータ
        return {
            "reference_horse": {
                "name": "ダンスインザダーク",
                "base_score": 100,
                "description": "Dロジック指数の基準馬"
            },
            "scoring_weights": {
                "distance_aptitude": 1.2,
                "bloodline_evaluation": 1.1,
                "jockey_compatibility": 1.0,
                "trainer_evaluation": 1.0,
                "track_aptitude": 1.1,
                "weather_aptitude": 0.9,
                "popularity_factor": 0.8,
                "weight_impact": 0.9,
                "horse_weight_impact": 0.8,
                "corner_specialist": 1.0,
                "margin_analysis": 1.1,
                "time_index": 1.2
            }
        }
    
    def _integrate_knowledge_bases(self) -> Dict[str, Any]:
        """ナレッジベース統合"""
        integrated = self.legacy_knowledge.copy()
        
        if self.ultimate_knowledge:
            # Phase D データを統合
            integrated.update({
                "phase_d_data": {
                    "legendary_horses": self.ultimate_knowledge.get("legendary_horses", {}),
                    "winning_patterns": self.ultimate_knowledge.get("winning_patterns", {}),
                    "prediction_accuracy": self.ultimate_knowledge.get("prediction_accuracy", {}),
                    "total_horses_analyzed": self.ultimate_knowledge.get("total_horses_analyzed", 0),
                    "database_stats": {
                        "total_records": 959620,
                        "total_horses": 109426,
                        "data_span_years": 71,
                        "analysis_timestamp": self.ultimate_knowledge.get("analysis_timestamp", "")
                    }
                },
                "enhanced_references": self._create_enhanced_references(),
                "llm_context": self._create_llm_context()
            })
        
        return integrated
    
    def _create_enhanced_references(self) -> Dict[str, Any]:
        """強化参照データ作成"""
        legendary_horses = self.ultimate_knowledge.get("legendary_horses", {})
        winning_patterns = self.ultimate_knowledge.get("winning_patterns", {})
        
        # 最強馬データから参照値を抽出
        distance_refs = {}
        jockey_refs = {}
        bloodline_refs = {}
        
        for horse_name, horse_data in legendary_horses.items():
            d_logic = horse_data.get("d_logic_scores", {})
            stats = horse_data.get("detailed_stats", {})
            
            # 高得点項目を参照データに追加
            if d_logic.get("1_distance_aptitude", 0) > 85:
                distance_refs[horse_name] = {
                    "score": d_logic.get("1_distance_aptitude"),
                    "win_rate": stats.get("win_rate", 0)
                }
            
            if d_logic.get("2_bloodline_evaluation", 0) >= 95:
                bloodline_refs[horse_name] = {
                    "score": d_logic.get("2_bloodline_evaluation"),
                    "total_wins": stats.get("wins", 0)
                }
        
        return {
            "legendary_distance_specialists": distance_refs,
            "legendary_bloodline_horses": bloodline_refs,
            "high_performers": winning_patterns.get("high_performers", []),
            "versatile_champions": winning_patterns.get("versatile_champions", [])
        }
    
    def _create_llm_context(self) -> Dict[str, Any]:
        """LLM用コンテキスト作成"""
        legendary_horses = self.ultimate_knowledge.get("legendary_horses", {})
        winning_patterns = self.ultimate_knowledge.get("winning_patterns", {})
        
        # トップ10馬の要約
        top_horses = []
        high_performers = winning_patterns.get("high_performers", [])[:10]
        
        for horse_info in high_performers:
            horse_name = horse_info.get("horse", "")
            if horse_name in legendary_horses:
                horse_data = legendary_horses[horse_name]
                top_horses.append({
                    "name": horse_name,
                    "score": horse_info.get("score", 0),
                    "grade": horse_info.get("grade", ""),
                    "wins": horse_info.get("wins", 0),
                    "win_rate": horse_info.get("win_rate", 0),
                    "career_span": horse_data.get("detailed_stats", {}).get("career_span", {}).get("span", ""),
                    "specialties": self._extract_horse_specialties(horse_data)
                })
        
        return {
            "database_summary": f"959,620レコード・109,426頭・71年間の日本競馬完全データベース",
            "analysis_method": "ダンスインザダーク基準100点・12項目D-Logic分析",
            "top_legendary_horses": top_horses,
            "winning_patterns_summary": {
                "high_performers_count": len(winning_patterns.get("high_performers", [])),
                "distance_specialists_count": len(winning_patterns.get("distance_specialists", [])),
                "versatile_champions_count": len(winning_patterns.get("versatile_champions", [])),
                "bloodline_excellence_count": len(winning_patterns.get("bloodline_excellence", []))
            },
            "prediction_accuracy": self.ultimate_knowledge.get("prediction_accuracy", {}),
            "last_updated": datetime.now().isoformat()
        }
    
    def _extract_horse_specialties(self, horse_data: Dict[str, Any]) -> List[str]:
        """馬の専門性を抽出"""
        d_logic = horse_data.get("d_logic_scores", {})
        specialties = []
        
        if d_logic.get("1_distance_aptitude", 0) > 90:
            specialties.append("距離適性抜群")
        if d_logic.get("2_bloodline_evaluation", 0) >= 95:
            specialties.append("血統優秀")
        if d_logic.get("3_jockey_compatibility", 0) > 90:
            specialties.append("騎手相性良好")
        if d_logic.get("5_track_aptitude", 0) > 85:
            specialties.append("馬場適性高")
        if d_logic.get("11_margin_analysis", 0) > 90:
            specialties.append("勝負強い")
        
        return specialties[:3]  # 上位3つの特徴
    
    def get_legendary_horses(self) -> Dict[str, Any]:
        """伝説の馬データ取得"""
        return self.integrated_knowledge.get("phase_d_data", {}).get("legendary_horses", {})
    
    def get_winning_patterns(self) -> Dict[str, Any]:
        """勝利パターン取得"""
        return self.integrated_knowledge.get("phase_d_data", {}).get("winning_patterns", {})
    
    def get_llm_context(self) -> Dict[str, Any]:
        """LLM用コンテキスト取得"""
        return self.integrated_knowledge.get("llm_context", {})
    
    def get_enhanced_references(self) -> Dict[str, Any]:
        """強化参照データ取得"""
        return self.integrated_knowledge.get("enhanced_references", {})
    
    def find_similar_horse(self, target_stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """類似馬検索"""
        legendary_horses = self.get_legendary_horses()
        target_win_rate = target_stats.get("win_rate", 0)
        target_races = target_stats.get("total_races", 0)
        
        best_match = None
        best_similarity = 0
        
        for horse_name, horse_data in legendary_horses.items():
            stats = horse_data.get("detailed_stats", {})
            horse_win_rate = stats.get("win_rate", 0)
            horse_races = stats.get("total_races", 0)
            
            # 類似度計算（勝率・出走数の差から）
            win_rate_diff = abs(target_win_rate - horse_win_rate)
            races_diff = abs(target_races - horse_races) / 100  # スケール調整
            
            similarity = 1 / (1 + win_rate_diff + races_diff)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    "name": horse_name,
                    "similarity": similarity,
                    "data": horse_data,
                    "comparison": {
                        "target_win_rate": target_win_rate,
                        "horse_win_rate": horse_win_rate,
                        "target_races": target_races,
                        "horse_races": horse_races
                    }
                }
        
        return best_match if best_similarity > 0.5 else None
    
    def get_prediction_insights(self, horse_name: str) -> Dict[str, Any]:
        """予想インサイト取得"""
        legendary_horses = self.get_legendary_horses()
        
        if horse_name in legendary_horses:
            horse_data = legendary_horses[horse_name]
            d_logic = horse_data.get("d_logic_scores", {})
            stats = horse_data.get("detailed_stats", {})
            
            # 強み・弱み分析
            strengths = []
            weaknesses = []
            
            for key, score in d_logic.items():
                item_name = key.split('_', 1)[1] if '_' in key else key
                
                if score > 85:
                    strengths.append(f"{item_name}: {score:.1f}")
                elif score < 50:
                    weaknesses.append(f"{item_name}: {score:.1f}")
            
            return {
                "total_score": horse_data.get("dance_in_the_dark_total_score", 0),
                "grade": horse_data.get("performance_grade", ""),
                "win_rate": stats.get("win_rate", 0),
                "total_races": stats.get("total_races", 0),
                "career_span": stats.get("career_span", {}).get("span", ""),
                "strengths": strengths[:3],
                "weaknesses": weaknesses[:2],
                "specialties": self._extract_horse_specialties(horse_data)
            }
        
        return {}
    
    def get_context_for_llm_prompt(self) -> str:
        """LLMプロンプト用コンテキスト文字列生成"""
        llm_context = self.get_llm_context()
        top_horses = llm_context.get("top_legendary_horses", [])[:5]
        
        context = f"""
競馬予想AI ナレッジベース概要:
- データベース: {llm_context.get('database_summary', '')}
- 分析手法: {llm_context.get('analysis_method', '')}

伝説の最強馬 TOP5:
"""
        
        for i, horse in enumerate(top_horses, 1):
            context += f"{i}. {horse.get('name', '')} - スコア{horse.get('score', 0):.1f} ({horse.get('grade', '')}) - 勝率{horse.get('win_rate', 0):.1%}\n"
            if horse.get('specialties'):
                context += f"   特徴: {', '.join(horse.get('specialties', []))}\n"
        
        winning_patterns = llm_context.get("winning_patterns_summary", {})
        context += f"""
勝利パターン分析:
- 高得点馬: {winning_patterns.get('high_performers_count', 0)}頭
- 距離スペシャリスト: {winning_patterns.get('distance_specialists_count', 0)}頭  
- 万能型チャンピオン: {winning_patterns.get('versatile_champions_count', 0)}頭
- 血統優秀馬: {winning_patterns.get('bloodline_excellence_count', 0)}頭

このナレッジベースを活用して、科学的根拠に基づいた競馬予想を提供してください。
"""
        
        return context.strip()
    
    def save_integrated_knowledge_base(self) -> str:
        """統合ナレッジベース保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"integrated_knowledge_base_{timestamp}.json"
        filepath = self.data_dir / filename
        
        # ディレクトリ作成
        self.data_dir.mkdir(exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.integrated_knowledge, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ 統合ナレッジベース保存: {filename}")
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return ""

# グローバルインスタンス
enhanced_knowledge_base = EnhancedKnowledgeBase()

if __name__ == "__main__":
    # テスト実行
    print("\n🧪 Phase D統合ナレッジベーステスト")
    
    # 伝説の馬確認
    legendary_horses = enhanced_knowledge_base.get_legendary_horses()
    print(f"📊 伝説の馬データ: {len(legendary_horses)}頭")
    
    # LLMコンテキスト確認
    context = enhanced_knowledge_base.get_context_for_llm_prompt()
    print(f"🤖 LLMコンテキスト長: {len(context)}文字")
    
    # 統合ナレッジベース保存
    saved_path = enhanced_knowledge_base.save_integrated_knowledge_base()
    print(f"💾 保存パス: {saved_path}")
    
    print("\n✅ Phase D統合ナレッジベース準備完了!")