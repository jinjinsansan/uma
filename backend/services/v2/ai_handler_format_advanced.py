"""
V2 AIハンドラー用の高度な展開予想フォーマット関数
predict_race_flow_advancedメソッドの出力に対応
"""

from typing import Dict, Any, List
import random

def get_pace_templates() -> Dict[str, List[str]]:
    """ペース予想の多様なテンプレートを返す"""
    return {
        'ハイペース_intro': [
            "序盤から激しい先行争いが予想され、ハイペースの展開となりそうです。",
            "スタート直後から各馬が積極的に前を取りに行き、速いペースで推移する可能性が高いです。",
            "前半から飛ばす展開が予想され、後半のスタミナ勝負が鍵となりそうです。",
            "逃げ馬が複数いることから、序盤のポジション争いが激化しそうです。",
        ],
        'ハイペース_effect': [
            "このようなハイペースでは、前半で脚を使った逃げ・先行馬が最後の直線で失速する可能性が高く、中団から後方で脚を溜めた差し・追込馬が有利な展開となりそうです。",
            "速いペースは差し・追込馬にとって絶好の展開。前が止まったところを一気に差し切る場面が見られそうです。",
            "前半の消耗戦により、後方待機組の末脚が炸裂する可能性が高まります。",
            "タフな流れになることで、スタミナに優れた馬や展開利を得られる差し馬が台頭しそうです。",
        ],
        'スローペース_intro': [
            "各馬が牽制し合い、スローペースの展開が予想されます。",
            "逃げ馬が単騎で楽に逃げられそうで、前半はゆったりとしたペースになりそうです。",
            "序盤は様子見ムードで、後半の瞬発力勝負になる可能性が高いです。",
            "前半は各馬が脚を溜め合う展開で、最後の直線での位置取りが重要になりそうです。",
        ],
        'スローペース_effect': [
            "スローペースでは前に行った馬が楽に走れるため、逃げ・先行馬が最後まで粘り込む可能性が高いです。",
            "前残りの展開が予想され、逃げ・先行馬の粘り込みに注意が必要です。",
            "溜めた脚を使える逃げ・先行馬が有利で、差し馬は届かない可能性があります。",
            "瞬発力勝負になりやすく、キレのある脚を持つ馬が有利な展開です。",
        ],
        '平均ペース_intro': [
            "平均的なペースで推移すると予想されます。",
            "極端な展開にはなりにくく、淡々とレースが進みそうです。",
            "標準的なペースが予想され、各馬の地力が試される展開です。",
            "バランスの取れたペースで、どの脚質にもチャンスがありそうです。",
        ],
        '平均ペース_effect': [
            "極端な展開にはなりにくく、各馬の総合的な能力が問われる真の実力勝負となりそうです。",
            "どの脚質にも平等にチャンスがあり、能力と調子の良い馬が好走しそうです。",
            "展開の有利不利が少ないため、素直に強い馬が勝つ可能性が高いです。",
            "総合力の高い馬や、安定感のある馬が力を発揮しやすい展開です。",
        ]
    }

def get_horse_description_templates() -> Dict[str, List[str]]:
    """馬の説明の多様なテンプレートを返す"""
    return {
        '逃げ_積極': [
            "{horse}は超積極的な逃げを見せる可能性が高く、序盤から大きくリードを取ろうとするでしょう。",
            "{horse}が果敢にハナを奪いに行き、後続を大きく引き離す逃げを打つ可能性があります。",
            "スタート直後から{horse}が先頭に立ち、マイペースで逃げる展開が予想されます。",
            "{horse}の積極的な逃げが予想され、どこまで粘れるかが注目されます。",
        ],
        '先行_積極': [
            "{horses}は積極的に前のポジションを取りに行き、2-3番手での競馬が予想されます。",
            "{horses}が好位を確保し、直線で先頭を狙う競馬をしそうです。",
            "先行力のある{horses}が前々で競馬を進め、粘り強く走りそうです。",
            "{horses}は番手から虎視眈々と逃げ馬を狙う位置取りになりそうです。",
        ],
        '差し_有利': [
            "ハイペースが予想される今回、{horses}などの差し馬には絶好の展開となりそうです。",
            "{horses}にとっては願ってもない展開で、最後の直線で爆発的な末脚が期待できます。",
            "展開が向きそうな{horses}の末脚に注目が集まります。",
            "{horses}は中団待機から、最後の直線で鋭い脚を使ってきそうです。",
        ],
        '追込_期待': [
            "{horses}などの追込馬も、前がバテる展開を待っています。",
            "最後方から一気の追込を狙う{horses}の末脚次第では激走もありえます。",
            "{horses}は後方一気の戦法で、直線での豪脚に期待がかかります。",
            "展開次第では{horses}の強烈な追込が炸裂する可能性があります。",
        ]
    }

