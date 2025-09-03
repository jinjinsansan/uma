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

### 5. 統合ナレッジファイル移行完了 (2025-09-03)
- **完了**: 全てのエンジンが統合ナレッジファイル（53,618頭）を使用
- **CDN**: Cloudflare R2 `https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json`
- **旧URL削除**: GitHub Releasesの古いナレッジファイル参照を全て削除
- **メモリ削減**: 重複ダウンロードを排除し、Renderのメモリ使用量を最適化

## 🏇 騎手名マッピングシステム (2025-01-31 追加)

### 問題の背景
netkeiba.comは騎手名を最大3文字までしか表示しません（例：「北村友」「岩田望」「松山」）。
しかし、騎手ナレッジファイルには正式名で保存されています（例：「北村友一」「岩田望来」「松山弘平」）。

### 解決策
`services/jockey_name_mapper.py`を作成し、3文字騎手名を正式名に自動変換：

```python
# 使用例
from services.jockey_name_mapper import normalize_jockey_name

normalize_jockey_name('北村友')   # → '北村友一'
normalize_jockey_name('岩田望')   # → '岩田望来'
normalize_jockey_name('松山')     # → '松山弘平'
```

### 適用状況
- ✅ **IMLogicエンジン**: 実装済み（services/imlogic_engine.py line 24-25）
- ✅ **ViewLogicエンジン**: 実装済み（services/viewlogic_engine.py _normalize_jockey_name内）
- ✅ **レースアナリシスV2**: 実装済み

### 重要な注意事項
- 新しいAI機能を追加する際は、必ず`jockey_name_mapper`を使用すること
- 騎手名が取得できない場合は、まずマッパーに騎手が登録されているか確認
- マッパーには主要な騎手約100名が登録済み

## 🚀 V2システム実装状況 (2025-08-27 更新)

### 実装完成度: 85%（マイページ実装待ち）
- ✅ ポイント制度基盤: 100%完成
- ⚠️ ポイント補充機能: 30%（マイページ未実装）
- ✅ チャット機能: 95%完成  
- ✅ レース情報フロー: 98%完成
- ✅ 出走表表示: 100%完成（Phase 1-3完了）

### 本日実装完了（Phase 1-3）
1. ✅ **出走表コンポーネント**（`/src/components/v2/race/RaceTable.tsx`）
2. ✅ **データパーサー**（`/src/lib/v2/raceDataParser.ts`） - netkeiba形式対応
3. ✅ **データ入力UI**（`/src/components/v2/race/RaceDataInput.tsx`）
4. ✅ **D-Logic バッチ計算API**（`/api/v2/dlogic.py`） - Redisキャッシュ付き
5. ✅ **モバイル対応アコーディオン**（`/src/components/v2/race/RaceAccordion.tsx`）
6. ✅ **管理者レース管理画面**（`/src/app/v2/admin/race-manager/page.tsx`）

### ✅ 全機能実装完了！
1. ✅ **レース限定分析制限**（`ai_handler.py`で実装済み）
2. ✅ **自然言語AI切り替え**（`V2ChatInterface.tsx`で実装済み）

### 実装計画（残り2フェーズ）
- Phase 4: AI制御（1日）- レース限定、自然言語切替
- Phase 5: ViewLogic待ち - ViewLogicデータ提供後に統合

詳細: `mcp__serena__read_memory` → `v2_system_implementation_status_20250825`

## 📊 V2ポイントシステムの現状と課題 (2025-08-27 調査)

### 管理者アクセスの仕組み
- **管理者メール**: goldbenchan@gmail.com
- **特権**: `is_test_mode`フラグでポイント消費をスキップ
- **実装場所**: 
  - フロント: `/src/app/v2/races/[date]/page.tsx` (行114-119)
  - バック: `/api/v2/chat.py` (行149-195)

### 実装済み機能 ✅
1. **基本ポイント機能**
   - 初回登録: 2ポイント自動付与
   - チャット作成: 1ポイント消費
   - ポイント0: チャット作成不可
   - 管理者: 無制限使用

