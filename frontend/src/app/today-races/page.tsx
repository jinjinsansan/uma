'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import AuthGuard from '@/components/auth/AuthGuard';

// 仮のレースデータ（後でmykeibadbから取得）
const sampleTodayRaces = [
  {
    id: 1,
    name: '中山記念',
    course: '中山',
    raceNumber: 11,
    time: '15:40',
    distance: '1800m',
    surface: '芝',
    condition: '良',
    grade: 'G2',
    prize: '56,000,000円',
    status: 'upcoming',
    horses: [
      { name: 'サンプルホース1', jockey: '福永祐一', weight: 58, popularity: 1 },
      { name: 'サンプルホース2', jockey: '戸崎圭太', weight: 57, popularity: 2 },
      { name: 'サンプルホース3', jockey: '川田将雅', weight: 56, popularity: 3 },
    ]
  },
  {
    id: 2,
    name: '阪急杯',
    course: '阪神',
    raceNumber: 11,
    time: '15:35',
    distance: '1400m',
    surface: '芝',
    condition: '良',
    grade: 'G3',
    prize: '38,000,000円',
    status: 'upcoming',
    horses: [
      { name: 'スプリンター1', jockey: '松山弘平', weight: 58, popularity: 1 },
      { name: 'スプリンター2', jockey: '横山武史', weight: 57, popularity: 2 },
      { name: 'スプリンター3', jockey: '坂井瑠星', weight: 56, popularity: 3 },
    ]
  }
];

