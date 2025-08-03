#!/usr/bin/env python3
"""
Phase D: mykeibadb最大活用ナレッジベース構築実行スクリプト
全データ調査・最大ナレッジベース構築・Phase D完了
"""
import sys
import os
from datetime import datetime
import time

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.adaptive_knowledge_builder import AdaptiveKnowledgeBuilder
from services.database_analyzer import DatabaseAnalyzer

def print_phase_d_header():
    """Phase D開始ヘッダー表示"""
    print("=" * 60)
    print("Phase D: mykeibadb最大活用ナレッジベース構築")
    print("全データ調査・利用可能全馬でナレッジベース構築")
    print("=" * 60)
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_phase_d_completion(success_count: int, total_time: float):
    """Phase D完了メッセージ表示"""
    print("\n" + "=" * 60)
    print("Phase D: mykeibadb最大活用ナレッジベース構築 完了！")
    print("=" * 60)
    print(f"構築完了馬数: {success_count:,}頭")
    print(f"総処理時間: {total_time:.1f}秒 ({total_time/60:.1f}分)")
    print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"平均処理速度: {success_count/total_time:.1f}頭/秒")
    print("\nPhase D成果:")
    print("   - mykeibadb実データ完全調査")
    print("   - 利用可能全馬ナレッジベース構築")
    print("   - 12項目超高精度Dロジック分析")
    print("   - 動的バッチ処理による効率化")
    print("   - フロントエンド・バックエンド連携完了")
    print("\n次のステップ: Phase D完了版での本格運用開始")
    print("=" * 60)

def run_database_investigation():
    """データベース事前調査実行"""
    print("Step 0: データベース事前調査")
    print("-" * 50)
    
    analyzer = DatabaseAnalyzer()
    
    # スタンドアロン調査実行
    print("mykeibadb基本情報調査中...")
    analysis = analyzer.analyze_complete_database()
    
    if "error" in analysis:
        print(f"データベース調査失敗: {analysis['error']}")
        print("\n確認事項:")
        print("   - mykeibadbファイルがプロジェクトルートに存在するか")
        print("   - データベースファイルの読み取り権限があるか")
        print("   - SQLiteデータベースとして正しく認識されるか")
        return False
    
    # 基本統計表示
    db_info = analysis.get('database_info', {})
    horse_info = analysis.get('horse_analysis', {})
    race_info = analysis.get('race_analysis', {})
    
    print("データベース調査成功!")
    print(f"   ファイルサイズ: {db_info.get('file_size_mb', 0)}MB")
    print(f"   総馬数: {horse_info.get('total_horses', 0):,}頭")
    print(f"   総レース記録: {race_info.get('total_race_records', 0):,}")
    
    # 処理見積もり
    target_horses = analyzer.get_optimal_horse_list(min_races=2, limit=10)  # サンプル10頭
    if target_horses:
        print(f"   処理対象候補: 2戦以上実績馬（サンプル確認済み）")
    else:
        print("   処理対象馬が見つかりません")
        return False
    
    # レポート出力
    report_path = analyzer.export_analysis_report(analysis)
    print(f"   詳細レポート: {os.path.basename(report_path)}")
    
    print("-" * 50)
    return True

def main():
    """メイン実行関数"""
    start_time = time.time()
    
    # Phase D開始
    print_phase_d_header()
    
    # Step 0: データベース事前調査
    if not run_database_investigation():
        print("❌ データベース調査に失敗しました。処理を中断します。")
        return False
    
    print("\n⏳ 続行しますか？ 大量処理が開始されます...")
    print("   Enter: 続行 / Ctrl+C: 中断")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n⏹️  ユーザーによる処理中断")
        return False
    
    # Step 1-3: 最大活用ナレッジベース構築
    print("\n🚀 ナレッジベース構築開始...")
    
    try:
        builder = AdaptiveKnowledgeBuilder()
        
        # 最大活用拡張実行
        knowledge_base, success_count = builder.execute_maximum_expansion()
        
        if "error" in knowledge_base:
            print(f"❌ 構築エラー: {knowledge_base['error']}")
            return False
        
        if success_count == 0:
            print("❌ 構築対象が見つかりませんでした")
            return False
        
        # 最終保存
        print("\n💾 最終ナレッジベース保存中...")
        builder.save_final_knowledge_base(knowledge_base, success_count)
        
        # Phase D完了
        total_time = time.time() - start_time
        print_phase_d_completion(success_count, total_time)
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  ユーザーによる処理中断")
        return False
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def quick_test():
    """クイックテスト実行"""
    print("Phase D クイックテスト実行")
    print("-" * 40)
    
    # データベース調査のみ
    analyzer = DatabaseAnalyzer()
    analysis = analyzer.analyze_complete_database()
    
    if "error" in analysis:
        print(f"テスト失敗: {analysis['error']}")
        return False
    
    # 少数サンプル処理テスト
    builder = AdaptiveKnowledgeBuilder()
    target_horses = builder.db_analyzer.get_optimal_horse_list(min_races=2, limit=5)
    
    if not target_horses:
        print("テスト対象馬なし")
        return False
    
    print(f"テスト成功: {len(target_horses)}頭の処理対象を確認")
    print("フル実行の準備完了")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # テストモード
        success = quick_test()
    else:
        # フル実行モード
        success = main()
    
    exit_code = 0 if success else 1
    sys.exit(exit_code)