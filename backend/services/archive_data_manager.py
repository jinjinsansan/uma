"""
アーカイブレースデータ管理
フロントエンドと同期したアーカイブデータを管理
"""
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ArchiveDataManager:
    """アーカイブレースデータの管理"""
    
    def __init__(self):
        # アーカイブデータ（実際のフロントエンドデータと同期）
        self.archive_data = {
            "2025-08-16": {
                "新潟": {
                    6: {
                        "race_name": "中郷T",
                        "distance": "1400m",
                        "track_condition": "良",
                        "horses": [
                            "イージーブリージー", "エストゥペンダ", "キューティリップ", "クライスレリアーナ",
                            "ニシノコマチムスメ", "フォーカルフラワー", "ペプロス", "ホーリーノット",
                            "メランジェ", "ラルンエベール", "レイユール"
                        ],
                        "jockeys": [
                            "菊沢一樹", "戸崎圭太", "江田照男", "津村明秀",
                            "今村聖奈", "田辺裕信", "荻野極", "北村友一",
                            "丸山元気", "川端海翼", "横山琉人"
                        ],
                        "posts": [1, 1, 2, 3, 3, 4, 5, 6, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                    },
                    7: {
                        "race_name": "糸魚川特別",
                        "distance": "1800m",
                        "track_condition": "良",
                        "horses": [
                            "メランジェ", "サクセスミノル", "ゼットレヨン", "ウォーターアンク",
                            "ナムラハイドラ", "ジャスティンエース", "モカラ", "ツキニホエル",
                            "ブラックジャッカル", "スカイトレイル", "ロードラスター"
                        ],
                        "jockeys": [
                            "丸山元気", "田中健", "西塚洸二", "内田博幸",
                            "鮫島克駿", "江田照男", "杉原誠人", "武藤雅",
                            "角田大河", "荻野極", "北村友一"
                        ],
                        "posts": [1, 1, 2, 3, 4, 5, 5, 6, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                    },
                    8: {
                        "race_name": "3歳以上1勝クラス",
                        "distance": "1200m",
                        "track_condition": "良",
                        "horses": [
                            "クールムーア", "アッティーヴォ", "レベルアップ", "クリノクリスタル",
                            "エイシンヤプ", "アオイフェリーチェ", "プランドルアップ", "コパノカピターノ",
                            "テオドラ", "サヨノイヴ", "ナムラダリア", "ランスタン",
                            "アルムポテンツァ", "カンティプール", "ナンクルナイサ"
                        ],
                        "jockeys": [
                            "北村友一", "田辺裕信", "横山琉人", "津村明秀",
                            "鮫島克駿", "武藤雅", "川端海翼", "菊沢一樹",
                            "戸崎圭太", "荻野極", "角田大河", "丸山元気",
                            "杉原誠人", "江田照男", "今村聖奈"
                        ],
                        "posts": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
                    },
                    9: {
                        "race_name": "村上特別",
                        "distance": "1600m",
                        "track_condition": "良",
                        "horses": [
                            "レインフロムヘヴン", "ロイヤルダンス", "サンライズシリウス", "スマートキャノン",
                            "モルタル", "リュウキュウカリー", "クリノヒーロー", "ビヨンドザタイム",
                            "ルピナスリード", "エクスプロイト", "スピードグラマー", "タイセイプライド"
                        ],
                        "jockeys": [
                            "津村明秀", "今村聖奈", "荻野極", "内田博幸",
                            "戸崎圭太", "田辺裕信", "江田照男", "菊沢一樹",
                            "北村友一", "杉原誠人", "鮫島克駿", "丸山元気"
                        ],
                        "posts": [1, 1, 2, 2, 3, 4, 5, 5, 6, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
                    }
                },
                "中京": {
                    6: {
                        "race_name": "知立T",
                        "distance": "1200m",
                        "track_condition": "良",
                        "horses": [
                            "ヴェルーリヤ", "セレッソプリマヴェラ", "メイショウツツジ", "エルディアブロ",
                            "エムズフラッシュ", "ビーオンザマーチ", "タイセイブリス", "ヴェルメリオ",
                            "ホイッスル", "イヴニングスター", "ハヤブサピアーノ", "スカイトゥーラ",
                            "スラーリドラーテ", "ケフィア"
                        ],
                        "jockeys": [
                            "武豊", "川田将雅", "藤岡康太", "松山弘平",
                            "坂井瑠星", "幸英明", "角田大和", "和田竜二",
                            "岩田望来", "池添謙一", "太宰啓介", "国分恭介",
                            "城戸義政", "松田大作"
                        ],
                        "posts": [1, 1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
                    },
                    7: {
                        "race_name": "3歳以上1勝クラス",
                        "distance": "2000m",
                        "track_condition": "良",
                        "horses": [
                            "プロミストウォリア", "コスモエクスプレス", "マテンロウボス", "シンフェスタ",
                            "サクラトップラン", "ヤマニンアドホック", "マレボプール", "キアナフリューゲル",
                            "ユイノオトコヤマ", "ワールドパレス", "マイネルカーライル", "メイショウソラフネ"
                        ],
                        "jockeys": [
                            "武豊", "川田将雅", "藤岡康太", "坂井瑠星",
                            "岩田望来", "太宰啓介", "古川吉洋", "和田竜二",
                            "角田大和", "池添謙一", "国分恭介", "城戸義政"
                        ],
                        "posts": [1, 1, 2, 2, 3, 4, 5, 5, 6, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
                    },
                    8: {
                        "race_name": "3歳以上2勝クラス",
                        "distance": "1600m",
                        "track_condition": "良",
                        "horses": [
                            "フォルテベローチェ", "ブランショセット", "ジュンブロッサム", "ビーウォーター",
                            "ラヴベローナ", "スパークフューチャー", "ミッキークイーン", "ナンヨーイヴェール",
                            "ルドヴィクス", "トロピカルストーム", "ロードラスター", "シンシティ",
                            "ウォーターアンク"
                        ],
                        "jockeys": [
                            "川田将雅", "坂井瑠星", "岩田望来", "藤岡康太",
                            "武豊", "太宰啓介", "池添謙一", "古川吉洋",
                            "角田大和", "和田竜二", "幸英明", "国分恭介",
                            "城戸義政"
                        ],
                        "posts": [1, 1, 2, 2, 3, 3, 4, 5, 6, 6, 7, 7, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
                    }
                },
                "札幌": {
                    9: {
                        "race_name": "富良野特別",
                        "distance": "1700m",
                        "track_condition": "良",
                        "horses": [
                            "サヴォーナ", "サトノヴィレ", "ニシノコマチムスメ", "エレガントミッシー",
                            "クオリティタイム", "モンタナアゲート", "ショウサンイチマツ", "コードジェニック",
                            "キュールエフウ", "ワンダフルデイズ", "シュヴェルトライテ", "アートハウス",
                            "サトノルフィアン", "リッキーファラオ"
                        ],
                        "jockeys": [
                            "C.ルメール", "武豊", "藤岡佑介", "横山和生",
                            "藤田菜七子", "吉田隼人", "丹内祐次", "斎藤新",
                            "松田大作", "秋山稔樹", "勝浦正樹", "小林美駒",
                            "菱田裕二", "黛弘人"
                        ],
                        "posts": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
                    },
                    10: {
                        "race_name": "十勝岳T",
                        "distance": "1800m",
                        "track_condition": "良",
                        "horses": [
                            "ヒンドゥタイムズ", "レイエスプランドール", "ラヴベローナ", "メイショウタイゲイ",
                            "ルーチェディルーナ", "フランク", "ワンダフルタウン", "モルタル",
                            "ブランショセット", "エイムトゥルー", "ヴェイパーコーン", "タヤスゴールド",
                            "ニシノデフィレ", "アドマイヤアリエル"
                        ],
                        "jockeys": [
                            "C.ルメール", "武豊", "横山和生", "藤岡佑介",
                            "吉田隼人", "斎藤新", "丹内祐次", "藤田菜七子",
                            "秋山稔樹", "勝浦正樹", "松田大作", "菱田裕二",
                            "小林美駒", "黛弘人"
                        ],
                        "posts": [1, 1, 2, 2, 3, 3, 4, 5, 5, 6, 6, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
                    },
                    11: {
                        "race_name": "札幌記念",
                        "distance": "2000m",
                        "track_condition": "良",
                        "horses": [
                            "ジャックドール", "ジャスティンパレス", "プログノーシス", "ローシャムパーク",
                            "ドウデュース", "マテンロウレオ", "ヒートオンビート", "シャフリヤール",
                            "ハヤヤッコ", "マイネルファンロン", "プラダリア", "ノースブリッジ",
                            "サリエラ", "ボッケリーニ", "ハーツコンチェルト", "シュヴァリエローズ"
                        ],
                        "jockeys": [
                            "藤岡佑介", "吉田隼人", "C.ルメール", "武豊",
                            "武豊", "横山和生", "横山武史", "川田将雅",
                            "鮫島克駿", "丹内祐次", "斎藤新", "藤田菜七子",
                            "池添謙一", "西村淳也", "秋山稔樹", "松田大作"
                        ],
                        "posts": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
                    },
                    12: {
                        "race_name": "大雪H",
                        "distance": "1200m",
                        "track_condition": "良",
                        "horses": [
                            "ダイメイフジ", "ピクシーナイト", "ルーチェドーロ", "レジェモー",
                            "ダンツキャッスル", "タガノビューティー", "カイザーノヴァ", "ジャズエイジ",
                            "アンジェーヌ", "ジャングロ", "エイシンスポッター", "レイハリア",
                            "コスモアンジュ", "ラブカンプー"
                        ],
                        "jockeys": [
                            "秋山稔樹", "横山武史", "C.ルメール", "吉田隼人",
                            "藤岡佑介", "武豊", "川田将雅", "斎藤新",
                            "横山和生", "丹内祐次", "鮫島克駿", "藤田菜七子",
                            "西村淳也", "池添謙一"
                        ],
                        "posts": [1, 1, 2, 2, 3, 3, 4, 5, 5, 6, 6, 7, 8, 8],
                        "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
                    }
                }
            }
        }
    
    def get_race_data(self, date: str, venue: str, race_number: int) -> Optional[Dict[str, Any]]:
        """
        指定された日付、開催場、レース番号のデータを取得
        """
        try:
            if date not in self.archive_data:
                logger.warning(f"No archive data for date: {date}")
                return None
                
            date_data = self.archive_data[date]
            if venue not in date_data:
                logger.warning(f"No archive data for venue: {venue} on {date}")
                return None
                
            venue_data = date_data[venue]
            if race_number not in venue_data:
                logger.warning(f"No archive data for race {race_number} at {venue} on {date}")
                return None
            
            race_info = venue_data[race_number]
            
            # レース分析エンジン用のフォーマットに変換
            return {
                'venue': venue,
                'race_number': race_number,
                'race_name': race_info['race_name'],
                'grade': race_info.get('grade', ''),
                'distance': race_info.get('distance', ''),
                'track_condition': race_info.get('track_condition', '良'),
                'horses': race_info.get('horses', []),
                'jockeys': race_info.get('jockeys', []),
                'posts': race_info.get('posts', []),
                'horse_numbers': race_info.get('horse_numbers', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting race data: {e}")
            return None
    
    def get_available_races(self, date: str, venue: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        指定された日付（と開催場）で利用可能なレースのリストを取得
        """
        races = []
        
        if date not in self.archive_data:
            return races
            
        date_data = self.archive_data[date]
        
        if venue:
            # 特定の開催場のみ
            if venue in date_data:
                venue_data = date_data[venue]
                for race_number, race_info in venue_data.items():
                    races.append({
                        'date': date,
                        'venue': venue,
                        'race_number': race_number,
                        'race_name': race_info['race_name'],
                        'has_data': True
                    })
        else:
            # すべての開催場
            for venue_name, venue_data in date_data.items():
                for race_number, race_info in venue_data.items():
                    races.append({
                        'date': date,
                        'venue': venue_name,
                        'race_number': race_number,
                        'race_name': race_info['race_name'],
                        'has_data': True
                    })
        
        return races

# シングルトンインスタンス
archive_data_manager = ArchiveDataManager()