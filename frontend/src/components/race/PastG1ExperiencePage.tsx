'use client';

import React, { useState, useEffect } from 'react';
import { Trophy, Calendar, MapPin, Clock, Users, Star } from 'lucide-react';
import RaceSpecificConditionSelector from './RaceSpecificConditionSelector';

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

interface PastG1Response {
  year: number | null;
  total_races: number;
  races: Race[];
}

const PastG1ExperiencePage: React.FC = () => {
  const [races, setRaces] = useState<Race[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [totalRaces, setTotalRaces] = useState(0);
  
  // 新8条件画面の状態管理
  const [showRaceConditions, setShowRaceConditions] = useState(false);
  const [selectedRace, setSelectedRace] = useState<Race | null>(null);

  useEffect(() => {
    fetchPastG1Races();
  }, [selectedYear]);

  const fetchPastG1Races = async () => {
    try {
      setLoading(true);
      const url = selectedYear 
        ? `http://localhost:8000/api/past-g1-races?year=${selectedYear}`
        : 'http://localhost:8000/api/past-g1-races';
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('G1レース情報の取得に失敗しました');
      }
      const data: PastG1Response = await response.json();
      setRaces(data.races);
      setTotalRaces(data.total_races);
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知のエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleRaceSelect = (raceCode: string) => {
    const selectedRace = races.find(race => race.race_code === raceCode);
    if (selectedRace) {
      setSelectedRace(selectedRace);
      setShowRaceConditions(true);
    }
  };

  const handleBackToRaceSelection = () => {
    setShowRaceConditions(false);
    setSelectedRace(null);
  };

  const years = [2024, 2023, 2022];

  // 新8条件画面が表示されている場合
  if (showRaceConditions && selectedRace) {
    return (
      <RaceSpecificConditionSelector
        selectedRace={selectedRace}
        onBack={handleBackToRaceSelection}
      />
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600"></div>
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

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Trophy className="w-8 h-8 text-yellow-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">
              過去G1レース体験
            </h1>
          </div>
          <p className="text-gray-600 mb-6">
            名勝負の過去レースで予想を体験しましょう
          </p>

          {/* 年選択 */}
          <div className="flex justify-center space-x-2 mb-8">
            <button
              onClick={() => setSelectedYear(null)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedYear === null
                  ? 'bg-yellow-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              全期間
            </button>
            {years.map((year) => (
              <button
                key={year}
                onClick={() => setSelectedYear(year)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedYear === year
                    ? 'bg-yellow-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {year}年
              </button>
            ))}
          </div>

          <div className="text-sm text-gray-500">
            {selectedYear ? `${selectedYear}年のG1レース` : '2022-2024年のG1レース'} 
            （{totalRaces}レース）
          </div>
        </div>

        {races.length === 0 ? (
          <div className="text-center py-12">
            <Trophy className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <div className="text-xl font-semibold text-gray-700 mb-2">
              該当するG1レースがございません
            </div>
            <div className="text-gray-500">
              別の年をお選びください
            </div>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {races.map((race) => (
              <div
                key={race.race_code}
                onClick={() => handleRaceSelect(race.race_code)}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-all cursor-pointer border-2 border-transparent hover:border-yellow-500"
              >
                <div className="bg-gradient-to-r from-yellow-600 to-amber-600 text-white p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      <Trophy className="w-5 h-5 mr-2" />
                      <span className="font-semibold">G1</span>
                    </div>
                    <Star className="w-4 h-4" />
                  </div>
                  <h3 className="font-bold text-lg">
                    {race.kyosomei_hondai}
                  </h3>
                </div>

                <div className="p-4">
                  <div className="flex items-center text-gray-600 mb-3">
                    <MapPin className="w-4 h-4 mr-2" />
                    <span className="text-sm">{race.keibajo_name}</span>
                  </div>

                  <div className="space-y-2 text-sm text-gray-600 mb-4">
                    <div className="flex justify-between">
                      <span>開催日</span>
                      <span className="font-medium">{race.formatted_date}</span>
                    </div>
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

                  <button className="w-full bg-yellow-600 hover:bg-yellow-700 text-white py-2 px-4 rounded-md transition-colors font-medium">
                    このレースで体験
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PastG1ExperiencePage; 