"""
ナレッジファイル選択ユーティリティ
環境変数で統合/分離を切り替え可能
"""
import os
import logging

logger = logging.getLogger(__name__)

class KnowledgeSelector:
    @staticmethod
    def get_cdn_urls():
        """環境変数に基づいてCDN URLを返す"""
        use_unified = os.getenv('USE_UNIFIED_KNOWLEDGE', 'true').lower() == 'true'
        
        if use_unified:
            logger.info("🎯 統合ナレッジファイルモード")
            return {
                'dlogic': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json',
                'extended': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json',
                'viewlogic': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json',
                'jockey': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json',
                'mode': 'unified'
            }
        else:
            logger.info("📦 分離ナレッジファイルモード（フォールバック）")
            return {
                'dlogic': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/dlogic_raw_knowledge.json',
                'extended': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/dlogic_extended_knowledge.json',
                'viewlogic': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/viewlogic_knowledge.json',
                'jockey': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json',
                'mode': 'separated'
            }
    
    @staticmethod
    def should_convert_format():
        """統合形式の変換が必要かどうか"""
        use_unified = os.getenv('USE_UNIFIED_KNOWLEDGE', 'true').lower() == 'true'
        return use_unified