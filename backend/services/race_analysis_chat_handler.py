"""
レースアナリシス用チャットハンドラー
レース名から自動的にレース情報を取得し、総合分析を行う
"""
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from .race_analysis_engine import race_analysis_engine
from .archive_race_fetcher import archive_fetcher
from .mock_archive_data import get_mock_race_data, search_mock_races_by_name

logger = logging.getLogger(__name__)

class RaceAnalysisChatHandler:
    """レースアナリシス用のチャット処理"""
    
    def __init__(self):
        """初期化"""
        # 主要レース辞書（開催場・距離・クラス情報）
        self.race_dictionary = {
            # G1レース
            "フェブラリーS": {"venue": "東京", "distance": "1600m", "grade": "G1", "full_name": "フェブラリーステークス"},
            "高松宮記念": {"venue": "中京", "distance": "1200m", "grade": "G1"},
            "大阪杯": {"venue": "阪神", "distance": "2000m", "grade": "G1"},
            "桜花賞": {"venue": "阪神", "distance": "1600m", "grade": "G1"},
            "皐月賞": {"venue": "中山", "distance": "2000m", "grade": "G1"},
            "天皇賞春": {"venue": "京都", "distance": "3200m", "grade": "G1", "full_name": "天皇賞（春）"},
            "NHKマイルC": {"venue": "東京", "distance": "1600m", "grade": "G1", "full_name": "NHKマイルカップ"},
            "ヴィクトリアマイル": {"venue": "東京", "distance": "1600m", "grade": "G1"},
            "オークス": {"venue": "東京", "distance": "2400m", "grade": "G1"},
            "日本ダービー": {"venue": "東京", "distance": "2400m", "grade": "G1", "full_name": "東京優駿"},
            "安田記念": {"venue": "東京", "distance": "1600m", "grade": "G1"},
            "宝塚記念": {"venue": "阪神", "distance": "2200m", "grade": "G1"},
            "スプリンターズS": {"venue": "中山", "distance": "1200m", "grade": "G1", "full_name": "スプリンターズステークス"},
            "秋華賞": {"venue": "京都", "distance": "2000m", "grade": "G1"},
            "菊花賞": {"venue": "京都", "distance": "3000m", "grade": "G1"},
            "天皇賞秋": {"venue": "東京", "distance": "2000m", "grade": "G1", "full_name": "天皇賞（秋）"},
            "エリザベス女王杯": {"venue": "京都", "distance": "2200m", "grade": "G1"},
            "マイルCS": {"venue": "京都", "distance": "1600m", "grade": "G1", "full_name": "マイルチャンピオンシップ"},
            "ジャパンC": {"venue": "東京", "distance": "2400m", "grade": "G1", "full_name": "ジャパンカップ"},
            "チャンピオンズC": {"venue": "中京", "distance": "1800m", "grade": "G1", "full_name": "チャンピオンズカップ"},
            "阪神JF": {"venue": "阪神", "distance": "1600m", "grade": "G1", "full_name": "阪神ジュベナイルフィリーズ"},
            "朝日杯FS": {"venue": "阪神", "distance": "1600m", "grade": "G1", "full_name": "朝日杯フューチュリティステークス"},
            "有馬記念": {"venue": "中山", "distance": "2500m", "grade": "G1"},
            "ホープフルS": {"venue": "中山", "distance": "2000m", "grade": "G1", "full_name": "ホープフルステークス"},
            
            # G2レース（主要なもの）
            "弥生賞": {"venue": "中山", "distance": "2000m", "grade": "G2", "full_name": "弥生賞ディープインパクト記念"},
            "京都記念": {"venue": "京都", "distance": "2200m", "grade": "G2"},
            "中山記念": {"venue": "中山", "distance": "1800m", "grade": "G2"},
            "金鯱賞": {"venue": "中京", "distance": "2000m", "grade": "G2"},
            "日経新春杯": {"venue": "京都", "distance": "2400m", "grade": "G2"},
            "京王杯SC": {"venue": "東京", "distance": "1400m", "grade": "G2", "full_name": "京王杯スプリングカップ"},
            "青葉賞": {"venue": "東京", "distance": "2400m", "grade": "G2"},
            "フローラS": {"venue": "東京", "distance": "2000m", "grade": "G2", "full_name": "フローラステークス"},
            "札幌記念": {"venue": "札幌", "distance": "2000m", "grade": "G2"},
            "オールカマー": {"venue": "中山", "distance": "2200m", "grade": "G2"},
            "神戸新聞杯": {"venue": "阪神", "distance": "2400m", "grade": "G2"},
            "セントライト記念": {"venue": "中山", "distance": "2200m", "grade": "G2"},
            "府中牝馬S": {"venue": "東京", "distance": "1800m", "grade": "G2", "full_name": "府中牝馬ステークス"},
            "毎日王冠": {"venue": "東京", "distance": "1800m", "grade": "G2"},
            
            # G3レース（有名なもの）
            "中山金杯": {"venue": "中山", "distance": "2000m", "grade": "G3"},
            "京都金杯": {"venue": "京都", "distance": "1600m", "grade": "G3"},
            "フェアリーS": {"venue": "中山", "distance": "1600m", "grade": "G3", "full_name": "フェアリーステークス"},
            "シンザン記念": {"venue": "京都", "distance": "1600m", "grade": "G3"},
            "ファルコンS": {"venue": "中京", "distance": "1400m", "grade": "G3", "full_name": "ファルコンステークス"},
            "共同通信杯": {"venue": "東京", "distance": "1800m", "grade": "G3"},
            "クイーンC": {"venue": "東京", "distance": "1600m", "grade": "G3", "full_name": "クイーンカップ"},
            "アーリントンC": {"venue": "阪神", "distance": "1600m", "grade": "G3", "full_name": "アーリントンカップ"},
            "チューリップ賞": {"venue": "阪神", "distance": "1600m", "grade": "G3"},
            "中日新聞杯": {"venue": "中京", "distance": "2000m", "grade": "G3"},
            "小倉記念": {"venue": "小倉", "distance": "2000m", "grade": "G3"},
            "関屋記念": {"venue": "新潟", "distance": "1600m", "grade": "G3"},
            "北九州記念": {"venue": "小倉", "distance": "1200m", "grade": "G3"},
            "新潟記念": {"venue": "新潟", "distance": "2000m", "grade": "G3"},
            "京成杯AH": {"venue": "中山", "distance": "1600m", "grade": "G3", "full_name": "京成杯オータムハンデキャップ"},
            "シリウスS": {"venue": "阪神", "distance": "2000m", "grade": "G3", "full_name": "シリウスステークス"},
            "武蔵野S": {"venue": "東京", "distance": "1600m", "grade": "G3", "full_name": "武蔵野ステークス"},
            "福島記念": {"venue": "福島", "distance": "2000m", "grade": "G3"},
            "アンドロメダS": {"venue": "京都", "distance": "2000m", "grade": "G3", "full_name": "アンドロメダステークス"},
            "チャレンジC": {"venue": "阪神", "distance": "1800m", "grade": "G3", "full_name": "チャレンジカップ"},
            "ターコイズS": {"venue": "中山", "distance": "1600m", "grade": "G3", "full_name": "ターコイズステークス"},
            "中山大障害": {"venue": "中山", "distance": "4100m", "grade": "J-G1"},
        }
        
        # アーカイブフェッチャーを設定
        self.archive_fetcher = archive_fetcher
        
    def is_race_analysis_request(self, message: str) -> bool:
        """レースアナリシス要求かどうかを判定"""
        # レース名が含まれているかチェック
        for race_name in self.race_dictionary.keys():
            if race_name in message:
                return True
        
        # パターンマッチング
        race_patterns = [
            r'(.*記念|.*賞|.*ステークス|.*カップ|.*マイル|.*トロフィー|.*S).*分析',
            r'(.*記念|.*賞|.*ステークス|.*カップ|.*マイル|.*トロフィー|.*S).*予想',
            r'.*レース.*分析',
            r'.*レース.*予想',
            r'今週の.*を分析',
            r'明日の.*を分析',
        ]
        
        for pattern in race_patterns:
            if re.search(pattern, message):
                return True
        
        return False
    
    def extract_race_info(self, message: str) -> Optional[Dict[str, Any]]:
        """メッセージからレース情報を抽出"""
        # 日付の抽出
        date_match = re.search(r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)', message)
        race_date = None
        if date_match:
            date_str = date_match.group(1)
            # 日付形式を統一
            date_str = re.sub(r'[年月]', '-', date_str).replace('日', '')
            try:
                race_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            except:
                pass
        
        # レース名の抽出と情報取得
        for race_name, race_info in self.race_dictionary.items():
            if race_name in message:
                return {
                    'race_name': race_info.get('full_name', race_name),
                    'venue': race_info['venue'],
                    'distance': race_info['distance'],
                    'grade': race_info['grade'],
                    'race_date': race_date or datetime.now().strftime('%Y-%m-%d'),
                    'found_in_dictionary': True
                }
        
        # 辞書にない場合は基本情報のみ
        return None
    
    def get_race_data_from_archive(self, race_date: str, venue: str, race_name: str) -> Optional[Dict[str, Any]]:
        """アーカイブからレースデータを取得"""
        logger.info(f"アーカイブからデータ取得を試みます: {race_date} {venue} {race_name}")
        
        # まずモックデータから検索（開発用）
        matching_races = search_mock_races_by_name(race_name, race_date)
        
        if matching_races:
            # 開催場が一致するものを優先
            for race in matching_races:
                if race.get('venue') == venue:
                    logger.info(f"モックデータから見つかりました: {race_name}")
                    return race
            
            # 開催場が一致しない場合は最初のものを返す
            logger.info(f"モックデータから見つかりました（別開催場）: {race_name}")
            return matching_races[0]
        
        # アーカイブフェッチャーも試す
        matching_races = self.archive_fetcher.search_race_by_name(race_name, race_date)
        
        if matching_races:
            # 開催場が一致するものを優先
            for race in matching_races:
                if race.get('venue') == venue:
                    return race
            
            # 開催場が一致しない場合は最初のものを返す
            return matching_races[0]
        
        # レース番号での検索も試みる（レース名から番号を抽出）
        race_number_match = re.search(r'(\d+)R', race_name)
        if race_number_match:
            race_number = int(race_number_match.group(1))
            
            # モックデータから取得を試みる
            mock_data = get_mock_race_data(race_date, venue, race_number)
            if mock_data:
                logger.info(f"モックデータから見つかりました（番号検索）: {venue} {race_number}R")
                return mock_data
            
            # アーカイブフェッチャーも試す
            race_data = self.archive_fetcher.get_race_data(race_date, venue, race_number)
            if race_data:
                return race_data
        
        return None
    
    def format_analysis_response(self, analysis_result: Dict[str, Any]) -> str:
        """分析結果をフォーマット"""
        if 'error' in analysis_result:
            return f"エラーが発生しました: {analysis_result['error']}"
        
        race_info = analysis_result.get('race_info', {})
        results = analysis_result.get('results', [])
        summary = analysis_result.get('summary', {})
        
        # ヘッダー
        response = f"🏆 I-Logic分析 - {race_info.get('race_name', 'レース')}\n"
        response += f"📍 {race_info.get('venue', '')} {race_info.get('distance', '')} "
        if race_info.get('grade'):
            response += f"【{race_info.get('grade')}】"
        response += "\n"
        response += f"🌤️ 馬場状態: {race_info.get('track_condition', '良')}\n"
        response += "=" * 50 + "\n\n"
        
        # ベース馬の説明
        response += "📊 分析基準: イクイノックス（100点）\n"
        response += "⚖️ 評価比率: 馬70% × 騎手30%\n\n"
        
        # 上位5頭の結果
        response += "🏇 総合評価ランキング\n"
        response += "-" * 40 + "\n"
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, result in enumerate(results[:5]):
            medal = medals[i] if i < 5 else f"{i+1}位"
            
            response += f"\n{medal} {result['rank']}位: {result['horse']} × {result['jockey']} "
            response += f"【{result['total_score']:.1f}点】\n"
            
            # 詳細情報
            response += f"   馬: {result['horse_score']:.1f}点"
            horse_details = result.get('horse_details', {})
            if horse_details.get('venue_distance_bonus', 0) != 0:
                response += f"（基準{horse_details.get('base', 0):.1f}"
                if horse_details.get('venue_distance_bonus', 0) > 0:
                    response += f" + 開催場{horse_details.get('venue_distance_bonus', 0):+.1f}"
                else:
                    response += f" - 開催場{abs(horse_details.get('venue_distance_bonus', 0)):.1f}"
                
                class_factor = horse_details.get('class_factor', 1.0)
                if class_factor != 1.0:
                    response += f" × クラス{class_factor:.2f}"
                response += "）"
            response += "\n"
            
            response += f"   騎手: {result['jockey_score']:+.1f}点"
            jockey_details = result.get('jockey_details', {})
            if any([jockey_details.get('venue', 0), jockey_details.get('post', 0)]):
                response += "（"
                parts = []
                if jockey_details.get('venue', 0) != 0:
                    parts.append(f"開催場{jockey_details.get('venue', 0):+.1f}")
                if jockey_details.get('post', 0) != 0:
                    parts.append(f"枠順{jockey_details.get('post', 0):+.1f}")
                response += " + ".join(parts)
                response += "）"
            response += "\n"
        
        # サマリー情報
        if summary and summary.get('top_horse'):
            response += "\n" + "=" * 50 + "\n"
            response += "💡 分析ポイント\n"
            
            top_horse = summary['top_horse']
            if top_horse.get('advantage'):
                response += f"◆ {top_horse['name']}の強み: "
                response += "、".join(top_horse['advantage'])
                response += "\n"
            
            if summary.get('venue_specialists'):
                response += "\n◆ 開催場巧者:\n"
                for specialist in summary['venue_specialists'][:3]:
                    response += f"  - {specialist['horse']}: {specialist['record']}\n"
            
            if summary.get('key_points'):
                response += "\n◆ 注目ポイント:\n"
                for point in summary['key_points']:
                    response += f"  - {point}\n"
        
        response += "\n" + "=" * 50 + "\n"
        response += "💬 この分析はイクイノックスを基準とした新方式です\n"
        response += "📝 従来のD-Logic分析も併用することをお勧めします"
        
        return response
    
    def process_race_analysis_request(self, message: str) -> Optional[Dict[str, Any]]:
        """レースアナリシスリクエストを処理"""
        # レース情報を抽出
        race_info = self.extract_race_info(message)
        
        if not race_info:
            return {
                'type': 'race_analysis_error',
                'message': "レース名を認識できませんでした。主要なレース名を含めてもう一度お試しください。"
            }
        
        # アーカイブからレースデータを取得
        race_data = self.get_race_data_from_archive(
            race_info['race_date'],
            race_info['venue'],
            race_info['race_name']
        )
        
        if not race_data:
            return {
                'type': 'race_analysis_info',
                'message': f"{race_info['race_name']}（{race_info['venue']} {race_info['distance']}）の分析を行います。\n"
                          f"出走馬情報がアーカイブにない場合は、出走馬リストをお教えください。",
                'race_info': race_info
            }
        
        # レース分析を実行
        analysis_result = race_analysis_engine.analyze_race(race_data)
        
        # 結果をフォーマット
        formatted_response = self.format_analysis_response(analysis_result)
        
        return {
            'type': 'race_analysis_result',
            'message': formatted_response,
            'raw_data': analysis_result
        }

# グローバルインスタンス
race_analysis_chat_handler = RaceAnalysisChatHandler()