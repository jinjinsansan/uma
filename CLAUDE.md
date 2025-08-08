# CLAUDE.md - D-Logic AI プロジェクト

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 重要な決定事項 (2025/08/08 更新)

### 1. ナレッジファイル管理の最終決定
- **結論**: ナレッジファイルはローカルPCで管理
- **理由**: 
  - Git LFS は Render で `git lfs` コマンドが使えない
  - 100MB超のファイルは GitHub にプッシュ不可
  - Render は既にローカル MySQL にアクセスしているので同じ仕組みで OK

### 2. 現在のシステム構成
```
[ユーザー] → [Vercel(フロントエンド)] → [Render(バックエンドAPI)]
                                              ↓
                                    [ローカルPC(常時稼働)]
                                    ├─ MySQL (172.25.160.1:3306)
                                    └─ dlogic_raw_knowledge.json (102MB+)
```

### 3. ナレッジファイル再構築計画
- **対象**: 2020-2025年の中央競馬馬
- **条件**: 5走以上の馬（約30,000頭想定）
- **保存先**: `backend/data/dlogic_raw_knowledge.json`
- **Git管理**: .gitignore に追加（プッシュしない）

### 4. D-Logic 機密情報の保護
- **基準馬名は絶対に秘密**
- システムプロンプトから削除済み
- 「独自基準100点」という表現で統一

### 5. 今後の課題と解決策
- **課題**: ローカルPC依存（電源、ネットワーク）
- **将来**: Supabase 等のクラウドストレージへ移行
- **現在**: PC常時稼働で運用

## 🔄 ナレッジファイル再構築手順 (2025/08/08 追記)

### 1. D-Logic計算エンジンの理解
- **12項目分析**: 各項目を指数化して総合評価
- **必要データ**: 過去5走分（最低3走）の生データ
- **データ期間**: 2020-2025年の全馬データ

### 2. 新バッチ処理スクリプト
**`batch_dlogic_knowledge_builder.py`** を使用：
```bash
cd backend
python batch_dlogic_knowledge_builder.py
```

#### 特徴：
- **2ファイル同時出力**:
  - `dlogic_raw_knowledge.json` - システム用
  - `dlogic_raw_knowledge_summary.txt` - 人間確認用
- **進捗確認**: テキストファイルでリアルタイム確認可能
- **収録馬リスト**: アルファベット順で全馬名を記録
- **干渉回避**: 既存スクリプトと独立して動作

### 3. Git管理の注意
`.gitignore` に以下を追加済み：
```
backend/data/dlogic_raw_knowledge.json
backend/data/immediate_batch_*.json
```

### 4. 既存バッチ処理スクリプト
以下のスクリプトが存在するが、新規作成した `batch_dlogic_knowledge_builder.py` を推奨：
- `batch_create_raw_knowledge.py` - 旧メイン処理
- `batch_immediate_start.py` - 軽量版
- `batch_rebuild_knowledge_2025.py` - 中間版

### 5. 動作確認方法
1. テキストファイルで収録馬を確認
2. チャットで収録馬名を入力してテスト
3. 未収録馬はMySQLから動的取得される

## 🎉 D-Logic 12項目計算の完成 (2025/08/08 更新)

### 問題の経緯
1. **ナレッジファイルの馬がヒットしない**
   - APIリクエストごとに新しいFastDLogicEngineインスタンスを作成
   - 150MBファイルを毎回ダウンロードしてタイムアウト

2. **計算結果が50点（デフォルト値）ばかり**
   - バッチ処理のフィールド名と計算関数のフィールド名が不一致
   - 12項目中2項目しか計算できない

### 解決策
1. **グローバルインスタンスの使用**
   ```python
   # モジュールレベルで1回だけ初期化
   fast_engine_instance = FastDLogicEngine()
   ```

2. **フィールド名マッピングの修正**
   - KISHUMEI_RYAKUSHO (騎手)
   - CHOKYOSHIMEI_RYAKUSHO (調教師)
   - TANSHO_NINKIJUN (人気)
   - FUTAN_JURYO (斤量)
   - BATAIJU (馬体重)
   - CORNER1_JUNI〜CORNER4_JUNI (コーナー)
   - SOHA_TIME (タイム)
   - TRACK_CODE, TENKO_CODE (トラック・天候)

3. **天候適性の実装**
   - TENKO_CODE: 1=晴, 2=曇, 3=雨, 4=小雨, 5=雪, 6=小雪
   - 馬場状態: 1=良, 2=稍重, 3=重, 4=不良
   - 天候×馬場状態の組み合わせで評価

### 最終結果
- **改善前**: 2/12項目のみ計算、総合スコア47.27点
- **改善後**: 12/12項目すべて計算、総合スコア81.84点（Sランク）

## 🔥 150MBナレッジファイル問題の解決履歴 (2025/08/08 更新)

### 問題の経緯
1. **当初の理解**: Renderからローカル MySQL/ファイルにアクセス可能と誤解
2. **現実**: Renderはローカルリソースにアクセス不可（ネットワーク的に別環境）
3. **課題**: 150MBのナレッジファイルをどうやってRenderで使うか