2. **APIエンドポイント**
   - `/api/v2/points/status` - ポイント確認
   - `/api/v2/points/transactions` - 履歴確認
   - `/api/v2/chat/create` - チャット作成（ポイント消費）

3. **データベース**
   - `v2_users` - ユーザー管理
   - `v2_user_points` - ポイント残高
   - `v2_point_transactions` - 取引履歴

### 未実装・問題点 ⚠️
1. **V2マイページが不完全**
   - LINE連携UIなし → ポイント追加不可
   - 友達紹介機能へのアクセスなし
   - ポイント購入機能なし

2. **ポイント補充方法がない**
   - 初回2ポイントを使い切ったら終了
   - 通常ユーザーは実質2回のみ使用可能

3. **環境変数の確認が必要**
   ```bash
   V2_POINTS_GOOGLE_AUTH=2      # 要確認
   V2_POINTS_LINE_CONNECT=12    # 要確認
   V2_POINTS_REFERRAL=22        # 要確認
   ```

### リリース前に必要な最低限の実装
1. **V2マイページ完成** (優先度: 最高)
   - LINE連携ボタンとフロー
   - 友達紹介URL表示と共有機能
   - ポイント残高の明確な表示

2. **環境変数設定確認**
   - Renderで正しく設定されているか確認

3. **将来的な拡張**（リリース後でも可）
   - Stripe決済でのポイント購入
   - デイリーログインボーナス
   - ポイントパッケージ販売

### 現状でのリリース影響
- 管理者: ✅ 問題なし（無制限使用可能）
- 通常ユーザー: ⚠️ 2回のみ使用可能
- ビジネスモデル: ❌ 収益化不可（購入機能なし）

**結論**: V2マイページのLINE連携と友達紹介機能を実装すれば、基本的なポイント制システムとして機能する。購入機能は後日実装でも可。

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

## レースアナリシスV2実装 (2025-08-17)

### アーカイブページシステムの重要な仕様

#### データ入力の流れ（毎週末）
1. **土日の作業**:
   - netkeiba.comから馬名、騎手、枠順をコピペ
   - 一度の入力で3つの分析機能に対応:
     - D-Logic/MyLogic: 馬名のみ使用（URLパラメータ）
     - レースアナリシス: 馬名＋騎手＋枠順（モーダル表示）

2. **月曜日の作業**:
   - MySQLから払い戻し結果を取得
   - レースアナリシス上位5頭を優先表示（D-Logic上位5頭より優先）
   - 的中判定を自動計算

#### 技術的な実装詳細

##### 1. データ構造（ArchiveRace型）
```typescript
interface ArchiveRace {
  // 基本情報
  race_id: string
  race_date: string
  venue: string
  race_number: number
  race_name: string
  horses: string[]
  
  // レースアナリシス用（オプション）
  distance?: string
  track_condition?: string
  jockeys?: string[]
  posts?: number[]
  horse_numbers?: number[]
  
  // 結果情報（月曜日に追加）
  result?: {
    first: string
    second: string
    third: string
    raceAnalysisTop5?: string[]  // 優先表示
    dlogicTop5?: string[]         // フォールバック
    hitType?: string
    hitDescription?: string
  }
}
```

##### 2. 3ボタン表示ロジック
- 騎手・枠順データがない場合: D-Logic、MyLogicの2ボタン
- 騎手・枠順データがある場合: D-Logic、MyLogic、レースアナリシスの3ボタン

##### 3. レースアナリシス結果の保存
- localStorage使用: `race_analysis_${race_id}`
- 保存内容: `{ analyzed_at, top5: string[] }`
- 月曜日の結果反映時に自動読み込み

##### 4. 結果表示の優先順位
1. レースアナリシス上位5頭（緑背景）
2. D-Logic上位5頭（グレー背景）
3. どちらもない場合は非表示

#### 運用上の注意事項
- **URL互換性維持**: D-Logic/MyLogicは馬名のみのパラメータを維持
- **モーダル方式**: レースアナリシスはURLパラメータを使わない
- **バックエンド独立性**: FastDLogicEngineインスタンスを共有（メモリ効率化）

