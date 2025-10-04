# N-Logic開発計画書
**新エンジン「N-Logic」- netkeibaのQuerySoftmax手法を参考にしたレース予測エンジン**

作成日: 2025-10-04  
バージョン: 1.0

---

## 📌 プロジェクト概要

### 目的
netkeibaの機械学習手法（CatBoost + QuerySoftmax）を参考に、レース単位で力関係を考慮した新予測エンジン「N-Logic」を開発する。

### 既存エンジンとの違い

| 項目 | D-Logic（既存） | N-Logic（新） |
|------|----------------|---------------|
| 予測単位 | 馬単体（独立予測） | **レース全体（力関係考慮）** |
| 機械学習 | ロジスティック回帰 | **CatBoost + QuerySoftmax** |
| 出力 | スコア（10-85点） | **支持率（合計1.0）→オッズ** |
| 後処理 | 比率計算が必要 | **不要（モデル内で完結）** |
| ナレッジ | unified_knowledge_20250903.json | **同じファイルを使用** |

### 参考資料
- netkeiba記事: https://logmi.jp/main/technology/330671
- netkeiba記事: https://logmi.jp/main/technology/330672

---

## 🏗️ システム構成

### ファイル構成
```
/mnt/e/dev/Cusor/chatbot/uma/backend/
├── services/
│   ├── nlogic_engine.py              # 【新規】N-Logicエンジン本体
│   ├── local_nlogic_engine_v2.py     # 【新規】地方競馬版N-Logic
│   └── v2/
│       └── ai_handler.py             # 【修正】N-Logicキーワード追加
├── data/
│   ├── nlogic_rank_model.cbm         # 【新規】順位予測モデル（学習後）
│   ├── nlogic_support_model.cbm      # 【新規】支持率予測モデル（学習後）
│   └── nlogic_training_config.json   # 【新規】学習設定
└── scripts/
    └── train_nlogic_model.py         # 【新規】学習パイプライン

/mnt/e/dev/Cusor/front/d-logic-ai-frontend/
└── claude-tools/race-analysis/
    ├── train_nlogic_pipeline.py      # 【新規】学習データ準備
    └── evaluate_nlogic.py            # 【新規】精度評価
```

---

## 📐 技術仕様

### 1. アルゴリズム

#### Phase 1: 順位予測（Rank Model）
```python
# CatBoost Ranker使用
# 目的: 上位馬の精度を優先するためのWeight生成

入力: 特徴量（各馬）
出力: rank_weights（各馬のスコア、Softmaxで正規化）

損失関数: PairwiseRanking
```

#### Phase 2: 支持率予測（Support Rate Model）
```python
# CatBoost + QuerySoftmax使用
# 目的: レース内の力関係を考慮した支持率予測

入力: 特徴量 + rank_weights
出力: support_rates（合計1.0の支持率）

損失関数: QuerySoftmax
- 自動的に合計1.0になる
- レース単位でグループ化
```

#### Phase 3: オッズ変換
```python
オッズ = 払戻率(0.8) / 支持率

例: 支持率35% → 0.8 / 0.35 = 2.3倍
```

### 2. 特徴量（D-Logicと同じ）

```python
features = {
    # 馬のナレッジ（CDN: unified_knowledge_20250903.json）
    'knowledge_total_races': 馬の総レース数,
    'knowledge_win_rate': 勝率,
    'knowledge_place_rate': 複勝率,
    'knowledge_avg_finish': 平均着順,
    'knowledge_avg_popularity': 平均人気,
    'knowledge_avg_corner4': 平均4コーナー順位,
    'knowledge_avg_kohan3f': 平均後半3F,
    
    # コース別成績
    'track_win_rate': コース別勝率,
    'track_avg_finish': コース別平均着順,
    
    # 距離適性
    'distance_aptitude': 距離適性スコア,
    
    # 騎手
    'jockey_win_rate': 騎手勝率,
    'jockey_place_rate': 騎手複勝率,
    
    # レースメタ情報
    'venue_code': 競馬場コード,
    'distance': 距離,
    'horse_count': 出走頭数,
}
```

### 3. ナレッジファイル（既存を使用）

```python
# JRA版
CDN_URL = "https://pub-c02b485a66fb4530a37c7faf4fea76e9.r2.dev/unified_knowledge_20250903.json"

# 地方競馬版
CDN_URL = "https://pub-c02b485a66fb4530a37c7faf4fea76e9.r2.dev/nar_unified_knowledge_v9_perfect_20250930.json"
```

---

## 🚀 開発ステップ（詳細）

---

### 【Phase 1: 環境準備・骨格作成】

#### Step 1-1: CatBoostインストール確認

**目的**: CatBoostライブラリがインストール済みか確認

