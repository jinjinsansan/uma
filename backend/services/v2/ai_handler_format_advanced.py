"""
V2 AIハンドラー用の高度な展開予想フォーマット関数
predict_race_flow_advancedメソッドの出力に対応
"""

from typing import Dict, Any

def format_flow_prediction_advanced(result: Dict[str, Any]) -> str:
    """高度な展開予想結果をフォーマット"""
    lines = []
    lines.append("🏇 **ViewLogic展開予想**")
    
    # レース情報
    race_info = result.get('race_info', {})
    lines.append(f"{race_info.get('venue', '')} {race_info.get('race_number', '')}R - {race_info.get('race_name', '')}")
    lines.append(f"距離: {race_info.get('distance', '')}")
    lines.append("")
    
    # ペース予想
    pace_pred = result.get('pace_prediction', {})
    pace = pace_pred.get('pace', '不明')
    confidence = pace_pred.get('confidence', 0)
    lines.append(f"**【ペース予想】{pace}**")
    lines.append(f"確信度: {confidence}%")
    lines.append(f"前半3F平均: {pace_pred.get('zenhan_avg', 0):.1f}秒")
    lines.append(f"後半3F平均: {pace_pred.get('kohan_avg', 0):.1f}秒")
    lines.append("")
    
    # 詳細な脚質分類
    detailed_styles = result.get('detailed_styles', {})
    lines.append("**【詳細な脚質分類】**")
    
    for main_style, sub_styles in detailed_styles.items():
        has_horses = any(horses for horses in sub_styles.values())
        if has_horses:
            lines.append(f"\n◆ {main_style}")
            for sub_style, horses in sub_styles.items():
                if horses:
                    horses_str = ', '.join(horses)
                    lines.append(f"  • {sub_style}: {horses_str}")
    lines.append("")
    
    # 位置取り安定性TOP3
    stability = result.get('position_stability', {})
    if stability:
        lines.append("**【位置取り安定性】**")
        sorted_stability = sorted(stability.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (horse, score) in enumerate(sorted_stability, 1):
            lines.append(f"{i}. {horse}: {score:.2f}")
        lines.append("")
    
    # 展開適性マッチング（上位3頭）
    flow_matching = result.get('flow_matching', {})
    if flow_matching:
        lines.append("**【展開適性スコア】**")
        sorted_matching = sorted(flow_matching.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (horse, score) in enumerate(sorted_matching, 1):
            lines.append(f"{i}. {horse}: {score:.1f}点")
        lines.append("")
    
    # レースシミュレーション
    simulation = result.get('race_simulation', {})
    if simulation:
        lines.append("**【展開シミュレーション】**")
        
        # スタート時の隊列（上位3頭）
        if 'start' in simulation:
            lines.append("◆ スタート時:")
            for i, entry in enumerate(simulation['start'][:3], 1):
                horse = entry.get('horse_name', '不明')
                lines.append(f"  {i}. {horse}")
        
        # 3コーナー（上位3頭）
        if 'corner3' in simulation:
            lines.append("◆ 3コーナー:")
            for i, entry in enumerate(simulation['corner3'][:3], 1):
                horse = entry.get('horse_name', '不明')
                lines.append(f"  {i}. {horse}")
        
        # 4コーナー（上位3頭）
        if 'corner4' in simulation:
            lines.append("◆ 4コーナー:")
            for i, entry in enumerate(simulation['corner4'][:3], 1):
                horse = entry.get('horse_name', '不明')
                lines.append(f"  {i}. {horse}")
        
        # ゴール予想（上位5頭）
        if 'finish' in simulation:
            lines.append("◆ ゴール予想:")
            for i, entry in enumerate(simulation['finish'][:5], 1):
                horse = entry.get('horse_name', '不明')
                lines.append(f"  {i}. {horse}")
        lines.append("")
    
    # ペースに応じた狙い目
    lines.append("**【狙い目】**")
    if 'ハイペース' in pace:
        lines.append("• 後方待機の差し・追込馬が有利")
        lines.append("• 前半飛ばす逃げ・先行馬は苦戦")
    elif 'スローペース' in pace:
        lines.append("• 前残りの可能性大")
        lines.append("• 逃げ・先行馬を重視")
        lines.append("• 追込一辺倒は厳しい")
    else:
        lines.append("• 平均ペースで力勝負")
        lines.append("• 総合力の高い馬を重視")
    
    return "\n".join(lines)