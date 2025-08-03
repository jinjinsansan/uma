import { motion } from 'framer-motion';
import { ConfidenceLevel } from '../../types/race';

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
  const getOrbColor = () => {
    if (isProcessing) return 'bg-yellow-500';
    switch (confidence) {
      case 'high': return 'bg-green-500';
      case 'medium': return 'bg-blue-500';
      case 'low': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="orb-container relative w-20 h-20">
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
        className={`w-full h-full rounded-full ${getOrbColor()}`}
        animate={isProcessing ? {
          scale: [1, 1.2, 1],
          opacity: [0.8, 1, 0.8]
        } : {
          scale: 1,
          opacity: 1
        }}
        transition={{
          duration: isProcessing ? 2 : 0.5,
          repeat: isProcessing ? Infinity : 0,
          ease: "easeInOut"
        }}
        whileHover={{
          scale: 1.1,
          filter: "brightness(1.3)",
        }}
      />
    </div>
  );
} 