## 🚀 V2 LINE連携・友達紹介・デイリーボーナス実装完了 (2025-08-25)

### 実装内容
V2ポイント制システムの初期ポイント付与機能を柔軟に実装完了。

#### バックエンドAPI
- **`/api/v2/config.py`**: 環境変数からポイント設定を読み込む中央設定
- **`/api/v2/line_referral.py`**: 6つのエンドポイント実装
  - `POST /api/v2/line/connect` - LINE連携（環境変数のポイント付与）
  - `POST /api/v2/line/referral` - 友達紹介コード適用（環境変数のポイント付与）
  - `POST /api/v2/line/daily-login` - デイリーログインボーナス（1日1回）
  - `GET /api/v2/line/referral/code` - 紹介コード取得・生成
  - `GET /api/v2/line/status` - LINE連携・紹介状態確認
  - `GET /api/v2/line/config` - 現在のポイント設定（公開情報）
- **`main.py`**: 新しいルーターを追加済み

#### フロントエンド
- **Supabaseマイグレーション**: v2_usersテーブルに必要フィールド追加
  - LINE連携: `line_user_id`, `line_connected_at`
  - 友達紹介: `referral_code`, `referral_count`, `referred_by`, `referred_at`
  - デイリーボーナス: `last_login_at`
- **`v2_referral_history`テーブル**: 紹介履歴管理

#### 環境変数設定
```bash
# .envファイルに追加済み
V2_POINTS_GOOGLE_AUTH=2      # Google認証時の付与ポイント
V2_POINTS_LINE_CONNECT=12    # LINE連携時の付与ポイント
V2_POINTS_REFERRAL=22        # 友達紹介適用時の付与ポイント
V2_POINTS_DAILY_LOGIN=1      # デイリーログインボーナス
V2_POINTS_PER_CHAT=1         # チャット作成時の消費ポイント
```

### セキュリティ対策
- 自己紹介防止
- 紹介コードの大文字統一（6文字英数字）
- 1人1回のみ紹介を受けられる制限
- すべてのAPIで認証必須

### 今後の実装予定
- フロントエンドのV2マイページ（ポイント表示・LINE連携・紹介URL表示）
- チャット作成時のポイント消費機能
- ポイント購入機能（プレミアムプラン）

## 🚀 現在進行中の開発 (2025-01-11)

### 天候適性D-Logic実装
- **計画書**: `/backend/WEATHER_DLOGIC_PLAN.md`
- **安定版タグ**: `v2.0-stable-before-weather`
- **概要**: 標準D-Logicに加えて稍重・重・不良の天候適性分析を追加
- **実装方式**: 階層的評価方式（第1層40%、第2層35%、第3層25%）

## 🏇 アーカイブレース ハイブリッド実装計画 (2025-08-19)

### 概要
レースアナリシスV2のアーカイブ認識機能を、TSファイル（高速）とSupabase（拡張性）のハイブリッド方式で実装。

### データ管理の3層構造

#### 1層目：最新5レース（TSファイル）- 超高速
```typescript
const RECENT_ARCHIVES = {
  '2025-08-24': [...], // 未来（土曜日）
  '2025-08-23': [...], // 未来（金曜日）
  '2025-08-17': [...], // 直近1
  '2025-08-16': [...], // 直近2
  '2025-08-10': [...], // 直近3
}
```

#### 2層目：メモリキャッシュ - 高速
- 頻繁にアクセスされる古いデータを一時保存

#### 3層目：Supabase - 完全なアーカイブ
- 2025-08-09以前のすべてのデータ
- 傾向分析エンジン用のSQLクエリ対応

