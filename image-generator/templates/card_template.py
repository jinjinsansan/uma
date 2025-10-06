from typing import Dict, Any, List, Optional
import json

def generate_card_html(card_data: Dict[str, Any]) -> str:
    """
    カードデータからHTMLを生成
    
    Args:
        card_data: カードデータ（raceMeta, analyses, userNote, hashtags, generatedAt）
        
    Returns:
        完全なHTML文字列
    """
    race_meta = card_data.get('raceMeta', {})
    analyses = card_data.get('analyses', [])
    user_note = card_data.get('userNote')
    hashtags = card_data.get('hashtags', [])
    generated_at = card_data.get('generatedAt')
    referral_url = card_data.get('referralUrl')
    
    # 最初の分析データから馬情報を取得
    top_pick = None
    if analyses:
        analysis = analyses[0]
        engine = analysis.get('engine', 'imlogic')
        data = analysis.get('data', {})
        top_pick = extract_top_pick(engine, data)
    
    # HTMLを生成
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                margin: 0; 
                background: #0B0E11; 
                font-family: "Noto Sans JP", "Inter", sans-serif; 
                color: #EAECEF;
                -webkit-font-smoothing: antialiased;
            }}
        </style>
    </head>
    <body>
        {generate_card_body(race_meta, top_pick, user_note, hashtags, generated_at, referral_url)}
    </body>
    </html>
    """
    
    return html

def extract_top_pick(engine: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """エンジンタイプに応じてトップピックを抽出"""
    
    if engine == 'imlogic':
        results = data.get('results', data.get('scores', []))
        if not results or not isinstance(results, list):
            return None
        
        sorted_results = sorted(
            [r for r in results if r and r.get('has_data') != False],
            key=lambda x: x.get('rank', 9999)
        )
        
        if not sorted_results:
            return None
        
        top = sorted_results[0]
        return {
            'engine': 'imlogic',
            'label': 'IM-LOGIC',
            'horseName': top.get('horse') or top.get('horse_name', '不明'),
            'badge': f"RANK {top.get('rank', 1)}",
            'highlight': f"総合 {top.get('total_score', 0):.1f}点" if top.get('total_score') else None,
            'description': format_imlogic_scores(top)
        }
    
    elif engine == 'ilogic':
        results = data.get('results', [])
        if not results:
            return None
        
        sorted_results = sorted(
            [r for r in results if r and r.get('has_data') != False],
            key=lambda x: x.get('rank', 9999)
        )
        
        if not sorted_results:
            return None
        
        top = sorted_results[0]
        return {
            'engine': 'ilogic',
            'label': 'I-LOGIC',
            'horseName': top.get('horse') or top.get('horse_name', '不明'),
            'badge': f"RANK {top.get('rank', 1)}",
            'highlight': f"総合 {top.get('total_score', 0):.1f}点" if top.get('total_score') else None,
            'description': f"騎手 {top.get('jockey') or top.get('jockey_name', '')}" if top.get('jockey') or top.get('jockey_name') else None
        }
    
    elif engine == 'dlogic':
        scores = data.get('scores', {})
        if not scores or not isinstance(scores, dict):
            return None
        
        entries = [
            {'horse': horse, **info}
            for horse, info in scores.items()
            if info and not isinstance(info.get('score'), type(None))
        ]
        
        sorted_entries = sorted(entries, key=lambda x: float(x.get('score', 0)), reverse=True)
        
        if not sorted_entries:
            return None
        
        top = sorted_entries[0]
        return {
            'engine': 'dlogic',
            'label': 'D-LOGIC',
            'horseName': top.get('horse', '不明'),
            'badge': f"RANK {top.get('rank', 1)}",
            'highlight': f"総合 {float(top.get('score', 0)):.1f}点" if top.get('score') else None,
            'description': format_dlogic_details(top)
        }
    
    elif engine == 'nlogic':
        # N-LOGICの処理: predictionsはオブジェクト形式（辞書）
        predictions = data.get('predictions', {})
        
        if not predictions or not isinstance(predictions, dict):
            return None
        
        # オブジェクトをリストに変換してrankでソート
        entries = [
            {'horse': horse, **info}
            for horse, info in predictions.items()
            if info and isinstance(info, dict)
        ]
        
        # rankでソート
        sorted_entries = sorted(
            [e for e in entries if e.get('rank') is not None],
            key=lambda x: int(x.get('rank', 9999))
        )
        
        if not sorted_entries:
            return None
        
        top = sorted_entries[0]
        
        # 勝率を取得（support_rateを100倍してパーセント表示）
        support_rate = top.get('support_rate')
        highlight_text = f"勝率 {float(support_rate) * 100:.1f}%" if support_rate else None
        
        # オッズを取得
        odds = top.get('odds') or top.get('fair_odds')
        description_text = f"予測オッズ {float(odds):.1f}倍" if odds else None
        
        return {
            'engine': 'nlogic',
            'label': 'N-LOGIC',
            'horseName': top.get('horse', '不明'),
            'badge': f"RANK {top.get('rank', 1)}",
            'highlight': highlight_text,
            'description': description_text
        }
    
    elif engine == 'flogic':
        rankings = data.get('rankings', [])
        if not rankings or not isinstance(rankings, list):
            return None
        
        top = rankings[0] if rankings else None
        if not top:
            return None
        
        signal = top.get('investment_signal') or top.get('value_rating')
        expected_value = top.get('expected_value')
        odds_divergence = top.get('odds_divergence')
        
        description_parts = []
        if expected_value is not None:
            description_parts.append(f"期待値 {float(expected_value):.2f}")
        if odds_divergence is not None:
            description_parts.append(f"乖離 {float(odds_divergence):.2f}倍")
        
        return {
            'engine': 'flogic',
            'label': 'F-Logic',
            'horseName': top.get('horse', '不明'),
            'badge': 'RANK 1',
            'highlight': f"投資判断 {signal}" if signal else None,
            'description': ' / '.join(description_parts) if description_parts else None
        }
    
    elif engine == 'metalogic':
        rankings = data.get('rankings', [])
        if not rankings or not isinstance(rankings, list):
            return None
        
        top = rankings[0] if rankings else None
        if not top:
            return None
        
        score = top.get('meta_score') or top.get('score')
        contributions = top.get('details', {})
        values = []
        for key in ['d_logic', 'i_logic', 'view_logic']:
            val = contributions.get(key)
            if val is not None:
                values.append(f"{float(val):.1f}")
        
        return {
            'engine': 'metalogic',
            'label': 'Meta-Logic',
            'horseName': top.get('horse', '不明'),
            'badge': f"RANK {top.get('rank', 1)}",
            'highlight': f"メタスコア {float(score):.2f}点" if score is not None else None,
            'description': f"構成 {'/'.join(values)}" if values else None
        }
    
    elif engine == 'viewlogic':
        data_type = str(data.get('type') or data.get('analysis_type') or data.get('analysisType') or '')
        
        # betting_recommendation type
        if data_type == 'betting_recommendation' or 'recommendations' in data:
            recommendations = data.get('recommendations', [])
            if not recommendations or not isinstance(recommendations, list):
                return None
            
            top = recommendations[0]
            ticket = top.get('ticket_type') or top.get('type', '推奨馬券')
            horses = top.get('horses')
            if isinstance(horses, list):
                horses = ' - '.join(horses)
            confidence = top.get('confidence')
            
            return {
                'engine': 'viewlogic',
                'label': 'View-Logic',
                'horseName': horses or '推奨馬券',
                'badge': str(ticket),
                'highlight': f"信頼度 {confidence}%" if confidence else None,
                'description': top.get('reason')
            }
        
        # data_analysis type
        if data_type == 'data_analysis' or 'top_horses' in data:
            top_horses = data.get('top_horses', [])
            if not top_horses or not isinstance(top_horses, list):
                return None
            
            top = top_horses[0]
            if isinstance(top, list):
                horse, rate = top[0], top[1] if len(top) > 1 else None
                return {
                    'engine': 'viewlogic',
                    'label': 'View-Logic',
                    'horseName': str(horse) if horse else '不明',
                    'badge': 'TOP HORSE',
                    'highlight': f"複勝率 {float(rate) * 100:.1f}%" if rate is not None else None,
                    'description': None
                }
            elif isinstance(top, str):
                return {
                    'engine': 'viewlogic',
                    'label': 'View-Logic',
                    'horseName': top,
                    'badge': 'TOP HORSE',
                    'highlight': None,
                    'description': None
                }
        
        return None
    
    # 他のエンジンタイプも同様に実装...
    return None

def format_imlogic_scores(data: Dict[str, Any]) -> Optional[str]:
    """IM-LOGICのスコア表示をフォーマット"""
    parts = []
    if data.get('horse_score'):
        parts.append(f"馬 {data['horse_score']:.1f}")
    if data.get('jockey_score'):
        parts.append(f"騎手 {data['jockey_score']:.1f}")
    return ' / '.join(parts) if parts else None

def format_dlogic_details(data: Dict[str, Any]) -> Optional[str]:
    """D-LOGICの詳細スコアをフォーマット"""
    details = data.get('details', {})
    if not details:
        return None
    
    # 最高スコアの項目を取得
    sorted_details = sorted(
        [(k, v) for k, v in details.items() if v and not isinstance(v, type(None))],
        key=lambda x: float(x[1]),
        reverse=True
    )
    
    if sorted_details:
        key, value = sorted_details[0]
        label = translate_dlogic_key(key)
        return f"{label} {float(value):.1f}点"
    
    return None

def translate_dlogic_key(key: str) -> str:
    """D-LOGICのキーを日本語に変換"""
    mapping = {
        # 番号付きキー（新フォーマット）
        '1_distance_aptitude': '距離適性',
        '2_bloodline_evaluation': '血統評価',
        '3_jockey_compatibility': '騎手相性',
        '4_trainer_evaluation': '厩舎評価',
        '5_track_aptitude': '馬場適性',
        '6_weather_aptitude': '天候適性',
        '7_popularity_factor': '人気影響',
        '8_weight_impact': '斤量影響',
        '9_horse_weight_impact': '馬体重影響',
        '10_corner_specialist_degree': 'コーナー巧者度',
        '11_margin_analysis': '着差分析',
        '12_time_index': 'タイム指数',
        # 番号なしキー（旧フォーマット対応）
        'distance_aptitude': '距離適性',
        'bloodline_evaluation': '血統評価',
        'jockey_compatibility': '騎手相性',
        'trainer_evaluation': '厩舎評価',
        'track_aptitude': '馬場適性',
        'weather_aptitude': '天候適性',
        'popularity_factor': '人気影響',
        'weight_impact': '斤量影響',
        'horse_weight_impact': '馬体重影響',
        'corner_specialist_degree': 'コーナー巧者度',
        'margin_analysis': '着差分析',
        'time_index': 'タイム指数',
        # その他のキー
        'course_record': 'コース実績',
        'recent_form': '近走成績',
        'pace_suitability': 'ペース適性',
        'race_spacing': '間隔適性',
        'field_suitability': '馬場適性',
        'class_performance': 'クラス実績',
        'consistency': '安定性'
    }
    return mapping.get(key, key)

def generate_card_body(
    race_meta: Dict[str, Any],
    top_pick: Optional[Dict[str, Any]],
    user_note: Optional[str],
    hashtags: List[str],
    generated_at: Optional[str],
    referral_url: Optional[str] = None
) -> str:
    """カードのボディ部分を生成"""
    
    # エンジンごとの色設定
    color_map = {
        'imlogic': {'border': '#EAB308', 'text': '#FCD34D', 'gradient': 'linear-gradient(to right, #FACC15, #EAB308)', 'shadow': '#FACC15'},
        'ilogic': {'border': '#2563EB', 'text': '#60A5FA', 'gradient': 'linear-gradient(to right, #60A5FA, #2563EB)', 'shadow': '#60A5FA'},
        'dlogic': {'border': '#059669', 'text': '#34D399', 'gradient': 'linear-gradient(to right, #34D399, #059669)', 'shadow': '#34D399'},
        'flogic': {'border': '#EC4899', 'text': '#F472B6', 'gradient': 'linear-gradient(to right, #F472B6, #EC4899)', 'shadow': '#EC4899'},
        'metalogic': {'border': '#EF4444', 'text': '#F97316', 'gradient': 'linear-gradient(to right, #F97316, #EF4444)', 'shadow': '#EF4444'},
        'nlogic': {'border': '#7C3AED', 'text': '#A855F7', 'gradient': 'linear-gradient(to right, #A855F7, #7C3AED)', 'shadow': '#7C3AED'},
        'viewlogic': {'border': '#0EA5E9', 'text': '#38BDF8', 'gradient': 'linear-gradient(to right, #38BDF8, #0EA5E9)', 'shadow': '#0EA5E9'}
    }
    
    colors = color_map.get(top_pick.get('engine') if top_pick else 'imlogic', color_map['imlogic'])
    
    return f"""
    <div data-share-card style="
        margin: 0 auto;
        display: flex;
        width: 1200px;
        flex-direction: column;
        gap: 20px;
        border-radius: 32px;
        border: 1px solid #1C2534;
        background: linear-gradient(to bottom, #070B12, #05070A, #020305);
        padding: 32px 36px;
        color: #EAECEF;
        box-shadow: 0 40px 120px rgba(0,0,0,0.45);
    ">
        {generate_header(race_meta)}
        {generate_prediction_section(top_pick, colors) if top_pick else '<div>No prediction available</div>'}
        {generate_user_note_section(user_note) if user_note else ''}
        {generate_footer(hashtags, generated_at, referral_url)}
    </div>
    """

def generate_header(race_meta: Dict[str, Any]) -> str:
    """ヘッダー部分を生成"""
    venue = str(race_meta.get('venue', '')) if race_meta.get('venue') else ''
    race_number = str(race_meta.get('raceNumber', '')) if race_meta.get('raceNumber') else ''
    race_name = str(race_meta.get('raceName', '')) if race_meta.get('raceName') else ''
    date = str(race_meta.get('date', '')) if race_meta.get('date') else ''
    distance = str(race_meta.get('distance', '')) if race_meta.get('distance') else ''
    
    return f"""
    <header style="display: flex; flex-direction: column; gap: 16px;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="display: inline-flex; align-items: center; gap: 8px; border-radius: 9999px; border: 1px solid rgba(240,185,11,0.4); background: rgba(240,185,11,0.1); padding: 4px 16px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.45em; color: #F0B90B;">
                競馬予想AI D-logic
            </span>
            <span style="border-radius: 9999px; border: 1px solid #1F2633; background: rgba(11,14,17,0.8); padding: 4px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.3em; color: #94A3B8;">
                Prediction Card
            </span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 4px; text-align: left;">
            {f'<p style="font-size: 26px; font-weight: 600; color: white; line-height: 1.25;">{venue}{f" {race_number}R" if race_number else ""}</p>' if venue else ''}
            {f'<p style="font-size: 42px; font-weight: 600; color: white; line-height: 1.2;">{race_name}</p>' if race_name else ''}
            {f'<p style="font-size: 20px; color: #A3A9B7; line-height: 1.625;">{" / ".join([x for x in [date, distance] if x])}</p>' if date or distance else ''}
        </div>
    </header>
    """

def generate_prediction_section(top_pick: Dict[str, Any], colors: Dict[str, str]) -> str:
    """予想セクションを生成"""
    return f"""
    <section style="position: relative; overflow: hidden; border-radius: 28px; border: 1px solid #1F2733; background: #080C13; padding: 24px;">
        <div style="pointer-events: none; position: absolute; left: -40px; top: -96px; height: 208px; width: 208px; border-radius: 9999px; background: rgba(240,185,11,0.1); filter: blur(48px);"></div>
        <div style="pointer-events: none; position: absolute; bottom: 0; right: 0; height: 192px; width: 192px; border-radius: 9999px; background: rgba(44,53,68,0.4); filter: blur(48px);"></div>
        
        <div style="position: relative; display: flex; flex-direction: column; align-items: center; gap: 24px;">
            <div style="text-align: center;">
                <p style="font-size: 18px; text-transform: uppercase; letter-spacing: 0.4em; color: #94A3B8;">ENGINE TOP PICK</p>
                <p style="margin-top: 8px; font-size: 28px; font-weight: 600; color: white; white-space: nowrap;">
                    {top_pick.get('label', '')} 1位予想
                </p>
            </div>
            
            <div style="display: flex; justify-content: center; width: 100%;">
                <div style="position: relative; display: flex; flex-direction: column; align-items: center; gap: 20px; border-radius: 28px; border: 1px solid {colors['border']}; background: linear-gradient(to bottom, #0E141F, #0B101A, #070B12); padding: 48px 40px; text-align: center; width: 100%; max-width: 512px; box-shadow: 0 0 40px {colors['shadow']}33;">
                    <span style="display: inline-flex; align-items: center; justify-content: center; border-radius: 9999px; background: {colors['gradient']}; padding: 8px 24px; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.35em; color: black; box-shadow: 0 10px 25px rgba(0,0,0,0.35); white-space: nowrap;">
                        {top_pick.get('label', '')}
                    </span>
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 16px;">
                        <p style="font-size: 24px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.35em;">
                            {top_pick.get('badge', 'TOP PICK')}
                        </p>
                        <p style="font-size: 48px; font-weight: 700; color: white; line-height: 1.25; max-width: 100%; word-break: keep-all; overflow-wrap: break-word;">
                            {top_pick.get('horseName', '不明')}
                        </p>
                        {f'<p style="font-size: 36px; font-weight: 600; color: {colors["text"]}; line-height: 1.25;">{top_pick.get("highlight")}</p>' if top_pick.get('highlight') else ''}
                        {f'<p style="max-width: 420px; font-size: 24px; color: #A0AEC0; line-height: 1.625;">{top_pick.get("description")}</p>' if top_pick.get('description') else ''}
                    </div>
                </div>
            </div>
        </div>
    </section>
    """

def generate_user_note_section(user_note: str) -> str:
    """ユーザーメモセクションを生成"""
    # HTMLエスケープ
    escaped_note = str(user_note).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return f"""
    <section style="border-radius: 24px; border: 1px solid #1F2733; background: #080C13; padding: 28px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
            <p style="font-size: 20px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3em; color: #FACC15;">MY NOTE</p>
            <span style="font-size: 16px; text-transform: uppercase; letter-spacing: 0.3em; color: #3C4454;">USER MEMO</span>
        </div>
        <p style="white-space: pre-wrap; font-size: 28px; font-weight: 600; line-height: 1.75; color: #FFFFFF;">
            {escaped_note}
        </p>
    </section>
    """

def generate_footer(hashtags: List[str], generated_at: Optional[str], referral_url: Optional[str] = None) -> str:
    """フッター部分を生成"""
    hashtag_line = ' '.join([f"#{tag}" if not tag.startswith('#') else tag for tag in hashtags]) if hashtags else '#Dlogic #競馬予想AI #競馬予想'
    generated_text = f"Shared {generated_at}" if generated_at else "Generated with D-Logic AI Predictions"
    
    # 招待URL行を事前に生成（f-stringのネストを回避）
    referral_line = ''
    if referral_url:
        referral_line = f'<p style="font-size: 18px; text-transform: none; letter-spacing: 0; color: #0ECB81; font-weight: 600;">{referral_url}</p>'
    
    return f"""
    <footer style="display: flex; flex-direction: column; gap: 6px; font-size: 16px; text-transform: uppercase; letter-spacing: 0.3em; color: #6B7280;">
        <p>{hashtag_line}</p>
        {referral_line}
        <p>{generated_text}</p>
    </footer>
    """