**コマンド**:
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 -m pip list | grep -i catboost
```

**期待される出力**:
- インストール済み: `catboost    1.2.x`
- 未インストール: 何も表示されない

**未インストールの場合**:
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 -m pip install catboost
```

**確認**:
```bash
python3 -c "import catboost; print(catboost.__version__)"
```

---

#### Step 1-2: N-Logicエンジン骨格作成（JRA版）

**ファイルパス**: `/mnt/e/dev/Cusor/chatbot/uma/backend/services/nlogic_engine.py`

**目的**: N-Logicエンジンの基本構造を作成

**実装内容**:
```python
"""
N-Logic Engine - netkeibaのQuerySoftmax手法を参考にしたレース予測エンジン
レース単位で力関係を考慮した支持率予測 → オッズ変換
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

# CatBoostは学習時のみ使用、予測時は動的インポート
try:
    from catboost import CatBoost, Pool
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    logger.warning("CatBoost not available")


class NLogicEngine:
    """N-Logic予測エンジン"""
    
    # 定数
    PAYBACK_RATE = 0.8  # 単勝払戻率
    
    def __init__(self):
        """初期化"""
        self.rank_model = None
        self.support_model = None
        self._load_models()
        
        # KnowledgeDataManagerは既存のものを使用
        from services.knowledge_data_manager import KnowledgeDataManager
        self.knowledge_manager = KnowledgeDataManager()
        
        logger.info("N-Logicエンジンを初期化しました")
    
    def _load_models(self):
        """学習済みモデルの読み込み"""
        try:
            if not CATBOOST_AVAILABLE:
                logger.warning("CatBoost未インストール、モデル読み込みスキップ")
                return
            
            base_dir = os.path.dirname(os.path.dirname(__file__))
            rank_model_path = os.path.join(base_dir, 'data', 'nlogic_rank_model.cbm')
            support_model_path = os.path.join(base_dir, 'data', 'nlogic_support_model.cbm')
            
            if os.path.exists(rank_model_path):
                self.rank_model = CatBoost()
                self.rank_model.load_model(rank_model_path)
                logger.info(f"Rank Modelを読み込みました: {rank_model_path}")
            else:
                logger.warning(f"Rank Modelが見つかりません: {rank_model_path}")
            
            if os.path.exists(support_model_path):
                self.support_model = CatBoost()
                self.support_model.load_model(support_model_path)
                logger.info(f"Support Modelを読み込みました: {support_model_path}")
            else:
                logger.warning(f"Support Modelが見つかりません: {support_model_path}")
                
        except Exception as e:
            logger.error(f"モデル読み込みエラー: {e}")
    
    def predict_race(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レース全体のオッズを予測
        
        Args:
            race_data: {
                'horses': ['馬A', '馬B', ...],
                'jockeys': ['騎手1', '騎手2', ...],
                'venue': '東京',
                'race_number': 11,
                'distance': 2000,
                ...
            }
        
        Returns:
            {
                'status': 'success',
                'predictions': {
                    '馬A': {'support_rate': 0.35, 'odds': 2.3, 'rank': 1},
                    '馬B': {'support_rate': 0.25, 'odds': 3.2, 'rank': 2},
                    ...
                },
                'venue': '東京',
                'race_number': 11,
            }
        """
        try:
            # モデル未読み込みの場合はエラー
            if self.rank_model is None or self.support_model is None:
                return {
                    'status': 'error',
                    'message': 'N-Logicモデルが読み込まれていません。学習を実行してください。'
                }
            
            horses = race_data.get('horses', [])
            if len(horses) < 3:
                return {
                    'status': 'error',
                    'message': 'レースには最低3頭の出走馬が必要です。'
                }
            
            # Step 1: 特徴量抽出
            features_list = self._extract_features_for_race(race_data)
            
            # Step 2: 順位予測（Rank Weight生成）
            rank_weights = self._predict_rank_weights(features_list)
            
            # Step 3: 支持率予測
            support_rates = self._predict_support_rates(features_list, rank_weights)
            
            # Step 4: オッズ変換
            predictions = self._convert_to_odds(support_rates, horses)
            
            return {
                'status': 'success',
                'type': 'nlogic_prediction',
                'venue': race_data.get('venue', '不明'),
                'race_number': race_data.get('race_number', ''),
                'total_horses': len(horses),
                'predictions': predictions,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"N-Logic予測エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'予測に失敗しました: {str(e)}'
            }
    
    def _extract_features_for_race(self, race_data: Dict[str, Any]) -> List[Dict[str, float]]:
        """レース内全頭の特徴量抽出"""
        # TODO: 実装（次のステップ）
        pass
    
    def _predict_rank_weights(self, features_list: List[Dict]) -> np.ndarray:
        """順位予測（Rank Weight生成）"""
        # TODO: 実装（次のステップ）
        pass
    
    def _predict_support_rates(
        self, 
        features_list: List[Dict], 
        rank_weights: np.ndarray
    ) -> np.ndarray:
        """支持率予測（QuerySoftmax的手法）"""
        # TODO: 実装（次のステップ）
        pass
    
    def _convert_to_odds(
        self,
        support_rates: np.ndarray,
        horse_names: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """支持率 → オッズ変換"""
        results = {}
        
        # 順位付け
        ranked_indices = np.argsort(-support_rates)  # 降順
        
        for i, horse_name in enumerate(horse_names):
            support_rate = support_rates[i]
            odds = self.PAYBACK_RATE / support_rate if support_rate > 0 else 999.9
            rank = int(np.where(ranked_indices == i)[0][0] + 1)
            
            results[horse_name] = {
                'support_rate': float(support_rate),
                'odds': round(odds, 1),
                'rank': rank,
                'probability': float(support_rate),
            }
        
        return results
```

