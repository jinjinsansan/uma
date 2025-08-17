"""
モックアーカイブデータ（開発・テスト用）
"""

# 2025-08-18のレースデータ
archive_data_20250818 = {
    "札幌": {
        11: {
            'venue': '札幌',
            'race_number': 11,
            'race_name': '札幌記念',
            'distance': '2000m',
            'grade': 'G2',
            'horses': [
                'プログノーシス', 'ローシャムパーク', 'ノースブリッジ', 'ウインカーネリアン',
                'ヒートオンビート', 'ダノンベルーガ', 'ジャスティンパレス', 'ドウデュース',
                'ブラストワンピース', 'マテンロウレオ', 'プラダリア', 'ホウオウバニラ'
            ],
            'jockeys': [
                'C.ルメール', 'M.デムーロ', '武豊', '藤岡佑介',
                '池添謙一', '戸崎圭太', '横山和生', '武豊',
                '吉田隼人', '横山琉人', '国分恭介', '丹内祐次'
            ],
            'posts': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6],
            'horse_numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'track_condition': '良'
        }
    },
    "新潟": {
        11: {
            'venue': '新潟',
            'race_number': 11,
            'race_name': '関屋記念',
            'distance': '1600m',
            'grade': 'G3',
            'horses': [
                'エルトンバローズ', 'トーセンヴァンノ', 'プログノーシス', 'ベレヌス',
                'セルバーグ', 'ロードベイリーフ', 'ダンツキャッスル', 'ルガル',
                'ソウルラッシュ', 'ピースオブエイト', 'エイシンスポッター', 'タガノビューティー',
                'ジュンライトボルト', 'カフェサンドリヨン', 'ディヴィーナ', 'レーベンスティール',
                'ロードヴァレンチ', 'ジャスティンカフェ'
            ],
            'jockeys': [
                '戸崎圭太', '横山和生', 'C.ルメール', '横山武史',
                '菅原明良', '田辺裕信', '岩田康誠', '坂井瑠星',
                'M.デムーロ', '石橋脩', '内田博幸', '川田将雅',
                '松山弘平', '津村明秀', '藤岡佑介', '吉田隼人',
                '武藤雅', '柴田大知'
            ],
            'posts': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 8, 8],
            'horse_numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            'track_condition': '良'
        }
    },
    "小倉": {
        11: {
            'venue': '小倉',
            'race_number': 11,
            'race_name': '北九州記念',
            'distance': '1200m',
            'grade': 'G3',
            'horses': [
                'オオバンブルマイ', 'マッドクール', 'サヴォーナ', 'ビッグシーザー',
                'ドルチェモア', 'タマモティータイム', 'ジャングロ', 'フルム',
                'モズメイメイ', 'トウシンマカオ', 'ロードベイリーフ', 'ゾンニッヒ',
                'エイシンスポッター', 'ナムラクレア', 'ボンボヤージ', 'ヴェントヴォーチェ',
                'オールアットワンス', 'ピクシーナイト'
            ],
            'jockeys': [
                '川田将雅', '松山弘平', '今村聖奈', '西村淳也',
                '藤岡康太', '富田暁', '岩田康誠', '鮫島克駿',
                '幸英明', '川須栄彦', '戸崎圭太', '和田竜二',
                '横山和生', '津村明秀', '北村友一', '永野猛蔵',
                '武藤雅', '菊沢一樹'
            ],
            'posts': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 8, 8],
            'horse_numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            'track_condition': '良'
        }
    }
}

# 過去G1レースのサンプルデータ
sample_g1_races = {
    "2024-12-29": {  # 有馬記念
        "中山": {
            11: {
                'venue': '中山',
                'race_number': 11,
                'race_name': '有馬記念',
                'distance': '2500m',
                'grade': 'G1',
                'horses': [
                    'ドウデュース', 'スターズオンアース', 'ジャスティンパレス', 'ダノンベルーガ',
                    'プログノーシス', 'タイトルホルダー', 'ローシャムパーク', 'ブローザホーン'
                ],
                'jockeys': [
                    '武豊', 'C.ルメール', '横山和生', '戸崎圭太',
                    'M.デムーロ', '松山弘平', '川田将雅', '藤岡佑介'
                ],
                'posts': [1, 2, 3, 4, 5, 6, 7, 8],
                'horse_numbers': [1, 2, 3, 4, 5, 6, 7, 8],
                'track_condition': '良'
            }
        }
    }
}

def get_mock_race_data(date: str, venue: str, race_number: int):
    """モックデータから指定されたレースを取得"""
    if date == "2025-08-18" and venue in archive_data_20250818:
        venue_data = archive_data_20250818[venue]
        if race_number in venue_data:
            return venue_data[race_number]
    
    # 過去G1レースデータも検索
    if date in sample_g1_races and venue in sample_g1_races[date]:
        venue_data = sample_g1_races[date][venue]
        if race_number in venue_data:
            return venue_data[race_number]
    
    return None

def search_mock_races_by_name(race_name: str, date: str = None):
    """レース名でモックデータを検索"""
    matching_races = []
    
    # 2025-08-18のデータを検索
    if date is None or date == "2025-08-18":
        for venue, races in archive_data_20250818.items():
            for race_num, race_data in races.items():
                if race_name in race_data.get('race_name', ''):
                    race_data_copy = race_data.copy()
                    race_data_copy['race_date'] = "2025-08-18"
                    matching_races.append(race_data_copy)
    
    # 過去G1レースも検索
    for race_date, venues in sample_g1_races.items():
        if date is None or date == race_date:
            for venue, races in venues.items():
                for race_num, race_data in races.items():
                    if race_name in race_data.get('race_name', ''):
                        race_data_copy = race_data.copy()
                        race_data_copy['race_date'] = race_date
                        matching_races.append(race_data_copy)
    
    return matching_races