### Supabaseテーブル設計
```sql
CREATE TABLE archive_races (
  id UUID PRIMARY KEY,
  race_id TEXT UNIQUE NOT NULL,
  race_date DATE NOT NULL,
  venue TEXT NOT NULL,
  race_number INTEGER NOT NULL,
  race_name TEXT NOT NULL,
  distance TEXT,
  track_condition TEXT DEFAULT '良',
  grade TEXT,
  horses TEXT[] NOT NULL,
  jockeys TEXT[],
  posts INTEGER[],
  horse_numbers INTEGER[],
  result JSONB, -- 払い戻し結果、的中情報など
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### 検索ロジック
1. TSファイルから検索（1-5ms）
2. 5件見つかったら即返却
3. 不足分をSupabaseから取得（50-200ms）
4. 結果をマージして返却

### 運用フロー
**毎週土曜日**：
1. netkeiba.comからコピペ
2. Claudeが最新TSファイルを更新
3. 自動的にSupabaseにも同期
4. 古いデータを自動アーカイブ

**月曜日**：
1. 払い戻し結果を更新
2. TSファイルとSupabase両方に反映

### パフォーマンス目標
- 80%のケース：1-5ms（TSファイルのみ）
- 20%のケース：50-200ms（Supabase併用）
- 平均レスポンス：約10ms

### 実装フェーズ
1. **Phase 1**: Supabaseテーブル作成と既存データ移行
2. **Phase 2**: ハイブリッド検索ロジック実装
3. **Phase 3**: 自動同期・メンテナンス機能
4. **Phase 4**: 傾向分析エンジン実装

### 注意事項
- D-Logic AI、MyLogicには一切干渉しない
- 既存のレースアナリシスV2機能を保護
- エラー時は3段階のフォールバック（TS→Supabase→エラー）

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

## 🚨 最新の作業状況 (2025-01-19 引き継ぎ)

### ✅ アーカイブページからのレースアナリシスV2 - 完成 (2025-01-19)

#### 実装状況
- **アーカイブページの分析ボタン**: 正常動作 ✅
- **日付表示**: 修正済み（必ず日付が表示される）✅
- **全馬表示**: 18頭すべて表示（5頭制限を削除）✅
- **企業秘密保護**: 「イクイノックス基準」→「レースアナリシスV2基準」に変更 ✅
- **計算ロジック**: 拡張ナレッジ（34,388頭）＋騎手ナレッジ（843騎手）で正常動作 ✅

#### 安定版タグ作成済み
- **タグ**: `v3.1-stable-archive-race-analysis-20250119`
- **バックエンド**: https://github.com/jinjinsansan/uma.git
- **フロントエンド**: https://github.com/jinjinsansan/d-logic-ai-frontend.git

#### D-Logic AI・MyLogic AIへの影響
- **影響なし**: 既存機能は一切変更していない ✅
- **独立動作**: レースアナリシスV2は完全に別システム ✅

### 🔄 次の実装予定
1. **自然言語でのレースアナリシス**（「新潟2Rを分析して」等）
   - 現在：エラー（ハイブリッドアーカイブハンドラーがフロントエンドAPIにアクセス失敗）
   - 解決方法：Supabaseでアーカイブデータを管理する実装が必要
   
### 🛠️ Memory MCP導入試行中 (2025-01-19)
- **インストール場所**: `/mnt/c/Users/USER/OneDrive/デスクトップ/Cusor/mcp-servers/`
- **状況**: サーバー起動は成功、Claude Codeからの接続が未確認
- **代替手段**: Serena MCPのメモリー機能を使用中

### 🔧 重要な修正履歴
1. **企業秘密の適切な管理**: 
   - ユーザーに見える部分のみ変更
   - 内部コメント・変数名は開発者用にそのまま保持
2. **計算ロジック検証**: 
   - 拡張ナレッジファイル（34,388頭）正常使用確認
   - ベイズ推定による保守的評価が正常動作
   - 未勝利戦のため低スコアは妥当

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

## 🔧 MyLogicAI保存エラー解決履歴 (2025-08-14)

### 問題の概要
MyLogicAI設定の保存時に「Total weight must be exactly 100, got 0」エラーが発生し、保存できない問題が発生。

### 根本原因
データベースとアプリケーション間でのフィールド名の不一致：

#### 1. フロントエンド（TypeScript）
```typescript
// 正しいフィールド名
{
  distance_aptitude: 8,
  bloodline_evaluation: 8,
  jockey_compatibility: 8,
  // ...
}
```

#### 2. データベース（PostgreSQL）
- **CHECK制約**: 古いフィールド名（speed, stamina等）を参照
- **Triggerバリデーション**: 同じく古いフィールド名を使用

#### 3. バックエンド（Python）
- `WeightConfig.values()` でエラー（Pydanticモデルを辞書に変換する必要があった）

### 解決手順

#### Step 1: 問題の調査
```sql
-- weightsフィールドの実データを確認
SELECT weights FROM user_my_logic_preferences WHERE user_id = 'xxx';
-- 結果: {"distance_aptitude": 8, "bloodline_evaluation": 8, ...}
```

#### Step 2: CHECK制約の修正
```sql
-- 古い制約を削除
ALTER TABLE user_my_logic_preferences 
DROP CONSTRAINT IF EXISTS user_my_logic_preferences_weights_check;

