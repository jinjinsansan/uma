/**
 * Phase C: 本日レース統合サービス
 * 本日開催レース情報とDロジック連携
 */

// 本日レース情報の型定義
export interface Horse {
  name: string;
  jockey: string;
  weight: string;
  horseWeight: string;
  weightChange: string;
  age: number;
  sex: string;
  trainer: string;
  odds: string;
  popularity: number;
}

export interface Race {
  raceId: string;
  raceNumber: number;
  raceName: string;
  time: string;
  distance: string;
  track: string;
  condition?: string;
  grade?: string | null;
  prizePool: string;
  entryCount: number;
  horses?: Horse[];
}

export interface Racecourse {
  name: string;
  courseId: string;
  weather: string;
  trackCondition: string;
  raceCount?: number;
  races: Race[];
}

export interface TodayRacesData {
  date: string;
  lastUpdate: string;
  racecourses: Racecourse[];
}

export interface RaceDetail {
  raceInfo: Race;
  racecourse: {
    name: string;
    courseId: string;
    weather: string;
    trackCondition: string;
  };
  horses: Horse[];
  date: string;
  lastUpdate: string;
}

export interface RaceSearchResult {
  searchResults: Array<{
    raceId: string;
    raceNumber: number;
    raceName: string;
    time: string;
    distance: string;
    track: string;
    racecourse: {
      name: string;
      courseId: string;
    };
    entryCount: number;
    prizePool: string;
  }>;
  resultCount: number;
  searchCriteria: {
    course_id?: string;
    race_number?: number;
    distance?: string;
    track?: string;
  };
  date: string;
  lastUpdate: string;
}

// Phase C: 本日レース統合サービス
export class TodayRaceService {
  private static readonly API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  /**
   * 本日レース一覧を取得
   * GET /api/today-races
   */
  static async getTodayRaces(): Promise<TodayRacesData> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/today-races`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result: TodayRacesData = await response.json();
      return result;
    } catch (error) {
      console.error('本日レース情報取得エラー:', error);
      throw new Error('本日レース情報の取得に失敗しました');
    }
  }

  /**
   * 指定レースの詳細情報を取得
   * GET /api/race-detail/{race_id}
   */
  static async getRaceDetail(raceId: string): Promise<RaceDetail> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/race-detail/${raceId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result: RaceDetail = await response.json();
      return result;
    } catch (error) {
      console.error('レース詳細取得エラー:', error);
      throw new Error('レース詳細の取得に失敗しました');
    }
  }

  /**
   * 指定競馬場の本日レース一覧を取得
   * GET /api/racecourse/{course_id}/races
   */
  static async getRacecourseRaces(courseId: string): Promise<{racecourse: Racecourse['name'], races: Race[]}> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/racecourse/${courseId}/races`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      return {
        racecourse: result.racecourse.name,
        races: result.races
      };
    } catch (error) {
      console.error('競馬場レース一覧取得エラー:', error);
      throw new Error('競馬場レース一覧の取得に失敗しました');
    }
  }

  /**
   * レース検索
   * GET /api/race-search?course_id=tokyo&race_number=3
   */
  static async searchRaces(searchParams: {
    courseId?: string;
    raceNumber?: number;
    distance?: string;
    track?: string;
  }): Promise<RaceSearchResult> {
    try {
      const params = new URLSearchParams();
      if (searchParams.courseId) params.append('course_id', searchParams.courseId);
      if (searchParams.raceNumber) params.append('race_number', searchParams.raceNumber.toString());
      if (searchParams.distance) params.append('distance', searchParams.distance);
      if (searchParams.track) params.append('track', searchParams.track);

      const response = await fetch(`${this.API_BASE_URL}/api/race-search?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result: RaceSearchResult = await response.json();
      return result;
    } catch (error) {
      console.error('レース検索エラー:', error);
      throw new Error('レース検索に失敗しました');
    }
  }

  /**
   * 本日レース一覧を整形して表示用データを作成
   */
  static formatTodayRacesForDisplay(data: TodayRacesData) {
    const formattedRaces = data.racecourses.map(course => ({
      courseName: course.name,
      courseId: course.courseId,
      weather: course.weather,
      trackCondition: course.trackCondition,
      races: course.races.map(race => ({
        raceId: race.raceId,
        raceNumber: race.raceNumber,
        raceName: race.raceName,
        time: race.time,
        distance: race.distance,
        track: race.track,
        entryCount: race.entryCount,
        prizePool: race.prizePool,
        displayText: `${race.raceNumber}R ${race.raceName} (${race.time}) ${race.distance} ${race.track} ${race.entryCount}頭`
      }))
    }));

    return {
      date: data.date,
      lastUpdate: data.lastUpdate,
      courses: formattedRaces
    };
  }

  /**
   * レース選択用のオプションリストを作成
   */
  static createRaceOptions(data: TodayRacesData) {
    const options: {value: string, label: string, raceId: string}[] = [];
    
    data.racecourses.forEach(course => {
      course.races.forEach(race => {
        options.push({
          value: `${course.courseId}_${race.raceNumber}`,
          label: `${course.name} ${race.raceNumber}R ${race.raceName} (${race.time})`,
          raceId: race.raceId
        });
      });
    });
    
    return options;
  }

  /**
   * 「東京3R」形式の文字列からレース情報を検索
   */
  static async findRaceByString(raceString: string): Promise<RaceDetail | null> {
    try {
      // 「東京3R」「中山2R」などのパターンを解析
      const match = raceString.match(/([東京中山阪神])(\d+)R?/);
      if (!match) return null;

      const courseMap: {[key: string]: string} = {
        '東京': 'tokyo',
        '中山': 'nakayama',
        '阪神': 'hanshin'
      };

      const courseName = match[1];
      const raceNumber = parseInt(match[2]);
      const courseId = courseMap[courseName];

      if (!courseId) return null;

      // レース検索
      const searchResult = await this.searchRaces({
        courseId,
        raceNumber
      });

      if (searchResult.resultCount === 0) return null;

      // 詳細情報を取得
      const raceId = searchResult.searchResults[0].raceId;
      return await this.getRaceDetail(raceId);

    } catch (error) {
      console.error('レース文字列解析エラー:', error);
      return null;
    }
  }

  /**
   * レース情報の表示用文字列を生成
   */
  static formatRaceDisplayString(raceDetail: RaceDetail): string {
    const { raceInfo, racecourse } = raceDetail;
    return `${racecourse.name}${raceInfo.raceNumber}R ${raceInfo.raceName} (${raceInfo.time}) ${raceInfo.distance} ${raceInfo.track} ${raceInfo.entryCount}頭`;
  }
} 