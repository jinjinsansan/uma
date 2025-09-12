-- ================================
-- JRA競馬データベース構造
-- 人間が見てわかりやすい設計
-- ================================

-- 1. レース基本情報テーブル
CREATE TABLE jra_races (
  -- 基本識別情報
  id SERIAL PRIMARY KEY,
  開催日 DATE NOT NULL,
  競馬場 VARCHAR(10) NOT NULL, -- '中山', '阪神', '東京' など
  レース番号 INT NOT NULL,
  レース名 VARCHAR(100),
  
  -- レース条件
  距離 INT NOT NULL, -- 1200, 1600, 2000 など
  コース VARCHAR(10) NOT NULL, -- '芝', 'ダート'
  グレード VARCHAR(10), -- 'G1', 'G2', 'G3', 'オープン', '3歳未勝利' など
  
  -- 当日の状態
  天候 VARCHAR(10), -- '晴', '曇', '雨'
  馬場状態 VARCHAR(10), -- '良', '稍重', '重', '不良'
  
  -- インデックス
  UNIQUE(開催日, 競馬場, レース番号),
  INDEX idx_date (開催日),
  INDEX idx_venue (競馬場)
);

-- 2. 出走馬情報テーブル
CREATE TABLE jra_horses (
  id SERIAL PRIMARY KEY,
  race_id INT REFERENCES jra_races(id),
  
  -- 馬情報
  馬番 INT NOT NULL,
  馬名 VARCHAR(50) NOT NULL,
  性齢 VARCHAR(10), -- '牡3', '牝4' など
  斤量 DECIMAL(3,1), -- 56.0, 54.0 など
  
  -- 騎手・調教師
  騎手名 VARCHAR(30),
  調教師名 VARCHAR(30),
  
  -- オッズ・人気
  単勝オッズ DECIMAL(6,1),
  人気順位 INT,
  
  -- 結果
  着順 INT, -- 1, 2, 3... (レース後に更新)
  タイム VARCHAR(10), -- '1:33.5' など
  着差 VARCHAR(20), -- 'クビ', '2馬身' など
  
  INDEX idx_race (race_id),
  INDEX idx_horse_name (馬名)
);

-- 3. エンジン予想テーブル
CREATE TABLE jra_predictions (
  id SERIAL PRIMARY KEY,
  race_id INT REFERENCES jra_races(id),
  
  -- エンジン種別
  エンジン名 VARCHAR(20) NOT NULL, -- 'D-Logic', 'I-Logic', 'ViewLogic'
  
  -- 上位5頭の予想（馬名で保存）
  予想1位 VARCHAR(50),
  予想1位スコア DECIMAL(5,1),
  予想2位 VARCHAR(50),
  予想2位スコア DECIMAL(5,1),
  予想3位 VARCHAR(50),
  予想3位スコア DECIMAL(5,1),
  予想4位 VARCHAR(50),
  予想4位スコア DECIMAL(5,1),
  予想5位 VARCHAR(50),
  予想5位スコア DECIMAL(5,1),
  
  -- 予想日時
  予想作成日時 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_race_engine (race_id, エンジン名)
);

-- 4. 払戻結果テーブル
CREATE TABLE jra_payouts (
  id SERIAL PRIMARY KEY,
  race_id INT REFERENCES jra_races(id),
  
  -- 単勝
  単勝_馬番 INT,
  単勝_払戻金 INT,
  
  -- 複勝
  複勝1_馬番 INT,
  複勝1_払戻金 INT,
  複勝2_馬番 INT,
  複勝2_払戻金 INT,
  複勝3_馬番 INT,
  複勝3_払戻金 INT,
  
  -- 馬連
  馬連_馬番1 INT,
  馬連_馬番2 INT,
  馬連_払戻金 INT,
  
  -- ワイド
  ワイド1_馬番1 INT,
  ワイド1_馬番2 INT,
  ワイド1_払戻金 INT,
  ワイド2_馬番1 INT,
  ワイド2_馬番2 INT,
  ワイド2_払戻金 INT,
  ワイド3_馬番1 INT,
  ワイド3_馬番2 INT,
  ワイド3_払戻金 INT,
  
  -- 馬単
  馬単_馬番1 INT,
  馬単_馬番2 INT,
  馬単_払戻金 INT,
  
  -- 3連複
  三連複_馬番1 INT,
  三連複_馬番2 INT,
  三連複_馬番3 INT,
  三連複_払戻金 INT,
  
  -- 3連単
  三連単_馬番1 INT,
  三連単_馬番2 INT,
  三連単_馬番3 INT,
  三連単_払戻金 INT,
  
  UNIQUE(race_id)
);

