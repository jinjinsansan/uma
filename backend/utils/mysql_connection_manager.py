#!/usr/bin/env python3
"""
MySQL接続管理クラス - 接続プール・リトライ・設定統一化
"""
import mysql.connector
from mysql.connector import pooling, Error
import os
import time
import logging
from functools import wraps
from typing import Optional, Any, Dict
from contextlib import contextmanager

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MySQLConnectionManager:
    """MySQL接続管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.config = {
            'host': os.getenv('MYSQL_HOST', '172.25.160.1'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', '04050405Aoi-'),
            'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
            'charset': 'utf8mb4',
            'autocommit': True,
            'connect_timeout': 60,
            'sql_mode': 'STRICT_TRANS_TABLES',
            'raise_on_warnings': True,
            'use_unicode': True,
            'collation': 'utf8mb4_unicode_ci'
        }
        
        # 接続プール設定
        self.pool_config = {
            'pool_name': 'dlogic_pool',
            'pool_size': int(os.getenv('MYSQL_POOL_SIZE', 10)),
            'pool_reset_session': True,
            **self.config
        }
        
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """接続プール初期化"""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(**self.pool_config)
            logger.info(f"✅ MySQL接続プール初期化完了 (サイズ: {self.pool_config['pool_size']})")
        except Error as e:
            logger.error(f"❌ MySQL接続プール初期化失敗: {e}")
            # フォールバック: 直接接続
            self.connection_pool = None
    
    def retry_on_connection_error(self, max_retries=3, delay=1):
        """接続エラー時のリトライデコレータ"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Error as e:
                        last_exception = e
                        
                        # リトライ対象エラー
                        if e.errno in [2003, 2013, 1045, 2006, 1040, 1203] and attempt < max_retries - 1:
                            wait_time = delay * (2 ** attempt)  # 指数バックオフ
                            logger.warning(f"⚠️ MySQL接続エラー (試行 {attempt + 1}/{max_retries}): {e}")
                            logger.info(f"🔄 {wait_time}秒後にリトライします...")
                            time.sleep(wait_time)
                            
                            # 接続プール再初期化
                            if attempt == max_retries - 2:
                                self._initialize_pool()
                            continue
                        else:
                            raise
                
                # 全試行失敗
                raise last_exception
            return wrapper
        return decorator
    
    @contextmanager
    def get_connection(self):
        """接続取得（コンテキストマネージャー）"""
        connection = None
        try:
            if self.connection_pool:
                connection = self.connection_pool.get_connection()
                logger.debug("🔗 プールから接続取得")
            else:
                connection = mysql.connector.connect(**self.config)
                logger.debug("🔗 直接接続作成")
            
            # 接続テスト
            if connection.is_connected():
                yield connection
            else:
                raise Error("接続が無効です")
                
        except Error as e:
            logger.error(f"❌ MySQL接続エラー: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
                logger.debug("🔌 接続クローズ")
    
    def execute_query(self, query: str, params=None, fetch_all=True):
        """クエリ実行（リトライ付き）"""
        retry_decorator = self.retry_on_connection_error(max_retries=3, delay=2)
        
        @retry_decorator
        def _execute():
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall() if fetch_all else cursor.fetchone()
                else:
                    result = cursor.rowcount
                    conn.commit()
                
                cursor.close()
                return result
        
        return _execute()
    
    def execute_batch(self, query: str, data_list: list):
        """バッチ実行（リトライ付き）"""
        retry_decorator = self.retry_on_connection_error(max_retries=3, delay=2)
        
        @retry_decorator
        def _execute_batch():
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, data_list)
                result = cursor.rowcount
                conn.commit()
                cursor.close()
                return result
        
        return _execute_batch()
    
    def test_connection(self) -> bool:
        """接続テスト"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                logger.info("✅ MySQL接続テスト成功")
                return result is not None
        except Exception as e:
            logger.error(f"❌ MySQL接続テスト失敗: {e}")
            return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """プール状態取得"""
        if not self.connection_pool:
            return {"status": "disabled", "pool_size": 0, "active_connections": 0}
        
        try:
            return {
                "status": "active",
                "pool_size": self.pool_config['pool_size'],
                "pool_name": self.pool_config['pool_name'],
                "active_connections": "不明"  # mysql-connector-pythonでは取得困難
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def close_pool(self):
        """プール終了"""
        if self.connection_pool:
            # 個別接続のクローズはガベージコレクションに任せる
            self.connection_pool = None
            logger.info("🔌 MySQL接続プール終了")

# シングルトンインスタンス
_connection_manager = None

def get_mysql_manager() -> MySQLConnectionManager:
    """MySQL接続マネージャー取得"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = MySQLConnectionManager()
    return _connection_manager

def get_mysql_connection():
    """後方互換性のための接続取得関数"""
    manager = get_mysql_manager()
    return manager.get_connection()

# 便利関数
def execute_query(query: str, params=None, fetch_all=True):
    """クエリ実行関数"""
    manager = get_mysql_manager()
    return manager.execute_query(query, params, fetch_all)

def execute_batch(query: str, data_list: list):
    """バッチ実行関数"""
    manager = get_mysql_manager()
    return manager.execute_batch(query, data_list)

def test_mysql_connection() -> bool:
    """接続テスト関数"""
    manager = get_mysql_manager()
    return manager.test_connection()

if __name__ == "__main__":
    # テスト実行
    print("🧪 MySQL接続マネージャーテスト")
    
    manager = get_mysql_manager()
    
    # 接続テスト
    if manager.test_connection():
        print("✅ 接続テスト成功")
        
        # プール状態表示
        status = manager.get_pool_status()
        print(f"📊 プール状態: {status}")
        
        # クエリテスト
        try:
            result = manager.execute_query("SELECT COUNT(*) as count FROM umagoto_race_joho LIMIT 1")
            print(f"📋 レコード数テスト: {result}")
        except Exception as e:
            print(f"❌ クエリテストエラー: {e}")
    else:
        print("❌ 接続テスト失敗")