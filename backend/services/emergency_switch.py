"""
緊急時のナレッジファイル切り替えスイッチ
Render環境変数で即座に切り替え可能
"""
import os

def get_knowledge_cdn_url():
    """環境変数に基づいてCDN URLを返す"""
    use_unified = os.getenv('USE_UNIFIED_KNOWLEDGE', 'true').lower() == 'true'
    
    if use_unified:
        # 統合ナレッジファイル（新）
        return {
            'dlogic': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json',
            'extended': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json',
            'viewlogic': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json',
            'jockey': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json'
        }
    else:
        # 旧ナレッジファイル（緊急時のフォールバック）
        return {
            'dlogic': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/dlogic_raw_knowledge.json',
            'extended': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/dlogic_extended_knowledge.json',
            'viewlogic': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/viewlogic_knowledge.json',
            'jockey': 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json'
        }