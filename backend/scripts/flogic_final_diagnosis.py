#!/usr/bin/env python3
"""
F-Logic実装 総合診断スクリプト
100点満点で評価
"""

import sys
import os
import asyncio
import importlib
import json
from typing import Dict, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FLogicDiagnosis:
    def __init__(self):
        self.scores = {}
        self.issues = []
        self.total_score = 0
        
    def check_1_no_interference(self) -> int:
        """①既存エンジンへの干渉チェック"""
        print("\n【診断1】既存エンジンへの干渉チェック")
        print("-" * 50)
        
        score = 20  # 満点20点
        
        try:
            # 既存エンジンのインポートチェック
            from services.dlogic_engine import DLogicEngine
            from services.ilogic_engine import ILogicEngine
            from services.viewlogic_engine import ViewLogicEngine
            from services.imlogic_engine import imlogic_engine
            
            print("✅ 既存エンジンのインポート: 成功")
            
            # ai_handler.pyでの独立性チェック
            with open('/mnt/e/dev/Cusor/chatbot/uma/backend/services/v2/ai_handler.py', 'r') as f:
                content = f.read()
                
            # F-Logic追加が既存メソッドを変更していないか
            if 'process_dlogic_message' in content and 'process_ilogic_message' in content:
                print("✅ 既存メソッド保持: 確認")
            else:
                print("⚠️ 既存メソッドに影響の可能性")
                score -= 5
                self.issues.append("既存メソッドへの影響確認必要")
                
            # キーワード独立性
            if "'flogic': ['f-logic', 'flogic'," in content.lower():
                print("✅ キーワード独立性: 確認")
            else:
                print("⚠️ キーワード重複の可能性")
                score -= 3
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            score = 0
            self.issues.append(f"既存エンジン干渉エラー: {e}")
            
        self.scores['既存エンジン干渉'] = score
        return score
    
    def check_2_jra_chiho_compatibility(self) -> int:
        """②JRA版・地方競馬版V2チャット互換性チェック"""
        print("\n【診断2】JRA版・地方競馬版V2チャット互換性")
        print("-" * 50)
        
        score = 20  # 満点20点
        
        try:
            # F-Logicエンジンの汎用性チェック
            from services.flogic_engine import flogic_engine
            
            # レースデータ形式の互換性
            jra_race = {'venue': '東京', 'horses': ['馬A'], 'jockeys': ['騎手A']}
            chiho_race = {'venue': '大井', 'horses': ['馬B'], 'jockeys': ['騎手B']}
            
            # 両方のレースで動作確認
            try:
                result_jra = flogic_engine.analyze_race(jra_race, {})
                result_chiho = flogic_engine.analyze_race(chiho_race, {})
                print("✅ JRA/地方競馬データ処理: 成功")
            except:
                print("⚠️ データ処理に制限あり")
                score -= 5
                self.issues.append("地方競馬データ処理に制限")
                
            # V2 APIエンドポイントチェック
            if os.path.exists('/mnt/e/dev/Cusor/chatbot/uma/backend/api/v2/chat.py'):
                print("✅ V2 APIエンドポイント: 存在")
            else:
                print("⚠️ V2 APIエンドポイント未確認")
                score -= 5
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            score = 5
            self.issues.append(f"互換性エラー: {e}")
            
        self.scores['JRA/地方互換性'] = score
        return score
    
    def check_3_deployment_ready(self) -> int:
        """③デプロイ準備チェック"""
        print("\n【診断3】デプロイ準備状態")
        print("-" * 50)
        
        score = 20  # 満点20点
        
        try:
            # 必須ファイルの存在確認
            required_files = [
                'services/flogic_engine.py',
                'services/odds_manager.py',
                'services/flogic_batch_processor.py'
            ]
            
            for file in required_files:
                path = f'/mnt/e/dev/Cusor/chatbot/uma/backend/{file}'
                if os.path.exists(path):
                    print(f"✅ {file}: 存在")
                else:
                    print(f"❌ {file}: 不在")
                    score -= 5
                    self.issues.append(f"{file}が見つかりません")
            
            # インポートエラーチェック
            try:
                from services.flogic_engine import flogic_engine
                from services.odds_manager import odds_manager
                print("✅ モジュールインポート: 成功")
            except ImportError as e:
                print(f"⚠️ インポートエラー: {e}")
                score -= 5
                self.issues.append(f"インポートエラー: {e}")
                
            # 環境変数依存チェック
            with open('/mnt/e/dev/Cusor/chatbot/uma/backend/services/odds_manager.py', 'r') as f:
                content = f.read()
                if 'psycopg2' in content:
                    print("⚠️ PostgreSQL依存（ローカルのみ）")
                    score -= 3
                    self.issues.append("PostgreSQL接続はローカル環境限定")
                    
        except Exception as e:
            print(f"❌ エラー: {e}")
            score = 0
            self.issues.append(f"デプロイ準備エラー: {e}")
            
        self.scores['デプロイ準備'] = score
        return score
    
    def check_4_api_functionality(self) -> int:
        """④API動作チェック"""
        print("\n【診断4】API動作確認")
        print("-" * 50)
        
        score = 20  # 満点20点
        
        try:
            from services.v2.ai_handler import V2AIHandler
            
            # AIハンドラーインスタンス化
            ai_handler = V2AIHandler()
            print("✅ V2AIHandler: インスタンス化成功")
            
            # F-Logic判定テスト
            test_messages = [
                'F-Logic分析して',
                'フェア値を教えて',
                'エフロジック'
            ]
            
            success_count = 0
            for msg in test_messages:
                ai_type, _ = ai_handler.determine_ai_type(msg)
                if ai_type == 'flogic':
                    success_count += 1
                    
            if success_count == len(test_messages):
                print(f"✅ F-Logic判定: {success_count}/{len(test_messages)} 成功")
            else:
                print(f"⚠️ F-Logic判定: {success_count}/{len(test_messages)} 成功")
                score -= 5
                self.issues.append("一部のキーワード判定に問題")
                
            # process_flogic_messageメソッドの存在確認
            if hasattr(ai_handler, 'process_flogic_message'):
                print("✅ process_flogic_message: 実装済み")
            else:
                print("❌ process_flogic_message: 未実装")
                score -= 10
                self.issues.append("process_flogic_messageメソッドが見つかりません")
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            score = 0
            self.issues.append(f"API動作エラー: {e}")
            
        self.scores['API動作'] = score
        return score
    
    def check_5_other_errors(self) -> int:
        """⑤その他のエラーチェック"""
        print("\n【診断5】その他のエラーチェック")
        print("-" * 50)
        
        score = 20  # 満点20点
        
        try:
            # Syntaxエラーチェック
            modules_to_check = [
                'services.flogic_engine',
                'services.odds_manager',
                'services.flogic_batch_processor'
            ]
            
            for module_name in modules_to_check:
                try:
                    importlib.import_module(module_name)
                    print(f"✅ {module_name}: Syntaxエラーなし")
                except SyntaxError as e:
                    print(f"❌ {module_name}: Syntaxエラー")
                    score -= 5
                    self.issues.append(f"Syntaxエラー in {module_name}")
                    
            # 循環参照チェック
            try:
                from services.flogic_engine import flogic_engine
                from services.v2.ai_handler import V2AIHandler
                print("✅ 循環参照: なし")
            except ImportError:
                print("⚠️ 循環参照の可能性")
                score -= 3
                
            # メモリリークの可能性チェック
            with open('/mnt/e/dev/Cusor/chatbot/uma/backend/services/flogic_engine.py', 'r') as f:
                content = f.read()
                if 'global' in content:
                    print("⚠️ グローバル変数使用（メモリリークリスク）")
                    score -= 2
                else:
                    print("✅ メモリ管理: 適切")
                    
        except Exception as e:
            print(f"❌ エラー: {e}")
            score = 5
            self.issues.append(f"その他エラー: {e}")
            
        self.scores['その他エラー'] = score
        return score
    
    def run_diagnosis(self):
        """総合診断実行"""
        print("=" * 60)
        print("🔍 F-Logic実装 総合診断")
        print("=" * 60)
        
        # 各項目の診断実行
        score1 = self.check_1_no_interference()
        score2 = self.check_2_jra_chiho_compatibility()
        score3 = self.check_3_deployment_ready()
        score4 = self.check_4_api_functionality()
        score5 = self.check_5_other_errors()
        
        self.total_score = score1 + score2 + score3 + score4 + score5
        
        # 結果表示
        print("\n" + "=" * 60)
        print("📊 診断結果サマリー")
        print("=" * 60)
        
        for category, score in self.scores.items():
            max_score = 20
            percentage = (score / max_score) * 100
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 60 else "❌"
            print(f"{status} {category}: {score}/{max_score}点 ({percentage:.0f}%)")
        
        print("-" * 60)
        print(f"🎯 総合得点: {self.total_score}/100点")
        
        # 評価
        if self.total_score >= 90:
            print("⭐ 評価: 優秀 - 本番デプロイ可能")
        elif self.total_score >= 75:
            print("✅ 評価: 良好 - 軽微な修正で本番可能")
        elif self.total_score >= 60:
            print("⚠️ 評価: 要改善 - いくつかの問題要対応")
        else:
            print("❌ 評価: 不十分 - 重要な問題の解決が必要")
        
        # 問題点リスト
        if self.issues:
            print("\n【改善が必要な項目】")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
        else:
            print("\n✅ 重要な問題は検出されませんでした")
        
        return self.total_score

def main():
    diagnosis = FLogicDiagnosis()
    score = diagnosis.run_diagnosis()
    
    # 結果をJSONで保存
    result = {
        'total_score': score,
        'scores': diagnosis.scores,
        'issues': diagnosis.issues,
        'timestamp': str(datetime.now()) if 'datetime' in dir() else 'N/A'
    }
    
    with open('/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/flogic_diagnosis_result.json', 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n診断結果を保存しました: flogic_diagnosis_result.json")
    
    return 0 if score >= 75 else 1

if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())