### 失敗した試み
1. **Git LFS** ❌
   - ローカルファイルがポインタに置き換わり、データ消失
   - Renderに `git lfs` コマンドがない

2. **GitHub直接プッシュ** ❌
   - 100MB制限でエラー
   - 150MBは大きすぎる

3. **ファイル分割案** ❌
   - アップロードは可能だが、16頭同時計算で全チャンク読み込み
   - パフォーマンス劣化

### 成功した解決策: GitHub Releases 🎉

#### 手順
1. **新リポジトリ作成**: `dlogic-knowledge-data`
2. **GitHub Releases でアップロード**:
   - Web UIから150MBファイルを直接アップロード
   - URL: `https://github.com/jinjinsansan/dlogic-knowledge-data/releases/download/V1.0/dlogic_raw_knowledge.json`

3. **バックエンド修正**: `dlogic_raw_data_manager.py`
   ```python
   def _download_from_github(self):
       github_url = "https://github.com/jinjinsansan/dlogic-knowledge-data/releases/download/V1.0/dlogic_raw_knowledge.json"
       response = requests.get(github_url, timeout=60)
       # Renderのメモリに保存
   ```

#### 最終アーキテクチャ
```
ユーザー → Vercel → Render → GitHub Releases
                      ↓
                  メモリに150MB保持
                  37,878頭で高速計算
```

## 📝 新規会話用プロンプト

以下を新しいClaude会話の最初に貼り付けてください：

```
私はD-Logic AI競馬予想システムの開発者です。以下がシステムの現状です：

## システム構成
- フロントエンド: Next.js (Vercel) - https://www.dlogicai.in
- バックエンド: FastAPI (Render) - https://uma-i30n.onrender.com
- ナレッジファイル: GitHub Releases (150MB, 37,878頭)
  URL: https://github.com/jinjinsansan/dlogic-knowledge-data/releases/download/V1.0/dlogic_raw_knowledge.json

## 重要な注意事項
1. D-Logicの「D」の意味（ダンスインザダーク）は絶対に秘密
2. 基準馬名は「独自基準100点」と表現
3. ナレッジファイルは Git LFS を使わない（データ消失の危険）
4. バックエンドは起動時にGitHub Releasesから自動ダウンロード

## ファイル構成
- /front/d-logic-ai-frontend - フロントエンド
- /chatbot/uma/backend - バックエンド
- /chatbot/uma/backend/data - ナレッジファイル（.gitignore済み）

## 現在の課題
[ここに現在取り組みたい課題を記入]
```

## 🎯 今後の運用

### データ更新時
1. `batch_dlogic_knowledge_builder_v2.py` でナレッジファイル再生成
2. GitHub Releases に新バージョンとしてアップロード
3. `dlogic_raw_data_manager.py` のURLを更新

### 注意事項
- ~~Renderの無料プランはメモリ512MB~~→ 有料プラン(2GB)にアップグレード済み
- 初回起動時のダウンロードに時間がかかる（その後は高速）
- GitHub Releases は2GBまでアップロード可能
- 全馬名検索対応（「ヤマニンバロネスは？」などのシンプルな質問もOK）

## 🎯 今後の課題

1. **aggregated_statsの追加**
   - 騎手・調教師別の集計データをバッチ処理に追加
   - より精度の高い分析が可能に

2. **ナレッジファイルの定期更新**
   - 新しいレースデータの反映
   - GitHub Releasesに新バージョンとしてアップロード

3. **パフォーマンス最適化**
   - キャッシュ機構の実装
   - 並列処理の導入

## プロジェクト構成

### フロントエンド
- **場所**: `/front/d-logic-ai-frontend`
- **技術**: Next.js 14, TypeScript, Tailwind CSS
- **ホスト**: Vercel (https://www.dlogicai.in)

### バックエンド
- **場所**: `/chatbot/uma/backend`
- **技術**: FastAPI, Python 3.13
- **ホスト**: Render (https://uma-i30n.onrender.com)
- **主要機能**:
  - D-Logic 計算エンジン
  - チャット API
  - MySQL/ナレッジファイル連携

### データソース（ローカル）
- **MySQL**: 172.25.160.1:3306
  - ユーザー: root
  - パスワード: admin
  - データベース: keiba_dw
- **ナレッジファイル**: `backend/data/dlogic_raw_knowledge.json`

## 開発時の注意事項

1. **ナレッジファイルは絶対に git add しない**
2. **基準馬名を含むコードは書かない**
3. **ローカルPCが起動していることを確認**
4. **MySQLサービスが稼働していることを確認**

## トラブルシューティング

### ナレッジファイルが見つからない
- ローカルで再構築: `python batch_immediate_start.py`

### MySQL接続エラー
- サービス確認: `services.msc` で MySQL80 を確認
- ファイアウォール: ポート 3306 を開放

### Render デプロイエラー
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`