**作成コマンド**:
```bash
# Createツールで上記コードを /mnt/e/dev/Cusor/chatbot/uma/backend/services/nlogic_engine.py に保存
```

---

#### Step 1-3: 学習パイプライン骨格作成

**ファイルパス**: `/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/train_nlogic_model.py`

**目的**: モデル学習のためのスクリプト骨格

**実装内容**:
```python
"""
N-Logic モデル学習パイプライン
過去レースデータから2つのモデルを学習
1. Rank Model（順位予測）
2. Support Rate Model（支持率予測、QuerySoftmax）
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from catboost import CatBoostRanker, CatBoostRegressor, Pool

# バックエンドのパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def load_training_data(data_path: str):
    """学習データの読み込み"""
    # TODO: 実装
    # 形式: CSV or JSON
    # 列: race_id, horse_name, 特徴量..., actual_rank, actual_support_rate
    pass

def prepare_features(df: pd.DataFrame):
    """特徴量の準備"""
    # TODO: 実装
    pass

def train_rank_model(X_train, y_train, group_ids):
    """Rank Modelの学習"""
    print("🔧 Rank Model学習開始...")
    
    # CatBoost Ranker
    model = CatBoostRanker(
        iterations=1000,
        learning_rate=0.03,
        depth=6,
        loss_function='PairLogit',
        verbose=100
    )
    
    # Poolデータ作成（group_id必須）
    train_pool = Pool(
        data=X_train,
        label=y_train,
        group_id=group_ids
    )
    
    model.fit(train_pool)
    
    print("✅ Rank Model学習完了")
    return model

def train_support_model(X_train, y_train, group_ids, rank_weights):
    """Support Rate Modelの学習（QuerySoftmax）"""
    print("🔧 Support Rate Model学習開始...")
    
    # Rank Weightを特徴量に追加
    X_train_with_weight = X_train.copy()
    X_train_with_weight['rank_weight'] = rank_weights
    
    # CatBoost + QuerySoftmax
    model = CatBoostRegressor(
        iterations=1000,
        learning_rate=0.03,
        depth=6,
        loss_function='QuerySoftMax',  # ←これが核心！
        verbose=100
    )
    
    # Poolデータ作成
    train_pool = Pool(
        data=X_train_with_weight,
        label=y_train,
        group_id=group_ids
    )
    
    model.fit(train_pool)
    
    print("✅ Support Rate Model学習完了")
    return model

def save_models(rank_model, support_model, output_dir):
    """モデルの保存"""
    os.makedirs(output_dir, exist_ok=True)
    
    rank_path = os.path.join(output_dir, 'nlogic_rank_model.cbm')
    support_path = os.path.join(output_dir, 'nlogic_support_model.cbm')
    
    rank_model.save_model(rank_path)
    support_model.save_model(support_path)
    
    print(f"✅ モデル保存完了:")
    print(f"  - Rank Model: {rank_path}")
    print(f"  - Support Model: {support_path}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("N-Logic モデル学習パイプライン")
    print("=" * 60)
    
    # TODO: データパス指定
    data_path = "path/to/training_data.csv"
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # Step 1: データ読み込み
    # df = load_training_data(data_path)
    
    # Step 2: 特徴量準備
    # X_train, y_rank, y_support, group_ids = prepare_features(df)
    
    # Step 3: Rank Model学習
    # rank_model = train_rank_model(X_train, y_rank, group_ids)
    
    # Step 4: Rank Weight生成
    # rank_weights = rank_model.predict(X_train)
    
    # Step 5: Support Model学習
    # support_model = train_support_model(X_train, y_support, group_ids, rank_weights)
    
    # Step 6: モデル保存
    # save_models(rank_model, support_model, output_dir)
    
    print("🎉 すべての学習が完了しました！")

if __name__ == '__main__':
    main()
```

---

### 【Phase 2: データ準備・特徴量実装】

#### Step 2-1: 学習データの準備

**目的**: 過去レースの結果データを収集

