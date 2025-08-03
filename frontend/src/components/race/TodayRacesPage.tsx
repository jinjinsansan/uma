'use client';

import React, { useState, useEffect } from 'react';
import { TodayRaceService, TodayRacesData } from '../../services/todayRaceService';

interface TodayRacesPageProps {
  onRaceSelect?: (racecourse: string, raceNumber: number) => void;
}

export default function TodayRacesPage({ onRaceSelect }: TodayRacesPageProps) {
  const [racesData, setRacesData] = useState<TodayRacesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTodayRaces();
  }, []);

  const loadTodayRaces = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await TodayRaceService.getTodayRaces();
      setRacesData(data);
    } catch (err) {
      setError('本日レース情報の取得に失敗しました');
      console.error('本日レース取得エラー:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRaceClick = (racecourse: string, raceNumber: number) => {
    if (onRaceSelect) {
      onRaceSelect(racecourse, raceNumber);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">本日レース情報を読み込み中...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h2 className="text-xl font-semibold text-red-800 mb-2">エラー</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={loadTodayRaces}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              再試行
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!racesData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-8">
            <p className="text-gray-600">レース情報が見つかりません</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* ヘッダー */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            本日レース情報
          </h1>
          <p className="text-gray-600">
            {racesData.date} 開催レース
          </p>
        </div>

        {/* レース一覧 */}
        <div className="space-y-6">
          {racesData.racecourses.map((course, courseIndex) => (
            <div key={courseIndex} className="bg-white rounded-lg shadow-lg overflow-hidden">
              {/* 競馬場名 */}
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
                <h2 className="text-xl font-semibold text-white">
                  {course.name}
                </h2>
              </div>

              {/* レース一覧 */}
              <div className="p-6">
                <div className="grid gap-4">
                  {course.races.map((race, raceIndex) => (
                    <div
                      key={raceIndex}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => handleRaceClick(course.name, race.raceNumber)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-4">
                            <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                              {race.raceNumber}R
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-800">
                                {race.raceName}
                              </h3>
                              <p className="text-sm text-gray-600">
                                {race.distance} • {race.horses?.length || 0}頭
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-semibold text-gray-800">
                            {race.time}
                          </div>
                          <div className="text-sm text-gray-500">
                            発走時刻
                          </div>
                        </div>
                      </div>

                      {/* 出走馬一覧 */}
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <p className="text-sm text-gray-600 mb-2">出走馬:</p>
                        <div className="flex flex-wrap gap-2">
                          {race.horses?.map((horse, horseIndex) => (
                            <span
                              key={horseIndex}
                              className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs"
                            >
                              {typeof horse === 'string' ? horse : horse.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* フッター */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            固定データを使用しています • 外部API接続なし
          </p>
        </div>
      </div>
    </div>
  );
} 