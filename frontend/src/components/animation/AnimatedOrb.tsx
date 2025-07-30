import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { ConfidenceLevel } from '../../types/race';

interface AnimatedOrbProps {
  confidence: ConfidenceLevel;
  isProcessing?: boolean;
}

// 信頼度別の色定義
const CONFIDENCE_COLORS = {
  high: {
    background: 'radial-gradient(circle at 30% 30%, #ffffff 0%, #f8f8f8 25%, #f0f0f0 50%, #e8e8e8 75%, #e0e0e0 100%)',
    shadow: '0 0 80px rgba(255, 255, 255, 0.8), inset 0 0 60px rgba(255, 255, 255, 0.6), 0 20px 40px rgba(0, 0, 0, 0.15), inset 0 -10px 20px rgba(0, 0, 0, 0.1)'
  },
  medium: {
    background: 'radial-gradient(circle at 30% 30%, #ffd700 0%, #ffed4e 25%, #f4d03f 50%, #f39c12 75%, #d68910 100%)',
    shadow: '0 0 60px rgba(255, 215, 0, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  low: {
    background: 'radial-gradient(circle at 30% 30%, #2c2c2c 0%, #1a1a1a 25%, #0f0f0f 50%, #080808 75%, #000000 100%)',
    shadow: '0 0 40px rgba(0, 50, 100, 0.4), inset 0 0 30px rgba(255, 255, 255, 0.2), 0 15px 30px rgba(0, 0, 0, 0.3), inset 0 -5px 10px rgba(0, 0, 0, 0.2)'
  }
};

export default function AnimatedOrb({ confidence, isProcessing }: AnimatedOrbProps) {
  const [currentConfidence, setCurrentConfidence] = useState<ConfidenceLevel>('waiting');
  const [isColorChanging, setIsColorChanging] = useState(false);
  const [colorChangeProgress, setColorChangeProgress] = useState(0);

  useEffect(() => {
    setCurrentConfidence(confidence);
  }, [confidence]);

  // 予想指数出力時（high, medium, low）に信頼度に応じた色に変化
  useEffect(() => {
    if (confidence === 'high' || confidence === 'medium' || confidence === 'low') {
      // 色変化のアニメーション開始
      setIsColorChanging(true);
      setColorChangeProgress(0);
      
      // じわじわとした色変化アニメーション
      const animationDuration = 3000; // 3秒
      const steps = 60; // 60ステップ
      const stepDuration = animationDuration / steps;
      
      let currentStep = 0;
      const interval = setInterval(() => {
        currentStep++;
        const progress = currentStep / steps;
        setColorChangeProgress(progress);
        
        if (currentStep >= steps) {
          setIsColorChanging(false);
          clearInterval(interval);
        }
      }, stepDuration);
      
      return () => clearInterval(interval);
    } else {
      // 予想結果以外の状態では色変化をリセット
      setIsColorChanging(false);
      setColorChangeProgress(0);
    }
  }, [confidence]);

  const getOrbClass = () => {
    switch (currentConfidence) {
      case 'high':
      case 'medium':
      case 'low':
        return 'orb prediction'; // 予想結果用のクラス
      case 'processing': 
        return 'orb processing';
      case 'chatting': 
        return 'orb chatting';
      default: 
        return 'orb waiting'; // デフォルトは薄いグリーン
    }
  };

  const getOrbStyle = () => {
    // 予想指数出力時のみ信頼度に応じた色を適用
    if (currentConfidence === 'high' || currentConfidence === 'medium' || currentConfidence === 'low') {
      if (isColorChanging) {
        // 色変化中のアニメーション
        const baseColor = {
          background: 'radial-gradient(circle at 30% 30%, #e8f5e8 0%, #d4e8d4 25%, #c0dbc0 50%, #acceac 75%, #98c198 100%)',
          boxShadow: '0 0 50px rgba(0, 0, 0, 0.15), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
        };
        
        const targetColor = CONFIDENCE_COLORS[currentConfidence as keyof typeof CONFIDENCE_COLORS];
        
        // 色の変化を滑らかに補間
        return {
          background: colorChangeProgress > 0.5 ? targetColor.background : baseColor.background,
          boxShadow: colorChangeProgress > 0.5 ? targetColor.shadow : baseColor.boxShadow,
          transition: 'all 0.1s ease-in-out'
        };
      } else {
        // 色変化完了後
        const targetColor = CONFIDENCE_COLORS[currentConfidence as keyof typeof CONFIDENCE_COLORS];
        return {
          background: targetColor.background,
          boxShadow: targetColor.shadow
        };
      }
    }
    return {};
  };

  return (
    <div className="orb-container">
      {/* 半透明の背景円 */}
      <div 
        className="absolute inset-0 rounded-full bg-white/20 backdrop-blur-sm"
        style={{
          width: '100%',
          height: '100%',
          transform: 'scale(1.2)',
        }}
      />
      <motion.div
        className={getOrbClass()}
        style={getOrbStyle()}
        animate={{
          scale: [1, 1.15, 1],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        whileHover={{
          scale: 1.1,
          filter: "brightness(1.3)",
        }}
      />
    </div>
  );
}