**必要なデータ**:
```
race_id, date, venue, race_number, distance, horse_name, jockey_name,
actual_rank（実際の着順）, actual_odds（実際のオッズ）,
特徴量13個...
```

**データソース候補**:
1. PostgreSQLデータベース（JVD_SE, NVD_SEテーブル）
2. 既存の予想結果JSON（`claude-tools/race-analysis/output/`）
3. TSファイル（`src/data/archive/races-*.ts`）

**推奨**: PostgreSQLから抽出

**抽出SQL例**:
```sql
-- JRA版
SELECT 
    CONCAT(kaisai_nengappi, '-', keibajo_code, '-', race_bango) as race_id,
    kaisai_nengappi as date,
    keibajo_code as venue_code,
    race_bango as race_number,
    kyori as distance,
    bamei as horse_name,
    kishu_mei as jockey_name,
    kakutei_chakujun as actual_rank,
    tansho_odds as actual_odds
FROM jvd_se
WHERE kaisai_nengappi >= '2024-08-31'
  AND kaisai_nengappi <= '2025-09-28'
  AND kakutei_chakujun IS NOT NULL
ORDER BY race_id, actual_rank;
```

**実行方法**:
```bash
cd /mnt/e/dev/Cusor/front/d-logic-ai-frontend/claude-tools/race-analysis
node -e "
const { Pool } = require('pg');
const fs = require('fs');
require('dotenv').config();

const pool = new Pool({ connectionString: process.env.JVD_DATABASE_URL });

pool.query(\`
  SELECT ...（上記SQL）
\`).then(result => {
  fs.writeFileSync('nlogic_training_data.json', JSON.stringify(result.rows, null, 2));
  console.log('✅ データ抽出完了:', result.rows.length, 'レース');
  pool.end();
});
"
```

---

#### Step 2-2: 特徴量抽出メソッドの実装

**ファイル**: `/mnt/e/dev/Cusor/chatbot/uma/backend/services/nlogic_engine.py`

**実装箇所**: `_extract_features_for_race()` メソッド

**詳細実装**:
```python
def _extract_features_for_race(self, race_data: Dict[str, Any]) -> List[Dict[str, float]]:
    """レース内全頭の特徴量抽出"""
    horses = race_data.get('horses', [])
    jockeys = race_data.get('jockeys', [])
    venue = race_data.get('venue', '')
    distance = race_data.get('distance', 0)
    
    features_list = []
    
    for i, horse_name in enumerate(horses):
        # ナレッジデータ取得（既存のKnowledgeDataManagerを使用）
        horse_knowledge = self.knowledge_manager.get_horse_knowledge(horse_name)
        
        jockey_name = jockeys[i] if i < len(jockeys) else None
        
        features = {
            # 馬のナレッジ
            'knowledge_total_races': horse_knowledge.get('total_races', 0),
            'knowledge_win_rate': horse_knowledge.get('win_rate', 0.0),
            'knowledge_place_rate': horse_knowledge.get('place_rate', 0.0),
            'knowledge_avg_finish': horse_knowledge.get('avg_finish', 10.0),
            'knowledge_avg_popularity': horse_knowledge.get('avg_popularity', 8.0),
            'knowledge_avg_corner4': horse_knowledge.get('avg_corner4', 8.0),
            'knowledge_avg_kohan3f': horse_knowledge.get('avg_kohan3f', 400),
            
            # コース別成績
            'track_win_rate': self._get_track_win_rate(horse_knowledge, venue),
            'track_avg_finish': self._get_track_avg_finish(horse_knowledge, venue),
            
            # 距離適性（D-Logicと同じロジック）
            'distance_aptitude': self._calc_distance_aptitude(horse_knowledge, distance),
            
            # 騎手（簡易版）
            'jockey_win_rate': 0.1,  # TODO: 騎手データ取得
            'jockey_place_rate': 0.3,
            
            # レースメタ情報
            'venue_code': self._get_venue_code(venue),
            'distance': float(distance),
            'horse_count': len(horses),
        }
        
        features_list.append(features)
    
    return features_list

def _get_track_win_rate(self, knowledge: Dict, venue: str) -> float:
    """コース別勝率"""
    track_stats = knowledge.get('track_stats', {})
    venue_data = track_stats.get(venue, {})
    return venue_data.get('win_rate', 0.0)

def _get_track_avg_finish(self, knowledge: Dict, venue: str) -> float:
    """コース別平均着順"""
    track_stats = knowledge.get('track_stats', {})
    venue_data = track_stats.get(venue, {})
    return venue_data.get('avg_finish', 10.0)

def _calc_distance_aptitude(self, knowledge: Dict, target_distance: int) -> float:
    """距離適性（D-Logicと同じ）"""
    # 簡易実装
    distance_stats = knowledge.get('distance_stats', {})
    if not distance_stats:
        return 0.5
    
    # 最も近い距離の成績を使用
    closest_dist = min(distance_stats.keys(), 
                      key=lambda d: abs(int(d) - target_distance),
                      default=None)
    if closest_dist:
        return distance_stats[closest_dist].get('win_rate', 0.0)
    return 0.5

def _get_venue_code(self, venue: str) -> int:
    """競馬場コード"""
    venue_map = {
        '札幌': 1, '函館': 2, '福島': 3, '新潟': 4,
        '東京': 5, '中山': 6, '中京': 7, '京都': 8,
        '阪神': 9, '小倉': 10
    }
    return venue_map.get(venue, 0)
```

