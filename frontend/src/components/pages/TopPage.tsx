'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface DatabaseStats {
  total_records: number;
  total_horses: number;
  total_races: number;
  years_span: number;
}

export default function TopPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [databaseStats, setDatabaseStats] = useState<DatabaseStats | null>(null);
  const [statsText, setStatsText] = useState('959,620レコード・109,426頭・82,738レース・71年間の蓄積データ');

  useEffect(() => {
    // ページロード時のアニメーション制御
    const timer1 = setTimeout(() => setCurrentStep(1), 500);
    const timer2 = setTimeout(() => setCurrentStep(2), 3500);
    const timer3 = setTimeout(() => setCurrentStep(3), 5000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  useEffect(() => {
    // データベース統計を取得
    const fetchDatabaseStats = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/stats/database');
        const data = await response.json();
        
        if (data.status === 'success' || data.status === 'fallback') {
          setDatabaseStats(data.database_stats);
          setStatsText(data.display_text.summary);
        }
      } catch (error) {
        // フォールバック値を使用（エラーは表示しない）
      }
    };

    fetchDatabaseStats();
    
    // 5分ごとに更新
    const interval = setInterval(fetchDatabaseStats, 300000);
    return () => clearInterval(interval);
  }, []);

  const description = `
    革命的なAI競馬予想システム
    
    ${statsText}と
    最新のAI技術を融合した
    次世代D-Logic分析エンジン
    
    独自基準100点満点による
    科学的で客観的な12項目評価
  `;

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-gray-900 to-black overflow-hidden">
      {/* Background Stars Effect */}
      <div className="absolute inset-0">
        {[...Array(50)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-gold-primary rounded-full opacity-70"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
            }}
          />
        ))}
      </div>

      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center container mx-auto px-4">
        
        {/* Step 1: D Logo Animation */}
        {currentStep >= 1 && (
          <div className="flex flex-col items-center">
            <div className={`d-logo zoom-rotate ${currentStep >= 1 ? 'pulse-gold' : ''}`}>
              D
            </div>
          </div>
        )}

        {/* Step 2: Description */}
        {currentStep >= 2 && (
          <div className="text-center mt-8 fade-in-up">
            <h1 className="text-4xl md:text-6xl font-bold text-gradient mb-6">
              D-Logic
            </h1>
            <p className="text-lg md:text-xl max-w-2xl mx-auto leading-relaxed whitespace-pre-line" style={{ color: 'var(--text-secondary)' }}>
              {description}
            </p>
          </div>
        )}

        {/* Step 3: Navigation Buttons */}
        {currentStep >= 3 && (
          <div className="mt-12 fade-in-up grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto w-full">
            
            {/* 本日の開催レース */}
            <Link href="/today-races" className="group">
              <div className="glass-effect rounded-lg p-6 text-center hover:scale-105 transition-all duration-300 hover:shadow-gold">
                <div className="text-4xl mb-4">🏇</div>
                <h3 className="text-xl font-bold text-gold-primary mb-2">本日の開催レース</h3>
                <p className="text-secondary text-sm">
                  リアルタイムデータによる<br />
                  今日のレース情報
                </p>
              </div>
            </Link>

            {/* 過去レースでD-Logic体験 */}
            <Link href="/past-races" className="group">
              <div className="glass-effect rounded-lg p-6 text-center hover:scale-105 transition-all duration-300 hover:shadow-gold">
                <div className="text-4xl mb-4">⭐</div>
                <h3 className="text-xl font-bold text-gold-primary mb-2">過去レースでD-Logic体験</h3>
                <p className="text-secondary text-sm">
                  G1レースで<br />
                  D-Logic分析を無料体験
                </p>
              </div>
            </Link>

            {/* D-Logic AI */}
            <Link href="/d-logic-ai" className="group">
              <div className="glass-effect rounded-lg p-6 text-center hover:scale-105 transition-all duration-300 hover:shadow-gold">
                <div className="text-4xl mb-4">🤖</div>
                <h3 className="text-xl font-bold text-gold-primary mb-2">D-Logic AI</h3>
                <p className="text-secondary text-sm">
                  AI搭載チャット<br />
                  馬名直接分析対応
                </p>
              </div>
            </Link>

            {/* 会員登録 */}
            <Link href="/register" className="group">
              <div className="glass-effect rounded-lg p-6 text-center hover:scale-105 transition-all duration-300 hover:shadow-gold">
                <div className="text-4xl mb-4">👤</div>
                <h3 className="text-xl font-bold text-gold-primary mb-2">会員登録</h3>
                <p className="text-secondary text-sm">
                  無料体験・有料プラン<br />
                  LINE連携特典あり
                </p>
              </div>
            </Link>

            {/* お問い合わせ */}
            <a 
              href="https://line.me/R/ti/p/@dlogic" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="group"
            >
              <div className="glass-effect rounded-lg p-6 text-center hover:scale-105 transition-all duration-300 hover:shadow-gold">
                <div className="text-4xl mb-4">📞</div>
                <h3 className="text-xl font-bold text-gold-primary mb-2">お問い合わせ</h3>
                <p className="text-secondary text-sm">
                  D-Logic公式LINE<br />
                  サポート・質問受付
                </p>
              </div>
            </a>

            {/* プレミアム機能 (将来用) */}
            <div className="group opacity-75">
              <div className="glass-effect rounded-lg p-6 text-center">
                <div className="text-4xl mb-4">🚀</div>
                <h3 className="text-xl font-bold text-gray-400 mb-2">プレミアム機能</h3>
                <p className="text-gray-500 text-sm">
                  近日公開予定<br />
                  Coming Soon
                </p>
              </div>
            </div>

          </div>
        )}

        {/* Footer */}
        {currentStep >= 3 && (
          <footer className="mt-16 text-center text-secondary text-sm fade-in-up">
            <p>&copy; 2025 D-Logic AI. All rights reserved.</p>
            <p className="mt-2">
              Powered by D-Logic Analysis Engine | 959,620 Records | 71 Years of Data
            </p>
          </footer>
        )}

      </div>
    </div>
  );
}