-- 正しいフィールド名で制約を再作成
ALTER TABLE user_my_logic_preferences 
ADD CONSTRAINT user_my_logic_preferences_weights_check CHECK (
  weights ? 'distance_aptitude' AND
  weights ? 'bloodline_evaluation' AND
  weights ? 'jockey_compatibility' AND
  weights ? 'trainer_evaluation' AND
  weights ? 'track_aptitude' AND
  weights ? 'weather_aptitude' AND
  weights ? 'popularity_factor' AND
  weights ? 'weight_impact' AND
  weights ? 'horse_weight_impact' AND
  weights ? 'corner_specialist_degree' AND
  weights ? 'margin_analysis' AND
  weights ? 'time_index'
);
```

#### Step 3: Trigger関数の修正
```sql
CREATE OR REPLACE FUNCTION validate_weights_total()
RETURNS TRIGGER AS $$
BEGIN
  -- 正しいフィールド名で合計を計算
  IF (
    COALESCE((NEW.weights->>'distance_aptitude')::int, 0) +
    COALESCE((NEW.weights->>'bloodline_evaluation')::int, 0) +
    COALESCE((NEW.weights->>'jockey_compatibility')::int, 0) +
    COALESCE((NEW.weights->>'trainer_evaluation')::int, 0) +
    COALESCE((NEW.weights->>'track_aptitude')::int, 0) +
    COALESCE((NEW.weights->>'weather_aptitude')::int, 0) +
    COALESCE((NEW.weights->>'popularity_factor')::int, 0) +
    COALESCE((NEW.weights->>'weight_impact')::int, 0) +
    COALESCE((NEW.weights->>'horse_weight_impact')::int, 0) +
    COALESCE((NEW.weights->>'corner_specialist_degree')::int, 0) +
    COALESCE((NEW.weights->>'margin_analysis')::int, 0) +
    COALESCE((NEW.weights->>'time_index')::int, 0)
  ) != 100 THEN
    RAISE EXCEPTION 'Total weight must be exactly 100, got %', 
      COALESCE((NEW.weights->>'distance_aptitude')::int, 0) +
      -- ... 省略
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### Step 4: バックエンドの修正
```python
# /chatbot/uma/backend/services/mylogic_calculator.py
def _calculate_mylogic_score(self, d_logic_scores: Dict[str, float], weights: Dict[str, int]) -> float:
    # weightsが辞書でない場合は辞書に変換
    if hasattr(weights, '__dict__'):
        weights = dict(weights)
    
    total_weight = sum(weights.values())
    # ...
```

### 教訓と今後の対策
1. **命名規則の統一**: プロジェクト全体でフィールド名を統一する
2. **マイグレーション管理**: Supabaseのマイグレーションファイルを正確に管理
3. **型変換の明示化**: Pydanticモデルと辞書の変換を明示的に行う
4. **テスト**: データベーストリガーのテストを含める

### 関連ファイル
- `/supabase/migrations/012_mylogic_preferences.sql` - 初期マイグレーション（問題のあった制約）
- `/supabase/fix_mylogic_complete.sql` - 完全な修正SQL
- `/chatbot/uma/backend/api/mylogic.py` - バックエンドAPI
- `/chatbot/uma/backend/services/mylogic_calculator.py` - 計算エンジン