---

#### Step 2-3: Rank Weight予測メソッドの実装

**実装箇所**: `_predict_rank_weights()` メソッド

```python
def _predict_rank_weights(self, features_list: List[Dict]) -> np.ndarray:
    """順位予測（Rank Weight生成）"""
    import pandas as pd
    
    # DataFrameに変換
    df = pd.DataFrame(features_list)
    
    # Rank Modelで予測
    rank_scores = self.rank_model.predict(df)
    
    # Softmaxで正規化
    rank_weights = self._softmax(rank_scores)
    
    return rank_weights

def _softmax(self, scores: np.ndarray) -> np.ndarray:
    """Softmax関数"""
    exp_scores = np.exp(scores - np.max(scores))
    return exp_scores / np.sum(exp_scores)
```

---

#### Step 2-4: Support Rate予測メソッドの実装

**実装箇所**: `_predict_support_rates()` メソッド

```python
def _predict_support_rates(
    self,
    features_list: List[Dict],
    rank_weights: np.ndarray
) -> np.ndarray:
    """支持率予測（QuerySoftmax的手法）"""
    import pandas as pd
    
    # DataFrameに変換
    df = pd.DataFrame(features_list)
    
    # Rank Weightを特徴量に追加
    df['rank_weight'] = rank_weights
    
    # Support Modelで予測
    support_rates = self.support_model.predict(df)
    
    # 念のため正規化（QuerySoftmaxは自動で合計1.0だが）
    support_rates = np.maximum(support_rates, 0)  # 負値防止
    total = np.sum(support_rates)
    if total > 0:
        support_rates = support_rates / total
    else:
        # 全て0の場合は均等割
        support_rates = np.ones(len(support_rates)) / len(support_rates)
    
    return support_rates
```

---

### 【Phase 3: 学習実行】

#### Step 3-1: 学習データCSVの作成

**実装**: データ準備スクリプト

**ファイル**: `/mnt/e/dev/Cusor/front/d-logic-ai-frontend/claude-tools/race-analysis/prepare_nlogic_data.py`

```python
"""
N-Logic学習データ準備スクリプト
PostgreSQLから過去レース結果を取得し、特徴量付きCSVを生成
"""

import os
import sys
import json
import pandas as pd
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# バックエンドパスを追加
sys.path.insert(0, '/mnt/e/dev/Cusor/chatbot/uma/backend')

from services.knowledge_data_manager import KnowledgeDataManager

def fetch_race_results():
    """PostgreSQLからレース結果を取得"""
    conn = psycopg2.connect(os.getenv('JVD_DATABASE_URL'))
    
    query = """
    SELECT 
        CONCAT(kaisai_nengappi, '-', keibajo_code, '-', race_bango) as race_id,
        kaisai_nengappi as date,
        keibajo_code as venue_code,
        race_bango as race_number,
        kyori as distance,
        bamei as horse_name,
        kishu_mei as jockey_name,
        kakutei_chakujun as actual_rank,
        tansho_odds::float / 10.0 as actual_odds
    FROM jvd_se
    WHERE kaisai_nengappi >= '2024-08-31'
      AND kaisai_nengappi <= '2025-09-28'
      AND kakutei_chakujun IS NOT NULL
      AND kakutei_chakujun > 0
    ORDER BY race_id, actual_rank
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"✅ {len(df)}件のレース結果を取得")
    return df

def add_features(df):
    """特徴量を追加"""
    km = KnowledgeDataManager()
    
    features = []
    
    for idx, row in df.iterrows():
        horse_name = row['horse_name']
        knowledge = km.get_horse_knowledge(horse_name)
        
        feat = {
            'race_id': row['race_id'],
            'horse_name': horse_name,
            'actual_rank': row['actual_rank'],
            'actual_odds': row['actual_odds'],
            'actual_support_rate': 0.8 / row['actual_odds'] if row['actual_odds'] > 0 else 0.0,
            
            # 特徴量
            'knowledge_total_races': knowledge.get('total_races', 0),
            'knowledge_win_rate': knowledge.get('win_rate', 0.0),
            'knowledge_place_rate': knowledge.get('place_rate', 0.0),
            'knowledge_avg_finish': knowledge.get('avg_finish', 10.0),
            'knowledge_avg_popularity': knowledge.get('avg_popularity', 8.0),
            'knowledge_avg_corner4': knowledge.get('avg_corner4', 8.0),
            'knowledge_avg_kohan3f': knowledge.get('avg_kohan3f', 400),
            
            'venue_code': row['venue_code'],
            'distance': row['distance'],
        }
        
        features.append(feat)
        
        if (idx + 1) % 100 == 0:
            print(f"  処理中: {idx + 1}/{len(df)}")
    
    return pd.DataFrame(features)

def main():
    print("=" * 60)
    print("N-Logic 学習データ準備")
    print("=" * 60)
    
    # Step 1: レース結果取得
    df_results = fetch_race_results()
    
    # Step 2: 特徴量追加
    df_with_features = add_features(df_results)
    
    # Step 3: CSV保存
    output_path = 'nlogic_training_data.csv'
    df_with_features.to_csv(output_path, index=False)
    
    print(f"✅ 学習データ保存: {output_path}")
    print(f"  総レコード数: {len(df_with_features)}")
    print(f"  ユニークレース数: {df_with_features['race_id'].nunique()}")

if __name__ == '__main__':
    main()
```

