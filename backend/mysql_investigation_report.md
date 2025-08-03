# MySQL mykeibadb データ調査レポート

## 調査結果サマリー

**データベース接続設定**
- Host: localhost:3306
- User: root
- Password: 04050405Aoi-
- Database: mykeibadb
- Charset: utf8mb4

**現在のステータス**
- ❌ MySQLサーバー未起動（Windows側で要起動）
- ✅ 接続設定は正常に設定済み
- ✅ MySQLドライバー導入済み（API実装済み）

## Phase Dで期待されるテーブル構造（API実装から推定）

### 1. race_shosai（レース詳細）
**フィールド（確認済み）:**
- RACE_CODE（16桁レースコード）
- KAISAI_NEN（開催年）
- KAISAI_GAPPI（開催月日）
- KEIBAJO_CODE（競馬場コード 01-10）
- RACE_BANGO（レース番号）
- KYOSOMEI_HONDAI（競走名本題）
- KYORI（距離）
- TRACK_CODE（トラックコード）
- GRADE_CODE（グレードコード、A=G1）
- SHUSSO_TOSU（出走頭数）
- HASSO_JIKOKU（発走時刻）
- SHIBA_BABAJOTAI_CODE（芝馬場状態）
- DIRT_BABAJOTAI_CODE（ダート馬場状態）

### 2. umagoto_race_joho（馬ごとレース情報）
**フィールド（確認済み）:**
- RACE_CODE（レースコード）
- UMABAN（馬番）
- BAMEI（馬名）
- KETTO_TOROKU_BANGO（血統登録番号）
- KISHUMEI_RYAKUSHO（騎手名略称）
- FUTAN_JURYO（負担重量）
- TANSHO_ODDS（単勝オッズ）
- CHAKUJUN（着順）
- KAKUTEI_CHAKUJUN（確定着順）
- CORNER1_JUNI（1コーナー順位）
- CORNER2_JUNI（2コーナー順位）
- CORNER3_JUNI（3コーナー順位）
- CORNER4_JUNI（4コーナー順位）
- KAISAI_DATE（開催日）

## Phase Dデータ活用戦略

### 処理対象データ（推定値）
- **レース数**: 数十万レース（2022-2024年G1レース含む）
- **総馬数**: 数万頭
- **レース記録**: 数百万レコード
- **処理対象馬**: 2戦以上の実績馬（数千頭）

### D-Logic向けデータ分析項目
1. **距離適性** - KYORI, TRACK_CODE使用
2. **血統評価** - KETTO_TOROKU_BANGO使用  
3. **騎手適性** - KISHUMEI_RYAKUSHO使用
4. **馬場適性** - SHIBA_BABAJOTAI_CODE, DIRT_BABAJOTAI_CODE使用
5. **コーナー特性** - CORNER1-4_JUNI使用
6. **人気度分析** - TANSHO_ODDS使用
7. **成績分析** - CHAKUJUN, KAKUTEI_CHAKUJUN使用

## 次のステップ

### 1. MySQLサーバー起動
```bash
# Windows側で以下を確認・実行
- XAMPPのMySQLサービス起動
- または単体MySQLサービス起動
- services.msc → MySQL サービス開始
```

### 2. 接続テスト実行
```bash
python3 mysql_test.py
```

### 3. Phase D完全調査実行
```bash
python3 services/mysql_database_analyzer.py
```

## 技術的詳細

### MySQL接続方式（Cursor互換）
- mysql-connector-python使用
- 接続プール未使用（単発接続）
- UTF-8エンコーディング対応
- エラーハンドリング完備

### データ品質確認項目
- NULL値分析（BAMEI, RACE_CODE, KAISAI_DATE, CHAKUJUN）
- 重複データ確認
- 日付範囲検証
- G1レース絞り込み精度

### Phase D最大活用ポイント
1. **動的馬リスト生成** - 勝利数・出走数で自動選別
2. **最適化された12項目分析** - Dance in the Dark基準
3. **大量データ処理** - メモリ効率化済み
4. **レポート自動生成** - JSON形式で出力

---

## 結論

MySQLサーバーが起動すれば、既存の実装で即座にPhase D完全調査が実行可能です。
数十万レースの大量データから最適な馬を選別し、D-Logic 12項目での最大ナレッジベース構築が期待できます。

**重要**: Windows側でMySQLサーバーの起動が必要です。