#!/usr/bin/env python3
"""
2024年G1全21レースのViewLogic展開予想結果を取得するバッチ処理
管理者権限でV2チャットセッションを使用
"""

import requests
import json
import time
from typing import Dict, List, Optional

# API設定
API_BASE_URL = "https://uma-i30n.onrender.com"
ADMIN_EMAIL = "goldbenchan@gmail.com"

# 2024年G1レース21戦のデータ
G1_RACES_2024 = [
    {
        "race_id": "202405010211",
        "name": "フェブラリーステークス",
        "date": "2024-02-18",
        "venue": "東京",
        "distance": 1600,
        "track_condition": "良",
        "horses": ["ドゥラエレーデ", "レモンポップ", "ハヤヤッコ", "ブトンドール", "ノットゥルノ",
                  "タスティエーラ", "ルージュエヴァイユ", "アネゴハダ", "セキフウ", "テーオーケインズ",
                  "カテドラル", "イグナイター", "ダノンファラオ", "ベラジオオペラ", "ミトノオー", "ケイアイターコイズ"]
    },
    {
        "race_id": "202407020911",
        "name": "高松宮記念",
        "date": "2024-03-24",
        "venue": "中京",
        "distance": 1200,
        "track_condition": "良",
        "horses": ["モズメイメイ", "ビッグシーザー", "オオバンブルマイ", "ヴェントヴォーチェ", "テイエムスパーダ",
                  "ウインマーベル", "トウシンマカオ", "ナムラクレア", "エイシンスポッター", "ママコチャ",
                  "ファストフォース", "ジャスパージャック", "マッドクール", "メイケイエール", "デュガ", "ダイアトニック"]
    },
    {
        "race_id": "202406020411",
        "name": "大阪杯",
        "date": "2024-03-31",
        "venue": "阪神",
        "distance": 2000,
        "track_condition": "良",
        "horses": ["ベラジオオペラ", "タスティエーラ", "サリエラ", "ジャスティンミラノ", "ダノンベルーガ",
                  "ジャックドール", "レッドガラン", "スタニングローズ", "アスクビクターモア", "エヒト"]
    },
    {
        "race_id": "202405010411",
        "name": "天皇賞（春）",
        "date": "2024-04-28",
        "venue": "京都",
        "distance": 3200,
        "track_condition": "良",
        "horses": ["カレンブーケドール", "サヴォーナ", "タスティエーラ", "ブローザホーン", "ディープボンド",
                  "マテンロウレオ", "サリエラ", "ニホンピロバロン", "ハヤヤッコ", "プリンスリターン",
                  "チャックネイト", "スマートファントム", "シルヴァーソニック", "ワンダフルタウン", "ショウナンバシット"]
    },
    {
        "race_id": "202405020511",
        "name": "宝塚記念",
        "date": "2024-06-23",
        "venue": "阪神",
        "distance": 2200,
        "track_condition": "良",
        "horses": ["ドウデュース", "アカイイト", "ダノンベルーガ", "ローシャムパーク", "プログノーシス",
                  "スタニングローズ", "ブローザホーン", "ベラジオオペラ", "タスティエーラ", "ヴェラアズール",
                  "ハヤヤッコ", "マテンロウレオ", "ガイアフォース", "カレンブーケドール", "ソールオリエンス",
                  "アスクビクターモア", "ショウナンバシット"]
    },
    {
        "race_id": "202410020911",
        "name": "スプリンターズステークス",
        "date": "2024-09-29",
        "venue": "中山",
        "distance": 1200,
        "track_condition": "良",
        "horses": ["ナムラクレア", "マッドクール", "ジャスパージャック", "ウインマーベル", "ママコチャ",
                  "ヴェントヴォーチェ", "オオバンブルマイ", "トウシンマカオ", "エイシンスポッター", "ダイアトニック",
                  "ブトンドール", "サトノレーヴ", "メイケイエール", "ルガル", "ビッグシーザー", "オールアットワンス"]
    },
    {
        "race_id": "202405020711",
        "name": "天皇賞（秋）",
        "date": "2024-10-27",
        "venue": "東京",
        "distance": 2000,
        "track_condition": "良",
        "horses": ["ドウデュース", "イクイノックス", "ジャスティンパレス", "ダノンベルーガ", "プログノーシス",
                  "スタニングローズ", "ガイアフォース", "ノースブリッジ", "ヒシイグアス", "シャフリヤール",
                  "ローシャムパーク", "ジャスティンミラノ", "ベラジオオペラ", "ステラヴェローチェ", "カラテ"]
    },
    {
        "race_id": "202407021011",
        "name": "ジャパンカップ",
        "date": "2024-11-24",
        "venue": "東京",
        "distance": 2400,
        "track_condition": "良",
        "horses": ["ドウデュース", "ジャスティンパレス", "スターズオンアース", "ダノンベルーガ", "ステラヴェローチェ",
                  "カラテ", "ローシャムパーク", "オーガスタス", "シンエンペラー", "ガイアフォース",
                  "ノースブリッジ", "ドゥレッツァ", "レーベンスティール", "ブローザホーン", "ベラジオオペラ"]
    },
    {
        "race_id": "202406021211",
        "name": "有馬記念",
        "date": "2024-12-22",
        "venue": "中山",
        "distance": 2500,
        "track_condition": "良",
        "horses": ["ドウデュース", "ジャスティンパレス", "スターズオンアース", "ローシャムパーク", "ダノンベルーガ",
                  "タスティエーラ", "カラテ", "オーガスタス", "ステラヴェローチェ", "ヒシイグアス",
                  "ディープボンド", "ブローザホーン", "ルージュエヴァイユ", "ベラジオオペラ", "シャフリヤール", "ウインファイブ"]
    },
    {
        "race_id": "202404010411",
        "name": "桜花賞",
        "date": "2024-04-07",
        "venue": "阪神",
        "distance": 1600,
        "track_condition": "良",
        "horses": ["アスコリピチェーノ", "ステレンボッシュ", "クイーンズウォーク", "ライトバック", "パーソナルハイ",
                  "レガレイラ", "フェーングロッテン", "ダイヤノジャック", "ボンドガール", "チェルヴィニア",
                  "ライトクオンタム", "ミスビアンカ", "ブレイディヴェーグ", "コナコースト", "フローラルビーチ",
                  "パラダイスコースト", "ダークエントリー", "クロスマジェスティ"]
    },
    {
        "race_id": "202405020811",
        "name": "オークス",
        "date": "2024-05-19",
        "venue": "東京",
        "distance": 2400,
        "track_condition": "良",
        "horses": ["チェルヴィニア", "ライトバック", "ステレンボッシュ", "アスコリピチェーノ", "クイーンズウォーク",
                  "スティクス", "パーソナルハイ", "コンクシェル", "シーズンリッチ", "ミスビアンカ",
                  "シンエンディ", "ニューアリオン", "ハーベストムーン", "エンパイアウエスト", "ダークエントリー",
                  "エリカヴィータ", "コナコースト", "レガレイラ"]
    },
    {
        "race_id": "202405010811",
        "name": "秋華賞",
        "date": "2024-10-13",
        "venue": "京都",
        "distance": 2000,
        "track_condition": "良",
        "horses": ["ステレンボッシュ", "レガレイラ", "チェルヴィニア", "ライトバック", "ポッドボレット",
                  "ニューアリオン", "コンクシェル", "アスコリピチェーノ", "パーソナルハイ", "ボンドガール",
                  "クイーンズウォーク", "ダークエントリー", "ハーベストムーン", "シーズンリッチ", "エモーショナル",
                  "カウアイレーン", "スティクス", "レイ"]
    },
    {
        "race_id": "202408010411",
        "name": "皐月賞",
        "date": "2024-04-14",
        "venue": "中山",
        "distance": 2000,
        "track_condition": "良",
        "horses": ["ジャンタルマンタル", "シティオブトロイ", "ダノンデサイル", "レガレイラ", "コスモキュランダ",
                  "ビザンチンドリーム", "アーバンシック", "サトノグランツ", "シンエンペラー", "メイショウタバル",
                  "トーセンアウローラ", "ガストリック", "アスコルターレ", "ジューンテイク", "ヴィルヘルム",
                  "ショウナンラプンタ", "アーデルワイゼ", "テンカハル"]
    },
    {
        "race_id": "202405030211",
        "name": "日本ダービー",
        "date": "2024-05-26",
        "venue": "東京",
        "distance": 2400,
        "track_condition": "良",
        "horses": ["ジャンタルマンタル", "コスモキュランダ", "レガレイラ", "ダノンデサイル", "シンエンペラー",
                  "シティオブトロイ", "アーバンシック", "ミスタージーティー", "シュガークン", "タスティエーラ",
                  "ビザンチンドリーム", "メイショウタバル", "アスコルターレ", "サトノグランツ", "トーセンアウローラ",
                  "ショウナンラプンタ", "ヴィルヘルム", "ホウオウビスケッツ"]
    },
    {
        "race_id": "202405011011",
        "name": "菊花賞",
        "date": "2024-10-20",
        "venue": "京都",
        "distance": 3000,
        "track_condition": "良",
        "horses": ["アーバンシック", "ダノンデサイル", "サヴォーナ", "メイショウタバル", "サトノグランツ",
                  "ヴィルヘルム", "コスモキュランダ", "アスコルターレ", "ヤマニンマヒア", "ガストリック",
                  "ウィルソンテソーロ", "レーヴドゥラプレ", "サトノクラウン", "トーセンアウローラ", "エコロプリンス",
                  "ショウナンラプンタ", "ポッドボレット", "テンカハル"]
    },
    {
        "race_id": "202409010411",
        "name": "NHKマイルカップ",
        "date": "2024-05-05",
        "venue": "東京",
        "distance": 1600,
        "track_condition": "良",
        "horses": ["ジャンタルマンタル", "ディスペランツァ", "カルロヴェローチェ", "ビザンチンドリーム", "コスモキュランダ",
                  "ノッキングポイント", "ダノンデサイル", "トリポリタニア", "サトノタイクーン", "サトノフィナーレ",
                  "フューチャーマーク", "ピューロマジック", "ポケットレディ", "シャンパンカラー", "タイセイブレイズ",
                  "シティオブトロイ", "ブレーヴジャーニー", "フォールクラング"]
    },
    {
        "race_id": "202410011111",
        "name": "エリザベス女王杯",
        "date": "2024-11-10",
        "venue": "京都",
        "distance": 2200,
        "track_condition": "良",
        "horses": ["ブレイディヴェーグ", "ハーパー", "キミノナハマリア", "ステレンボッシュ", "ウィルソナス",
                  "スタニングローズ", "タガノエルピス", "ダンツキャッスル", "アリスヴェリテ", "レイベリング",
                  "シンリョクカ", "ノンレグレット", "ルビーカサブランカ", "マスクドディーヴァ", "クロスセリング",
                  "チェルヴィニア", "トゥータラジャー", "ライトバック"]
    },
    {
        "race_id": "202404011211",
        "name": "マイルチャンピオンシップ",
        "date": "2024-11-17",
        "venue": "京都",
        "distance": 1600,
        "track_condition": "良",
        "horses": ["ソウルラッシュ", "ナミュール", "ソーダズリング", "エルトンバローズ", "セリフォス",
                  "ウインカーネリアン", "フィアスプライド", "ジャスティンミラノ", "ソウルスターリング", "ドゥーラ",
                  "トウシンマカオ", "タイセイディバイン", "ガルヴァナイズ", "ロータスランド", "ベラジオオペラ",
                  "ヒストリックノヴァ", "デュガ", "メタルスピード"]
    },
    {
        "race_id": "202405011211",
        "name": "チャンピオンズカップ",
        "date": "2024-12-01",
        "venue": "中京",
        "distance": 1800,
        "track_condition": "良",
        "horses": ["レモンポップ", "ドゥラエレーデ", "ウィルソンテソーロ", "ハヤヤッコ", "ベラジオオペラ",
                  "タガノビューティー", "ミトノオー", "エレフセリア", "ノットゥルノ", "テーオーケインズ",
                  "ケイアイターコイズ", "ダノンファラオ", "メイショウドヒョウ", "トウセツ", "ハギノアレグリアス", "サンライズジパング"]
    },
    {
        "race_id": "202406011011",
        "name": "阪神ジュベナイルフィリーズ",
        "date": "2024-12-08",
        "venue": "阪神",
        "distance": 1600,
        "track_condition": "良",
        "horses": ["シンソウノヴァ", "モンドプリューム", "コートアリシアン", "クラスアップ", "ララアムール",
                  "ドロップオブライト", "ビシャモンテン", "テンマデトドケ", "ムジャッキーラ", "エイトキング",
                  "マサハヤアトム", "ダートフレイム", "イマジン", "フラッグシップ", "エマヌエーレ",
                  "エスケーアドミラル", "フリード", "メリディアンスター"]
    },
    {
        "race_id": "202410011211",
        "name": "朝日杯フューチュリティステークス",
        "date": "2024-12-15",
        "venue": "阪神",
        "distance": 1600,
        "track_condition": "良",
        "horses": ["グランテスト", "モンドプリューム", "エコロガナドール", "コモンウェルス", "ティアップリオン",
                  "サトノアスカロン", "マジックサンズ", "フレイムウィングス", "タマモティーカップ", "エバーサクセス",
                  "ロジアイリッシュ", "ショットオブワン", "ゴッドセレクション", "ルーシャスシティ", "アビッグサプライズ", "トータクエリート"]
    }
]