-- 5. エンジン的中分析テーブル（集計用）
CREATE TABLE jra_engine_analysis (
  id SERIAL PRIMARY KEY,
  race_id INT REFERENCES jra_races(id),
  
  -- 各エンジンの的中状況
  DLogic_1着的中 BOOLEAN DEFAULT FALSE,
  DLogic_2着的中 BOOLEAN DEFAULT FALSE,
  DLogic_3着的中 BOOLEAN DEFAULT FALSE,
  DLogic_複勝的中数 INT DEFAULT 0,
  
  ILogic_1着的中 BOOLEAN DEFAULT FALSE,
  ILogic_2着的中 BOOLEAN DEFAULT FALSE,
  ILogic_3着的中 BOOLEAN DEFAULT FALSE,
  ILogic_複勝的中数 INT DEFAULT 0,
  
  ViewLogic_1着的中 BOOLEAN DEFAULT FALSE,
  ViewLogic_2着的中 BOOLEAN DEFAULT FALSE,
  ViewLogic_3着的中 BOOLEAN DEFAULT FALSE,
  ViewLogic_複勝的中数 INT DEFAULT 0,
  
  -- 分析日時
  分析実行日時 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(race_id)
);

-- ================================
-- ビュー（見やすい集計用）
-- ================================

-- レース一覧ビュー（CSV出力用）
CREATE VIEW v_race_list AS
SELECT 
  r.開催日,
  r.競馬場,
  r.レース番号,
  r.レース名,
  r.距離,
  r.コース,
  r.グレード,
  r.天候,
  r.馬場状態,
  COUNT(h.id) as 出走頭数
FROM jra_races r
LEFT JOIN jra_horses h ON r.id = h.race_id
GROUP BY r.id
ORDER BY r.開催日 DESC, r.競馬場, r.レース番号;

-- エンジン的中率ビュー
CREATE VIEW v_engine_accuracy AS
SELECT 
  エンジン名,
  COUNT(*) as 予想レース数,
  SUM(CASE WHEN a.DLogic_1着的中 THEN 1 ELSE 0 END) as 単勝的中数,
  ROUND(AVG(CASE WHEN エンジン名 = 'D-Logic' AND a.DLogic_1着的中 THEN 1 ELSE 0 END) * 100, 1) as 単勝的中率,
  SUM(CASE WHEN a.DLogic_複勝的中数 > 0 THEN 1 ELSE 0 END) as 複勝的中数,
  ROUND(AVG(CASE WHEN エンジン名 = 'D-Logic' AND a.DLogic_複勝的中数 > 0 THEN 1 ELSE 0 END) * 100, 1) as 複勝的中率
FROM jra_predictions p
JOIN jra_engine_analysis a ON p.race_id = a.race_id
GROUP BY エンジン名;

-- コメント追加
COMMENT ON TABLE jra_races IS 'JRA中央競馬のレース基本情報';
COMMENT ON TABLE jra_horses IS '各レースの出走馬情報';
COMMENT ON TABLE jra_predictions IS '各エンジンによる予想結果';
COMMENT ON TABLE jra_payouts IS 'レースの払戻金情報';
COMMENT ON TABLE jra_engine_analysis IS 'エンジンの的中分析結果';