## 🚀 MyLogicAI新計算方式 (2025-08-14実装)

### 概要
MyLogicAIの計算式を「偏差値変換＋累乗方式」に変更し、ユーザーの重み付けによる劇的な差別化を実現。

### 計算ロジック

#### Step 1: 偏差値変換（線形拡張）
```python
# 元のD-Logicスコア（20-95点）を0-100点に拡張
expanded_score = (score - 20) / 75 * 100
```

#### Step 2: 重み付けの累乗適用
```python
# ユーザーの重み付けを累乗指数に変換
power = weight / 33.3  # weight=100で3乗
powered_value = (expanded_score / 100) ** power
contribution = powered_value * weight
```

#### Step 3: 最終スコア計算
```python
mylogic_score = Σ(各項目の貢献度)  # 0-100点で表示
```

### パラメータ設定
```python
MIN_ORIGINAL = 20   # D-Logicスコアの実際の最小値
MAX_ORIGINAL = 95   # D-Logicスコアの実際の最大値
POWER_FACTOR = 33.3 # 累乗の強さ（100点で3乗）
```

### 実装例：血統100%設定
| 馬名 | 元の血統点 | MyLogicスコア | 標準D-Logic |
|------|-----------|---------------|-------------|
| イクイノックス | 100点 | 100.00点 | 93.18点 |
| ドウデュース | 80点 | 51.17点 | 81.73点 |
| エフフォーリア | 40点 | 1.89点 | 64.85点 |
| ジャスティンパレス | 0点 | 0.00点 | 61.36点 |

### 効果
1. **劇的な差別化**: 100点 vs 0点の極端な差
2. **順位の大逆転**: 標準D-Logicとは全く異なる評価
3. **ユーザーカスタマイズの明確化**: 重視項目が結果に直結

### テストスクリプト
- `/chatbot/uma/backend/test_mylogic_dramatic.py` - 新計算式の動作確認用

## レース結果管理システム (2025-08-18)

### 概要
D-Logic V2開発のためのデータ収集を目的とした、レース結果の記録・表示システムを実装。

### 実装内容

#### 1. 結果表示コンポーネント
- **ファイル**: `/src/components/race/RaceResultDisplay.tsx`
- **機能**:
  - 払い戻し結果（1着・2着・3着）
  - D-Logic上位5頭
  - 的中タイプ（🎯的中/⚡一部的中/❌不的中）
  - グラデーション背景による美しいUI

#### 2. バッチD-Logic分析機能
- **管理者パネル**: `/admin/batch-analysis`
- **対象**:
  - 土日のアーカイブレース
  - 2024年過去G1レース（全21レース）
- **APIエンドポイント**:
  - `POST /api/admin/batch-dlogic-analyze`
  - `POST /api/admin/apply-dlogic-results`
  - `GET /api/admin/g1-results`

#### 3. 払い戻し結果の運用フロー

##### 毎週月曜日の定期作業
1. **MySQLから結果取得**
   ```bash
   cd /chatbot/uma/backend
   python get_weekend_race_results.py
   ```

2. **Claudeが結果を報告**
   - 土日の全レース結果（1-3着）
   - JSON形式で保存済み

3. **管理者がメモ**

4. **チャットで更新指示**
   - 「アーカイブページに払い戻し結果を反映させてください」
   - 結果データを貼り付け

5. **Claudeが更新実行**
   - アーカイブページの各レースに結果追加
   - RaceResultDisplayで自動表示

#### 4. データ構造
```typescript
interface RaceResult {
  first: string;        // 1着馬
  second: string;       // 2着馬  
  third: string;        // 3着馬
  dlogicTop5?: string[]; // D-Logic上位5頭
  hitType?: string;      // 的中タイプ
  hitDescription?: string; // 的中詳細
}
```

#### 5. 重要な変更点
- **サンプルデータの完全削除**: 競馬予想において架空のデータは不適切
- **実データのみ使用**: 管理者パネルでの分析実行後に表示
- **段階的なデータ蓄積**: V2開発に向けた3ヶ月間のデータ収集