---

#### Step 3-2: 学習の実行

**コマンド**:
```bash
# Step 1: データ準備
cd /mnt/e/dev/Cusor/front/d-logic-ai-frontend/claude-tools/race-analysis
python3 prepare_nlogic_data.py

# Step 2: 学習実行
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 scripts/train_nlogic_model.py
```

**期待される出力**:
```
🔧 Rank Model学習開始...
0:  learn: 0.6543  total: 50ms  remaining: 1m 30s
100:  learn: 0.5234  total: 5s  remaining: 45s
...
✅ Rank Model学習完了

🔧 Support Rate Model学習開始...
0:  learn: 0.0234  total: 60ms  remaining: 1m 40s
100:  learn: 0.0123  total: 6s  remaining: 54s
...
✅ Support Rate Model学習完了

✅ モデル保存完了:
  - Rank Model: data/nlogic_rank_model.cbm
  - Support Model: data/nlogic_support_model.cbm

🎉 すべての学習が完了しました！
```

---

### 【Phase 4: ai_handlerへの統合】

#### Step 4-1: ai_handlerにN-Logicキーワード追加

**ファイル**: `/mnt/e/dev/Cusor/chatbot/uma/backend/services/v2/ai_handler.py`

**修正箇所1**: キーワード定義（55行目付近）

```python
self.AI_KEYWORDS = {
    'imlogic': ['分析', '評価', 'IMLogic', 'IM', 'アイエム'],
    'viewlogic_trend': ['騎手分析', '傾向', 'トレンド', '統計', 'コース傾向', '騎手成績', '枠順'],
    'viewlogic_recommendation': ['推奨', 'おすすめ', '買い目', '馬券', '予想'],
    'viewlogic_flow': ['展開', '流れ', 'ペース', '4コーナー', '直線'],
    'viewlogic_horse_history': ['過去成績', '馬の実績', 'レース履歴', '戦績', '過去レース'],
    'viewlogic_jockey_history': ['騎手の過去', '騎乗実績', '騎手履歴'],
    'viewlogic_sire': ['種牡馬分析', '種牡馬', '父', '母父', '血統分析', '父馬', '母馬', '母父馬', 'sire', 'dam', 'broodmare'],
    'viewlogic_sire_father': ['血統父のみ', '血統父分析', '種牡馬のみ', '父馬のみ', '父だけ分析'],
    'viewlogic_sire_broodmare': ['血統母父のみ', '血統母父分析', '母父のみ', 'ブルードメアサイア', '母父だけ分析'],
    'viewlogic_data': ['データ上位', 'データ分析', 'データ抽出', '複勝率上位', '上位3頭', '上位三頭', 'トップ3'],
    'dlogic': ['d-logic', 'ディーロジック', 'D-Logic', 'Dロジック', '指数', 'スコア', '12項目', '評価点'],
    'ilogic': ['i-logic', 'ilogic', 'アイロジック', 'I-Logic', 'Iロジック', '騎手', '総合', 'レースアナリシス', 'アナリシス'],
    'nlogic': ['n-logic', 'nlogic', 'エヌロジック', 'N-Logic', 'Nロジック', 'オッズ予測', '支持率', 'レース予測'],  # ← 追加
    'flogic': ['f-logic', 'flogic', 'エフロジック', 'F-Logic', 'Fロジック', 'フェア値']
}
```

**修正箇所2**: インポート（12行目付近）

```python
from services.imlogic_engine import IMLogicEngine
from services.dlogic_raw_data_manager import DLogicRawDataManager
from services.nlogic_engine import NLogicEngine  # ← 追加
```

**修正箇所3**: エンジン初期化（32行目付近）

