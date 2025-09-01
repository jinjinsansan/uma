#!/usr/bin/env python3
"""
実際のレースでViewLogic展開予想をテストし、完全な出力を表示
"""

from services.viewlogic_engine import ViewLogicEngine
import json

def test_real_race(race_data):
    """実際のレースデータでテスト"""
    
    print("="*70)
    print("ViewLogic展開予想 - 実レーステスト")
    print("="*70)
    
    engine = ViewLogicEngine()
    result = engine.predict_race_flow_advanced(race_data)
    
    if result.get('status') == 'success':
        # 1. ペース予測の確認
        pace_pred = result.get('pace_prediction', {})
        print("\n【ペース予測データ】")
        print(f"ペース: {pace_pred.get('pace')}")
        print(f"確信度: {pace_pred.get('confidence')}%")
        print(f"前半3F平均: {pace_pred.get('zenhan_avg', 0):.1f}秒")
        print(f"後半3F平均: {pace_pred.get('kohan_avg', 0):.1f}秒")
        
        # 2. 上位5頭の確認
        print("\n【上位5頭予想】")
        if 'race_simulation' in result and 'finish' in result['race_simulation']:
            finish_order = result['race_simulation']['finish']
            for i, horse_info in enumerate(finish_order[:5], 1):
                horse_name = horse_info.get('horse_name', '不明')
                position = horse_info.get('position', 99)
                print(f"{i}位: {horse_name} (予測値: {position:.2f})")
        
        # 3. フローマッチングスコア
        print("\n【展開適性スコア】")
        flow_matching = result.get('flow_matching', {})
        sorted_matching = sorted(flow_matching.items(), key=lambda x: x[1], reverse=True)[:5]
        for horse, score in sorted_matching:
            print(f"  {horse}: {score:.1f}点")
        
        # 4. 完全な日本語出力
        print("\n" + "="*70)
        print("【完全な出力文章】")
        print("="*70)
        formatted = result.get('formatted_output', '')
        if formatted:
            print(formatted)
        else:
            print("※ フォーマット出力がありません")
        
        return True
    else:
        print(f"\n❌ エラー: {result.get('message', '不明')}")
        return False

if __name__ == "__main__":
    # ここにレースデータを入力
    # 新潟12R 雷光特別[2勝クラス]のデータ
    race_data = {
        'venue': '中京',
        'race_number': 10,
        'race_name': '白川郷S[3勝クラス]',
        'distance': '1900m',
        'track_condition': '良',
        'horses': [
            'ビップスコーピオン', 'ハギノサステナブル', 'グランジョルノ',
            'メイショウポペット', 'アスクデビューモア', 'バリアントバイオ',
            'メイショウソウタ', 'リューデスハイム', 'カゼノランナー',
            'レッドプロフェシー', 'オンザライン', 'ダイメイセブン',
            'アーマルコライト', 'クーアフュルスト', 'グラヴィス',
            'ジュタロウ'
        ]
    }
    
    test_real_race(race_data)