export default function TodayRacesPage() {
  const [races, setRaces] = useState(sampleTodayRaces);
  const [loading, setLoading] = useState(false);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [databaseStats, setDatabaseStats] = useState({ total_records: 1050000, total_horses: 115000, total_races: 85000 });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleAnalyzeRace = (raceId: number) => {
    // D-Logic AI ページに遷移
    window.location.href = `/d-logic-ai?race=${raceId}&type=today`;
  };

  // バックエンドAPIからリアルタイムデータを取得
  const fetchTodayRaces = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/today-races');
      if (!response.ok) {
        throw new Error('APIからのデータ取得に失敗しました');
      }
      const data = await response.json();
      
      // APIデータを既存フォーマットに変換
      const convertedRaces = data.racecourses.flatMap((course: any) => 
        course.races.map((race: any, index: number) => ({
          id: `${course.courseId}_${race.raceNumber}`,
          name: race.raceName,
          course: course.name,
          raceNumber: race.raceNumber,
          time: race.time,
          distance: race.distance,
          surface: race.track,
          condition: course.trackCondition,
          grade: race.grade || 'N/A',
          prize: race.prizePool,
          status: 'upcoming',
          weather: course.weather,
          horses: (race.horses || []).slice(0, 6).map((horse: any, hIndex: number) => ({
            name: horse.name,
            jockey: horse.jockey,
            weight: parseInt(horse.weight) || 56,
            popularity: horse.popularity || hIndex + 1,
            odds: horse.odds || '未定'
          }))
        }))
      );
      
      setRaces(convertedRaces);
      setLoading(false);
    } catch (error) {
      // APIエラー時は仮データを使用
      setLoading(false);
    }
  };

  // データベース統計を取得
  const fetchDatabaseStats = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/stats/database');
      const data = await response.json();
      if (data.status === 'success' || data.status === 'fallback') {
        setDatabaseStats(data.database_stats);
      }
    } catch (error) {
      // Database stats fetch failed, using fallback
    }
  };

  useEffect(() => {
    fetchTodayRaces();
    fetchDatabaseStats();
  }, []);

  if (maintenanceMode) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black via-gray-900 to-black flex items-center justify-center">
        <div className="text-center">
          <div className="loading-d mb-6">D</div>
          <h1 className="text-2xl font-bold text-gold-primary mb-4">メンテナンス中</h1>
          <p className="text-secondary mb-8">
            データ更新システムのメンテナンス中です。<br />
            しばらくお待ちください。
          </p>
          <Link href="/past-races" className="outline-button">
            過去レース体験に戻る
          </Link>
        </div>
      </div>
    );
  }

  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-gradient-to-b from-black via-gray-900 to-black">
      {/* Header */}
      <header className="bg-bg-secondary border-b border-border-primary">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <span className="d-logo-small">D</span>
            <span className="text-xl font-bold text-gold-primary">本日の開催レース</span>
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-6">
            <Link href="/past-races" className="outline-button px-4 py-2 text-sm">
              過去レース体験
            </Link>
            <Link href="/d-logic-ai" className="outline-button px-4 py-2 text-sm">
              D-Logic AI
            </Link>
            <Link href="/register" className="gold-button px-4 py-2 text-sm">
              会員登録
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden text-gold-primary p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-bg-tertiary border-t border-border-primary">
            <nav className="container mx-auto px-4 py-4 flex flex-col space-y-3">
              <Link 
                href="/past-races" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                過去レース体験
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
                className="gold-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                会員登録
              </Link>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="relative py-12">
        {/* Hero Section */}
        <section className="mb-12">
          <div className="container mx-auto px-4 text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-gradient mb-4">
              本日の開催レース
            </h1>
            <p className="text-lg text-secondary max-w-2xl mx-auto mb-8">
              リアルタイムデータによる最新のレース情報<br />
              D-Logic分析で科学的な予想をお届けします
            </p>
            
            <div className="flex items-center justify-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-secondary">データ更新中</span>
              </div>
              <div className="text-secondary">
                最終更新: {new Date().toLocaleTimeString('ja-JP')}
              </div>
            </div>
          </div>
        </section>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="loading-d mb-4">D</div>
            <p className="text-secondary">レースデータを取得中...</p>
          </div>
        )}

        {/* Race List */}
        {!loading && (
          <section>
            <div className="container mx-auto px-4">
              <div className="space-y-6 max-w-6xl mx-auto">
                {races.map((race) => (
                  <div key={race.id} className="glass-effect rounded-lg overflow-hidden">
                    {/* Race Header */}
                    <div className="bg-bg-tertiary px-6 py-4 border-b border-border-primary">
                      <div className="flex flex-wrap items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <span className="bg-red-600 text-white px-3 py-1 rounded text-sm font-bold">
                            {race.grade}
                          </span>
                          <h3 className="text-xl font-bold text-gold-primary">{race.name}</h3>
                          <span className="text-secondary">{race.time} 発走</span>
                        </div>
                        
                        <button
                          onClick={() => handleAnalyzeRace(race.id)}
                          className="gold-button"
                        >
                          D-Logic分析する
                        </button>
                      </div>
                      
                      <div className="mt-2 flex flex-wrap items-center space-x-6 text-sm text-secondary">
                        <span>{race.course} {race.raceNumber}R</span>
                        <span>{race.distance}</span>
                        <span>{race.surface}</span>
                        <span>馬場：{race.condition}</span>
                        <span>賞金：{race.prize}</span>
                      </div>
                    </div>

                    {/* Sample Horses Preview */}
                    <div className="p-6">
                      <h4 className="text-gold-primary font-semibold mb-3">主要出走馬（プレビュー）</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {race.horses.slice(0, 3).map((horse, index) => (
                          <div key={index} className="bg-bg-secondary rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-semibold text-primary">{horse.name}</span>
                              <span className="text-sm bg-gold-primary text-black px-2 py-1 rounded">
                                {horse.popularity}番人気
                              </span>
                            </div>
                            <div className="text-sm text-secondary">
                              <div>{horse.jockey}</div>
                              <div>{horse.weight}kg</div>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      <div className="mt-4 text-center">
                        <button
                          onClick={() => handleAnalyzeRace(race.id)}
                          className="outline-button px-6 py-2"
                        >
                          全出走馬をD-Logic分析
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Info Section */}
        <section className="mt-16 py-12 bg-bg-secondary/50">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-2xl font-bold text-gold-primary mb-4">
              D-Logic統合分析エンジン
            </h2>
            <p className="text-secondary mb-8 max-w-2xl mx-auto">
              {databaseStats.total_records.toLocaleString()}レコードの膨大なデータから<br />
              12項目のD-Logic分析を瞬時に実行
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="glass-effect rounded-lg p-6">
                <div className="text-3xl mb-3">📊</div>
                <h3 className="font-bold text-gold-primary mb-2">{databaseStats.total_records.toLocaleString()}レコード</h3>
                <p className="text-sm text-secondary">日本競馬史上最大規模のデータベース</p>
              </div>
              
              <div className="glass-effect rounded-lg p-6">
                <div className="text-3xl mb-3">🎯</div>
                <h3 className="font-bold text-gold-primary mb-2">12項目分析</h3>
                <p className="text-sm text-secondary">独自基準による科学的12項目評価</p>
              </div>
              
              <div className="glass-effect rounded-lg p-6">
                <div className="text-3xl mb-3">⚡</div>
                <h3 className="font-bold text-gold-primary mb-2">瞬時判定</h3>
                <p className="text-sm text-secondary">数秒以内での高精度分析</p>
              </div>
            </div>
          </div>
        </section>
      </main>
      </div>
    </AuthGuard>
  );
}