```python
def __init__(self):
    # IMLogicEngineは毎回新規作成するため、ここでは初期化しない
    # /logic-chatと同じ動作を保証
    # DLogicRawDataManagerは血統分析で使用するため初期化
    self.dlogic_manager = None
    self.nlogic_engine = None  # ← 追加
    try:
        from services.dlogic_raw_data_manager import DLogicRawDataManager
        self.dlogic_manager = DLogicRawDataManager()
        logger.info("DLogicRawDataManager initialized for V2")
    except Exception as e:
        logger.error(f"Failed to initialize DLogicRawDataManager: {e}")
    
    # N-Logic初期化  ← 追加
    try:
        from services.nlogic_engine import NLogicEngine
        self.nlogic_engine = NLogicEngine()
        logger.info("NLogicEngine initialized for V2")
    except Exception as e:
        logger.error(f"Failed to initialize NLogicEngine: {e}")
```

**修正箇所4**: AI判定メソッド（500行目付近）

```python
# N-Logic（オッズ予測）  ← 追加
if any(keyword in message_lower for keyword in self.AI_KEYWORDS['nlogic']):
    return ('nlogic', 'prediction')
```

**修正箇所5**: 処理メソッド（1500行目付近、`process_message()`内）

```python
elif ai_type == 'nlogic':
    logger.info(f"N-Logic処理開始: sub_type={sub_type}")
    result = self._handle_nlogic(race_data, sub_type)
    if result.get('status') == 'success':
        response = self._format_nlogic_result(result)
    else:
        response = f"⚠️ N-Logic予測に失敗しました: {result.get('message', '不明なエラー')}"
```

**修正箇所6**: ハンドラーメソッド（最後に追加）

```python
def _handle_nlogic(self, race_data: Dict[str, Any], sub_type: str) -> Dict[str, Any]:
    """N-Logic処理"""
    try:
        if self.nlogic_engine is None:
            return {
                'status': 'error',
                'message': 'N-Logicエンジンが初期化されていません'
            }
        
        result = self.nlogic_engine.predict_race(race_data)
        return result
        
    except Exception as e:
        logger.error(f"N-Logic処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': f'N-Logic処理に失敗しました: {str(e)}'
        }

def _format_nlogic_result(self, result: Dict[str, Any]) -> str:
    """N-Logic結果のフォーマット"""
    try:
        lines = []
        lines.append("🎯 N-Logic オッズ予測")
        
        venue = result.get('venue', '不明')
        race_number = result.get('race_number', '')
        total_horses = result.get('total_horses', 0)
        
        if race_number:
            lines.append(f"{venue} {race_number}R")
        else:
            lines.append(f"{venue}")
        lines.append(f"出走頭数: {total_horses}頭")
        lines.append("")
        
        # 予測結果
        predictions = result.get('predictions', {})
        if not predictions:
            lines.append("⚠️ 予測結果がありません")
            return "\n".join(lines)
        
        # 順位順にソート
        sorted_predictions = sorted(
            predictions.items(),
            key=lambda x: x[1]['rank']
        )
        
        lines.append("【予測オッズ】")
        lines.append("")
        
        for horse_name, pred in sorted_predictions[:10]:  # 上位10頭
            rank = pred['rank']
            odds = pred['odds']
            support_rate = pred['support_rate'] * 100
            
            emoji = ['🥇', '🥈', '🥉'][rank-1] if rank <= 3 else f"{rank}位"
            
            lines.append(f"{emoji} {horse_name}")
            lines.append(f"  オッズ: {odds}倍  支持率: {support_rate:.1f}%")
            lines.append("")
        
        lines.append("---")
        lines.append("💡 N-Logicはレース内の力関係を考慮したオッズ予測エンジンです")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"N-Logic結果フォーマットエラー: {e}")
        return f"⚠️ 結果の表示に失敗しました: {str(e)}"
```

---

### 【Phase 5: テスト・デプロイ】

#### Step 5-1: ローカルテスト

**テストスクリプト**: `/mnt/e/dev/Cusor/chatbot/uma/backend/test_nlogic.py`

```python
"""N-Logicエンジンのテストスクリプト"""

from services.nlogic_engine import NLogicEngine

def test_nlogic():
    print("=" * 60)
    print("N-Logicエンジン テスト")
    print("=" * 60)
    
    # エンジン初期化
    engine = NLogicEngine()
    
    # テストデータ
    race_data = {
        'horses': ['ドウデュース', 'イクイノックス', 'タイトルホルダー', 
                   'ジャックドール', 'パンサラッサ'],
        'jockeys': ['川田将雅', 'ルメール', '横山和生', '岩田康誠', '吉田隼人'],
        'venue': '東京',
        'race_number': 11,
        'distance': 2000,
    }
    
    # 予測実行
    result = engine.predict_race(race_data)
    
    # 結果表示
    print("\n【予測結果】")
    print(f"ステータス: {result.get('status')}")
    
    if result['status'] == 'success':
        predictions = result['predictions']
        sorted_pred = sorted(predictions.items(), key=lambda x: x[1]['rank'])
        
        print(f"\n{result['venue']} {result['race_number']}R")
        print(f"出走頭数: {result['total_horses']}頭\n")
        
        for horse, pred in sorted_pred:
            print(f"{pred['rank']}位: {horse}")
            print(f"  オッズ: {pred['odds']}倍")
            print(f"  支持率: {pred['support_rate']*100:.1f}%")
            print()
    else:
        print(f"エラー: {result.get('message')}")

if __name__ == '__main__':
    test_nlogic()
```