### 注意事項
- 払い戻し結果の更新は手動作業（自動化は将来検討）
- D-Logic分析は管理者パネルから実行必要
- 結果データはgit管理外（`data/archive_updates/`）

## 🏇 D-Logic レースアナリシス実装計画 (2025-08-17開始)

### 概要
馬と騎手の総合分析により、レース全体を高精度で予想する新システム。イクイノックスを基準（100点）とし、開催場適性・クラス補正・馬場適性を考慮。

### 技術仕様
- **基準馬**: イクイノックス（現行D-Logicのダンスインザダークから変更）
- **分析比率**: 馬70%：騎手30%
- **表示形式**: シンプル表示＋詳細展開式
- **データソース**: アーカイブページ（騎手・枠順情報付き）
- **アクセス**: URLダイレクトのみ（ナビゲーションバー非表示）

### 実装ステータス (2025-08-17 23:00更新)

#### ✅ Phase 2: バックエンド拡張エンジン実装（完了）
1. **イクイノックス基準エンジン**
   - `/backend/services/modern_dlogic_engine.py` 実装完了
   - イクイノックス基準（100点）での評価システム
   - 開催場・距離の統合評価（重要: 別々ではなく組み合わせで評価）
   - クラス補正係数（G1: 1.3倍, G2: 1.2倍, ... 未勝利: 0.9倍）
   - 馬場適性評価（-5～+5点）

2. **騎手分析エンジン**
   - `/backend/services/jockey_data_manager.py` 実装完了
   - 騎手ナレッジファイル（843騎手）をCDNから自動取得
   - 開催場適性（-10～+10点）
   - 枠順適性（-7.5～+7.5点）
   - 種牡馬相性（将来拡張用）

3. **統合分析エンジン**
   - `/backend/services/race_analysis_engine.py` 実装完了
   - 馬70%：騎手30%の重み付け
   - エラー耐性（一部の馬でエラーが出ても継続）
   - 詳細な分析情報の提供

4. **APIエンドポイント**
   - `/api/race-analysis-v2` 実装完了
   - `/api/race-analysis-v2/quick` 簡易版も実装
   - 開催場・距離データの自動取得対応

#### 📝 Phase 1: 会話フロー実装（進行中）
1. **アーカイブページ拡張**
   ```typescript
   // 拡張後の形式
   {
     venue: '札幌',
     race_number: 11,
     race_name: '札幌記念（G3）',
     distance: '2000m',
     horses: ['ドウデュース', ...],
     jockeys: ['武豊', ...],
     posts: [1, 2, ...],  // 枠順
     horse_numbers: [1, 2, ...]  // 馬番
   }
   ```

2. **レース名辞書作成**
   - 主要レース50個の情報（開催場・距離・クラス）
   - パターンマッチングによる自動認識

3. **会話フロー設計**
   ```
   ユーザー：「札幌記念を分析して」
   システム：レース情報自動取得 → 馬場確認 → 総合分析
   ```

#### ⏳ Phase 3: フロントエンド統合（未着手）
1. **非表示ページ作成**
   - `/race-analysis`（ナビゲーションに含まない）
   - チャット経由でのアクセスのみ

2. **結果表示UI**
   ```
   🏆 D-Logic レースアナリシス（イクイノックス基準）
   
   🥇 ドウデュース × 武豊 【95.5点】
   🥈 プログノーシス × C.ルメール 【92.3点】
   
   詳細を見る ▼（展開式）
   ```

#### ⏳ Phase 4: テスト（未着手）
- 運営チームでの内部テスト
- 2024年G1全21レースでの精度検証
- パフォーマンス最適化

### 重要な実装ポイント
1. **既存D-Logicとの分離**: 現行システムは変更しない
2. **段階的リリース**: 運営テスト後、全ユーザー公開
3. **キャッシュ戦略**: 頻繁なレース情報はメモリキャッシュ
4. **エラーハンドリング**: アーカイブデータ欠損時の対応

