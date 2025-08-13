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

## 🚀 現在進行中の開発 (2025-01-11)

### 天候適性D-Logic実装
- **計画書**: `/backend/WEATHER_DLOGIC_PLAN.md`
- **安定版タグ**: `v2.0-stable-before-weather`
- **概要**: 標準D-Logicに加えて稍重・重・不良の天候適性分析を追加
- **実装方式**: 階層的評価方式（第1層40%、第2層35%、第3層25%）

## 🔄 月次ナレッジファイル更新システム (2025/08/12 追加)

### 概要
MySQLデータベースから新しい馬のデータを取得し、ナレッジファイルを月次で更新するシステム。管理者が手動でコントロール可能。

### アクセス方法
- **秘密URL**: `/admin/knowledge-updater?key=dlogic-knowledge-2025-secret`
- **バックエンドAPI**: `/api/admin/knowledge-update/{secret_key}`
- **注意**: この URL は一般ユーザーには公開しない

### 機能
1. **差分更新**: 前回更新日以降に3走以上した馬のデータを取得
2. **既存データとマージ**: 新しい馬を追加、既存馬は更新
3. **ファイル生成**: JSON形式および圧縮版（.gz）を生成
4. **履歴管理**: 過去の更新ファイルの管理（ダウンロード・削除）

### 更新手順
1. 毎月第一月曜日に秘密URLにアクセス
2. 「月次更新を実行」ボタンをクリック
3. 生成されたファイルをダウンロード
4. GitHub Releases に新バージョンとしてアップロード
5. `dlogic_raw_data_manager.py` の URL を更新
6. Render で再デプロイ

### 技術詳細
- **サービス**: `services/monthly_knowledge_updater.py`
- **APIルーター**: `api/admin_knowledge.py`
- **フロントエンド**: `src/app/admin/knowledge-updater/page.tsx`
- **出力先**: `backend/data/monthly_updates/`

### セキュリティ
- 秘密キーによるアクセス制限
- ファイル名の検証によるディレクトリトラバーサル対策
- 管理者のみが知る URL

## 🎫 LINE友達紹介機能実装計画 (2025/08/12 開始)

### 概要
LINE友達紹介システムを実装し、ユーザー獲得と利用促進を図る。紹介者には分析回数増加の特典を提供。

### 使用制限の設計
1. **Google認証のみ**: 1回/日（お試し）
2. **Google認証 + LINE連携**: 2回/日
3. **LINE友達紹介1人達成**: 12回/日
4. **13回以上**: プレミアムプラン必要

### データベース設計
```sql
-- 紹介管理テーブル
line_referrals (
  id uuid primary key,
  referrer_id uuid references users(id),
  referred_id uuid references users(id),
  referral_code text unique,
  status text default 'pending',
  created_at timestamp default now(),
  completed_at timestamp
)

-- ユーザーテーブルに追加
users テーブルに追加:
- referral_code text unique
- referral_count integer default 0
```

### 実装フェーズ
1. **Phase 1**: データベース設計（1日）
2. **Phase 2**: バックエンドAPI（1日）
   - 紹介コード生成API
   - 紹介登録API
   - 使用制限API更新
3. **Phase 3**: フロントエンド（2日）
   - マイアカウントに紹介URL表示
   - 紹介経由の登録処理
   - 使用制限表示の更新
4. **Phase 4**: テスト・調整（1日）

### 重要な実装ポイント
- 紹介URLフォーマット: `https://www.dlogicai.in/?ref=ABC123`
- 紹介コード: 6-8文字の英数字
- 不正対策: 同一IP制限、短期間の大量紹介ブロック
- キャッシュ考慮: 紹介数カウントの効率化

### 安定版タグ
- **実装前バックアップ**: `v2.2-stable-before-referral`

## 🎯 今後の課題

### ✅ 複数馬分析機能 (2025/08/08 完了)

実装完了した機能：
- 最大20頭までの複数馬同時分析
- レース情報の自動検出（G1レース名、日付など）
- 出力パターンの自動切り替え（単頭/複数頭/G1レース）
- エラーハンドリングと部分的な分析結果の返却
- 18頭のパフォーマンステスト（0.018秒で完了）

### 次の実装目標：OCR機能でレース情報登録 (2025/08/08 追記)

#### 概要
管理画面でOCRを使ってレース情報を読み込み、本日の開催レースページから簡単にD-Logic分析ができる仕組み

#### 技術仕様
- **OCR**: Claude API（claude-3-5-sonnet-20241022）
- **画像形式**: Base64エンコード
- **データ保存**: 一時的（当日のみ、メモリ内管理）
- **既存実装**: かけるのAIのコードを参考に簡略化

#### 開発計画
**Step 1: バックエンドOCR基盤**
- OCRエンドポイント作成 (`/api/admin/ocr-race`)
- レース情報一時保存API (`/api/today-races/ocr`)

**Step 2: フロントエンド管理画面**
- OCRコンポーネント作成
- 管理画面レース入力ページ実装

**Step 3: ユーザー側機能連携**
- 本日レースページにD-Logic分析ボタン追加
- チャット画面への自動遷移機能

**Step 4: 過去レース対応**
- 2024年G1レーステンプレート作成

**Step 5: テストと最終調整**
- エンドツーエンドテスト実施

### その他の課題

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

## 📝 安全な実装手順

### 複数馬分析機能の実装時の注意
1. **テストファースト**
   - まずローカルで動作確認
   - 少数の馬（2-3頭）でテスト
   - 大量の馬（16-18頭）でパフォーマンス確認

2. **既存機能への影響を最小化**
   - 単頭分析の動作を変更しない
   - 新しい判定ロジックを追加するだけ

3. **エラーハンドリング**
   - 不明な馬名の処理
   - タイムアウト対策
   - メモリ使用量の監視

## 🚀 MyLogicAI実装 (2025-01-13)

### 概要
ユーザーが12項目の重み付けをカスタマイズして、独自のD-Logic分析を作成できる機能

### 実装状況
- **Phase 1-4**: 完了 ✅
  - フロントエンド: 紫色のテーマ、12項目スライダー
  - データベース: Supabaseマイグレーション作成済み
  - バックエンドAPI: モック実装（`/api/mylogic.py`）
  - フロント統合: 全ページAPI連携済み

- **Phase 5**: 実施中 🚧
  - フロントエンド: Vercelデプロイ済み
  - バックエンド: Renderデプロイ準備中

### APIエンドポイント
- GET `/api/my-logic/preferences` - 設定取得
- POST `/api/my-logic/preferences` - 設定保存
- GET `/api/my-logic/can-edit` - 編集権限確認
- POST `/api/my-logic/analyze` - MyLogic分析
- POST `/api/my-logic/preview` - プレビュー分析
- GET `/api/my-logic/history` - 編集履歴

### 重要な注意点
- 現在はモック実装（実際のD-Logic計算は未統合）
- 認証は簡易実装（本番では要改善）
- Supabase連携は次フェーズで実装予定