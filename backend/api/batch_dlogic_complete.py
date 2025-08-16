from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import json
import os
from datetime import datetime
from services.fast_dlogic_engine import FastDLogicEngine

router = APIRouter()

# グローバルインスタンス（起動時に1回だけ初期化）
fast_engine = FastDLogicEngine()

@router.post("/api/admin/batch-dlogic-analyze")
async def batch_dlogic_analyze(data: Dict[str, Any]):
    """指定日のアーカイブレースを一括D-Logic分析"""
    archive_date = data.get('archive_date')
    
    try:
        # 過去G1レースの場合
        if archive_date == 'past-g1-2024':
            # 過去G1データを直接定義
            races = get_past_g1_2024_data()
        else:
            # アーカイブデータファイルを読み込み
            archive_file = f"data/archive_races/{archive_date.replace('-', '')}.json"
            
            if os.path.exists(archive_file):
                with open(archive_file, 'r', encoding='utf-8') as f:
                    races = json.load(f)
            else:
                # JSONファイルがない場合は、アーカイブページのデータから生成
                # 実際の運用では、事前にconvert_archive_to_json.pyを実行しておく
                return {
                    "status": "error",
                    "message": "アーカイブデータファイルが見つかりません。convert_archive_to_json.pyを実行してください。"
                }
        
        # 各レースを分析
        results = []
        
        for race in races:
            try:
                # レース情報
                venue = race['venue']
                race_number = race['race_number']
                horses = race['horses']
                
                print(f"分析中: {venue} {race_number}R ({len(horses)}頭)")
                
                # 各馬のD-Logicスコアを計算
                horse_scores = []
                
                for horse_name in horses:
                    try:
                        # D-Logic計算
                        d_logic_results = fast_engine.calculate_single(
                            horse_name=horse_name,
                            race_date=race['race_date'],
                            jyo=venue,
                            race_num=str(race_number)
                        )
                        
                        if d_logic_results and 'results' in d_logic_results and len(d_logic_results['results']) > 0:
                            result = d_logic_results['results'][0]
                            total_score = result.get('dLogicTotal', 50)
                            horse_scores.append({
                                'horse_name': horse_name,
                                'score': total_score
                            })
                        else:
                            # データがない場合はデフォルトスコア
                            horse_scores.append({
                                'horse_name': horse_name,
                                'score': 50
                            })
                    except Exception as e:
                        print(f"馬の分析エラー: {horse_name} - {str(e)}")
                        horse_scores.append({
                            'horse_name': horse_name,
                            'score': 50
                        })
                
                # スコア順にソート（降順）
                horse_scores.sort(key=lambda x: x['score'], reverse=True)
                
                # 上位5頭を抽出
                dlogic_top5 = [h['horse_name'] for h in horse_scores[:5]]
                
                results.append({
                    'venue': venue,
                    'race_number': race_number,
                    'horses': horses,
                    'dlogic_top5': dlogic_top5,
                    'status': 'success'
                })
                
            except Exception as e:
                print(f"レース分析エラー: {venue} {race_number}R - {str(e)}")
                results.append({
                    'venue': venue,
                    'race_number': race_number,
                    'horses': race.get('horses', []),
                    'dlogic_top5': [],
                    'status': 'error',
                    'error': str(e)
                })
        
        # 結果を保存
        os.makedirs('data/dlogic_results', exist_ok=True)
        result_file = f"data/dlogic_results/batch_{archive_date.replace('-', '')}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'archive_date': archive_date,
                'results': results,
                'analyzed_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        # 成功数をカウント
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return {
            "status": "success",
            "results": results,
            "message": f"{success_count}/{len(results)}レースの分析が完了しました"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/admin/apply-dlogic-results")
async def apply_dlogic_results(data: Dict[str, Any]):
    """D-Logic分析結果をアーカイブページに反映"""
    archive_date = data.get('archive_date')
    results = data.get('results', [])
    
    try:
        # 過去G1の場合
        if archive_date == 'past-g1-2024':
            # 過去G1用の更新ファイルを作成
            g1_update = {}
            for result in results:
                if result['status'] == 'success':
                    # race_idを使用（例: 'february-stakes-2024'）
                    race_id = None
                    # venueとrace_nameから過去G1のrace_idを特定
                    g1_races = get_past_g1_2024_data()
                    for g1_race in g1_races:
                        if g1_race['venue'] == result['venue'] and g1_race['race_number'] == result['race_number']:
                            race_id = g1_race['race_id']
                            break
                    
                    if race_id:
                        g1_update[race_id] = {
                            'dlogic_top5': result['dlogic_top5'],
                            'updated_at': datetime.now().isoformat()
                        }
            
            # 過去G1更新ファイルを保存
            update_file = f"data/archive_updates/past_g1_2024_dlogic.json"
            os.makedirs('data/archive_updates', exist_ok=True)
            
            with open(update_file, 'w', encoding='utf-8') as f:
                json.dump(g1_update, f, ensure_ascii=False, indent=2)
            
            return {
                "status": "success",
                "message": "過去G1ページへの反映準備が完了しました",
                "update_file": update_file
            }
        
        # 通常のアーカイブの場合
        archive_update = {}
        
        for result in results:
            if result['status'] == 'success':
                key = f"{result['venue']}_{result['race_number']}"
                archive_update[key] = {
                    'dlogic_top5': result['dlogic_top5'],
                    'updated_at': datetime.now().isoformat()
                }
        
        # アーカイブ更新ファイルを保存
        update_file = f"data/archive_updates/{archive_date.replace('-', '')}_dlogic.json"
        os.makedirs('data/archive_updates', exist_ok=True)
        
        with open(update_file, 'w', encoding='utf-8') as f:
            json.dump(archive_update, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "message": "アーカイブページへの反映準備が完了しました",
            "update_file": update_file
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/admin/g1-results")
async def get_g1_results():
    """過去G1の分析結果を取得"""
    try:
        result_file = "data/archive_updates/past_g1_2024_dlogic.json"
        
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_past_g1_2024_data():
    """2024年の過去G1レースデータを返す"""
    return [
        {
            'race_id': 'february-stakes-2024',
            'venue': '東京',
            'race_number': 11,
            'race_date': '2024-02-18',
            'race_name': 'フェブラリーステークス',
            'horses': [
                'ペプチドナイル',
                'ガイアフォース',
                'セキフウ',
                'タガノビューティー',
                'キングズソード',
                'レッドルゼル',
                'ミックファイア',
                'ウィルソンテソーロ',
                'ドンフランキー',
                'アルファマム',
                'イグナイター',
                'ドゥラエレーデ',
                'スピーディキック',
                'オメガギネス',
                'カラテ',
                'シャンパンカラー'
            ]
        },
        {
            'race_id': 'takamatsunomiya-kinen-2024',
            'venue': '中京',
            'race_number': 11,
            'race_date': '2024-03-24',
            'race_name': '高松宮記念',
            'horses': [
                'マッドクール',
                'ナムラクレア',
                'ビクターザウィナー',
                'ウインカーネリアン',
                'ロータスランド',
                'トウシンマカオ',
                'ビッグシーザー',
                'ママコチャ',
                'メイケイエール',
                'ルガル',
                'ディヴィーナ',
                'ウインマーベル',
                'シュバルツカイザー',
                'ソーダズリング',
                'モズメイメイ',
                'マテンロウオリオン',
                'シャンパンカラー',
                'テイエムスパーダ'
            ]
        },
        {
            'race_id': 'osaka-hai-2024',
            'venue': '阪神',
            'race_number': 11,
            'race_date': '2024-03-31',
            'race_name': '大阪杯',
            'horses': [
                'ベラジオオペラ',
                'ローシャムパーク',
                'ルージュエヴァイユ',
                'ステラヴェローチェ',
                'ジオグリフ',
                'プラダリア',
                'ソールオリエンス',
                'スタニングローズ',
                'カテドラル',
                'エピファニー',
                'タスティエーラ',
                'ハヤヤッコ',
                'ハーパー',
                'ミッキーゴージャス',
                'キラーアビリティ',
                'リカンカブール'
            ]
        },
        {
            'race_id': 'oka-sho-2024',
            'venue': '阪神',
            'race_number': 11,
            'race_date': '2024-04-07',
            'race_name': '桜花賞',
            'horses': [
                'ステレンボッシュ',
                'アスコリピチェーノ',
                'ライトバック',
                'スウィープフィート',
                'エトヴプレ',
                'ワイドラトゥール',
                'セキトバイースト',
                'クイーンズウォーク',
                'テウメッサ',
                'ハワイアンティアレ',
                'イフェイオン',
                'シカゴスティング',
                'チェルヴィニア',
                'マスクオールウィン',
                'セシリエプラージュ',
                'コラソンビート',
                'ショウナンマヌエラ',
                'キャットファイト'
            ]
        },
        {
            'race_id': 'satsuki-sho-2024',
            'venue': '中山',
            'race_number': 11,
            'race_date': '2024-04-14',
            'race_name': '皐月賞',
            'horses': [
                'ジャスティンミラノ',
                'コスモキュランダ',
                'ジャンタルマンタル',
                'アーバンシック',
                'シンエンペラー',
                'レガレイラ',
                'エコロヴァルツ',
                'ルカランフィースト',
                'サンライズジパング',
                'ミスタージーティー',
                'ホウオウプロサンゲ',
                'サンライズアース',
                'ビザンチンドリーム',
                'シリウスコルト',
                'アレグロブリランテ',
                'ウォーターリヒト',
                'メイショウタバル'
            ]
        },
        {
            'race_id': 'tenno-sho-spring-2024',
            'venue': '京都',
            'race_number': 11,
            'race_date': '2024-04-28',
            'race_name': '天皇賞（春）',
            'horses': [
                'テーオーロイヤル',
                'ブローザホーン',
                'ディープボンド',
                'スマートファントム',
                'ワープスピード',
                'サヴォーナ',
                'タスティエーラ',
                'メイショウブレゲ',
                'ゴールドプリンセス',
                'プリュムドール',
                'スカーフェイス',
                'サリエラ',
                'マテンロウレオ',
                'チャックネイト',
                'ドゥレッツァ',
                'シルヴァーソニック'
            ]
        },
        {
            'race_id': 'nhk-mile-cup-2024',
            'venue': '東京',
            'race_number': 11,
            'race_date': '2024-05-05',
            'race_name': 'NHKマイルカップ',
            'horses': [
                'ジャンタルマンタル',
                'アスコリピチェーノ',
                'ロジリオン',
                'ゴンバデカーブース',
                'イフェイオン',
                'チャンネルトンネル',
                'ディスペランツァ',
                'ウォーターリヒト',
                'アルセナール',
                'エンヤラヴフェイス',
                'ユキノロイヤル',
                'ノーブルロジャー',
                'ダノンマッキンリー',
                'アレンジャー',
                'マスクオールウィン',
                'シュトラウス',
                'ボンドガール',
                'キャプテンシー'
            ]
        },
        {
            'race_id': 'oaks-2024',
            'venue': '東京',
            'race_number': 11,
            'race_date': '2024-05-19',
            'race_name': 'オークス（優駿牝馬）',
            'horses': [
                'チェルヴィニア',
                'ステレンボッシュ',
                'ライトバック',
                'クイーンズウォーク',
                'ランスオブクイーン',
                'スウィープフィート',
                'サンセットビュー',
                'エセルフリーダ',
                'アドマイヤベル',
                'ホーエリート',
                'ラヴァンダ',
                'コガネノソラ',
                'サフィラ',
                'ミアネーロ',
                'パレハ',
                'タガノエルピーダ',
                'ショウナンマヌエラ',
                'ヴィントシュティレ'
            ]
        },
        {
            'race_id': 'tokyo-yushun-2024',
            'venue': '東京',
            'race_number': 11,
            'race_date': '2024-05-26',
            'race_name': '日本ダービー（東京優駿）',
            'horses': [
                'ダノンデサイル',
                'ジャスティンミラノ',
                'シンエンペラー',
                'サンライズアース',
                'レガレイラ',
                'コスモキュランダ',
                'シュガークン',
                'エコロヴァルツ',
                'シックスペンス',
                'ジューンテイク',
                'アーバンシック',
                'サンライズジパング',
                'ゴンバデカーブース',
                'ダノンエアズロック',
                'ショウナンラプンタ',
                'ミスタージーティー',
                'ビザンチンドリーム'
            ]
        },
        {
            'race_id': 'yasuda-kinen-2024',
            'venue': '東京',
            'race_number': 11,
            'race_date': '2024-06-02',
            'race_name': '安田記念',
            'horses': [
                'ロマンチックウォリアー',
                'ナミュール',
                'ソウルラッシュ',
                'ガイアフォース',
                'セリフォス',
                'ジオグリフ',
                'フィアスプライド',
                'エルトンバローズ',
                'ステラヴェローチェ',
                'エアロロノア',
                'レッドモンレーヴ',
                'コレペティトール',
                'パラレルヴィジョン',
                'ウインカーネリアン',
                'ダノンスコーピオン',
                'カテドラル',
                'ヴォイッジバブル',
                'ドーブネ'
            ]
        },
        {
            'race_id': 'takarazuka-kinen-2024',
            'venue': '阪神',
            'race_number': 11,
            'race_date': '2024-06-23',
            'race_name': '宝塚記念',
            'horses': [
                'ブローザホーン',
                'ソールオリエンス',
                'ベラジオオペラ',
                'プラダリア',
                'ローシャムパーク',
                'ドウデュース',
                'ディープボンド',
                'ルージュエヴァイユ',
                'ヤマニンサンパ',
                'ジャスティンパレス',
                'シュトルーヴェ',
                'ヒートオンビート',
                'カラテ'
            ]
        },
        {
            'race_id': 'sprinters-stakes-2024',
            'venue': '中山',
            'race_number': 11,
            'race_date': '2024-09-29',
            'race_name': 'スプリンターズステークス',
            'horses': [
                'ルガル',
                'トウシンマカオ',
                'ナムラクレア',
                'ママコチャ',
                'ウインマーベル',
                'ビクターザウィナー',
                'サトノレーヴ',
                'ピューロマジック',
                'エイシンスポッター',
                'モズメイメイ',
                'オオバンブルマイ',
                'マッドクール',
                'ムゲン',
                'ウイングレイテスト',
                'ダノンスコーピオン',
                'ヴェントヴォーチェ'
            ]
        },
        {
            'race_id': 'shuka-sho-2024',
            'venue': '京都',
            'race_number': 11,
            'race_date': '2024-10-13',
            'race_name': '秋華賞',
            'horses': [
                'チェルヴィニア',
                'ボンドガール',
                'ステレンボッシュ',
                'ラヴァンダ',
                'クリスマスパレード',
                'ミアネーロ',
                'タガノエルピーダ',
                'チルカーノ',
                'コガネノソラ',
                'ホーエリート',
                'ラビットアイ',
                'アドマイヤベル',
                'セキトバイースト',
                'ランスオブクイーン',
                'クイーンズウォーク'
            ]
        },
        {
            'race_id': 'kikka-sho-2024',
            'venue': '京都',
            'race_number': 11,
            'race_date': '2024-10-20',
            'race_name': '菊花賞',
            'horses': [
                'アーバンシック',
                'ヘデントール',
                'アドマイヤテラ',
                'ショウナンラプンタ',
                'ビザンチンドリーム',
                'ダノンデサイル',
                'シュバルツクーゲル',
                'ハヤテノフクノスケ',
                'エコロヴァルツ',
                'アレグロブリランテ',
                'ウエストナウ',
                'ミスタージーティー',
                'メリオーレム',
                'コスモキュランダ',
                'ピースワンデュック',
                'メイショウタバル',
                'アスクカムオンモア',
                'ノーブルスカイ'
            ]
        },
        {
            'race_id': 'tenno-sho-autumn-2024',
            'venue': '東京',
            'race_number': 11,
            'race_date': '2024-10-27',
            'race_name': '天皇賞（秋）',
            'horses': [
                'ドウデュース',
                'タスティエーラ',
                'ホウオウビスケッツ',
                'ジャスティンパレス',
                'マテンロウスカイ',
                'ベラジオオペラ',
                'ソールオリエンス',
                'レーベンスティール',
                'ステラヴェローチェ',
                'ニシノレヴナント',
                'ノースブリッジ',
                'キングズパレス',
                'リバティアイランド',
                'ダノンベルーガ',
                'シルトホルン'
            ]
        },
        {
            'race_id': 'queen-elizabeth-cup-2024',
            'venue': '京都',
            'race_number': 11,
            'race_date': '2024-11-10',
            'race_name': 'エリザベス女王杯',
            'horses': [
                'スタニングローズ',
                'ラヴェル',
                'ホールネス',
                'シンリョクカ',
                'レガレイラ',
                'ライラック',
                'サリエラ',
                'ゴールドエクリプス',
                'コスタボニータ',
                'シンティレーション',
                'キミノナハマリア',
                'エリカヴィータ',
                'ルージュリナージュ',
                'モリアーナ',
                'ピースオブザライフ',
                'コンクシェル',
                'ハーパー'
            ]
        },
        {
            'race_id': 'mile-championship-2024',
            'venue': '京都',
            'race_number': 11,
            'race_date': '2024-11-17',
            'race_name': 'マイルチャンピオンシップ',
            'horses': [
                'ソウルラッシュ',
                'エルトンバローズ',
                'ウインマーベル',
                'ブレイディヴェーグ',
                'チャリン',
                'セリフォス',
                'タイムトゥヘヴン',
                'ニホンピロキーフ',
                'フィアスプライド',
                'ジュンブロッサム',
                'アルナシーム',
                'オオバンブルマイ',
                'バルサムノート',
                'マテンロウスカイ',
                'コムストックロード',
                'レイベリング',
                'ナミュール'
            ]
        },
        {
            'race_id': 'japan-cup-2024',
            'venue': '東京',
            'race_number': 11,
            'race_date': '2024-11-24',
            'race_name': 'ジャパンカップ',
            'horses': [
                'ドウデュース',
                'シンエンペラー',
                'ドゥレッツァ',
                'チェルヴィニア',
                'ジャスティンパレス',
                'ゴリアット',
                'スターズオンアース',
                'オーギュストロダン',
                'ダノンベルーガ',
                'シュトルーヴェ',
                'ファンタスティックムーン',
                'ブローザホーン',
                'カラテ',
                'ソールオリエンス'
            ]
        },
        {
            'race_id': 'champions-cup-2024',
            'venue': '中京',
            'race_number': 11,
            'race_date': '2024-12-01',
            'race_name': 'チャンピオンズカップ',
            'horses': [
                'レモンポップ',
                'ウィルソンテソーロ',
                'ドゥラエレーデ',
                'ハギノアレグリアス',
                'ペプチドナイル',
                'サンライズジパング',
                'アーテルアストレア',
                'ペイシャエス',
                'グロリアムンディ',
                'ミトノオー',
                'クラウンプライド',
                'セラフィックコール',
                'ミックファイア',
                'テーオードレフォン',
                'ガイアフォース',
                'スレイマン'
            ]
        },
        {
            'race_id': 'asahi-hai-2024',
            'venue': '阪神',
            'race_number': 11,
            'race_date': '2024-12-15',
            'race_name': '朝日杯フューチュリティステークス',
            'horses': [
                'アドマイヤズーム',
                'ミュージアムマイル',
                'ランスオブカオス',
                'ダイシンラー',
                'アルテヴェローチェ',
                'クラスペディア',
                'ドラゴンブースト',
                'コスモストーム',
                'ニタモノドウシ',
                'アルレッキーノ',
                'エルムラント',
                'パンジャタワー',
                'トータルクラリティ',
                'エイシンワンド',
                'タイセイカレント',
                'テイクイットオール'
            ]
        },
        {
            'race_id': 'arima-kinen-2024',
            'venue': '中山',
            'race_number': 11,
            'race_date': '2024-12-22',
            'race_name': '有馬記念',
            'horses': [
                'レガレイラ',
                'シャフリヤール',
                'ダノンデサイル',
                'ベラジオオペラ',
                'ジャスティンパレス',
                'アーバンシック',
                'ローシャムパーク',
                'スタニングローズ',
                'ダノンベルーガ',
                'シュトルーヴェ',
                'プログノーシス',
                'ブローザホーン',
                'ディープボンド',
                'スターズオンアース',
                'ハヤヤッコ'
            ]
        }
    ]
