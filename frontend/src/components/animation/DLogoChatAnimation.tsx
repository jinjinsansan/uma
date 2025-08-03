'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

interface DLogoChatAnimationProps {
  score: number; // 0-100の指数
  isVisible: boolean;
  onAnimationComplete?: () => void;
}

export default function DLogoChatAnimation({ 
  score, 
  isVisible, 
  onAnimationComplete 
}: DLogoChatAnimationProps) {
  const [animationPhase, setAnimationPhase] = useState<'appearing' | 'pulsing' | 'disappearing'>('appearing');

  // 指数に応じた色を決定
  const getDLogoColor = (score: number) => {
    if (score >= 98) {
      // MAX指数: レインボー
      return 'rainbow';
    } else if (score >= 90) {
      // 90-97: 金色（SS級）
      return '#ffd700';
    } else if (score >= 80) {
      // 80-89: 銀色（S級）
      return '#c0c0c0';
    } else if (score >= 70) {
      // 70-79: 銅色（A級）
      return '#cd7f32';
    } else if (score >= 60) {
      // 60-69: 青色（B級）
      return '#4a90e2';
    } else if (score >= 50) {
      // 50-59: 緑色（C級）
      return '#50c878';
    } else {
      // 50未満: 灰色（D級）
      return '#808080';
    }
  };

  const color = getDLogoColor(score);

  // レインボーアニメーション用のCSS
  const rainbowStyle = color === 'rainbow' ? {
    background: 'linear-gradient(45deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3)',
    backgroundSize: '400% 400%',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    animation: 'rainbow-flow 2s ease-in-out infinite'
  } : {};

  useEffect(() => {
    if (!isVisible) return;

    // 3秒間のアニメーション
    const timer1 = setTimeout(() => {
      setAnimationPhase('pulsing');
    }, 500);

    const timer2 = setTimeout(() => {
      setAnimationPhase('disappearing');
    }, 2500);

    const timer3 = setTimeout(() => {
      onAnimationComplete?.();
    }, 3000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [isVisible, onAnimationComplete]);

  if (!isVisible) return null;

  return (
    <>
      {/* レインボーアニメーション用のCSS */}
      <style jsx>{`
        @keyframes rainbow-flow {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
      `}</style>

      {/* オーバーレイ背景 */}
      <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ 
            opacity: animationPhase === 'disappearing' ? 0 : 0.15
          }}
          transition={{ duration: 0.5 }}
          className="absolute inset-0 bg-black"
        />

        {/* Dロゴ */}
        <motion.div
          initial={{ 
            scale: 0.1, 
            opacity: 0,
            rotate: -180
          }}
          animate={{
            scale: animationPhase === 'appearing' ? 1 : 
                   animationPhase === 'pulsing' ? [1, 1.1, 1] : 0.1,
            opacity: animationPhase === 'disappearing' ? 0 : 0.8,
            rotate: animationPhase === 'appearing' ? 0 : 
                   animationPhase === 'pulsing' ? [0, 5, -5, 0] : 180
          }}
          transition={{
            duration: animationPhase === 'appearing' ? 0.5 :
                     animationPhase === 'pulsing' ? 2 : 0.5,
            repeat: animationPhase === 'pulsing' ? Infinity : 0,
            ease: "easeInOut"
          }}
          className="relative"
        >
          <div 
            className="text-[20rem] md:text-[25rem] lg:text-[30rem] font-bold leading-none select-none"
            style={{
              color: color === 'rainbow' ? 'transparent' : color,
              filter: `drop-shadow(0 0 30px ${color === 'rainbow' ? '#ffd700' : color})`,
              ...rainbowStyle
            }}
          >
            D
          </div>

          {/* 指数表示 */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ 
              opacity: animationPhase === 'disappearing' ? 0 : 1,
              y: animationPhase === 'disappearing' ? -50 : 0
            }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full"
          >
            <div className="text-center">
              <div 
                className="text-4xl md:text-5xl font-bold mb-2"
                style={{ color: color === 'rainbow' ? '#ffd700' : color }}
              >
                {score.toFixed(1)}
              </div>
              <div className="text-white text-lg opacity-80">
                {score >= 98 ? 'MAX級' :
                 score >= 90 ? 'SS級' :
                 score >= 80 ? 'S級' :
                 score >= 70 ? 'A級' :
                 score >= 60 ? 'B級' :
                 score >= 50 ? 'C級' : 'D級'}
              </div>
            </div>
          </motion.div>

          {/* エフェクト用の輝き */}
          {color === 'rainbow' && (
            <motion.div
              animate={{ 
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.7, 0.3]
              }}
              transition={{ 
                duration: 1.5, 
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute inset-0 rounded-full"
              style={{
                background: 'radial-gradient(circle, rgba(255,215,0,0.3) 0%, transparent 70%)',
                filter: 'blur(20px)'
              }}
            />
          )}
        </motion.div>

        {/* 背景のパーティクル効果（MAX指数時のみ） */}
        {color === 'rainbow' && (
          <div className="absolute inset-0 pointer-events-none">
            {[...Array(20)].map((_, i) => (
              <motion.div
                key={i}
                initial={{ 
                  x: Math.random() * window.innerWidth,
                  y: Math.random() * window.innerHeight,
                  scale: 0
                }}
                animate={{
                  scale: [0, 1, 0],
                  rotate: [0, 360],
                  x: Math.random() * (window?.innerWidth || 1000),
                  y: Math.random() * (window?.innerHeight || 800)
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  delay: Math.random() * 2,
                  ease: "easeInOut"
                }}
                className="absolute w-2 h-2 rounded-full bg-yellow-400 opacity-60"
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}