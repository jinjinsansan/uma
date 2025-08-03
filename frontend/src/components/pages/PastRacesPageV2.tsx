'use client';

import React, { useState, useEffect } from 'react'
import { Calendar, Trophy, Target, Star, BarChart3, Clock, MapPin } from 'lucide-react'

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
  result?: number; // 着順
  dLogicScore?: number; // D-Logic指数
  dLogicRank?: number; // D-Logic順位
  winProbability?: number; // 勝率予想
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

const PastRacesPageV2: React.FC = () => {
  const [selectedRace, setSelectedRace] = useState<PastRace | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [pastRaces, setPastRaces] = useState<PastRace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [raceDetails, setRaceDetails] = useState<PastRace | null>(null);

  // APIから過去レースデータを取得
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
      console.error('過去レース取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchRaceDetails = async (raceId: string) => {
    try {
      const response = await fetch(`http://localhost:8001/api/past-races/${raceId}`);
      const data = await response.json();
      
      if (data.horses) {
        setRaceDetails({
          ...selectedRace!,
          horses: data.horses
        });
      }
    } catch (error) {
      console.error('レース詳細取得エラー:', error);
    }
  };

  const handleRaceSelect = async (race: PastRace) => {
    setSelectedRace(race);
    setShowResults(false);
    setRaceDetails(null);
    
    // レース詳細データを取得
    if (race.raceId) {
      await fetchRaceDetails(race.raceId);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedRace) return;
    
    setIsAnalyzing(true);
    
    try {
      // D-Logic分析APIを呼び出し
      const response = await fetch(`http://localhost:8001/api/past-races/${selectedRace.raceId}/analyze`, {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.horses) {
        setRaceDetails({
          ...selectedRace,
          horses: result.horses
        });
      }
    } catch (error) {
      console.error('D-Logic分析エラー:', error);
    }
    
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

  const getResultIcon = (result: number | undefined) => {
    if (!result) return null;
    if (result === 1) return <Trophy className="w-4 h-4 text-[#ffd700]" />;
    if (result === 2) return <Star className="w-4 h-4 text-gray-400" />;
    if (result === 3) return <Star className="w-4 h-4 text-orange-600" />;
    return null;
  };

  return (
    <div className="min-h-screen bg-black text-white p-6">
      {/* ヘッダー */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-[#ffd700] to-[#ffed4a] bg-clip-text text-transparent">
            過去レースD-Logic体験
          </h1>
          <p className="text-xl text-gray-300 mb-6">
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
            <p className="text-gray-400">G1レースデータを読み込み中...</p>
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
                
                {race.description && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <p className="text-sm text-gray-300">{race.description}</p>
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
              disabled={isAnalyzing || !raceDetails}
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
        {selectedRace && showResults && raceDetails?.horses && (
          <div className="bg-gray-900 border border-[#ffd700]/30 rounded-lg p-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-[#ffd700] mb-2">
                D-Logic分析結果
              </h2>
              <p className="text-gray-300">
                {selectedRace.raceName} - {selectedRace.date}
              </p>
            </div>

            {/* 予想精度 */}
            <div className="bg-black border border-[#ffd700]/20 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold text-[#ffd700] mb-3 flex items-center">
                <Target className="w-5 h-5 mr-2" />
                D-Logic予想精度
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-500">
                    {(() => {
                      const top1 = raceDetails.horses.find(h => h.dLogicRank === 1);
                      return top1?.result === 1 ? '◎' : '○';
                    })()}
                  </div>
                  <div className="text-sm text-gray-400">1位予想</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-500">
                    {(() => {
                      const top3 = raceDetails.horses.filter(h => h.dLogicRank && h.dLogicRank <= 3);
                      const hit = top3.filter(h => h.result && h.result <= 3).length;
                      return `${hit}/3`;
                    })()}
                  </div>
                  <div className="text-sm text-gray-400">3着内的中</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-500">
                    {raceDetails.horses.length}頭
                  </div>
                  <div className="text-sm text-gray-400">出走頭数</div>
                </div>
              </div>
            </div>

            {/* 出走馬一覧 */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-[#ffd700] mb-4">
                全出走馬D-Logic分析結果
              </h3>
              
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
                      <th className="p-2 text-sm font-medium text-center text-[#ffd700]">予想順位</th>
                      <th className="p-2 text-sm font-medium text-center">勝率予想</th>
                      <th className="p-2 text-sm font-medium text-center">着順</th>
                    </tr>
                  </thead>
                  <tbody>
                    {raceDetails.horses
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
                              {getResultIcon(horse.result)}
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
                          <td className="p-2 text-center text-[#ffd700] font-semibold">
                            {horse.dLogicRank || '-'}位
                          </td>
                          <td className="p-2 text-center text-green-400">
                            {horse.winProbability ? `${horse.winProbability}%` : '-'}
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

            {/* 分析コメント */}
            <div className="mt-6 p-4 bg-black border border-[#ffd700]/20 rounded-lg">
              <h4 className="text-lg font-semibold text-[#ffd700] mb-2">
                D-Logic分析コメント
              </h4>
              <p className="text-gray-300 leading-relaxed">
                {(() => {
                  const top1 = raceDetails.horses.find(h => h.dLogicRank === 1);
                  const winner = raceDetails.horses.find(h => h.result === 1);
                  
                  if (top1 && winner && top1.name === winner.name) {
                    return `このレースでは、D-Logic1位の${top1.name}が見事に勝利。指数${top1.dLogicScore}は、Dance in the Darkの基準値100を大きく上回り、圧倒的な能力値を示していました。D-Logicの精度の高さが実証されたレースです。`;
                  } else if (winner) {
                    return `このレースでは、実際の勝利馬は${winner.name}でした。D-Logic上位陣も好走しており、予想の参考として十分な精度を示しています。競馬の醍醐味である「番狂わせ」も含めて楽しめるレースでした。`;
                  } else {
                    return `D-Logic分析により、各馬の能力値が明確に数値化されました。基準値100を超える馬が上位に来る傾向が確認でき、予想の重要な指標となっています。`;
                  }
                })()}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PastRacesPageV2;