### 技術的な発見事項
1. **馬のナレッジファイルにはトラックコードと距離情報が存在**
   - TRACK_CODE: 17=札幌, 11=東京, 13=京都など
   - KYORI: 距離（メートル単位）
   - 血統情報は現在含まれていない

2. **騎手名の正規化が必要**
   - 騎手名の末尾スペースを除去する処理を実装

3. **開催場と距離は統合評価が必要**
   - 例: 「札幌2000m」という組み合わせで評価
   - 開催場だけ、距離だけの評価では不十分

### テスト結果の例
```
🏆 D-Logic レースアナリシス - 2024 有馬記念

🥇 1位: ドウデュース × 武豊 【87.3点】
   馬: 91.5点（基準73.0 + 開催場+3.0 × クラス1.30）
   騎手: -5.5点（開催場-2.5 + 枠順-3.0）

🥈 2位: スターズオンアース × C.ルメール 【86.8点】
   馬: 92.4点（基準71.0 + 開催場+5.0 × クラス1.30）
   騎手: -11.0点（開催場-4.0 + 枠順-7.0）
```

### 期待される成果
- **的中率**: 現在40% → 目標55-65%
- **分析時間**: 5分（手動入力）→ 3秒（自動取得）
- **ユーザー体験**: 大幅改善

### バックアップタグ
- **実装前**: `v3.2-before-race-analysis-20250817`

## レースアナリシスV2 アーカイブページ統合 (2025-08-17)

### 重要な設計決定
レースアナリシスV2機能をアーカイブページに統合する際、既存のD-Logic/MyLogic機能に影響を与えない設計を採用。

### データ形式の拡張
```typescript
interface ArchiveRace {
  // 既存フィールド（D-Logic/MyLogic用）
  race_id: string;
  race_date: string;
  venue: string;
  race_number: number;
  race_name: string;
  horses: string[];              // 馬名のみ
  
  // レースアナリシスV2用の追加フィールド
  distance?: string;             // "2000m"
  track_condition?: string;      // "良"
  jockeys?: string[];           // 騎手名リスト
  posts?: number[];             // 枠順リスト
  horse_numbers?: number[];     // 馬番リスト
}
```

### 3つの分析ボタンの実装
```typescript
{/* D-Logic分析（馬名のみ使用） */}
<button onClick={() => router.push(`/d-logic-ai?horses=${horses.join(',')}`)}>
  D-Logic分析
</button>

{/* MyLogic分析（馬名のみ使用） */}
<button onClick={() => router.push(`/my-logic-ai?horses=${horses.join(',')}`)}>
  MyLogic分析
</button>

{/* レースアナリシス（全情報使用）- モーダル表示 */}
<button onClick={() => openRaceAnalysisModal({
  horses, jockeys, posts, horse_numbers, venue, distance, track_condition
})}>
  レースアナリシス
</button>
```

### 運用効率化のポイント
1. **一度のデータ入力で3機能対応**
   - netkeiba.comからコピペした情報を一括で処理
   - D-Logic/MyLogic: 馬名のみ抽出
   - レースアナリシス: 全情報を活用

2. **既存機能への影響ゼロ**
   - URLパラメータは馬名のみ維持
   - チャットAPIの動作に変更なし
   - レースアナリシスは独立したモーダル処理

3. **週末の作業フロー**
   ```
   1. netkeiba.comから情報コピー
   2. Claudeにペースト
   3. アーカイブページに以下を一括追加:
      - horses: [...] （全機能で使用）
      - jockeys: [...] （レースアナリシスのみ）
      - posts: [...] （レースアナリシスのみ）
      - horse_numbers: [...] （レースアナリシスのみ）
   ```

### 技術的な分離
- **D-Logic/MyLogic**: `/api/chat/message` エンドポイント（馬名のみ）
- **レースアナリシスV2**: `/api/race-analysis-v2` エンドポイント（全情報）
- **モーダル実装**: 結果をその場で表示、ページ遷移なし

この設計により、毎週の運用作業が効率化され、かつ既存機能の安定性を保証します。