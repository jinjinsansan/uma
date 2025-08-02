import { motion } from 'framer-motion';
import { ConfidenceLevel } from '../../types/race';
import { useRaceOrbAnimation } from '../../hooks/useRaceOrbAnimation';

interface RaceAnimatedOrbProps {
  confidence: ConfidenceLevel;
  isProcessing?: boolean;
  lastMessage?: string;
  isConditionsSelected?: boolean;
  isPredictionResult?: boolean;
}

export default function RaceAnimatedOrb({ 
  confidence, 
  isProcessing, 
  lastMessage, 
  isConditionsSelected = false,
  isPredictionResult = false 
}: RaceAnimatedOrbProps) {
  const {
    currentConfidence,
    isColorChanging,
    colorChangeProgress,
    pulseMode,
    isOrbTopic,
    orbAnimationKey,
    currentRandomColor,
    isShrinking,
    isExpanding,
    getOrbClass,
    getOrbStyle,
    getPulseAnimation,
    getPulseTransition
  } = useRaceOrbAnimation(
    confidence,
    isProcessing,
    lastMessage || '',
    isConditionsSelected,
    isPredictionResult
  );

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
        key={orbAnimationKey}
        className={getOrbClass()}
        style={getOrbStyle()}
        animate={getPulseAnimation()}
        transition={getPulseTransition()}
        whileHover={{
          scale: 1.1,
          filter: "brightness(1.3)",
        }}
        onAnimationStart={() => {
          // console.log('🚀 RaceAnimatedOrb アニメーション開始 - key:', orbAnimationKey);
        }}
        onAnimationComplete={() => {
          // console.log('✅ RaceAnimatedOrb アニメーション完了 - key:', orbAnimationKey);
        }}
      />
    </div>
  );
} 