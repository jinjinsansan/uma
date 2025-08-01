/**
 * 本日レース連携サービス
 * リアルタイムで本日開催レースを取得
 */

export interface TodayRace {
  race_code: string;
  keibajo_name: string;
  race_bango: string;
  kyosomei_hondai: string;
  kyori: string;
  hasso_jikoku: string;
  shusso_tosu: string;
}

export interface RaceDetail {
  race_code: string;
  keibajo_name: string;
  race_bango: string;
  kyosomei_hondai: string;
  kyori: string;
  track_condition: string;
  weather: string;
  hasso_jikoku: string;
  shusso_tosu: number;
  horses: Array<{
    horse_id: string;
    horse_name: string;
    jockey_name: string;
    trainer_name: string;
    weight: number;
    weight_change: number;
    odds?: number;
  }>;
}

export class TodayRaceService {
  private static readonly API_BASE_URL = 'http://localhost:8000/api';

  /**
   * 本日開催レース一覧取得
   */
  static async fetchTodayRaces(): Promise<TodayRace[]> {
    try {
      // TODO: Phase Cで実装予定
      // 現在は固定データで基盤準備
      const mockTodayRaces: TodayRace[] = [
        {
          race_code: "202412010101",
          keibajo_name: "東京",
          race_bango: "1R",
          kyosomei_hondai: "2歳未勝利",
          kyori: "1600",
          hasso_jikoku: "10:30",
          shusso_tosu: "12"
        },
        {
          race_code: "202412010102",
          keibajo_name: "東京", 
          race_bango: "2R",
          kyosomei_hondai: "3歳以上1勝クラス",
          kyori: "2000",
          hasso_jikoku: "11:00",
          shusso_tosu: "10"
        }
      ];

      return mockTodayRaces;
    } catch (error) {
      console.error('本日レース取得エラー:', error);
      return [];
    }
  }

  /**
   * 特定レースの詳細取得
   */
  static async fetchRaceDetail(raceCode: string): Promise<RaceDetail | null> {
    try {
      // TODO: Phase Cで実装予定
      return {
        race_code: raceCode,
        keibajo_name: "東京",
        race_bango: "1R",
        kyosomei_hondai: "2歳未勝利",
        kyori: "1600",
        track_condition: "良",
        weather: "晴",
        hasso_jikoku: "10:30",
        shusso_tosu: 12,
        horses: [
          {
            horse_id: "001",
            horse_name: "サンプル馬1",
            jockey_name: "サンプル騎手1",
            trainer_name: "サンプル調教師1",
            weight: 55.0,
            weight_change: 0.0,
            odds: 3.5
          }
        ]
      };
    } catch (error) {
      console.error('レース詳細取得エラー:', error);
      return null;
    }
  }
} 