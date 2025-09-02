# ViewLogic展開予想 デュアルペースシステム仕様書

## 概要
ViewLogic展開予想において、**的中率**と**表示の多様性**を両立するための二段階ペース判定システム。

## 問題の背景
1. **元の閾値（33.5/34.0/34.5）**: 的中率は高いが、ほぼ全レースが「スローペース」と判定される
2. **新しい閾値（35.0/36.0/37.0）**: 4段階に分散するが、的中率が低下する
3. **解決策**: 内部計算と表示を分離し、両方の利点を活かす

## システム構造

### 1. 二段階ペース判定（`_advanced_pace_prediction`メソッド）

```python
# 前半3Fの平均タイムを計算
zenhan_avg = mean(zenhan_times)  # 例: 35.51秒

# 1. 内部計算用ペース判定（展開適性・上位5頭選出に使用）
if zenhan_avg <= 33.5:
    calculation_pace = "超ハイペース"
elif zenhan_avg <= 34.0:
    calculation_pace = "ハイペース"
elif zenhan_avg <= 34.5:
    calculation_pace = "平均ペース"
else:
    calculation_pace = "スローペース"

# 2. 表示用ペース判定（日本語出力に使用）
if zenhan_avg <= 35.0:
    display_pace = "超ハイペース"
elif zenhan_avg <= 36.0:
    display_pace = "ハイペース"
elif zenhan_avg <= 37.0:
    display_pace = "平均ペース"
else:
    display_pace = "スローペース"
```

### 2. 内部計算での使用箇所

#### `_calculate_flow_matching`メソッド
```python
# 内部計算用ペースを使用（的中率向上のため）
pace = pace_prediction.get('calculation_pace', pace_prediction['pace'])
```

#### `_predict_finish_position`メソッド
```python
# 内部計算用ペースを使用（的中率向上のため）
pace = pace_prediction.get('calculation_pace', pace_prediction['pace'])
```

### 3. 戻り値の構造

```python
return {
    'pace': display_pace,  # 表示用（日本語出力）
    'calculation_pace': calculation_pace,  # 内部計算用（展開適性・上位馬選出）
    'confidence': confidence,
    'zenhan_avg': zenhan_avg,
    'kohan_avg': kohan_avg,
    'pace_index': (kohan_avg - zenhan_avg) * 10
}
```

## 実装ファイル
- **メインファイル**: `/mnt/e/dev/Cusor/chatbot/uma/backend/services/viewlogic_engine.py`
- **修正行番号**: 
  - 617-662行目: `_advanced_pace_prediction`メソッド
  - 841行目: `_calculate_flow_matching`内での使用
  - 1009行目: `_predict_finish_position`内での使用

## テスト結果例

### 新潟記念(G3)の例
```
前半3F平均: 35.51秒

内部計算用判定: スローペース（閾値34.5以上）
表示用判定: ハイペース（閾値35.0-36.0）

結果:
- 上位5頭の選出精度: 維持（元のロジック使用）
- 表示の多様性: 改善（ハイペースと表示）
```

## 効果

### 1. 的中率の維持
- 内部計算は元の閾値を使用
- 展開適性スコアの計算精度を保持
- 上位5頭の選出ロジックに変更なし

### 2. 表示の多様性
- ユーザーに見える日本語出力は4段階に分散
- 「スローペース」ばかりの単調な表示を回避
- より興味深い展開予想を提供

### 3. 実データでの検証結果
| レース | 前半3F | 内部判定 | 表示判定 |
|--------|--------|---------|----------|
| 新潟4R | 36.12秒 | スローペース | 平均ペース |
| 新潟記念 | 35.51秒 | スローペース | ハイペース |
| 札幌日高S | 35.03秒 | スローペース | ハイペース |

## 注意事項
1. **`calculation_pace`フィールドは必須**: 内部計算で必ず参照する
2. **後方互換性**: 既存のAPIインターフェースは維持
3. **ログ出力**: デバッグ時は両方のペースを確認可能

## 今後の拡張可能性
1. 閾値の微調整（実データの蓄積により最適化）
2. コース別の閾値設定
3. 季節・天候による動的調整

---
*実装日: 2025-09-02*
*作成者: ViewLogicエンジン開発チーム*