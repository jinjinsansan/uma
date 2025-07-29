# UmaOracle AI - 競馬予想チャットボット

JRAの過去データ + 独自計算式 + LLMを組み合わせた競馬予想チャットボットWebアプリケーションです。

## 技術スタック

### フロントエンド
- Next.js 14 + TypeScript + Tailwind CSS + App Router
- Framer Motion (アニメーション)
- Zustand (状態管理)
- Lucide React (アイコン)

### バックエンド
- Python FastAPI + uvicorn
- OpenAI API (GPT-4)

## 機能

- 🎯 8条件計算エンジン（脚質、距離、コース等）
- 🤖 AIチャットボット（自然な会話）
- 🎨 美しい3D球体アニメーション
- 📱 レスポンシブデザイン
- ⚡ リアルタイム予想処理

## 8条件定義

1. **脚質**: 逃げ、先行、差し、追込の適性
2. **右周り・左周り複勝率**: コース回り方向別成績
3. **距離毎複勝率**: 1000-3600mの距離別成績
4. **出走間隔毎複勝率**: 連闘、中1、中2、中3-4、中5-8、中9-12、中13以上
5. **コース毎複勝率**: 競馬場・芝ダート・距離の組み合わせ
6. **出走頭数毎複勝率**: 7頭以下、8-12頭、13-16頭、16-17頭、16-18頭
7. **馬場毎複勝率**: 良、重、やや重、不良
8. **季節毎複勝率**: 1-3月、4-6月、7-9月、10-12月

## セットアップ

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd keiba-ai
```

### 2. フロントエンドのセットアップ
```bash
cd frontend
npm install
```

### 3. バックエンドのセットアップ
```bash
cd ../backend
pip install -r requirements.txt
```

### 4. 環境変数の設定
```bash
# フロントエンド
cp frontend/env.local frontend/.env.local

# バックエンド（オプション）
export OPENAI_API_KEY=your_openai_api_key
```

### 5. 開発サーバーの起動

**Terminal 1: FastAPI**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2: Next.js**
```bash
cd frontend
npm run dev
```

## 使用方法

1. ブラウザで `http://localhost:3000` にアクセス
2. チャットボットに「今日のレースの予想は？」と入力
3. 8条件から4つを選択（優先順位付き）
4. AIが予想結果を表示

## アーキテクチャ

```
┌─ Next.js App (Port 3000) ─┐    ┌─ Python FastAPI (Port 8000) ─┐
│ ・チャットUI               │────│ ・8条件計算エンジン          │
│ ・アニメーション           │    │ ・予想指数算出               │
│ ・条件選択UI               │    │ ・OpenAI API統合             │
│ ・結果表示                 │    │ ・JV-Linkデータ取得（将来）  │
└─────────────────────────┘    └─────────────────────────┘
```

## 開発優先順位

- **Phase 1**: 基盤構築（1-3日）
- **Phase 2**: UI/UX実装（3-5日）
- **Phase 3**: AI統合（1-2日）
- **Phase 4**: 最適化・テスト（1-2日）

## 注意事項

- JRAデータ利用規約: 個人利用限定、商用化制限あり
- レスポンシブ対応: モバイルファーストで設計
- パフォーマンス: 大量データ処理時の最適化
- エラーハンドリング: API障害時の適切な対応
- セキュリティ: API Key等の環境変数管理

## ライセンス

このプロジェクトは個人利用目的でのみ使用してください。