def get_conclusion_templates() -> Dict[str, List[str]]:
    """結論部分の多様なテンプレートを返す"""
    return {
        'ハイペース': [
            "ハイペースの消耗戦が予想され、後方待機組の台頭に期待が持てる展開です。",
            "前半の激しい流れが、後半の大きな展開変化を生みそうです。",
            "スタミナと末脚の両方が求められる、タフなレースになりそうです。",
            "差し・追込馬にとって絶好の展開が予想されます。",
        ],
        'スローペース': [
            "前残りの可能性が高く、逃げ・先行馬を中心とした馬券が面白そうです。",
            "瞬発力勝負になりやすく、キレのある脚を持つ馬に注目です。",
            "前に行った馬が有利な展開で、先行力のある馬を重視したいです。",
            "スローの瞬発力勝負では、位置取りとタイミングが重要になりそうです。",
        ],
        '平均ペース': [
            "バランスの取れた展開で、総合力の高い馬が素直に好走しそうです。",
            "展開の有利不利が少なく、実力通りの結果になる可能性が高いです。",
            "どの脚質にもチャンスがあり、調子の良い馬を見極めることが重要です。",
            "安定感のある馬や、このコースで実績のある馬が狙い目です。",
        ]
    }

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
    
    # デバッグログ追加
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"ViewLogic展開予想 - zenhan_avg: {zenhan_avg}, kohan_avg: {kohan_avg}, pace: {pace}")
    
    # ペース予想セクションを非表示化（スローペース予想が多いため）
    # lines.append("### ペース予想")
    # lines.append("")
    # lines.append(f"**予想ペース: {pace}** （確信度: {confidence}%）")
    # lines.append("")
    # 
    # # ペースに応じた詳細な解説
    # templates = get_pace_templates()
    # 
    # # zenhan_avgが異常に小さい場合（データ不足）は別の表現を使用
    # if zenhan_avg < 20:  # 20秒未満は物理的に不可能
    #     # データが不足している場合の汎用的な表現
    #     if 'ハイペース' in pace:
    #         lines.append(random.choice(templates['ハイペース_intro']))
    #     elif 'スローペース' in pace:
    #         lines.append(random.choice(templates['スローペース_intro']))
    #     else:
    #         lines.append(random.choice(templates['平均ペース_intro']))
    # elif 'ハイペース' in pace:
    #     lines.append(f"前半は速いペースで推移し、{random.choice(templates['ハイペース_intro'])}")
    #     lines.append(random.choice(templates['ハイペース_effect']))
    #     lines.append("後半は前半のペース反動で失速が懸念される展開です。")
    # elif 'スローペース' in pace:
    #     if zenhan_avg >= 20:  # 正常な値の場合のみ抽象表現を使用
    #         lines.append(f"前半は遅めのペースで、{random.choice(templates['スローペース_intro'])}")
    #         lines.append(random.choice(templates['スローペース_effect']))
    #         lines.append("後半は瞬発力勝負になりそうですが、前残りの可能性が高い展開です。")
    #     else:
    #         lines.append(random.choice(templates['スローペース_intro']))
    #         lines.append(random.choice(templates['スローペース_effect']))
    # else:
    #     if zenhan_avg >= 20:  # 正常な値の場合のみ抽象表現を使用
    #         lines.append(f"前半・後半ともに標準的なペースで、{random.choice(templates['平均ペース_intro'])}")
    #         lines.append(random.choice(templates['平均ペース_effect']))
    #     else:
    #         lines.append(random.choice(templates['平均ペース_intro']))
    #         lines.append(random.choice(templates['平均ペース_effect']))
    # lines.append("")
    
    # 脚質別の馬名整理（馬番順）
    detailed_styles = result.get('detailed_styles', {})

    # 各脚質の馬を馬番順に整理
    nige_horses = []
    senko_horses = []
    sashi_horses = []
    oikomi_horses = []

    # 馬番情報を取得してソート用に使用
    horses_data = result.get('horses_data', [])
    horse_to_number = {}
    for horse_data in horses_data:
        if isinstance(horse_data, dict):
            horse_name = horse_data.get('horse_name', '')
            horse_number = horse_data.get('horse_number', 999)  # 馬番がない場合は999
            if horse_name:
                horse_to_number[horse_name] = horse_number

    # 各脚質の馬を収集
    if '逃げ' in detailed_styles:
        for sub_style, horses in detailed_styles['逃げ'].items():
            if horses:
                nige_horses.extend(horses)

    if '先行' in detailed_styles:
        for sub_style, horses in detailed_styles['先行'].items():
            if horses:
                senko_horses.extend(horses)

    if '差し' in detailed_styles:
        for sub_style, horses in detailed_styles['差し'].items():
            if horses:
                sashi_horses.extend(horses)

    if '追込' in detailed_styles:
        for sub_style, horses in detailed_styles['追込'].items():
            if horses:
                oikomi_horses.extend(horses)

    # 馬番順にソート
    nige_horses = sorted(nige_horses, key=lambda x: horse_to_number.get(x, 999))
    senko_horses = sorted(senko_horses, key=lambda x: horse_to_number.get(x, 999))
    sashi_horses = sorted(sashi_horses, key=lambda x: horse_to_number.get(x, 999))
    oikomi_horses = sorted(oikomi_horses, key=lambda x: horse_to_number.get(x, 999))

    # 脚質別馬名を自然な文章に組み込む
    lines.append("### 展開予想の詳細分析")
    lines.append("")

    # ペース展開と脚質構成の説明
    if nige_horses or senko_horses:
        lines.append("#### 前半の隊列形成")
        if nige_horses:
            if len(nige_horses) == 1:
                lines.append(f"スタートから**{nige_horses[0]}**が単騎で逃げを打つ展開が予想されます。")
            else:
                lines.append(f"逃げを狙うのは**{', '.join(nige_horses)}**で、序盤の主導権争いが注目されます。")

        if senko_horses:
            if len(senko_horses) <= 3:
                lines.append(f"先行勢として**{', '.join(senko_horses)}**が好位を確保し、逃げ馬をマークする形になりそうです。")
            else:
                lines.append(f"先行勢は**{', '.join(senko_horses[:3])}**を中心に、{'、'.join(senko_horses[3:])}も前目のポジションを取りに行きそうです。")
        lines.append("")

    # 中団から後方の馬
    if sashi_horses or oikomi_horses:
        lines.append("#### 中団から後方の布陣")
        if sashi_horses:
            if len(sashi_horses) <= 3:
                lines.append(f"中団待機組の**{', '.join(sashi_horses)}**は、前半は脚を溜めて直線での差し脚に賭けます。")
            else:
                lines.append(f"差し馬は**{', '.join(sashi_horses[:3])}**が中心となり、{'、'.join(sashi_horses[3:])}も中団から虎視眈々と上位を狙います。")

        if oikomi_horses:
            if 'ハイペース' in pace:
                lines.append(f"後方から追い込みを狙う**{', '.join(oikomi_horses)}**にとっては、ペースが速くなることで展開利が生まれそうです。")
            else:
                lines.append(f"追い込み勢の**{', '.join(oikomi_horses)}**は後方待機となりますが、展開一つで激走の可能性を秘めています。")
        lines.append("")

    # ペースと脚質の相性分析
    lines.append("#### 展開予想のポイント")
    # ペース予想の文言を削除し、馬の展開分析のみを残す
    # if 'ハイペース' in pace:
    #     if nige_horses or senko_horses:
    #         lines.append(f"ハイペースが予想される中、逃げ・先行勢の{'、'.join(nige_horses[:2] + senko_horses[:2])}は序盤から厳しい流れに巻き込まれそうです。")
    #     if sashi_horses or oikomi_horses:
    #         lines.append(f"この展開は差し・追込馬の{'、'.join(sashi_horses[:2] + oikomi_horses[:1])}にとって絶好の展開となり、直線での末脚勝負が期待されます。")
    # elif 'スローペース' in pace:
    #     if nige_horses:
    #         lines.append(f"スローペースが予想される中、逃げ馬の**{nige_horses[0]}**は楽に逃げられる可能性が高く、粘り込みが期待できます。")
    #     if senko_horses:
    #         lines.append(f"先行勢の{'、'.join(senko_horses[:3])}も前半で脚を使わずに済むため、直線でもしっかりとした脚を使えそうです。")
    # else:
    #     lines.append("ミドルペースでの流れとなりそうで、各馬の地力が試される展開になりそうです。")
    #     if senko_horses:
    #         lines.append(f"このペースは先行馬の{'、'.join(senko_horses[:3])}にとって理想的で、持ち味を発揮しやすい流れとなりそうです。")
    
    # ペースに依存しない展開予想の分析
    if nige_horses:
        lines.append(f"逃げ馬の**{nige_horses[0]}**がどのようなペースを刻むかが展開の鍵となりそうです。")
    if senko_horses:
        lines.append(f"先行勢の{'、'.join(senko_horses[:3])}の位置取りが重要になってきます。")
    if sashi_horses or oikomi_horses:
        lines.append(f"差し・追込馬の{'、'.join(sashi_horses[:2] + oikomi_horses[:1])}は、直線での末脚勝負に持ち込みたいところです。")

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
            if len(corner3_horses) >= 1:
                lines.append(f"3コーナーを迎える頃には、**{corner3_horses[0]}**がリードを保ち、")
            if len(corner3_horses) >= 3:
                lines.append(f"2番手に**{corner3_horses[1]}**、3番手に**{corner3_horses[2]}**という隊列になりそうです。")
            elif len(corner3_horses) >= 2:
                lines.append(f"2番手に**{corner3_horses[1]}**が続く展開になりそうです。")
            if 'ハイペース' in pace:
                lines.append("ペースが速いため、後方待機組が徐々に進出を開始する場面です。")
            lines.append("")
        
        # 終盤の展開
        if 'corner4' in simulation and len(simulation['corner4']) > 0:
            corner4_horses = [entry.get('horse_name', '不明') for entry in simulation['corner4'][:5]]
            lines.append("#### 勝負所（4コーナー）")
            if len(corner4_horses) >= 1:
                lines.append(f"最後の4コーナーでは、**{corner4_horses[0]}**が依然として先頭をキープしていますが、")
            if 'ハイペース' in pace:
                lines.append("ハイペースの影響で脚色が鈍り始め、後続の差し・追込馬が一気に接近してきます。")
                if len(corner4_horses) >= 4:
                    lines.append(f"特に**{corner4_horses[2]}**や**{corner4_horses[3]}**の末脚が注目されます。")
                elif len(corner4_horses) >= 3:
                    lines.append(f"特に**{corner4_horses[2]}**の末脚が注目されます。")
            else:
                if len(corner4_horses) >= 3:
                    lines.append(f"**{corner4_horses[1]}**と**{corner4_horses[2]}**が虎視眈々と逆転を狙っています。")
                elif len(corner4_horses) >= 2:
                    lines.append(f"**{corner4_horses[1]}**が虎視眈々と逆転を狙っています。")
            lines.append("")
        
        # ゴール予想（上位5頭の表示を削除し、展開の流れとして記述）
        if 'finish' in simulation and len(simulation['finish']) > 0:
            finish_horses = [entry.get('horse_name', '不明') for entry in simulation['finish'][:5]]
            lines.append("#### ゴール前の攻防")

            # 展開を自然な文章で表現（順位は明示しない）
            if 'ハイペース' in pace:
                lines.append("ハイペースの流れを活かして、後方待機組が一気に差し切る可能性があります。")
                if len(finish_horses) >= 3:
                    lines.append(f"特に**{finish_horses[0]}**、**{finish_horses[1]}**、**{finish_horses[2]}**あたりの末脚が注目されます。")
            elif 'スローペース' in pace:
                lines.append("スローペースからの瞬発力勝負となり、前残りの可能性も十分にあります。")
                if len(finish_horses) >= 2:
                    lines.append(f"**{finish_horses[0]}**と**{finish_horses[1]}**の叩き合いが予想されます。")
            else:
                lines.append("ミドルペースでの総合力勝負となりそうです。")
                if len(finish_horses) >= 3:
                    lines.append(f"**{finish_horses[0]}**を中心に、**{finish_horses[1]}**、**{finish_horses[2]}**が有力候補となりそうです。")
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
    
    # 結論部分のテンプレート化
    conclusion_templates = get_conclusion_templates()
    lines.append("")
    lines.append("### まとめ")
    if 'ハイペース' in pace:
        lines.append(random.choice(conclusion_templates['ハイペース']))
    elif 'スローペース' in pace:
        lines.append(random.choice(conclusion_templates['スローペース']))
    else:
        lines.append(random.choice(conclusion_templates['平均ペース']))

    # 脚質別馬名の明示的なリストを追加
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### 📊 脚質別出走馬一覧")
    lines.append("")

    # 逃げ馬
    if nige_horses:
        lines.append(f"**逃げ**：{'、'.join(nige_horses)}")
    else:
        lines.append("**逃げ**：該当なし")

    # 先行馬
    if senko_horses:
        lines.append(f"**先行**：{'、'.join(senko_horses)}")
    else:
        lines.append("**先行**：該当なし")

    # 差し馬
    if sashi_horses:
        lines.append(f"**差し**：{'、'.join(sashi_horses)}")
    else:
        lines.append("**差し**：該当なし")

    # 追込馬
    if oikomi_horses:
        lines.append(f"**追込**：{'、'.join(oikomi_horses)}")
    else:
        lines.append("**追込**：該当なし")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*このレース展開予想は、過去のレースデータと各馬の脚質傾向を基に、ViewLogicエンジンが算出したものです。*")
    lines.append("*実際のレースでは、当日の馬場状態や各馬のコンディションにより、予想と異なる展開になる可能性があります。*")
    
    return "\n".join(lines)