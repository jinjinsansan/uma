#!/usr/bin/env python3
"""
ViewLogic出力文章の多様性をテスト
"""

from services.viewlogic_engine import ViewLogicEngine

def test_output_diversity():
    """同じレースデータで複数回実行して出力の多様性を確認"""
    
    engine = ViewLogicEngine()
    
    # テスト用レースデータ
    test_race = {
        'venue': '東京',
        'race_number': 11,
        'distance': '2000m',
        'horses': [
            'ドウデュース', 'イクイノックス', 'ジャスティンパレス',
            'ダノンベルーガ', 'プラダリア', 'タスティエーラ'
        ]
    }
    
    print("=== ViewLogic出力文章の多様性テスト ===\n")
    print("同じレースデータで3回実行して、異なる文章が生成されることを確認します\n")
    
    # 3回実行して出力を比較
    outputs = []
    for i in range(3):
        print(f"\n【実行{i+1}回目】")
        print("=" * 60)
        
        result = engine.predict_race_flow_advanced(test_race)
        
        if result.get('status') == 'success':
            # formatted_outputを取得
            formatted = result.get('formatted_output', '')
            
            # ペース部分と結論部分を抽出して表示
            lines = formatted.split('\n')
            
            # ペース説明部分を抽出（最初の説明文）
            pace_desc = None
            conclusion = None
            
            for j, line in enumerate(lines):
                if '序盤から' in line or 'スタート直後' in line or '前半から' in line or '各馬が' in line or '平均的な' in line:
                    pace_desc = line
                    break
            
            # まとめ部分を抽出
            for j, line in enumerate(lines):
                if 'ハイペースの消耗戦' in line or '前半の激しい' in line or '前残りの可能性' in line or 'バランスの取れた' in line:
                    conclusion = line
                    break
            
            print(f"ペース説明: {pace_desc[:60]}..." if pace_desc else "ペース説明が見つかりません")
            print(f"結論: {conclusion[:60]}..." if conclusion else "結論が見つかりません")
            
            outputs.append(formatted)
        else:
            print(f"エラー: {result.get('message', '不明')}")
    
    # 出力の違いを確認
    print("\n\n【多様性の確認】")
    print("=" * 60)
    
    if len(outputs) >= 2:
        # 最初の100文字を比較
        for i in range(len(outputs)):
            print(f"\n実行{i+1}の冒頭:")
            # ペース予想の説明部分を探す
            lines = outputs[i].split('\n')
            for line in lines:
                if '序盤' in line or 'スタート' in line or '各馬' in line or '平均' in line:
                    print(f"  {line[:80]}")
                    break
        
        # 出力が異なることを確認
        if outputs[0] == outputs[1]:
            print("\n⚠️ 警告: 出力が同一です。テンプレートが機能していない可能性があります。")
        else:
            print("\n✅ 成功: 出力に多様性が確認できました！")
    
if __name__ == "__main__":
    test_output_diversity()