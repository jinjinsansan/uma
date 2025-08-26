"""
V2 AIハンドラーのシングルトン
メモリ使用量を削減するため、グローバルインスタンスを1つだけ作成
"""
import logging

logger = logging.getLogger(__name__)

# グローバルインスタンス
_ai_handler_instance = None

def get_ai_handler():
    """V2AIHandlerのシングルトンインスタンスを取得"""
    global _ai_handler_instance
    
    if _ai_handler_instance is None:
        logger.info("V2AIHandlerの新規インスタンスを作成します...")
        from services.v2.ai_handler import V2AIHandler
        _ai_handler_instance = V2AIHandler()
        logger.info("V2AIHandlerのインスタンス作成完了")
    else:
        logger.debug("既存のV2AIHandlerインスタンスを再利用")
    
    return _ai_handler_instance