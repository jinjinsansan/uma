-- ================================
-- JRA競馬データベース構造（PostgreSQL版）
-- 人間が見てわかりやすい設計
-- ================================

-- 1. レース基本情報テーブル
CREATE TABLE IF NOT EXISTS jra_races (
  id SERIAL PRIMARY KEY,
  開催日 DATE NOT NULL,
  競馬場 VARCHAR(10) NOT NULL,
  レース番号 INT NOT NULL,
  レース名 VARCHAR(100),
  距離 INT,
  コース VARCHAR(10),
  グレード VARCHAR(20),
  天候 VARCHAR(10),
  馬場状態 VARCHAR(10),
  UNIQUE(開催日, 競馬場, レース番号)
);

-- インデックスを別途作成
CREATE INDEX IF NOT EXISTS idx_開催日 ON jra_races(開催日);
CREATE INDEX IF NOT EXISTS idx_競馬場 ON jra_races(競馬場);

-- 2. 出走馬情報テーブル
CREATE TABLE IF NOT EXISTS jra_horses (
  id SERIAL PRIMARY KEY,
  race_id INT REFERENCES jra_races(id),
  馬番 INT NOT NULL,
  馬名 VARCHAR(50) NOT NULL,
  性齢 VARCHAR(10),
  斤量 DECIMAL(3,1),
  騎手名 VARCHAR(30),
  調教師名 VARCHAR(30),
  単勝オッズ DECIMAL(6,1),
  人気順位 INT,
  着順 INT,
  タイム VARCHAR(10),
  着差 VARCHAR(20)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_race_id ON jra_horses(race_id);
CREATE INDEX IF NOT EXISTS idx_馬名 ON jra_horses(馬名);

-- 3. エンジン予想テーブル
CREATE TABLE IF NOT EXISTS jra_predictions (
  id SERIAL PRIMARY KEY,
  race_id INT REFERENCES jra_races(id),
  エンジン名 VARCHAR(20) NOT NULL,
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
  予想作成日時 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_race_engine ON jra_predictions(race_id, エンジン名);

-- 4. 払戻結果テーブル
CREATE TABLE IF NOT EXISTS jra_payouts (
  id SERIAL PRIMARY KEY,
  race_id INT REFERENCES jra_races(id),
  単勝_馬番 INT,
  単勝_払戻金 INT,
  複勝1_馬番 INT,
  複勝1_払戻金 INT,
  複勝2_馬番 INT,
  複勝2_払戻金 INT,
  複勝3_馬番 INT,
  複勝3_払戻金 INT,
  馬連_馬番1 INT,
  馬連_馬番2 INT,
  馬連_払戻金 INT,
  ワイド1_馬番1 INT,
  ワイド1_馬番2 INT,
  ワイド1_払戻金 INT,
  ワイド2_馬番1 INT,
  ワイド2_馬番2 INT,
  ワイド2_払戻金 INT,
  ワイド3_馬番1 INT,
  ワイド3_馬番2 INT,
  ワイド3_払戻金 INT,
  馬単_馬番1 INT,
  馬単_馬番2 INT,
  馬単_払戻金 INT,
  三連複_馬番1 INT,
  三連複_馬番2 INT,
  三連複_馬番3 INT,
  三連複_払戻金 INT,
  三連単_馬番1 INT,
  三連単_馬番2 INT,
  三連単_馬番3 INT,
  三連単_払戻金 INT,
  UNIQUE(race_id)
);

-- 5. エンジン的中分析テーブル（集計用）
CREATE TABLE IF NOT EXISTS jra_engine_analysis (
  id SERIAL PRIMARY KEY,
  race_id INT REFERENCES jra_races(id),
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
  分析実行日時 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(race_id)
);

-- ================================
-- ビュー（見やすい集計用）
-- ================================

-- レース一覧ビュー（CSV出力用）
CREATE OR REPLACE VIEW v_race_list AS
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
GROUP BY r.id, r.開催日, r.競馬場, r.レース番号, r.レース名, 
         r.距離, r.コース, r.グレード, r.天候, r.馬場状態
ORDER BY r.開催日 DESC, r.競馬場, r.レース番号;

-- エンジン的中率ビュー
CREATE OR REPLACE VIEW v_engine_accuracy AS
SELECT 
  p.エンジン名,
  COUNT(DISTINCT p.race_id) as 予想レース数,
  SUM(CASE 
    WHEN p.エンジン名 = 'D-Logic' AND a.DLogic_1着的中 THEN 1
    WHEN p.エンジン名 = 'I-Logic' AND a.ILogic_1着的中 THEN 1
    WHEN p.エンジン名 = 'ViewLogic' AND a.ViewLogic_1着的中 THEN 1
    ELSE 0 
  END) as 単勝的中数,
  ROUND(
    AVG(CASE 
      WHEN p.エンジン名 = 'D-Logic' AND a.DLogic_1着的中 THEN 1
      WHEN p.エンジン名 = 'I-Logic' AND a.ILogic_1着的中 THEN 1
      WHEN p.エンジン名 = 'ViewLogic' AND a.ViewLogic_1着的中 THEN 1
      ELSE 0 
    END) * 100, 1
  ) as 単勝的中率,
  SUM(CASE 
    WHEN p.エンジン名 = 'D-Logic' AND a.DLogic_複勝的中数 > 0 THEN 1
    WHEN p.エンジン名 = 'I-Logic' AND a.ILogic_複勝的中数 > 0 THEN 1
    WHEN p.エンジン名 = 'ViewLogic' AND a.ViewLogic_複勝的中数 > 0 THEN 1
    ELSE 0 
  END) as 複勝的中数,
  ROUND(
    AVG(CASE 
      WHEN p.エンジン名 = 'D-Logic' AND a.DLogic_複勝的中数 > 0 THEN 1
      WHEN p.エンジン名 = 'I-Logic' AND a.ILogic_複勝的中数 > 0 THEN 1
      WHEN p.エンジン名 = 'ViewLogic' AND a.ViewLogic_複勝的中数 > 0 THEN 1
      ELSE 0 
    END) * 100, 1
  ) as 複勝的中率
FROM jra_predictions p
LEFT JOIN jra_engine_analysis a ON p.race_id = a.race_id
GROUP BY p.エンジン名;

-- 最近のレース結果ビュー
CREATE OR REPLACE VIEW v_recent_race_results AS
SELECT 
  r.開催日,
  r.競馬場,
  r.レース番号,
  r.レース名,
  h1.馬名 as 一着馬,
  h1.単勝オッズ as 一着オッズ,
  h2.馬名 as 二着馬,
  h3.馬名 as 三着馬,
  p.単勝_払戻金,
  p.三連単_払戻金
FROM jra_races r
LEFT JOIN jra_horses h1 ON r.id = h1.race_id AND h1.着順 = 1
LEFT JOIN jra_horses h2 ON r.id = h2.race_id AND h2.着順 = 2
LEFT JOIN jra_horses h3 ON r.id = h3.race_id AND h3.着順 = 3
LEFT JOIN jra_payouts p ON r.id = p.race_id
WHERE r.開催日 >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY r.開催日 DESC, r.競馬場, r.レース番号;

-- コメント追加
COMMENT ON TABLE jra_races IS 'JRA中央競馬のレース基本情報';
COMMENT ON TABLE jra_horses IS '各レースの出走馬情報';
COMMENT ON TABLE jra_predictions IS '各エンジンによる予想結果';
COMMENT ON TABLE jra_payouts IS 'レースの払戻金情報';
COMMENT ON TABLE jra_engine_analysis IS 'エンジンの的中分析結果';

COMMENT ON COLUMN jra_races.開催日 IS 'レース開催日';
COMMENT ON COLUMN jra_races.競馬場 IS '競馬場名（中山、阪神、東京など）';
COMMENT ON COLUMN jra_races.レース番号 IS 'レース番号（1R〜12R）';
COMMENT ON COLUMN jra_races.距離 IS 'レース距離（メートル）';
COMMENT ON COLUMN jra_races.コース IS 'コース種別（芝/ダート）';

COMMENT ON COLUMN jra_horses.馬番 IS '馬番号（ゼッケン番号）';
COMMENT ON COLUMN jra_horses.馬名 IS '競走馬名';
COMMENT ON COLUMN jra_horses.単勝オッズ IS '最終単勝オッズ';
COMMENT ON COLUMN jra_horses.人気順位 IS '最終人気順位';
COMMENT ON COLUMN jra_horses.着順 IS '確定着順';

COMMENT ON COLUMN jra_predictions.エンジン名 IS '予想エンジン名（D-Logic/I-Logic/ViewLogic）';
COMMENT ON COLUMN jra_predictions.予想1位 IS '1位予想馬名';
COMMENT ON COLUMN jra_predictions.予想1位スコア IS '1位予想馬のスコア';