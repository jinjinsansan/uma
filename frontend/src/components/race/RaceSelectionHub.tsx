'use client';

import React, { useState, useEffect } from 'react';
import { Calendar, Trophy, Clock, ArrowLeft } from 'lucide-react';
import TodayRacesPage from './TodayRacesPage';
import PastG1ExperiencePage from './PastG1ExperiencePage';

interface RaceExistsResponse {
  date: string;
  has_races: boolean;
  race_count: number;
  day_of_week: string;
}

const RaceSelectionHub: React.FC = () => {
  const [hasRacesToday, setHasRacesToday] = useState<boolean | null>(null);
  const [currentView, setCurrentView] = useState<'today' | 'past' | 'selection'>('selection');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkTodayRaces();
  }, []);

  const checkTodayRaces = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/race-exists-today');
      const data: RaceExistsResponse = await response.json();
      setHasRacesToday(data.has_races);
      
      // 開催レースがある場合は自動的に本日レースページに移動
      if (data.has_races) {
        setCurrentView('today');
      }
    } catch (error) {
      console.error('レース確認エラー:', error);
      setHasRacesToday(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // 現在のビューを表示
  if (currentView === 'today') {
    return (
      <div>
        <div className="p-4 bg-white border-b">
          <button
            onClick={() => setCurrentView('selection')}
            className="flex items-center text-blue-600 hover:text-blue-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            選択画面に戻る
          </button>
        </div>
        <TodayRacesPage />
      </div>
    );
  }

  if (currentView === 'past') {
    return (
      <div>
        <div className="p-4 bg-white border-b">
          <button
            onClick={() => setCurrentView('selection')}
            className="flex items-center text-yellow-600 hover:text-yellow-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            選択画面に戻る
          </button>
        </div>
        <PastG1ExperiencePage />
      </div>
    );
  }

  // 選択画面
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            競馬予想を始めましょう
          </h1>
          <p className="text-xl text-gray-600">
            本日開催レースまたは過去のG1レースをお選びください
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* 本日開催レース */}
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden border-2 border-transparent hover:border-blue-500 transition-all">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-8">
              <div className="flex items-center mb-4">
                <Calendar className="w-8 h-8 mr-3" />
                <h2 className="text-2xl font-bold">本日開催レース</h2>
              </div>
              <p className="text-blue-100">
                {hasRacesToday 
                  ? '今日開催されるレースで予想しましょう'
                  : '本日は開催レースがございません'
                }
              </p>
            </div>

            <div className="p-8">
              <div className="space-y-4 mb-6">
                <div className="flex items-center text-gray-700">
                  <Clock className="w-5 h-5 mr-3 text-blue-600" />
                  <span>リアルタイム開催情報</span>
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="w-5 h-5 mr-3 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-bold">AI</span>
                  </div>
                  <span>8条件AI予想システム</span>
                </div>
              </div>

              <button
                onClick={() => setCurrentView('today')}
                disabled={!hasRacesToday}
                className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all ${
                  hasRacesToday
                    ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {hasRacesToday ? '本日のレースを見る' : '開催レースなし'}
              </button>
            </div>
          </div>

          {/* 過去G1レース体験 */}
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden border-2 border-transparent hover:border-yellow-500 transition-all">
            <div className="bg-gradient-to-r from-yellow-600 to-amber-600 text-white p-8">
              <div className="flex items-center mb-4">
                <Trophy className="w-8 h-8 mr-3" />
                <h2 className="text-2xl font-bold">過去G1レース体験</h2>
              </div>
              <p className="text-yellow-100">
                名勝負の過去レースで予想を体験
              </p>
            </div>

            <div className="p-8">
              <div className="space-y-4 mb-6">
                <div className="flex items-center text-gray-700">
                  <Trophy className="w-5 h-5 mr-3 text-yellow-600" />
                  <span>2022-2024年のG1レース</span>
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="w-5 h-5 mr-3 bg-yellow-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-bold">★</span>
                  </div>
                  <span>実績データで学習体験</span>
                </div>
              </div>

              <button
                onClick={() => setCurrentView('past')}
                className="w-full bg-yellow-600 hover:bg-yellow-700 text-white py-4 px-6 rounded-xl font-semibold text-lg transition-all shadow-lg hover:shadow-xl"
              >
                過去G1レースで体験
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RaceSelectionHub; 