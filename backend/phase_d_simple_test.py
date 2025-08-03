#!/usr/bin/env python3
"""
Phase D: 簡易テスト（Windowsエンコーディング対応）
"""
import sqlite3
import os
import sys

def find_mykeibadb():
    """mykeibadbファイルを検索"""
    possible_paths = [
        'mykeibadb',
        '../mykeibadb',
        '../../mykeibadb',
        '../../../mykeibadb'
    ]
    
    for path in possible_paths:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            return full_path
    
    return None

def test_database_connection():
    """データベース接続テスト"""
    print("Phase D データベース接続テスト")
    print("=" * 40)
    
    # データベース検索
    db_path = find_mykeibadb()
    if not db_path:
        print("ERROR: mykeibadbファイルが見つかりません")
        print("確認してください:")
        print("  - プロジェクトルートにmykeibadbファイルが存在するか")
        return False
    
    print(f"データベース発見: {db_path}")
    print(f"ファイルサイズ: {os.path.getsize(db_path) / (1024*1024):.1f}MB")
    
    # 接続テスト
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テーブル一覧
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        
        print(f"テーブル数: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # umagoto_race_johoテーブル確認
        if ('umagoto_race_joho',) in tables:
            # 総レコード数
            total_records = cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho").fetchone()[0]
            print(f"総レース記録: {total_records:,}")
            
            # 馬数
            total_horses = cursor.execute("""
                SELECT COUNT(DISTINCT BAMEI) FROM umagoto_race_joho 
                WHERE BAMEI IS NOT NULL AND BAMEI != ''
            """).fetchone()[0]
            print(f"総馬数: {total_horses:,}頭")
            
            # サンプル馬（2戦以上）
            sample_horses = cursor.execute("""
                SELECT BAMEI, COUNT(*) as races
                FROM umagoto_race_joho 
                WHERE BAMEI IS NOT NULL AND BAMEI != ''
                GROUP BY BAMEI 
                HAVING races >= 2
                ORDER BY races DESC
                LIMIT 5
            """).fetchall()
            
            print("処理対象サンプル（2戦以上）:")
            for horse, races in sample_horses:
                print(f"  - {horse}: {races}戦")
            
            print("\nPhase D 準備完了!")
            print("フル実行でナレッジベース構築が可能です")
            
        else:
            print("ERROR: umagoto_race_johoテーブルが見つかりません")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: データベースエラー - {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("\n=== テスト成功 ===")
        print("run_phase_d.batでフル実行を開始できます")
    else:
        print("\n=== テスト失敗 ===")
        print("データベースの確認が必要です")
    
    exit_code = 0 if success else 1
    sys.exit(exit_code)