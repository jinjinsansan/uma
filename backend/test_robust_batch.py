#!/usr/bin/env python3
"""
堅牢バッチシステムのテスト実行（10頭限定）
"""
import sys
import os
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batch_robust_knowledge_builder import RobustKnowledgeBuilder

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_robust_batch():
    """堅牢バッチシステムテスト"""
    logger.info("🧪 堅牢バッチシステムテスト開始（10頭限定）")
    
    try:
        builder = RobustKnowledgeBuilder()
        
        # 10頭限定でテスト実行
        builder.run_robust_batch(max_horses=10)
        
        logger.info("✅ テスト完了")
        
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_robust_batch()
    if success:
        print("\n✅ テスト成功! 本格実行の準備が整いました。")
        print("次のコマンドで本格実行:")
        print("python batch_robust_knowledge_builder.py")
    else:
        print("\n❌ テスト失敗。問題を修正してください。")