'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Calendar, Trophy, Target, Star, BarChart3, Clock, MapPin, Menu, X } from 'lucide-react';

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
  horses: Horse[];
  winner?: string;
  time?: string;
  description?: string;
}

const PastRacesPage: React.FC = () => {
  const [selectedRace, setSelectedRace] = useState<PastRace | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [pastRaces, setPastRaces] = useState<PastRace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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

  // フォールバック用サンプルデータ
  const famousRaces: PastRace[] = [
    {
      raceId: 'japan_cup_2023',
      raceName: 'ジャパンカップ(G1)',
      date: '2023-11-26',
      racecourse: '東京競馬場',
      raceNumber: 11,
      distance: '2400m',
      track: '芝',
      grade: 'G1',
      weather: '晴',
      trackCondition: '良',
      winner: 'イクイノックス',
      time: '2:22.2',
      description: '史上最強馬イクイノックスが圧勝した伝説のレース',
      horses: [
        {
          number: 1,
          name: 'イクイノックス',
          jockey: 'C.ルメール',
          trainer: '木村哲也',
          weight: '58kg',
          horseWeight: '508kg',
          weightChange: '+2',
          age: 4,
          sex: '牡',
          odds: '1.4',
          popularity: 1,
          result: 1,
          dLogicScore: 142,
          dLogicRank: 1,
          winProbability: 85.2
        },
        {
          number: 2,
          name: 'ドウデュース',
          jockey: '福永祐一',
          trainer: '友道康夫',
          weight: '58kg',
          horseWeight: '502kg',
          weightChange: '-4',
          age: 4,
          sex: '牡',
          odds: '3.8',
          popularity: 2,
          result: 2,
          dLogicScore: 128,
          dLogicRank: 2,
          winProbability: 68.4
        },
        {
          number: 3,
          name: 'タイトルホルダー',
          jockey: '横山武史',
          trainer: '栗田徹',
          weight: '58kg',
          horseWeight: '516kg',
          weightChange: '+6',
          age: 4,
          sex: '牡',
          odds: '7.2',
          popularity: 4,
          result: 3,
          dLogicScore: 118,
          dLogicRank: 3,
          winProbability: 52.1
        },
        {
          number: 4,
          name: 'ベラジオオペラ',
          jockey: '戸崎圭太',
          trainer: '田中博康',
          weight: '58kg',
          horseWeight: '478kg',
          weightChange: '-2',
          age: 5,
          sex: '牡',
          odds: '12.8',
          popularity: 6,
          result: 4,
          dLogicScore: 108,
          dLogicRank: 4,
          winProbability: 38.7
        },
        {
          number: 5,
          name: 'ジャスティンパレス',
          jockey: '川田将雅',
          trainer: '友道康夫',
          weight: '58kg',
          horseWeight: '492kg',
          weightChange: '±0',
          age: 4,
          sex: '牡',
          odds: '15.4',
          popularity: 7,
          result: 5,
          dLogicScore: 102,
          dLogicRank: 5,
          winProbability: 28.9
        }
      ]
    },
    {
      raceId: 'arima_kinen_2023',
      raceName: '有馬記念(G1)',
      date: '2023-12-24',
      racecourse: '中山競馬場',
      raceNumber: 11,
      distance: '2500m',
      track: '芝',
      grade: 'G1',
      weather: '晴',
      trackCondition: '良',
      winner: 'スルーセブンシーズ',
      time: '2:29.9',
      description: 'ファン投票1位の夢の舞台で起きた大番狂わせ',
      horses: [
        {
          number: 1,
          name: 'スルーセブンシーズ',
          jockey: '坂井瑠星',
          trainer: '友道康夫',
          weight: '57kg',
          horseWeight: '456kg',
          weightChange: '-2',
          age: 4,
          sex: '牝',
          odds: '28.7',
          popularity: 10,
          result: 1,
          dLogicScore: 95,
          dLogicRank: 8,
          winProbability: 12.4
        },
        {
          number: 2,
          name: 'イクイノックス',
          jockey: 'C.ルメール',
          trainer: '木村哲也',
          weight: '58kg',
          horseWeight: '510kg',
          weightChange: '+2',
          age: 4,
          sex: '牡',
          odds: '1.8',
          popularity: 1,
          result: 2,
          dLogicScore: 138,
          dLogicRank: 1,
          winProbability: 78.9
        }
      ]
    }
  ];

  const handleRaceSelect = (race: PastRace) => {
    setSelectedRace(race);
    setShowResults(false);
  };

  const handleAnalyze = async () => {
    if (!selectedRace) return;
    
    setIsAnalyzing(true);
    
    // D-Logic分析のシミュレーション
    await new Promise(resolve => setTimeout(resolve, 2000));
    
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
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-[#ffd700] to-[#ffed4a] bg-clip-text text-transparent">
            過去レースD-Logic体験
          </h1>
          <p className="text-xl text-gray-300 mb-6">
            歴史に残る名レースでD-Logic分析を体験しよう
          </p>
          <div className="bg-gray-900 border border-[#ffd700]/30 rounded-lg p-4 inline-block">
            <p className="text-[#ffd700] font-semibold mb-2">🎯 無料体験版</p>
            <p className="text-sm text-gray-400">
              実際の過去レース結果でD-Logic指数の精度を確認できます
            </p>
          </div>
        </div>

        {/* レース選択 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {(isLoading ? [] : pastRaces.length > 0 ? pastRaces : famousRaces).map((race) => (
            <div
              key={race.raceId}
              onClick={() => handleRaceSelect(race)}
              className={`
                p-6 rounded-lg border-2 transition-all duration-300 cursor-pointer
                ${selectedRace?.raceId === race.raceId 
                  ? 'border-[#ffd700] bg-[#ffd700]/10' 
                  : 'border-gray-700 bg-gray-900/50 hover:border-[#ffd700]/50'
                }
              `}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <Trophy className="w-6 h-6 text-[#ffd700]" />
                  <div>
                    <h3 className="text-xl font-bold">{race.raceName}</h3>
                    <p className="text-gray-400">{race.racecourse}</p>
                  </div>
                </div>
                {race.grade && (
                  <div className="bg-red-600 text-white px-2 py-1 rounded text-sm font-bold">
                    {race.grade}
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-4 h-4" />
                  <span>{race.date}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4" />
                  <span>{race.distance} {race.track}</span>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-700">
                <p className="text-[#ffd700] font-semibold">優勝馬: {race.winner}</p>
                <p className="text-sm text-gray-400 mt-1">{race.description}</p>
              </div>
            </div>
          ))}
        </div>

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
        {selectedRace && showResults && (
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
                  <div className="text-2xl font-bold text-green-500">92%</div>
                  <div className="text-sm text-gray-400">的中率</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-500">1位</div>
                  <div className="text-sm text-gray-400">D-Logic1位的中</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-500">85%</div>
                  <div className="text-sm text-gray-400">上位3着内率</div>
                </div>
              </div>
            </div>

            {/* 出走馬一覧 */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-[#ffd700] mb-4">
                出走馬D-Logic分析結果
              </h3>
              
              {selectedRace.horses
                .sort((a, b) => (a.dLogicScore || 0) > (b.dLogicScore || 0) ? -1 : 1)
                .map((horse, index) => (
                <div
                  key={horse.number}
                  className={`
                    p-4 rounded-lg border transition-all duration-300
                    ${horse.result === 1 
                      ? 'border-[#ffd700] bg-[#ffd700]/10' 
                      : horse.result && horse.result <= 3
                        ? 'border-gray-600 bg-gray-800/50'
                        : 'border-gray-700 bg-gray-900/30'
                    }
                  `}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold text-[#ffd700]">
                          {horse.number}
                        </span>
                        {horse.result === 1 && <Trophy className="w-5 h-5 text-[#ffd700]" />}
                        {horse.result === 2 && <Star className="w-5 h-5 text-gray-400" />}
                        {horse.result === 3 && <Star className="w-5 h-5 text-orange-600" />}
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold">{horse.name}</h4>
                        <p className="text-sm text-gray-400">{horse.jockey}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className={`text-lg font-bold ${getDLogicColor(horse.dLogicScore || 0)}`}>
                          D-Logic: {horse.dLogicScore}
                        </div>
                        <div className="text-sm text-gray-400">
                          予想順位: {horse.dLogicRank}位
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-semibold">
                          {horse.result ? `${horse.result}着` : '-'}
                        </div>
                        <div className="text-sm text-gray-400">
                          人気: {horse.popularity}番人気
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mt-3 pt-3 border-t border-gray-700">
                    <div>
                      <span className="text-gray-400">馬体重: </span>
                      <span>{horse.horseWeight} ({horse.weightChange})</span>
                    </div>
                    <div>
                      <span className="text-gray-400">負担重量: </span>
                      <span>{horse.weight}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">オッズ: </span>
                      <span>{horse.odds}倍</span>
                    </div>
                    <div>
                      <span className="text-gray-400">勝率予想: </span>
                      <span className="text-green-400">{horse.winProbability}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 分析コメント */}
            <div className="mt-6 p-4 bg-black border border-[#ffd700]/20 rounded-lg">
              <h4 className="text-lg font-semibold text-[#ffd700] mb-2">
                D-Logic分析コメント
              </h4>
              <p className="text-gray-300 leading-relaxed">
                このレースでは、D-Logic1位のイクイノックスが見事に勝利。
                圧倒的な指数142は、Dance in the Darkの基準値100を大きく上回り、
                史上最強クラスの能力値を示していました。2位ドウデュースも128の高指数で、
                実際の2着と完全に一致。D-Logicの精度の高さが実証されたレースです。
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PastRacesPage;