def create_v2_session(admin_email: str, race_data: Dict) -> Optional[str]:
    """V2チャットセッションを作成"""
    url = f"{API_BASE_URL}/api/v2/chat/create"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_email}"
    }
    data = {
        "race_id": race_data['race_id'],
        "race_name": race_data['name'],
        "race_date": race_data['date'],
        "venue": race_data['venue'],
        "race_number": 11,  # G1なので11Rとする
        "horses": race_data['horses']
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('session_id')
        else:
            print(f"セッション作成エラー: {response.status_code}")
            print(f"  詳細: {response.text}")
            return None
    except Exception as e:
        print(f"セッション作成例外: {e}")
        return None


def get_viewlogic_result(session_id: str, race_data: Dict) -> Optional[Dict]:
    """ViewLogic展開予想を取得"""
    url = f"{API_BASE_URL}/api/v2/chat/session/{session_id}/message"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ADMIN_EMAIL}"
    }
    
    # メッセージ構築
    horses_str = "、".join(race_data['horses'])
    message = f"{race_data['venue']}{race_data['distance']}mの展開予想"
    
    data = {
        "message": message,
        "race_context": {
            "venue": race_data['venue'],
            "distance": race_data['distance'],
            "track_condition": race_data['track_condition'],
            "horses": race_data['horses']
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            result = response.json()
            
            # レスポンスから上位5頭を抽出
            if 'response' in result:
                response_text = result['response']
                
                # 上位5頭の抽出（フォーマット例：【展開上位5頭】1位：馬名）
                top5 = []
                lines = response_text.split('\n')
                for line in lines:
                    if '位' in line and '：' in line:
                        # 「1位：馬名」のパターンを抽出
                        parts = line.split('：')
                        if len(parts) >= 2:
                            horse_name = parts[1].split('（')[0].strip()
                            if horse_name in race_data['horses']:
                                top5.append(horse_name)
                                if len(top5) >= 5:
                                    break
                
                return {
                    'race_name': race_data['name'],
                    'top5': top5[:5] if top5 else None,
                    'full_response': response_text
                }
        else:
            print(f"メッセージ送信エラー ({race_data['name']}): {response.status_code}")
            return None
    except Exception as e:
        print(f"メッセージ送信例外 ({race_data['name']}): {e}")
        return None


def main():
    """メイン処理"""
    print("=" * 70)
    print("2024年G1全21レース ViewLogic展開予想取得")
    print("=" * 70)
    
    all_results = []
    successful_count = 0
    
    for i, race in enumerate(G1_RACES_2024, 1):
        print(f"\n[{i}/21] {race['name']} 処理中...")
        
        # セッション作成
        session_id = create_v2_session(ADMIN_EMAIL, race)
        if not session_id:
            print(f"  ❌ セッション作成失敗")
            all_results.append({
                'race_name': race['name'],
                'top5': None,
                'error': 'セッション作成失敗'
            })
            continue
        
        # ViewLogic結果取得
        result = get_viewlogic_result(session_id, race)
        
        if result and result.get('top5'):
            successful_count += 1
            print(f"  ✅ 成功: {', '.join(result['top5'])}")
            all_results.append(result)
        else:
            print(f"  ❌ 失敗: ViewLogic結果を取得できませんでした")
            all_results.append({
                'race_name': race['name'],
                'top5': None,
                'error': 'ViewLogic結果取得失敗'
            })
        
        # API負荷軽減のため少し待機
        time.sleep(2)
    
    # 結果サマリー
    print("\n" + "=" * 70)
    print("ViewLogic展開予想 取得結果一覧")
    print("=" * 70)
    
    for i, result in enumerate(all_results, 1):
        race_name = result['race_name']
        if result.get('top5'):
            top5_str = ", ".join(result['top5'])
            print(f"{i:2}. {race_name:30} → {top5_str}")
        else:
            error = result.get('error', '不明なエラー')
            print(f"{i:2}. {race_name:30} → ❌ {error}")
    
    print(f"\n成功: {successful_count}/21レース")
    
    # 結果をJSONファイルに保存
    output_file = "viewlogic_g1_results_2024.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n結果を {output_file} に保存しました")


if __name__ == "__main__":
    main()