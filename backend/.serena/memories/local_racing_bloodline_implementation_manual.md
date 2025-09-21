# 地方競馬版 血統分析（産駒成績）実装マニュアル

## 📅 作成日: 2025-09-21
## 👤 作成者: Claude + ユーザー様
## 📝 前提: JRA版の実装完了済み（d0dd4ed）

---

## 🎯 目標
地方競馬（南関東4場：川崎・大井・船橋・浦和）の血統分析に産駒成績を追加

---

## ⚠️ JRA版での失敗から学んだ重要な教訓

### 1. ❌ **絶対にやってはいけないこと**
- **ViewLogicEngineを毎回初期化** → 39,674頭を毎回スキャンで1分以上かかる
- **インデックスなしで全データスキャン** → O(n)検索で超低速
- **100頭制限** → データ不完全でユーザーに価値なし
- **デバッグログの過剰実装** → パフォーマンス低下の原因

### 2. ✅ **必ずやるべきこと**
- **シングルトンパターン** → 初期化は起動時1回のみ
- **インデックス構築** → 起動時に種牡馬→産駒リストのマッピング作成
- **O(1)検索** → インデックスから即座に産駒リスト取得
- **全データ使用** → 制限なしで完全なデータ提供

---

## 📐 設計方針

### 1. **LocalSirePerformanceAnalyzer クラス**
```python
class LocalSirePerformanceAnalyzer:
    _instance = None  # シングルトン
    
    def __init__(self):
        # 地方競馬版マネージャーV2を使用
        from services.local_dlogic_raw_data_manager_v2 import LocalDLogicRawDataManagerV2
        self.local_manager = LocalDLogicRawDataManagerV2()  # 18,788頭
        
        # インデックス（起動時1回だけ構築）
        self.sire_index = defaultdict(list)
        self.broodmare_sire_index = defaultdict(list)
        self._build_index()
```

### 2. **フィールドマッピング（重要！）**
```python
# JRA版とは異なるフィールド名の可能性
# 必ず実データを確認してマッピング
field_mapping = {
    'venue': 'KEIBAJO_CODE',  # または別フィールド
    'distance': 'KYORI',
    'order': 'KAKUTEI_CHAKUJUN',
    'track_condition': 'BABA_JOTAI_CODE'  # 地方はダート中心
}
```

### 3. **馬場状態の扱い**
- 地方競馬は**ダート中心**
- `DIRT_BABAJOTAI_CODE`を優先的に使用
- 芝レースがある場合のみ`SHIBA_BABAJOTAI_CODE`

---

## 🔧 実装手順

### ステップ1: データ構造の確認
```python
# check_local_data_structure.py
from services.local_dlogic_raw_data_manager_v2 import LocalDLogicRawDataManagerV2
manager = LocalDLogicRawDataManagerV2()
horses_data = manager.knowledge_data.get('horses', {})

# サンプル馬のデータ構造を確認
sample_horse = list(horses_data.values())[0]
print("フィールド一覧:", sample_horse.get('races', [{}])[0].keys())
```

### ステップ2: LocalSirePerformanceAnalyzer作成
- `/services/local_sire_performance_analyzer.py`
- シングルトンパターン必須
- インデックス構築は`__init__`で1回だけ

### ステップ3: ai_handler.pyへの統合
```python
# V2AIHandler.__init__に追加
if self._is_local_racing(venue):
    from services.local_sire_performance_analyzer import get_local_sire_analyzer
    self.local_sire_analyzer = get_local_sire_analyzer()
```

### ステップ4: 会場コードマッピング
```python
local_venue_codes = {
    '川崎': '41',  # 実際のコードを確認
    '大井': '42',
    '船橋': '43', 
    '浦和': '44'
}
```

---

## 🧪 テスト計画

### 1. **単体テスト（必須）**
```python
# test_local_performance.py
def test_index_build_time():
    """インデックス構築時間が5秒以内"""
    
def test_search_speed():
    """検索が0.1秒以内"""
    
def test_data_completeness():
    """全18,788頭のデータを使用"""
```

### 2. **統合テスト**
- 川崎12Rなど実際のレースでテスト
- 16頭の血統分析が1秒以内で完了
- 馬場状態別データが正しく表示

### 3. **パフォーマンス目標**
- 初期化: 10秒以内（18,788頭）
- 検索: 0.1秒以内（インデックス使用）
- 16頭分析: 1秒以内

---

## 📋 チェックリスト

実装前：
- [ ] 地方競馬データのフィールド名を確認
- [ ] 会場コードマッピングを確認
- [ ] 馬場状態フィールドを確認（ダート中心）

実装中：
- [ ] シングルトンパターンで実装
- [ ] インデックスを起動時1回だけ構築
- [ ] 18,788頭全データを使用（制限なし）
- [ ] O(1)検索を実現

テスト：
- [ ] ローカルで速度テスト（1秒以内）
- [ ] 実際のレースデータでテスト
- [ ] 馬場状態別データの確認

デプロイ：
- [ ] テストファイル削除
- [ ] git add -A && git commit
- [ ] git push origin main

---

## 🚨 最重要ポイント

1. **パフォーマンスファースト**
   - インデックス化は必須
   - シングルトンで初期化は1回だけ
   - 全データスキャンは絶対NG

2. **データの完全性**
   - 100頭制限など絶対NG
   - 全18,788頭のデータを使用
   - 0戦のデータも表示

3. **テストの徹底**
   - 必ず実際のレースデータでテスト
   - パフォーマンス測定必須
   - 本番デプロイ前に全項目確認

---

## 📚 参考実装
- JRA版: `/services/sire_performance_analyzer.py`
- コミット: d0dd4ed（成功版）
- 避けるべき実装: 090dfed以降のデバッグログ追加版

---

## 💡 成功の鍵
「最初から正しく実装する」
- インデックス化
- シングルトン
- 全データ使用
- パフォーマンステスト

これらを最初から組み込めば、JRA版のような試行錯誤は不要！