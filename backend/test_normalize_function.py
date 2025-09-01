#!/usr/bin/env python3
"""
データ正規化関数のテスト
Phase 1の実装前に動作確認
"""

def normalize_3f_time(value):
    """
    3Fタイムを秒単位に正規化
    
    ViewLogicナレッジファイルのデータ形式：
    - 0.1秒単位（300以上）: 331.0 = 33.1秒
    - 秒の整数部分（30-50）: 35 = 35.0秒
    - 欠損値（0, 999）: None
    - 中間値（100-299）: 0.1秒単位として扱う
    """
    # 欠損値チェック
    if value == 0 or value == 999 or value == 999.0:
        return None
    
    # 0.1秒単位の値（300以上）
    if value >= 300:
        return value / 10  # 331.0 → 33.1秒
    
    # 秒の整数部分（50以下）
    elif value <= 50:
        return float(value)  # 35 → 35.0秒
    
    # 中間値（100-299）も0.1秒単位として扱う
    else:
        return value / 10  # 295.0 → 29.5秒

def test_normalize():
    """正規化関数のテスト"""
    print("=== normalize_3f_time関数のテスト ===\n")
    
    # テストケース
    test_cases = [
        (331.0, "0.1秒単位（331.0）"),
        (35, "秒の整数部分（35）"),
        (35.0, "秒の整数部分（35.0）"),
        (369.0, "0.1秒単位（369.0）"),
        (0, "欠損値（0）"),
        (999.0, "欠損値（999.0）"),
        (295.0, "中間値（295.0）"),
        (40, "秒の整数部分（40）"),
        (422.0, "0.1秒単位（422.0）"),
    ]
    
    for value, description in test_cases:
        result = normalize_3f_time(value)
        if result is None:
            print(f"{description:25} → None（欠損値）")
        else:
            print(f"{description:25} → {result:.1f}秒")
    
    print("\n【実データでのテスト】")
    # 実際のレースデータ例
    real_data = [
        {"horse": "アーヴァイン", "zenhan": 331.0, "kohan": 340.0},
        {"horse": "バッキンガムパレス", "zenhan": 34.6, "kohan": 387.0},
        {"horse": "ヴィジブルライト", "zenhan": 303.0, "kohan": 389.0},
        {"horse": "サトノアルタイル", "zenhan": 35.1, "kohan": 369.0},
        {"horse": "データなし馬", "zenhan": 0, "kohan": 0},
    ]
    
    for data in real_data:
        zenhan_norm = normalize_3f_time(data['zenhan'])
        kohan_norm = normalize_3f_time(data['kohan'])
        
        print(f"\n{data['horse']}:")
        print(f"  前半3F: {data['zenhan']} → ", end="")
        if zenhan_norm:
            print(f"{zenhan_norm:.1f}秒")
        else:
            print("欠損")
        
        print(f"  後半3F: {data['kohan']} → ", end="")
        if kohan_norm:
            print(f"{kohan_norm:.1f}秒")
        else:
            print("欠損")
        
        # 脚質指数も計算
        if zenhan_norm and kohan_norm:
            style_index = kohan_norm - zenhan_norm
            print(f"  脚質指数: {style_index:.1f} （{'差し・追込' if style_index > 0 else '逃げ・先行'}）")

if __name__ == "__main__":
    test_normalize()