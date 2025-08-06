#!/usr/bin/env python3
"""
最終ナレッジ構築実行スクリプト
失敗した6,029頭の処理を完了させる
"""
import sys
import os
import logging
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batch_robust_knowledge_builder import RobustKnowledgeBuilder

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'final_build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """最終ナレッジ構築実行"""
    logger.info("🏁 D-Logic最終ナレッジ構築開始")
    logger.info("📋 目標: 失敗した6,029頭の処理完了")
    
    try:
        builder = RobustKnowledgeBuilder()
        
        # 改善されたチャンクサイズで実行
        builder.chunk_size = 50  # 小さなチャンクで安定処理
        builder.reconnect_interval = 500  # 頻繁な接続リフレッシュ
        
        # 最大3000頭を処理（安全マージン）
        builder.run_robust_batch(max_horses=3000)
        
        logger.info("🎉 最終ナレッジ構築完了!")
        
        # 最終統計表示
        final_data = builder.raw_manager.knowledge_data
        total_horses = len(final_data.get('horses', {}))
        logger.info(f"📊 最終統計:")
        logger.info(f"  - 総登録馬数: {total_horses}頭")
        logger.info(f"  - 今回成功: {builder.processed_count}頭")
        logger.info(f"  - 今回エラー: {builder.error_count}頭")
        
        # 目標達成確認
        if total_horses >= 6000:
            logger.info("✅ 目標達成! 6,000頭以上の登録完了")
        else:
            remaining = 6000 - total_horses
            logger.info(f"⚠️ 残り{remaining}頭の登録が必要")
        
    except Exception as e:
        logger.error(f"❌ 最終構築エラー: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎊 D-Logicナレッジ構築システム完成!")
        print("次は高速D-Logic計算エンジンのテストを実行できます。")
    else:
        print("\n❌ 構築に問題が発生しました。ログを確認してください。")