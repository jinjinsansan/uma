'use client';

import { useEffect, useState } from 'react';

interface LoadingDProps {
  message?: string;
  duration?: number; // ローディング時間（ミリ秒）
}

export default function LoadingD({ message = "分析中", duration = 3000 }: LoadingDProps) {
  const [colorStage, setColorStage] = useState(0);

  useEffect(() => {
    // 15段階の色変化を制御
    const interval = setInterval(() => {
      setColorStage(prev => (prev + 1) % 15);
    }, duration / 15);

    return () => clearInterval(interval);
  }, [duration]);

  const getColorFromStage = (stage: number): string => {
    const colors = [
      '#330000', // loading-1
      '#440000', // loading-2
      '#550000', // loading-3
      '#663300', // loading-4
      '#774400', // loading-5
      '#885500', // loading-6
      '#996600', // loading-7
      '#aa7700', // loading-8
      '#bb8800', // loading-9
      '#cc9900', // loading-10
      '#ddaa00', // loading-11
      '#eebb00', // loading-12
      '#ffcc00', // loading-13
      '#ffdd00', // loading-14
      '#ffed4e', // loading-15 (gold-secondary)
    ];
    return colors[stage] || '#ffd700';
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-64">
      {/* D Logo with Color Animation */}
      <div 
        className="text-8xl font-black font-mono mb-6 transition-colors duration-200"
        style={{ 
          color: getColorFromStage(colorStage),
          textShadow: `0 0 20px ${getColorFromStage(colorStage)}40`,
          fontFamily: 'Arial Black, sans-serif'
        }}
      >
        D
      </div>

      {/* Message */}
      <div className="text-center">
        <p className="text-lg text-primary mb-2">{message}</p>
        <p className="text-sm text-secondary">
          数値化レベル: {Math.round((colorStage + 1) / 15 * 100)}%
        </p>
      </div>

      {/* Progress Bar */}
      <div className="w-64 bg-bg-tertiary rounded-full h-2 mt-4">
        <div 
          className="h-2 rounded-full transition-all duration-200"
          style={{
            width: `${((colorStage + 1) / 15) * 100}%`,
            backgroundColor: getColorFromStage(colorStage)
          }}
        />
      </div>

      {/* Analysis Steps */}
      <div className="mt-6 text-center max-w-sm">
        <div className="grid grid-cols-3 gap-2 text-xs text-secondary">
          <div className={colorStage < 5 ? 'text-gold-primary' : 'text-green-400'}>
            データ収集
          </div>
          <div className={colorStage >= 5 && colorStage < 10 ? 'text-gold-primary' : colorStage >= 10 ? 'text-green-400' : 'text-secondary'}>
            12項目分析
          </div>
          <div className={colorStage >= 10 ? 'text-gold-primary' : 'text-secondary'}>
            結果生成
          </div>
        </div>
      </div>
    </div>
  );
}