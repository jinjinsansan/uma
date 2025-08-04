'use client';

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { Calendar, Trophy, Target, Star, BarChart3, Clock, MapPin, Menu, X } from 'lucide-react'
import LineAddFriendPopup from '@/components/line/LineAddFriendPopup'
import { useLineAddFriendDetection } from '@/hooks/useLineAddFriendDetection'

interface Horse {
  number: number;
  name: string;
  jockey: string;
  trainer: string;
  weight: string;
  horseWeight: string;
  weightChange: string;
  age: number;
  sex: string;
  odds: string;
  popularity: number;
  result?: number;
  dLogicScore?: number;
  dLogicRank?: number;
  winProbability?: number;
}

interface PastRace {
  raceId: string;
  raceName: string;
  date: string;
  racecourse: string;
  raceNumber: number;
  distance: string;
  track: string;
  grade?: string;
  weather: string;
  trackCondition: string;
  horses?: Horse[];
  winner?: string;
  time?: string;
  description?: string;
  entryCount?: number;
}

const G1RacesPage: React.FC = () => {
  const [selectedRace, setSelectedRace] = useState<PastRace | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [pastRaces, setPastRaces] = useState<PastRace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { shouldShowPopup, hidePopup, onTicketClaimed } = useLineAddFriendDetection({
    delaySeconds: 30, // 過去レース体験中30秒後に表示
  });

  useEffect(() => {
    fetchPastRaces();
  }, []);

  const fetchPastRaces = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:8001/api/past-races');
      const data = await response.json();
      
      if (data.races && data.races.length > 0) {
        setPastRaces(data.races);
      }
    } catch (error) {
      // 過去レース取得エラー時は空配列を維持
    } finally {
      setIsLoading(false);
    }
  };

  const handleRaceSelect = (race: PastRace) => {
    setSelectedRace(race);
    setShowResults(false);
  };

  const handleAnalyze = async () => {
    if (!selectedRace) return;
    
    setIsAnalyzing(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsAnalyzing(false);
    setShowResults(true);
  };

  const getDLogicColor = (score: number) => {
    if (score >= 130) return 'text-red-500 font-bold';
    if (score >= 120) return 'text-orange-500 font-semibold';
    if (score >= 110) return 'text-yellow-500 font-semibold';
    if (score >= 100) return 'text-green-500';
    return 'text-gray-500';
  };


  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="bg-gray-900/50 border-b border-[#ffd700]/30">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <span className="text-[#ffd700] text-2xl font-bold">D</span>
            <span className="text-xl font-bold text-[#ffd700]">過去レース体験</span>
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-6">
            <Link href="/today-races" className="outline-button px-4 py-2 text-sm">
              本日のレース
            </Link>
            <Link href="/d-logic-ai" className="outline-button px-4 py-2 text-sm">
              D-Logic AI
            </Link>
            <Link href="/register" className="outline-button px-4 py-2 text-sm">
              会員登録
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden text-[#ffd700] p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-gray-900 border-t border-[#ffd700]/30">
            <nav className="container mx-auto px-4 py-4 flex flex-col space-y-3">
              <Link 
                href="/today-races" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                本日のレース
              </Link>
              <Link 
                href="/d-logic-ai" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                D-Logic AI
              </Link>
              <Link 
                href="/register" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                会員登録
              </Link>
            </nav>
          </div>
        )}
      </header>

      <div className="max-w-7xl mx-auto p-6 mb-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-[#ffd700] to-[#ffed4a] bg-clip-text text-transparent leading-tight">
            過去レースD-Logic体験
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            2024年JRA公式G1レース全13戦でD-Logic分析を体験しよう
          </p>
          <div className="bg-gray-900 border border-[#ffd700]/30 rounded-lg p-4 inline-block">
            <p className="text-[#ffd700] font-semibold mb-2">🎯 無料体験版</p>
            <p className="text-sm text-gray-400">
              実際の過去レース結果でD-Logic指数の精度を確認できます
            </p>
          </div>
        </div>


        {/* レース選択 */}
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-[#ffd700] border-t-transparent mx-auto mb-4"></div>
            <p className="text-gray-400">2024年G1レースデータを読み込み中...</p>
          </div>
        ) : pastRaces.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-red-400">❌ データが取得できませんでした</p>
            <button 
              onClick={fetchPastRaces}
              className="mt-4 bg-blue-600 px-4 py-2 rounded"
            >
              再読み込み
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {pastRaces.map((race) => (
              <div
                key={race.raceId}
                onClick={() => handleRaceSelect(race)}
                className={`
                  p-4 rounded-lg border-2 transition-all duration-300 cursor-pointer
                  ${selectedRace?.raceId === race.raceId 
                    ? 'border-[#ffd700] bg-[#ffd700]/10' 
                    : 'border-gray-700 bg-gray-900/50 hover:border-[#ffd700]/50'
                  }
                `}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <Trophy className="w-5 h-5 text-[#ffd700]" />
                    <div>
                      <h3 className="text-lg font-bold">{race.raceName}</h3>
                      <p className="text-sm text-gray-400">{race.racecourse}</p>
                    </div>
                  </div>
                  {race.grade && (
                    <div className="bg-red-600 text-white px-2 py-1 rounded text-xs font-bold">
                      {race.grade}
                    </div>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center space-x-1 text-gray-400">
                    <Calendar className="w-3 h-3" />
                    <span>{race.date}</span>
                  </div>
                  <div className="flex items-center space-x-1 text-gray-400">
                    <MapPin className="w-3 h-3" />
                    <span>{race.distance}</span>
                  </div>
                </div>
                
                {race.entryCount && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <p className="text-sm text-gray-300">
                      {race.entryCount}頭立て • {race.description || 'G1級レース'}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 分析ボタン */}
        {selectedRace && (
          <div className="text-center mb-8">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="
                bg-gradient-to-r from-[#ffd700] to-[#ffed4a] text-black font-bold
                px-8 py-4 rounded-lg hover:from-[#ffed4a] hover:to-[#ffd700]
                transition-all duration-300 transform hover:scale-105
                disabled:opacity-50 disabled:cursor-not-allowed
                flex items-center space-x-2 mx-auto
              "
            >
              {isAnalyzing ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-black border-t-transparent"></div>
                  <span>D-Logic分析中...</span>
                </>
              ) : (
                <>
                  <BarChart3 className="w-5 h-5" />
                  <span>D-Logic分析開始</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* 分析結果 */}
        {selectedRace && showResults && selectedRace.horses && (
          <div className="bg-gray-900 border border-[#ffd700]/30 rounded-lg p-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-[#ffd700] mb-2">
                D-Logic分析結果
              </h2>
              <p className="text-gray-300">
                {selectedRace.raceName} - {selectedRace.date}
              </p>
            </div>

            {/* 出走馬一覧テーブル */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-gray-700 text-left">
                    <th className="p-2 text-sm font-medium">馬番</th>
                    <th className="p-2 text-sm font-medium">馬名</th>
                    <th className="p-2 text-sm font-medium">騎手</th>
                    <th className="p-2 text-sm font-medium">斤量</th>
                    <th className="p-2 text-sm font-medium text-center">オッズ</th>
                    <th className="p-2 text-sm font-medium text-center">人気</th>
                    <th className="p-2 text-sm font-medium text-center text-[#ffd700]">D-Logic</th>
                    <th className="p-2 text-sm font-medium text-center">着順</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedRace.horses
                    .sort((a, b) => (b.dLogicScore || 0) - (a.dLogicScore || 0))
                    .map((horse) => (
                      <tr
                        key={horse.number}
                        className={`
                          border-b border-gray-800 hover:bg-gray-900/50 transition-colors
                          ${horse.result === 1 
                            ? 'bg-[#ffd700]/10' 
                            : horse.result && horse.result <= 3
                              ? 'bg-gray-800/30'
                              : ''
                          }
                        `}
                      >
                        <td className="p-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-lg">{horse.number}</span>
                            {horse.result === 1 && <Trophy className="w-4 h-4 text-[#ffd700]" />}
                            {horse.result === 2 && <Star className="w-4 h-4 text-gray-400" />}
                            {horse.result === 3 && <Star className="w-4 h-4 text-orange-600" />}
                          </div>
                        </td>
                        <td className="p-2 font-semibold">{horse.name}</td>
                        <td className="p-2 text-sm">{horse.jockey}</td>
                        <td className="p-2 text-sm">{horse.weight}</td>
                        <td className="p-2 text-center">{horse.odds}倍</td>
                        <td className="p-2 text-center">{horse.popularity}番</td>
                        <td className={`p-2 text-center font-bold ${getDLogicColor(horse.dLogicScore || 0)}`}>
                          {horse.dLogicScore || '-'}
                        </td>
                        <td className="p-2 text-center font-semibold">
                          {horse.result ? `${horse.result}着` : '-'}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* LINE友達追加ポップアップ */}
      <LineAddFriendPopup
        isOpen={shouldShowPopup}
        onClose={hidePopup}
        onTicketClaimed={onTicketClaimed}
      />
    </div>
  );
};

export default G1RacesPage;