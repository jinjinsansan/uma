from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse, JSONResponse
import logging
import os
from typing import Optional
from datetime import datetime
from services.monthly_knowledge_updater import MonthlyKnowledgeUpdater

router = APIRouter(prefix="/api/admin", tags=["Admin Knowledge"])
logger = logging.getLogger(__name__)

# 秘密キー（環境変数から取得、デフォルトは固定値）
SECRET_KEY = os.getenv("KNOWLEDGE_UPDATE_SECRET", "dlogic-knowledge-2025-secret")

@router.post("/knowledge-update/{secret_key}")
async def trigger_knowledge_update(secret_key: str):
    """月次ナレッジファイル更新をトリガー"""
    
    # 秘密キーの検証
    if secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    try:
        # 更新サービスのインスタンス作成
        updater = MonthlyKnowledgeUpdater()
        
        # 更新を実行
        logger.info("Starting monthly knowledge update...")
        result = updater.generate_monthly_update()
        
        if result['status'] == 'success':
            logger.info(f"Knowledge update completed successfully. File: {result['file_path']}")
            return JSONResponse(content={
                "status": "success",
                "message": "月次更新が正常に完了しました",
                "result": {
                    "file_name": os.path.basename(result['file_path']),
                    "file_size_mb": round(result['file_size_mb'], 2),
                    "gz_file_size_mb": round(result['gz_file_size_mb'], 2),
                    "total_horses": result['total_horses'],
                    "new_horses": result['new_horses'],
                    "update_info": result['update_info']
                }
            })
        else:
            raise HTTPException(status_code=500, detail="Update failed")
            
    except Exception as e:
        logger.error(f"Knowledge update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-update-status/{secret_key}")
async def get_update_status(secret_key: str):
    """更新履歴と現在の状態を取得"""
    
    # 秘密キーの検証
    if secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    try:
        updater = MonthlyKnowledgeUpdater()
        
        # 現在のナレッジ情報
        from services.dlogic_raw_data_manager import dlogic_manager
        current_info = {
            "total_horses": len(dlogic_manager.knowledge_data.get('horses', {})),
            "last_updated": dlogic_manager.knowledge_data.get('meta', {}).get('last_updated', 'unknown'),
            "github_url": "https://github.com/jinjinsansan/dlogic-knowledge-data/releases/download/V1.0/dlogic_raw_knowledge.json"
        }
        
        # 更新履歴
        history = updater.get_update_history()
        
        # 最後の更新日
        last_update_date = updater.get_last_update_date()
        
        return {
            "current_knowledge": current_info,
            "last_update_check": last_update_date.strftime('%Y-%m-%d'),
            "update_history": history,
            "next_update_recommended": (datetime.now().day == 1)  # 毎月1日を推奨
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download-knowledge-update/{secret_key}/{filename}")
async def download_knowledge_update(secret_key: str, filename: str):
    """生成されたナレッジファイルをダウンロード"""
    
    # 秘密キーの検証
    if secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # セキュリティ: ファイル名の検証
    if not filename.startswith('dlogic_knowledge_update_') or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # ファイルパスの構築
    updater = MonthlyKnowledgeUpdater()
    file_path = os.path.join(updater.output_dir, filename)
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # ファイルを返す
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/json' if filename.endswith('.json') else 'application/gzip'
    )

@router.delete("/knowledge-update/{secret_key}/{filename}")
async def delete_knowledge_update(secret_key: str, filename: str):
    """古い更新ファイルを削除"""
    
    # 秘密キーの検証
    if secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # セキュリティ: ファイル名の検証
    if not filename.startswith('dlogic_knowledge_update_') or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    try:
        updater = MonthlyKnowledgeUpdater()
        file_path = os.path.join(updater.output_dir, filename)
        
        # JSONファイルとGZファイルの両方を削除
        deleted_files = []
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted_files.append(filename)
        
        gz_path = file_path + '.gz'
        if os.path.exists(gz_path):
            os.remove(gz_path)
            deleted_files.append(filename + '.gz')
        
        if deleted_files:
            return {
                "status": "success",
                "deleted_files": deleted_files
            }
        else:
            raise HTTPException(status_code=404, detail="File not found")
            
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))