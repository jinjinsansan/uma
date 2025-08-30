"""
V2 AIハンドラー用の高度な展開予想フォーマット関数
predict_race_flow_advancedメソッドの出力に対応
"""

from typing import Dict, Any

def format_flow_prediction_advanced(result: Dict[str, Any]) -> str:
    """高度な展開予想結果をフォーマット - 長文の自然言語で出力"""
    lines = []
    lines.append("## 🏇 **ViewLogic展開予想**")
    lines.append("")
    
    # レース情報
    race_info = result.get('race_info', {})
    venue = race_info.get('venue', '')
    race_number = race_info.get('race_number', '')
    distance = race_info.get('distance', '')
    
    lines.append(f"### {venue} {race_number}R - {race_info.get('race_name', '')}")
    lines.append(f"**距離**: {distance}")
    lines.append("")
    
    # コース特性の説明（距離と開催場に応じた解説）
    lines.append("### レース展開の見通し")
    lines.append("")
    
    # 開催場別のコース特性説明
    if venue == "新潟":
        if "1800" in str(distance):
            lines.append(f"新潟{distance}は直線が長く、最後の直線での瞬発力勝負になりやすいコースです。外回りコースのため、")
            lines.append("スタート後のポジション取りが重要で、中団から後方で脚を溜めた馬の台頭が期待できます。")
        elif "1000" in str(distance):
            lines.append(f"新潟{distance}直線は日本最短距離の直線競馬です。スタートダッシュと瞬発力が全てを決める特殊なレースとなります。")
        else:
            lines.append(f"{venue}{distance}は、直線の長い新潟競馬場の特性を活かした展開が予想されます。")
    elif venue == "東京":
        lines.append(f"東京{distance}は直線が長く、最後の直線での瞬発力と持続力が問われるコースです。")
        lines.append("広いコースレイアウトのため、外を回っても不利が少なく、後方からの追い込みも決まりやすい傾向があります。")
    elif venue == "中山":
        lines.append(f"中山{distance}は急坂と小回りが特徴的なコースです。先行力と器用さが求められ、")
        lines.append("逃げ・先行馬が粘り込みやすい傾向があります。")
    else:
        lines.append(f"{venue}{distance}の展開を分析します。")
    lines.append("")
    
    # ペース予想の詳細説明
    pace_pred = result.get('pace_prediction', {})
    pace = pace_pred.get('pace', '不明')
    confidence = pace_pred.get('confidence', 0)
    zenhan_avg = pace_pred.get('zenhan_avg', 0)
    kohan_avg = pace_pred.get('kohan_avg', 0)
    
    lines.append("### ペース予想")
    lines.append("")
    lines.append(f"**予想ペース: {pace}** （確信度: {confidence}%）")
    lines.append("")
    
    # ペースに応じた詳細な解説
    if 'ハイペース' in pace:
        lines.append(f"前半3Fの予想平均タイムは{zenhan_avg:.1f}秒と速く、序盤から激しい先行争いが予想されます。")
        lines.append("このようなハイペースでは、前半で脚を使った逃げ・先行馬が最後の直線で失速する可能性が高く、")
        lines.append("中団から後方で脚を溜めた差し・追込馬が有利な展開となりそうです。")
        lines.append(f"後半3Fは{kohan_avg:.1f}秒と予想され、前半のペースの反動で後半の失速が懸念されます。")
    elif 'スローペース' in pace:
        lines.append(f"前半3Fの予想平均タイムは{zenhan_avg:.1f}秒と遅く、各馬が牽制し合う展開が予想されます。")
        lines.append("スローペースでは前に行った馬が楽に走れるため、逃げ・先行馬が最後まで粘り込む可能性が高いです。")
        lines.append(f"後半3Fは{kohan_avg:.1f}秒の瞬発力勝負になりそうですが、前残りの可能性が高い展開です。")
    else:
        lines.append(f"前半3Fは{zenhan_avg:.1f}秒、後半3Fは{kohan_avg:.1f}秒の平均的なペースが予想されます。")
        lines.append("極端な展開にはなりにくく、各馬の総合的な能力が問われる真の実力勝負となりそうです。")
    lines.append("")
    
    # 詳細な脚質分類と各馬の解説
    detailed_styles = result.get('detailed_styles', {})
    lines.append("### 各馬の脚質分析")
    lines.append("")
    
    # 逃げ馬の分析
    if '逃げ' in detailed_styles and any(detailed_styles['逃げ'].values()):
        lines.append("#### 🏃 逃げ馬の動向")
        for sub_style, horses in detailed_styles['逃げ'].items():
            if horses:
                if sub_style == '超積極逃げ':
                    lines.append(f"**{horses[0]}**は超積極的な逃げを見せる可能性が高く、序盤から大きくリードを取ろうとするでしょう。")
                    lines.append("この馬がハナを切れば、後続との差を広げて逃げ切りを図る展開が予想されます。")
                elif sub_style == '状況逃げ':
                    lines.append(f"**{', '.join(horses)}**は状況を見ながらの逃げが予想され、他に逃げ馬がいなければ積極的に前に出そうです。")
                elif sub_style == '消極逃げ':
                    lines.append(f"**{', '.join(horses)}**は消極的な逃げとなる可能性があり、無理に逃げることはなさそうです。")
        lines.append("")
    
    # 先行馬の分析
    if '先行' in detailed_styles and any(detailed_styles['先行'].values()):
        lines.append("#### 🎯 先行馬の布陣")
        for sub_style, horses in detailed_styles['先行'].items():
            if horses:
                if sub_style == '前寄り先行':
                    lines.append(f"**{', '.join(horses[:2])}**は積極的に前のポジションを取りに行き、2-3番手での競馬が予想されます。")
                elif sub_style == '安定先行':
                    lines.append(f"**{', '.join(horses[:2])}**は安定した先行策を取り、好位でレースを進めそうです。")
                elif sub_style == '後寄り先行':
                    lines.append(f"**{', '.join(horses[:2])}**は先行グループの後方に控え、展開を見ながらの競馬となりそうです。")
        lines.append("")
    
    # 差し・追込馬の分析
    if ('差し' in detailed_styles and any(detailed_styles['差し'].values())) or ('追込' in detailed_styles and any(detailed_styles['追込'].values())):
        lines.append("#### ⚡ 差し・追込勢の台頭")
        if '差し' in detailed_styles:
            for sub_style, horses in detailed_styles['差し'].items():
                if horses and len(horses) > 0:
                    if 'ハイペース' in pace:
                        lines.append(f"ハイペースが予想される今回、**{', '.join(horses[:3])}**などの差し馬には絶好の展開となりそうです。")
                        lines.append("前半で脚を溜め、最後の直線で爆発的な末脚を発揮する可能性があります。")
                    else:
                        lines.append(f"**{', '.join(horses[:3])}**は中団から後方に控え、最後の直線勝負に賭けることになりそうです。")
                    break
        
        if '追込' in detailed_styles:
            for sub_style, horses in detailed_styles['追込'].items():
                if horses and len(horses) > 0:
                    if 'ハイペース' in pace:
                        lines.append(f"**{', '.join(horses[:2])}**などの追込馬も、前がバテる展開を待っています。")
                    else:
                        lines.append(f"**{', '.join(horses[:2])}**は後方一気の追込を狙いますが、展開次第では届かない可能性もあります。")
                    break
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
    
    # レースシミュレーション詳細
    simulation = result.get('race_simulation', {})
    if simulation:
        lines.append("### 展開シミュレーション")
        lines.append("")
        
        # スタートから序盤の展開
        if 'start' in simulation and len(simulation['start']) > 0:
            start_horses = [entry.get('horse_name', '不明') for entry in simulation['start'][:3]]
            lines.append("#### スタート〜序盤")
            lines.append(f"スタート直後は**{start_horses[0]}**が積極的にハナを主張し、")
            if len(start_horses) > 1:
                lines.append(f"**{start_horses[1]}**がそれに続く形になりそうです。")
            lines.append("")
        
        # 中盤の展開
        if 'corner3' in simulation and len(simulation['corner3']) > 0:
            corner3_horses = [entry.get('horse_name', '不明') for entry in simulation['corner3'][:5]]
            lines.append("#### 中盤の展開（3コーナー付近）")
            lines.append(f"3コーナーを迎える頃には、**{corner3_horses[0]}**がリードを保ち、")
            lines.append(f"2番手に**{corner3_horses[1]}**、3番手に**{corner3_horses[2]}**という隊列になりそうです。")
            if 'ハイペース' in pace:
                lines.append("ペースが速いため、後方待機組が徐々に進出を開始する場面です。")
            lines.append("")
        
        # 終盤の展開
        if 'corner4' in simulation and len(simulation['corner4']) > 0:
            corner4_horses = [entry.get('horse_name', '不明') for entry in simulation['corner4'][:5]]
            lines.append("#### 勝負所（4コーナー）")
            lines.append(f"最後の4コーナーでは、**{corner4_horses[0]}**が依然として先頭をキープしていますが、")
            if 'ハイペース' in pace:
                lines.append("ハイペースの影響で脚色が鈍り始め、後続の差し・追込馬が一気に接近してきます。")
                lines.append(f"特に**{corner4_horses[2]}**や**{corner4_horses[3]}**の末脚が注目されます。")
            else:
                lines.append(f"**{corner4_horses[1]}**と**{corner4_horses[2]}**が虎視眈々と逆転を狙っています。")
            lines.append("")
        
        # ゴール予想
        if 'finish' in simulation and len(simulation['finish']) > 0:
            finish_horses = [entry.get('horse_name', '不明') for entry in simulation['finish'][:5]]
            lines.append("#### ゴール前の攻防")
            lines.append(f"最後の直線では、**{finish_horses[0]}**が抜け出す可能性が高く、")
            lines.append(f"**{finish_horses[1]}**と**{finish_horses[2]}**が激しく追い上げる展開が予想されます。")
            lines.append("")
            lines.append("**【上位5頭予想】**")
            for i, horse in enumerate(finish_horses, 1):
                lines.append(f"{i}. **{horse}**")
        lines.append("")
    
    # 最終的な狙い目と推奨
    lines.append("### 🎯 最終予想と狙い目")
    lines.append("")
    
    if 'ハイペース' in pace:
        lines.append("#### ハイペースを活かす狙い方")
        lines.append("今回のレースは**ハイペースが予想される**ため、以下の点に注目してください：")
        lines.append("")
        lines.append("1. **後方待機の差し・追込馬を重視**")
        lines.append("   前半のハイペースで前の馬がスタミナを消耗するため、最後の直線で差し・追込馬の一発があります。")
        lines.append("")
        lines.append("2. **前半飛ばす逃げ・先行馬は割引**")
        lines.append("   序盤から速いペースに巻き込まれる逃げ・先行馬は、最後まで持たない可能性が高いです。")
        lines.append("")
        lines.append("3. **スタミナと末脚の両立**")
        lines.append("   ハイペースに対応できるスタミナと、最後に伸びる末脚を持つ馬が理想的です。")
        
    elif 'スローペース' in pace:
        lines.append("#### スローペースでの前残り狙い")
        lines.append("今回は**スローペースが予想される**ため、以下の戦略が有効です：")
        lines.append("")
        lines.append("1. **前残りの可能性大**")
        lines.append("   楽なペースで逃げ・先行できる馬は、最後まで余力を残して粘り込む可能性があります。")
        lines.append("")
        lines.append("2. **逃げ・先行馬を重視**")
        lines.append("   スローペースでは前に行った馬が有利。特に逃げ馬の逃げ切りも十分あり得ます。")
        lines.append("")
        lines.append("3. **追込一辺倒は危険**")
        lines.append("   前が止まらない展開では、後方からの追込馬は届かないリスクがあります。")
        
    else:
        lines.append("#### 平均ペースでの実力勝負")
        lines.append("今回は**平均的なペース**が予想されるため、総合力が問われます：")
        lines.append("")
        lines.append("1. **総合力の高い馬を重視**")
        lines.append("   極端な展開にならないため、能力の高い馬が素直に好走する可能性が高いです。")
        lines.append("")
        lines.append("2. **器用さと対応力**")
        lines.append("   どんな展開にも対応できる器用な馬が有利です。")
        lines.append("")
        lines.append("3. **実績と安定感**")
        lines.append("   過去の実績が安定している馬を信頼できる展開です。")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*このレース展開予想は、過去のレースデータと各馬の脚質傾向を基に、ViewLogicエンジンが算出したものです。*")
    lines.append("*実際のレースでは、当日の馬場状態や各馬のコンディションにより、予想と異なる展開になる可能性があります。*")
    
    return "\n".join(lines)