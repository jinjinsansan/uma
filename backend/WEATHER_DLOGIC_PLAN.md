# 天候適性D-Logic実装計画

## 🎯 実装概要
標準D-Logic（良馬場）に加えて、稍重・重・不良の3パターンの天候適性分析を追加実装

## 📅 実装開始日: 2025-01-11
## 🏷️ 安定版タグ: v2.0-stable-before-weather

## ✅ 実装チェックリスト

### フェーズ1: バックエンド基盤実装（リスク: 低）

- [ ] **Step 1**: 天候適性計算メソッドの追加
  - ファイル: `/backend/services/dlogic_raw_data_manager.py`
  - メソッド: `calculate_weather_adaptive_dlogic(horse_name, baba_condition)`
  - 階層的評価方式の実装（第1層40%、第2層35%、第3層25%）

- [ ] **Step 2**: FastDLogicEngineへの統合
  - ファイル: `/backend/services/fast_dlogic_engine.py`
  - メソッド: `analyze_single_horse_weather(horse_name, baba_condition)`
  - 既存の `analyze_single_horse()` は変更しない

### フェーズ2: API実装（リスク: 中）

- [ ] **Step 3**: 天候適性APIエンドポイント
  - ファイル: `/backend/api/chat.py`
  - エンドポイント: `/api/chat/weather-analysis`
  - リクエスト形式:
    ```json
    {
      "horse_names": ["レガレイラ"],
      "baba_condition": 3,  // 1=良, 2=稍重, 3=重, 4=不良
      "original_result": {...}
    }
    ```

### フェーズ3: フロントエンドUI実装（リスク: 中〜高）

- [ ] **Step 4**: 天候選択ボタンコンポーネント
  - 新規ファイル: `/frontend/src/components/chat/WeatherConditionSelector.tsx`
  - Binanceスタイルの4ボタン（良・稍重・重・不良）
  - モバイル対応2×2グリッド

- [ ] **Step 5**: DLogicChatInterfaceの拡張
  - ファイル: `/frontend/src/components/chat/DLogicChatInterface.tsx`
  - 標準分析後に天候ボタンを表示
  - 天候選択時の追加分析表示

### フェーズ4: 統合テスト（リスク: 高）

- [ ] **Step 6**: エンドツーエンドテスト
  - レガレイラで4パターンテスト
  - 複数馬での動作確認
  - パフォーマンス測定

## 🚨 リスクと対策

### 高リスク
1. **チャット状態管理**: 標準結果を保持してdiff表示
2. **複数馬計算負荷**: 選択された天候のみ計算
3. **レスポンス遅延**: 非同期処理とプログレス表示

### 中リスク
1. **UI一貫性**: 既存Binanceスタイルを踏襲
2. **モバイル対応**: 2×2グリッドレイアウト

## 🔙 ロールバック手順
```bash
# 問題発生時は安定版に戻る
git checkout v2.0-stable-before-weather

# 特定ステップのコミットに戻る
git log --oneline | grep "Step"
git checkout <commit-hash>
```

## 📝 コミットメッセージ規約
```
feat(weather): Step 1 - Add weather adaptive calculation method
feat(weather): Step 2 - Integrate weather analysis to FastDLogicEngine
feat(weather): Step 3 - Add weather analysis API endpoint
feat(weather): Step 4 - Create weather condition selector component
feat(weather): Step 5 - Extend chat interface for weather analysis
test(weather): Step 6 - Complete end-to-end testing
```

## 🎯 成功基準
- [ ] レガレイラで良/稍重/重/不良の4パターンが表示される
- [ ] 計算時間が2秒以内
- [ ] モバイルでも操作しやすい
- [ ] 既存機能に影響なし

## 📊 階層的評価方式の詳細

### 第1層（基礎能力）40%
- 馬体重評価（470kg以上でボーナス）
- 過去の該当馬場実績
- 血統の馬場適性（実装保留）

### 第2層（適応能力）35%
- 騎手の該当馬場成績
- 調教師の該当馬場調整力
- 脚質（逃げ先行にボーナス）

### 第3層（当日要因）25%
- 枠順補正（重馬場で内枠不利解消）
- 展開予想（簡易版）
- 馬場の部分的な状態差（簡易版）