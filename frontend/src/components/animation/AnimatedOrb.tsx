import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { ConfidenceLevel } from '../../types/race';

interface AnimatedOrbProps {
  confidence: ConfidenceLevel;
  isProcessing?: boolean;
}

// 予想指数出力時のランダム色パターン（15種類）
const PREDICTION_COLORS = [
  // 金色系
  {
    name: 'gold',
    background: 'radial-gradient(circle at 30% 30%, #ffd700 0%, #ffed4e 25%, #f4d03f 50%, #f39c12 75%, #d68910 100%)',
    shadow: '0 0 60px rgba(255, 215, 0, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'golden-yellow',
    background: 'radial-gradient(circle at 30% 30%, #ffed4e 0%, #f4d03f 25%, #f39c12 50%, #e67e22 75%, #d68910 100%)',
    shadow: '0 0 60px rgba(255, 237, 78, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'amber',
    background: 'radial-gradient(circle at 30% 30%, #ffb347 0%, #ffa500 25%, #ff8c00 50%, #ff7f00 75%, #ff6b35 100%)',
    shadow: '0 0 60px rgba(255, 179, 71, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'brass',
    background: 'radial-gradient(circle at 30% 30%, #cd7f32 0%, #b8860b 25%, #daa520 50%, #bdb76b 75%, #f4a460 100%)',
    shadow: '0 0 60px rgba(205, 127, 50, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'copper',
    background: 'radial-gradient(circle at 30% 30%, #b87333 0%, #cd853f 25%, #d2691e 50%, #a0522d 75%, #8b4513 100%)',
    shadow: '0 0 60px rgba(184, 115, 51, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  // 銀色系
  {
    name: 'silver',
    background: 'radial-gradient(circle at 30% 30%, #c0c0c0 0%, #b8b8b8 25%, #a8a8a8 50%, #989898 75%, #888888 100%)',
    shadow: '0 0 60px rgba(192, 192, 192, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'platinum',
    background: 'radial-gradient(circle at 30% 30%, #e5e4e2 0%, #d3d3d3 25%, #c0c0c0 50%, #a8a8a8 75%, #909090 100%)',
    shadow: '0 0 60px rgba(229, 228, 226, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'steel',
    background: 'radial-gradient(circle at 30% 30%, #4682b4 0%, #5f9ea0 25%, #708090 50%, #778899 75%, #b0c4de 100%)',
    shadow: '0 0 60px rgba(70, 130, 180, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'chrome',
    background: 'radial-gradient(circle at 30% 30%, #f5f5f5 0%, #e8e8e8 25%, #d3d3d3 50%, #c0c0c0 75%, #a8a8a8 100%)',
    shadow: '0 0 60px rgba(245, 245, 245, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'aluminum',
    background: 'radial-gradient(circle at 30% 30%, #d3d3d3 0%, #c0c0c0 25%, #a8a8a8 50%, #909090 75%, #787878 100%)',
    shadow: '0 0 60px rgba(211, 211, 211, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  // レインボー系
  {
    name: 'rainbow-red',
    background: 'radial-gradient(circle at 30% 30%, #ff6b6b 0%, #ff5252 25%, #ff3838 50%, #ff1f1f 75%, #e60000 100%)',
    shadow: '0 0 60px rgba(255, 107, 107, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'rainbow-blue',
    background: 'radial-gradient(circle at 30% 30%, #4facfe 0%, #00f2fe 25%, #667eea 50%, #764ba2 75%, #f5576c 100%)',
    shadow: '0 0 60px rgba(79, 172, 254, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'rainbow-green',
    background: 'radial-gradient(circle at 30% 30%, #4ecdc4 0%, #44a08d 25%, #2ecc71 50%, #27ae60 75%, #16a085 100%)',
    shadow: '0 0 60px rgba(78, 205, 196, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'rainbow-purple',
    background: 'radial-gradient(circle at 30% 30%, #9b59b6 0%, #8e44ad 25%, #7d3c98 50%, #6c3483 75%, #5b2c6f 100%)',
    shadow: '0 0 60px rgba(155, 89, 182, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  },
  {
    name: 'rainbow-orange',
    background: 'radial-gradient(circle at 30% 30%, #ff9f43 0%, #f39c12 25%, #e67e22 50%, #d68910 75%, #cd6133 100%)',
    shadow: '0 0 60px rgba(255, 159, 67, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  }
];

export default function AnimatedOrb({ confidence, isProcessing }: AnimatedOrbProps) {
  const [currentConfidence, setCurrentConfidence] = useState<ConfidenceLevel>('waiting');
  const [predictionColor, setPredictionColor] = useState(PREDICTION_COLORS[0]);
  const [isColorChanging, setIsColorChanging] = useState(false);
  const [colorChangeProgress, setColorChangeProgress] = useState(0);

  useEffect(() => {
    setCurrentConfidence(confidence);
  }, [confidence]);

  // 予想指数出力時（high, medium, low）にランダム色を選択し、じわじわと変化
  useEffect(() => {
    if (confidence === 'high' || confidence === 'medium' || confidence === 'low') {
      const randomColor = PREDICTION_COLORS[Math.floor(Math.random() * PREDICTION_COLORS.length)];
      
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
          setPredictionColor(randomColor);
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
    // 予想指数出力時のみランダム色を適用
    if (currentConfidence === 'high' || currentConfidence === 'medium' || currentConfidence === 'low') {
      if (isColorChanging) {
        // 色変化中のアニメーション
        const baseColor = {
          background: 'radial-gradient(circle at 30% 30%, #e8f5e8 0%, #d4e8d4 25%, #c0dbc0 50%, #acceac 75%, #98c198 100%)',
          boxShadow: '0 0 50px rgba(0, 0, 0, 0.15), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
        };
        
        const targetColor = predictionColor;
        
        // 色の変化を滑らかに補間
        return {
          background: colorChangeProgress > 0.5 ? targetColor.background : baseColor.background,
          boxShadow: colorChangeProgress > 0.5 ? targetColor.shadow : baseColor.boxShadow,
          transition: 'all 0.1s ease-in-out'
        };
      } else {
        // 色変化完了後
        return {
          background: predictionColor.background,
          boxShadow: predictionColor.shadow
        };
      }
    }
    return {};
  };

  return (
    <div className="orb-container">
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