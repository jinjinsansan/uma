"""
Logic Chat V2 シミュレーションテスト
実際のユーザーシナリオを想定した統合テスト
"""
import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List

# テスト用のベースURL（ローカル環境）
BASE_URL = "http://localhost:8000"

# テスト用ユーザー情報
TEST_USER = {
    "id": "00000000-0000-0000-0000-000000000000",
    "email": "test@example.com",
    "name": "テストユーザー"
}

# テスト用レースデータ
TEST_RACE = {
    "race_id": "test-tokyo-11r-20250111",
    "race_date": "2025-01-11",
    "venue": "東京",
    "race_number": 11,
    "race_name": "テスト記念（G2）",
    "horses": [
        "イクイノックス", "ドウデュース", "リバティアイランド", 
        "ソダシ", "ジャスティンパレス", "タイトルホルダー"
    ],
    "jockeys": ["C.ルメール", "武豊", "川田将雅", "吉田隼人", "横山和生", "横山武史"],
    "posts": [1, 2, 3, 4, 5, 6],
    "horse_numbers": [1, 2, 3, 4, 5, 6]
}

class LogicChatV2Simulator:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.chat_id = None
        self.settings_id = None
        
    async def close(self):
        await self.client.aclose()
    
    async def simulate_user_journey(self):
        """ユーザーの完全な利用フローをシミュレート"""
        print("🚀 Logic Chat V2 シミュレーションテスト開始")
        print("=" * 80)
        
        try:
            # Step 1: IMLogic設定の作成
            await self.test_create_imlogic_settings()
            
            # Step 2: プリセット一覧の取得
            await self.test_get_presets()
            
            # Step 3: レース固定チャットの作成
            await self.test_create_chat()
            
            # Step 4: IMLogic分析の実行（デフォルト設定）
            await self.test_analyze_with_default()
            
            # Step 5: カスタム設定での分析
            await self.test_analyze_with_custom()
            
            # Step 6: 設定の更新
            await self.test_update_settings()
            
            # Step 7: 更新後の分析
            await self.test_analyze_after_update()
            
            # Step 8: チャット履歴の確認
            await self.test_get_chat_history()
            
            # Step 9: ViewLogic分析（開発中）
            await self.test_viewlogic_analysis()
            
            print("\n✅ すべてのテストが成功しました！")
            
        except Exception as e:
            print(f"\n❌ テストエラー: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_create_imlogic_settings(self):
        """Step 1: IMLogic設定の作成"""
        print("\n📝 Step 1: IMLogic設定の作成")
        print("-" * 40)
        
        # 血統重視型の設定を作成
        settings_data = {
            "name": "血統重視カスタム",
            "horse_weight": 80,
            "jockey_weight": 20,
            "item_weights": {
                "1_distance_aptitude": 5.0,
                "2_bloodline_evaluation": 40.0,  # 血統に40%！
                "3_jockey_compatibility": 5.0,
                "4_trainer_evaluation": 5.0,
                "5_track_aptitude": 5.0,
                "6_weather_aptitude": 5.0,
                "7_popularity_factor": 5.0,
                "8_weight_impact": 5.0,
                "9_horse_weight_impact": 5.0,
                "10_corner_specialist": 5.0,
                "11_margin_analysis": 5.0,
                "12_time_index": 10.0
            }
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/imlogic-settings/create",
            json=settings_data
        )
        
        assert response.status_code == 200, f"設定作成失敗: {response.text}"
        result = response.json()
        self.settings_id = result["id"]
        
        print(f"✅ 設定作成成功")
        print(f"   設定ID: {self.settings_id}")
        print(f"   設定名: {result['settings']['name']}")
        print(f"   馬/騎手比率: {result['settings']['horse_weight']}% / {result['settings']['jockey_weight']}%")
    
    async def test_get_presets(self):
        """Step 2: プリセット一覧の取得"""
        print("\n📋 Step 2: プリセット一覧の取得")
        print("-" * 40)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v2/imlogic-settings/presets/list"
        )
        
        assert response.status_code == 200, f"プリセット取得失敗: {response.text}"
        result = response.json()
        
        print(f"✅ {len(result['presets'])}個のプリセットを取得")
        for preset in result['presets']:
            print(f"   - {preset['name']}: {preset['description']}")
    
    async def test_create_chat(self):
        """Step 3: レース固定チャットの作成"""
        print("\n💬 Step 3: レース固定チャットの作成")
        print("-" * 40)
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/logic-chat/create",
            json=TEST_RACE
        )
        
        assert response.status_code == 200, f"チャット作成失敗: {response.text}"
        result = response.json()
        self.chat_id = result["chat_id"]
        
        print(f"✅ チャット作成成功")
        print(f"   チャットID: {self.chat_id}")
        print(f"   レース: {result['race_data']['venue']} {result['race_data']['race_number']}R")
        print(f"   出走頭数: {len(result['race_data']['horses'])}頭")
    
    async def test_analyze_with_default(self):
        """Step 4: IMLogic分析の実行（デフォルト設定）"""
        print("\n🔍 Step 4: IMLogic分析（デフォルト設定）")
        print("-" * 40)
        
        analysis_request = {
            "chat_id": self.chat_id,
            "engine_type": "imlogic",
            "imlogic_settings_id": "default",
            "message": "全馬分析して"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/logic-chat/analyze",
            json=analysis_request
        )
        
        assert response.status_code == 200, f"分析失敗: {response.text}"
        result = response.json()
        
        print(f"✅ デフォルト設定での分析完了")
        if 'analysis_result' in result and 'results' in result['analysis_result']:
            results = result['analysis_result']['results']
            print(f"\n   上位3頭:")
            for horse in results[:3]:
                print(f"   {horse['rank']}位: {horse['horse']} × {horse['jockey']}")
                print(f"      総合: {horse['total_score']}点 (馬: {horse['horse_score']} / 騎手: {horse['jockey_score']})")
    
    async def test_analyze_with_custom(self):
        """Step 5: カスタム設定での分析"""
        print("\n🔍 Step 5: IMLogic分析（血統重視カスタム）")
        print("-" * 40)
        
        analysis_request = {
            "chat_id": self.chat_id,
            "engine_type": "imlogic",
            "imlogic_settings_id": self.settings_id,
            "message": "血統重視で分析して"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/logic-chat/analyze",
            json=analysis_request
        )
        
        assert response.status_code == 200, f"分析失敗: {response.text}"
        result = response.json()
        
        print(f"✅ 血統重視カスタム設定での分析完了")
        if 'analysis_result' in result and 'results' in result['analysis_result']:
            results = result['analysis_result']['results']
            print(f"\n   上位3頭（血統40%重視）:")
            for horse in results[:3]:
                print(f"   {horse['rank']}位: {horse['horse']} × {horse['jockey']}")
                print(f"      総合: {horse['total_score']}点 (馬: {horse['horse_score']} / 騎手: {horse['jockey_score']})")
            
            # カスタム重み付けの影響を表示
            if 'summary' in result['analysis_result'] and result['analysis_result']['summary'].get('custom_weights_impact'):
                print(f"\n   💡 重み付けの影響:")
                for impact in result['analysis_result']['summary']['custom_weights_impact']:
                    print(f"      {impact['item']}: {impact['weight']}% → {impact['contribution']}点の貢献")
    
    async def test_update_settings(self):
        """Step 6: 設定の更新"""
        print("\n🔄 Step 6: IMLogic設定の更新")
        print("-" * 40)
        
        # 騎手重視に変更
        update_data = {
            "name": "騎手重視に変更",
            "horse_weight": 50,
            "jockey_weight": 50,
            "item_weights": {
                "1_distance_aptitude": 8.0,
                "2_bloodline_evaluation": 5.0,
                "3_jockey_compatibility": 25.0,  # 騎手相性重視
                "4_trainer_evaluation": 8.0,
                "5_track_aptitude": 8.0,
                "6_weather_aptitude": 5.0,
                "7_popularity_factor": 5.0,
                "8_weight_impact": 5.0,
                "9_horse_weight_impact": 5.0,
                "10_corner_specialist": 8.0,
                "11_margin_analysis": 8.0,
                "12_time_index": 10.0
            }
        }
        
        response = await self.client.put(
            f"{BASE_URL}/api/v2/imlogic-settings/{self.settings_id}",
            json=update_data
        )
        
        assert response.status_code == 200, f"設定更新失敗: {response.text}"
        result = response.json()
        
        print(f"✅ 設定更新成功")
        print(f"   新しい設定名: {result['settings']['name']}")
        print(f"   新しい馬/騎手比率: {result['settings']['horse_weight']}% / {result['settings']['jockey_weight']}%")
    
    async def test_analyze_after_update(self):
        """Step 7: 更新後の分析"""
        print("\n🔍 Step 7: 更新後の分析（騎手重視）")
        print("-" * 40)
        
        analysis_request = {
            "chat_id": self.chat_id,
            "engine_type": "imlogic",
            "imlogic_settings_id": self.settings_id,
            "message": "騎手重視で再分析"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/logic-chat/analyze",
            json=analysis_request
        )
        
        assert response.status_code == 200, f"分析失敗: {response.text}"
        result = response.json()
        
        print(f"✅ 騎手重視設定での分析完了")
        if 'analysis_result' in result and 'results' in result['analysis_result']:
            results = result['analysis_result']['results']
            print(f"\n   上位3頭（騎手50%、騎手相性25%）:")
            for horse in results[:3]:
                print(f"   {horse['rank']}位: {horse['horse']} × {horse['jockey']}")
                print(f"      総合: {horse['total_score']}点 (馬: {horse['horse_score']} / 騎手: {horse['jockey_score']})")
    
    async def test_get_chat_history(self):
        """Step 8: チャット履歴の確認"""
        print("\n📜 Step 8: チャット履歴の確認")
        print("-" * 40)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v2/logic-chat/chat/{self.chat_id}"
        )
        
        assert response.status_code == 200, f"チャット取得失敗: {response.text}"
        result = response.json()
        
        print(f"✅ チャット履歴取得成功")
        print(f"   チャットID: {result['id']}")
        print(f"   作成日時: {result['created_at']}")
        print(f"   更新日時: {result['updated_at']}")
        
        if 'chat_history' in result and result['chat_history']:
            print(f"   メッセージ数: {len(result['chat_history'])}")
            for i, entry in enumerate(result['chat_history'][-3:], 1):
                print(f"   最近のメッセージ{i}: {entry['user_message'][:30]}...")
    
    async def test_viewlogic_analysis(self):
        """Step 9: ViewLogic分析（開発中）"""
        print("\n👁️ Step 9: ViewLogic分析（開発中）")
        print("-" * 40)
        
        analysis_request = {
            "chat_id": self.chat_id,
            "engine_type": "viewlogic",
            "message": "レースの傾向を分析して"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/logic-chat/analyze",
            json=analysis_request
        )
        
        assert response.status_code == 200, f"分析失敗: {response.text}"
        result = response.json()
        
        print(f"✅ ViewLogic応答確認")
        if 'analysis_result' in result:
            print(f"   メッセージ: {result['analysis_result'].get('message', 'なし')}")
    
    async def test_error_cases(self):
        """エラーケースのテスト"""
        print("\n⚠️ エラーケースのテスト")
        print("-" * 40)
        
        # 1. 無効な馬名での分析
        print("\n1️⃣ 無効な馬名での分析テスト")
        analysis_request = {
            "chat_id": self.chat_id,
            "engine_type": "imlogic",
            "imlogic_settings_id": "default",
            "message": "「存在しない馬」を分析して"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/logic-chat/analyze",
            json=analysis_request
        )
        
        if response.status_code == 400:
            print("✅ 期待通りエラーを返却")
            print(f"   エラー: {response.json()['detail']}")
        
        # 2. 無効な設定IDでの分析
        print("\n2️⃣ 無効な設定IDでの分析テスト")
        analysis_request = {
            "chat_id": self.chat_id,
            "engine_type": "imlogic",
            "imlogic_settings_id": "invalid-settings-id",
            "message": "分析して"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/logic-chat/analyze",
            json=analysis_request
        )
        
        if response.status_code in [404, 500]:
            print("✅ 期待通りエラーを返却")
        
        # 3. 重みの合計が100でない設定
        print("\n3️⃣ 重みの合計が100でない設定テスト")
        invalid_settings = {
            "name": "無効な設定",
            "horse_weight": 60,
            "jockey_weight": 60,  # 合計120%！
            "item_weights": {}
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v2/imlogic-settings/create",
            json=invalid_settings
        )
        
        if response.status_code == 400:
            print("✅ 期待通りバリデーションエラー")
            print(f"   エラー: {response.json()['detail']}")

async def main():
    """メインテスト実行"""
    simulator = LogicChatV2Simulator()
    try:
        # 通常のユーザーフローテスト
        await simulator.simulate_user_journey()
        
        # エラーケーステスト
        await simulator.test_error_cases()
        
        print("\n" + "=" * 80)
        print("🎉 Logic Chat V2 シミュレーションテスト完了！")
        print("=" * 80)
        
    finally:
        await simulator.close()

if __name__ == "__main__":
    asyncio.run(main())