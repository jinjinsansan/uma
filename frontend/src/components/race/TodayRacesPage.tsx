'use client';

import React, { useState, useEffect } from 'react';
import { Calendar, Clock, MapPin, Users, ArrowLeft } from 'lucide-react';

interface Race {
  race_code: string;
  kaisai_nen: string;
  kaisai_gappi: string;
  keibajo_code: string;
  keibajo_name: string;
  race_bango: string;
  kyosomei_hondai: string;
  kyori: string;
  track_code: string;
  hasso_jikoku: string;
  shusso_tosu: string;
  formatted_date: string;
  formatted_time: string;
}

interface TodayRacesResponse {
  date: string;
  race_count: number;
  races: Race[];
  has_races: boolean;
}

const TodayRacesPage: React.FC = () => {
  const [races, setRaces] = useState<Race[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTodayRaces();
  }, []);

  const fetchTodayRaces = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/today-races');
      if (!response.ok) {
        throw new Error('レース情報の取得に失敗しました');
      }
      const data: TodayRacesResponse = await response.json();
      setRaces(data.races);
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知のエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleRaceSelect = (raceCode: string) => {
    // TODO: Phase 3で実装 - レース選択後の処理
    console.log('Selected race:', raceCode);
    alert(`レース選択: ${raceCode}\n（Phase 3で8条件画面に移動予定）`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="text-red-600 text-lg font-semibold mb-2">エラー</div>
          <div className="text-gray-600">{error}</div>
        </div>
      </div>
    );
  }

  if (races.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <div className="text-xl font-semibold text-gray-700 mb-2">
            本日は開催レースがございません
          </div>
          <div className="text-gray-500">
            週末の開催をお待ちください
          </div>
        </div>
      </div>
    );
  }

  // 競馬場別にグループ化
  const racesByKeibajo = races.reduce((acc, race) => {
    const keibajo = race.keibajo_code;
    if (!acc[keibajo]) {
      acc[keibajo] = [];
    }
    acc[keibajo].push(race);
    return acc;
  }, {} as { [key: string]: Race[] });

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            本日開催レース
          </h1>
          <p className="text-gray-600">
            {new Date().toLocaleDateString('ja-JP', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric',
              weekday: 'long'
            })}
          </p>
        </div>

        <div className="grid gap-8">
          {Object.entries(racesByKeibajo).map(([keibajoCode, keibajoRaces]) => (
            <div key={keibajoCode} className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="bg-blue-600 text-white px-6 py-4">
                <div className="flex items-center">
                  <MapPin className="w-5 h-5 mr-2" />
                  <h2 className="text-xl font-semibold">
                    {keibajoRaces[0].keibajo_name}
                  </h2>
                  <span className="ml-auto bg-blue-500 px-3 py-1 rounded-full text-sm">
                    {keibajoRaces.length}レース
                  </span>
                </div>
              </div>

              <div className="grid gap-4 p-6 md:grid-cols-2 lg:grid-cols-3">
                {keibajoRaces.map((race) => (
                  <div
                    key={race.race_code}
                    onClick={() => handleRaceSelect(race.race_code)}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-semibold">
                          {race.race_bango}R
                        </span>
                        <div className="ml-3 flex items-center text-gray-600">
                          <Clock className="w-4 h-4 mr-1" />
                          <span className="text-sm">{race.formatted_time}</span>
                        </div>
                      </div>
                    </div>

                    <h3 className="font-semibold text-gray-900 mb-2">
                      {race.kyosomei_hondai}
                    </h3>

                    <div className="space-y-2 text-sm text-gray-600">
                      <div className="flex justify-between">
                        <span>距離</span>
                        <span className="font-medium">{race.kyori}m</span>
                      </div>
                      <div className="flex justify-between">
                        <span>出走頭数</span>
                        <div className="flex items-center">
                          <Users className="w-4 h-4 mr-1" />
                          <span className="font-medium">{race.shusso_tosu}頭</span>
                        </div>
                      </div>
                    </div>

                    <button className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors font-medium">
                      このレースを予想する
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TodayRacesPage; 