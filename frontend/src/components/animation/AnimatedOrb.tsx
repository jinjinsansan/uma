import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { ConfidenceLevel } from '../../types/race';

interface AnimatedOrbProps {
  confidence: ConfidenceLevel;
  isProcessing?: boolean;
}

export default function AnimatedOrb({ confidence, isProcessing }: AnimatedOrbProps) {
  const [currentConfidence, setCurrentConfidence] = useState<ConfidenceLevel>('rainbow');

  useEffect(() => {
    setCurrentConfidence(confidence);
  }, [confidence]);

  const getOrbClass = () => {
    switch (currentConfidence) {
      case 'high': return 'orb high-confidence';
      case 'medium': return 'orb medium-confidence';
      case 'low': return 'orb low-confidence';
      case 'processing': return 'orb processing';
      default: return 'orb rainbow';
    }
  };

  return (
    <div className="orb-container">
      <motion.div
        className={getOrbClass()}
        animate={{
          scaleY: [1, 1.2, 1],
          rotateY: [0, 360],
        }}
        transition={{
          scaleY: { duration: 3, repeat: Infinity, ease: "easeInOut" },
          rotateY: { duration: 6, repeat: Infinity, ease: "linear" },
        }}
        whileHover={{
          scale: 1.1,
          filter: "brightness(1.3)",
        }}
      />
    </div>
  );
}