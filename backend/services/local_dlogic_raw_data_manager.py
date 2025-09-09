#!/usr/bin/env python3
"""
地方競馬版D-Logic生データナレッジマネージャー
南関東4場（大井・川崎・船橋・浦和）専用
JRA版から継承して、URLのみ変更
"""
import logging
from .dlogic_raw_data_manager import DLogicRawDataManager

logger = logging.getLogger(__name__)

class LocalDLogicRawDataManager(DLogicRawDataManager):
    """地方競馬版D-Logic生データ管理システム"""
    
    def __init__(self):
        """初期化：地方競馬版専用のキャッシュパスを設定"""
        # 親クラスの初期化を呼ばない（JRAデータを読み込まないため）
        # super().__init__()
        
        # 必要な属性を直接設定
        import os
        if os.environ.get('RENDER'):
            self.knowledge_file = '/var/data/local_dlogic_raw_knowledge.json'  # localプレフィックス
        else:
            self.knowledge_file = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'local_dlogic_raw_knowledge.json'
            )
        print(f"🏇 地方競馬版キャッシュパス: {self.knowledge_file}")
        
        # ナレッジデータを読み込み
        self.knowledge_data = self._load_knowledge()
        
        # 地方競馬版CDN URL
        self.cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_unified_knowledge_20250907.json"
    
    def _load_knowledge(self):
        """地方競馬版ナレッジファイルの読み込み"""
        import os
        import json
        
        # キャッシュファイルが存在する場合
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    horse_count = len(data.get('horses', {}))
                    print(f"✅ 地方競馬ナレッジファイル読み込み: {horse_count}頭")
                    
                    # データ構造の確認
                    if horse_count > 0:
                        sample_horse = list(data['horses'].values())[0] if 'horses' in data else {}
                        print(f"📊 データ構造確認 - サンプル馬: {sample_horse.get('horse_name', 'N/A')}")
                        if sample_horse:
                            print(f"   キー: {list(sample_horse.keys())[:4]}")
                    
                    return data
            except Exception as e:
                print(f"❌ ナレッジファイル読み込みエラー: {e}")
        
        # CDNからダウンロード
        print("📥 CDNからダウンロード中...")
        return self._download_from_github()
    
    def _download_from_github(self):
        """Cloudflare R2から地方競馬版ナレッジファイルをダウンロード"""
        # 地方競馬版統合ナレッジファイルURL
        self.cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_unified_knowledge_20250907.json"
        
        import requests
        from datetime import datetime
        
        try:
            print("🏇 Cloudflare R2から地方競馬版ナレッジファイルをダウンロード中...")
            response = requests.get(self.cdn_url, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                # データ構造を確認（馬名が直接キーになっている）
                if isinstance(data, dict) and 'horses' not in data:
                    horse_count = len(data)
                    print(f"✅ 地方競馬版ダウンロード完了: {horse_count}頭のデータを取得")
                    # horsesキーでラップしてJRA版と同じ構造にする
                    data = {
                        "meta": {
                            "version": "1.0",
                            "type": "local_racing",
                            "created_at": datetime.now().isoformat()
                        },
                        "horses": data
                    }
                else:
                    horse_count = len(data.get('horses', {}))
                    print(f"✅ 地方競馬版ダウンロード完了: {horse_count}頭のデータを取得")
                
                # ローカルに保存（キャッシュとして）- JRA版と同じ処理
                import os
                import json
                try:
                    if os.environ.get('RENDER'):
                        os.makedirs('/var/data', exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
                    
                    with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"💾 地方競馬版を永続ディスクに保存完了: {self.knowledge_file}")
                except Exception as e:
                    print(f"⚠️ ローカル保存失敗（メモリ上で動作継続）: {e}")
                
                return data
            else:
                print(f"❌ ダウンロード失敗: HTTPステータス {response.status_code}")
                
        except Exception as e:
            print(f"❌ ダウンロードエラー: {e}")
        
        # フォールバック：空のナレッジ構造を返す
        print("⚠️ 地方競馬版ナレッジファイルが取得できません。")
        return {
            "meta": {
                "version": "1.0",
                "type": "local_racing",
                "created_at": datetime.now().isoformat()
            },
            "horses": {}
        }

# グローバルインスタンス（シングルトン）
local_dlogic_manager = LocalDLogicRawDataManager()
print(f"🏇 地方競馬版マネージャー初期化完了")