**実行**:
```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 test_nlogic.py
```

---

#### Step 5-2: Git コミット・プッシュ

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend

git add services/nlogic_engine.py
git add services/v2/ai_handler.py
git add scripts/train_nlogic_model.py
git add data/nlogic_rank_model.cbm
git add data/nlogic_support_model.cbm

git commit -m "feat: N-Logicエンジン実装（QuerySoftmax手法）

- CatBoost + QuerySoftmaxでレース単位オッズ予測
- Rank Model（順位予測）+ Support Model（支持率予測）
- ai_handlerに統合、V2チャットで利用可能
- 学習パイプライン実装

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"

git push origin main
```

---

#### Step 5-3: Renderデプロイ確認

**Renderログ確認**:
```
[Build] Installing dependencies...
[Build] pip install -r requirements.txt
[Build] catboost==1.2.x installed
[Deploy] Starting service...
[Deploy] NLogicEngine initialized for V2
[Deploy] Service ready
```

---

#### Step 5-4: V2チャットでテスト

**テストメッセージ**:
```
東京11R N-Logic
```

**期待される出力**:
```
🎯 N-Logic オッズ予測
東京 11R
出走頭数: 16頭

【予測オッズ】

🥇 ドウデュース
  オッズ: 2.3倍  支持率: 34.8%

🥈 イクイノックス
  オッズ: 3.2倍  支持率: 25.0%

🥉 タイトルホルダー
  オッズ: 4.5倍  支持率: 17.8%

...

💡 N-Logicはレース内の力関係を考慮したオッズ予測エンジンです
```

---

## 📝 トラブルシューティング

### 問題1: CatBoostインストールエラー

**症状**: `pip install catboost` でエラー

**解決策**:
```bash
# 古いpipをアップグレード
python3 -m pip install --upgrade pip

# システムパッケージインストール
sudo apt-get update
sudo apt-get install -y python3-dev

# 再度インストール
python3 -m pip install catboost
```

---

### 問題2: モデル読み込みエラー

**症状**: `nlogic_rank_model.cbm not found`

**原因**: モデルがまだ学習されていない

**解決策**:
```bash
# 学習パイプライン実行
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 scripts/train_nlogic_model.py
```

---

### 問題3: 予測時にエラー

**症状**: `predict_race()` でエラー

**確認事項**:
1. モデルが正しく読み込まれているか
2. 特徴量の数が学習時と一致しているか
3. race_dataに必要なキーが全て含まれているか

**デバッグ**:
```python
# test_nlogic.py の結果確認
# ログ確認
tail -f /var/log/render.log
```

---

## 🎯 次のステップ

### 優先度: 高
1. ✅ Phase 1完了後、このドキュメントの「Phase 2」に進む
2. ✅ 学習データ準備
3. ✅ モデル学習実行

### 優先度: 中
4. 地方競馬版N-Logic実装（`local_nlogic_engine_v2.py`）
5. 精度評価スクリプト作成
6. 定期再学習パイプライン構築

### 優先度: 低
7. フロントエンド専用UI作成
8. オッズ履歴トラッキング
9. A/Bテスト（D-Logic vs N-Logic）

---

## 📚 参考資料

### 内部ドキュメント
- D-Logicロジスティック回帰メモ（本プロジェクト）
- ViewLogicエンジン実装（`services/viewlogic_engine.py`）

### 外部資料
- [netkeiba記事1](https://logmi.jp/main/technology/330671)
- [netkeiba記事2](https://logmi.jp/main/technology/330672)
- [CatBoost公式ドキュメント](https://catboost.ai/docs/)
- [QuerySoftmax Loss](https://catboost.ai/docs/concepts/loss-functions-ranking.html#QuerySoftMax)

---

## 📞 サポート

質問・問題がある場合は、このドキュメントと以下の情報を共有してください：

1. どのPhase/Stepで問題が発生したか
2. エラーメッセージ全文
3. 実行したコマンド
4. 期待される動作 vs 実際の動作

---

**最終更新**: 2025-10-04  
**作成者**: Droid AI Assistant  
**バージョン**: 1.0
