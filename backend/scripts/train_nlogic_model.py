"""
N-Logic モデル学習パイプライン
過去レースデータから2つのモデルを学習
1. Rank Model（順位予測）
2. Support Rate Model（支持率予測、QuerySoftMax）

使用方法:
  python3 scripts/train_nlogic_model.py --data training_data.csv

注意: CatBoostと学習データが必要
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

# バックエンドのパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def check_catboost():
    """CatBoostがインストールされているか確認"""
    try:
        from catboost import CatBoostRanker, CatBoostRegressor, Pool
        print("✅ CatBoost available")
        return True
    except ImportError:
        print("❌ CatBoost not installed")
        print("   Install: pip install catboost")
        return False

def load_training_data(data_path: str):
    """学習データの読み込み"""
    print(f"📂 学習データ読み込み: {data_path}")
    
    if not os.path.exists(data_path):
        print(f"❌ ファイルが見つかりません: {data_path}")
        return None
    
    # CSV形式を想定
    df = pd.read_csv(data_path)
    print(f"✅ {len(df)}レコード読み込み完了")
    print(f"   列: {list(df.columns)}")
    
    return df

def prepare_features(df: pd.DataFrame):
    """特徴量とラベルの準備"""
    print("\n🔧 特徴量とラベルを準備中...")
    
    # 必要な列を確認
    required_cols = [
        'race_id', 'horse_name', 'actual_rank', 'actual_support_rate',
        'knowledge_total_races', 'knowledge_win_rate', 'knowledge_place_rate',
        'knowledge_avg_finish', 'knowledge_avg_popularity', 'knowledge_avg_corner4',
        'knowledge_avg_kohan3f', 'venue_code', 'distance'
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ 必要な列が不足: {missing_cols}")
        return None, None, None, None
    
    # CatBoost Rankerのため、race_idでソート（重要！）
    df = df.sort_values('race_id').reset_index(drop=True)
    print("✅ データをrace_idでソート完了")
    
    # 特徴量
    feature_cols = [
        'knowledge_total_races', 'knowledge_win_rate', 'knowledge_place_rate',
        'knowledge_avg_finish', 'knowledge_avg_popularity', 'knowledge_avg_corner4',
        'knowledge_avg_kohan3f', 'venue_code', 'distance'
    ]
    
    X = df[feature_cols].values
    
    # ラベル（順位予測用）
    y_rank = df['actual_rank'].values
    
    # ラベル（支持率予測用）
    y_support = df['actual_support_rate'].values
    
    # グループID（レース単位でグループ化）
    group_ids = df['race_id'].values
    
    print(f"✅ 特徴量準備完了")
    print(f"   特徴量数: {X.shape[1]}")
    print(f"   サンプル数: {X.shape[0]}")
    print(f"   ユニークレース数: {len(np.unique(group_ids))}")
    
    return X, y_rank, y_support, group_ids

def train_rank_model(X_train, y_train, group_ids):
    """Rank Modelの学習"""
    from catboost import CatBoostRanker, Pool
    
    print("\n🔧 Rank Model学習開始...")
    print("   目的: 順位予測（上位馬の精度を優先）")
    
    # Poolデータ作成（group_id必須）
    train_pool = Pool(
        data=X_train,
        label=y_train,
        group_id=group_ids
    )
    
    # CatBoost Ranker
    model = CatBoostRanker(
        iterations=1000,
        learning_rate=0.03,
        depth=6,
        loss_function='PairLogit',
        verbose=100,
        random_seed=42
    )
    
    model.fit(train_pool)
    
    print("✅ Rank Model学習完了")
    return model

def train_support_model(X_train, y_train, group_ids, rank_weights):
    """Support Rate Modelの学習（Rankerとして学習）"""
    from catboost import CatBoostRanker, Pool
    
    print("\n🔧 Support Rate Model学習開始...")
    print("   目的: 支持率予測（Rankerとして学習、予測時にSoftmax適用）")
    
    # Rank Weightを特徴量に追加
    X_train_with_weight = np.column_stack([X_train, rank_weights])
    
    # Poolデータ作成
    train_pool = Pool(
        data=X_train_with_weight,
        label=y_train,
        group_id=group_ids
    )
    
    # CatBoost Ranker（PairLogitLoss）
    # 予測時にSoftmaxを適用することで支持率に変換
    model = CatBoostRanker(
        iterations=1000,
        learning_rate=0.03,
        depth=6,
        loss_function='PairLogit',
        verbose=100,
        random_seed=42
    )
    
    model.fit(train_pool)
    
    print("✅ Support Rate Model学習完了")
    print("   ※予測時にSoftmaxを適用して支持率に変換します")
    return model

def save_models(rank_model, support_model, output_dir):
    """モデルの保存"""
    print("\n💾 モデル保存中...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    rank_path = os.path.join(output_dir, 'nlogic_rank_model.cbm')
    support_path = os.path.join(output_dir, 'nlogic_support_model.cbm')
    
    rank_model.save_model(rank_path)
    support_model.save_model(support_path)
    
    print(f"✅ モデル保存完了:")
    print(f"   Rank Model: {rank_path}")
    print(f"   Support Model: {support_path}")
    
    # メタデータも保存
    metadata = {
        'created': datetime.now().isoformat(),
        'rank_model': rank_path,
        'support_model': support_path,
        'iterations': 1000,
        'loss_functions': {
            'rank': 'PairLogit',
            'support': 'QuerySoftMax'
        }
    }
    
    import json
    metadata_path = os.path.join(output_dir, 'nlogic_training_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"   Metadata: {metadata_path}")

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='N-Logic モデル学習パイプライン')
    parser.add_argument('--data', type=str, help='学習データCSVファイルパス')
    parser.add_argument('--output', type=str, default='data', help='モデル出力ディレクトリ')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("N-Logic モデル学習パイプライン")
    print("=" * 60)
    
    # Step 0: CatBoostチェック
    if not check_catboost():
        return 1
    
    # Step 1: データ読み込み
    if not args.data:
        print("\n⚠️ 学習データが指定されていません")
        print("\n使用方法:")
        print("  python3 scripts/train_nlogic_model.py --data training_data.csv")
        print("\nサンプルデータ作成方法:")
        print("  1. PostgreSQLから過去レース結果を抽出")
        print("  2. 特徴量を計算")
        print("  3. CSV形式で保存")
        print("\n必要な列:")
        print("  - race_id: レースID")
        print("  - horse_name: 馬名")
        print("  - actual_rank: 実際の着順")
        print("  - actual_support_rate: 実際の支持率（0.8/オッズ）")
        print("  - knowledge_*: 馬のナレッジ特徴量")
        print("  - venue_code: 競馬場コード")
        print("  - distance: 距離")
        return 1
    
    df = load_training_data(args.data)
    if df is None:
        return 1
    
    # Step 2: 特徴量準備
    X_train, y_rank, y_support, group_ids = prepare_features(df)
    if X_train is None:
        return 1
    
    # Step 3: Rank Model学習
    rank_model = train_rank_model(X_train, y_rank, group_ids)
    
    # Step 4: Rank Weight生成
    print("\n🔧 Rank Weight生成中...")
    rank_weights = rank_model.predict(X_train)
    print(f"✅ Rank Weight生成完了（範囲: {rank_weights.min():.3f} - {rank_weights.max():.3f}）")
    
    # Step 5: Support Model学習
    support_model = train_support_model(X_train, y_support, group_ids, rank_weights)
    
    # Step 6: モデル保存
    output_dir = os.path.join(os.path.dirname(__file__), '..', args.output)
    save_models(rank_model, support_model, output_dir)
    
    print("\n" + "=" * 60)
    print("🎉 すべての学習が完了しました！")
    print("=" * 60)
    print("\n次のステップ:")
    print("  1. モデルをバックエンドで読み込む")
    print("  2. ai_handlerでN-Logicを有効化")
    print("  3. V2チャットでテスト")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
