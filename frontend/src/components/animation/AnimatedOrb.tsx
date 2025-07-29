import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { ConfidenceLevel } from '../../types/race';

interface AnimatedOrbProps {
  confidence: ConfidenceLevel;
  isProcessing?: boolean;
}

const CHAT_COLORS = [
  '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
  '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43',
  '#10ac84', '#ee5a24', '#0abde3', '#ff6b6b', '#48dbfb'
];

export default function AnimatedOrb({ confidence, isProcessing }: AnimatedOrbProps) {
  const [currentConfidence, setCurrentConfidence] = useState<ConfidenceLevel>('waiting');
  const [chatColor, setChatColor] = useState(CHAT_COLORS[0]);

  useEffect(() => {
    setCurrentConfidence(confidence);
  }, [confidence]);

  useEffect(() => {
    if (confidence === 'chatting') {
      const interval = setInterval(() => {
        const randomColor = CHAT_COLORS[Math.floor(Math.random() * CHAT_COLORS.length)];
        setChatColor(randomColor);
      }, 2000); // 2秒ごとに色を変更

      return () => clearInterval(interval);
    }
  }, [confidence]);

  const getOrbClass = () => {
    switch (currentConfidence) {
      case 'high': return 'orb high-confidence';
      case 'medium': return 'orb medium-confidence';
      case 'low': return 'orb low-confidence';
      case 'processing': return 'orb processing';
      case 'chatting': return 'orb chatting';
      default: return 'orb waiting';
    }
  };

  const getOrbStyle = () => {
    if (currentConfidence === 'chatting') {
      return {
        background: `radial-gradient(
          circle at 30% 30%,
          ${chatColor} 0%,
          ${chatColor}dd 20%,
          ${chatColor}bb 40%,
          ${chatColor}99 60%,
          ${chatColor}77 80%,
          ${chatColor}55 100%
        )`,
        boxShadow: `
          0 0 60px ${chatColor}99,
          inset 0 0 50px rgba(255, 255, 255, 0.3),
          0 20px 40px rgba(0, 0, 0, 0.2),
          inset 0 -10px 20px rgba(0, 0, 0, 0.1)
        `
      };
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