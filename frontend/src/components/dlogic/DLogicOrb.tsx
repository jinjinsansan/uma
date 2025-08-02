'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface DLogicOrbProps {
  isCalculating: boolean;
  calculationProgress?: number;
}

const DLogicOrb: React.FC<DLogicOrbProps> = ({ 
  isCalculating, 
  calculationProgress = 0 
}) => {
  const [orbColor, setOrbColor] = useState('#3B82F6');

  useEffect(() => {
    if (isCalculating) {
      // Dロジック計算中の色変化
      const colors = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B'];
      let colorIndex = 0;
      
      const colorInterval = setInterval(() => {
        setOrbColor(colors[colorIndex]);
        colorIndex = (colorIndex + 1) % colors.length;
      }, 500);

      return () => clearInterval(colorInterval);
    } else {
      setOrbColor('#10B981'); // 計算完了時の緑色
    }
  }, [isCalculating]);

  return (
    <div className="flex items-center justify-center">
      <motion.div
        className="relative"
        animate={isCalculating ? {
          scale: [1, 1.2, 1],
          rotate: [0, 360]
        } : {
          scale: 1,
          rotate: 0
        }}
        transition={{
          duration: 2,
          repeat: isCalculating ? Infinity : 0,
          ease: "easeInOut"
        }}
      >
        {/* メイン球体 */}
        <div
          className="w-32 h-32 rounded-full shadow-lg"
          style={{
            background: `radial-gradient(circle at 30% 30%, ${orbColor}, ${orbColor}dd)`,
            border: `2px solid ${orbColor}`
          }}
        />
        
        {/* 計算進捗リング */}
        {isCalculating && (
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-transparent"
            style={{
              borderTopColor: orbColor,
              borderRightColor: orbColor
            }}
            animate={{
              rotate: [0, 360]
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        )}
        
        {/* 計算完了時のチェックマーク */}
        {!isCalculating && calculationProgress >= 100 && (
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div className="text-white text-4xl font-bold">✓</div>
          </motion.div>
        )}
      </motion.div>
      
      {/* 計算状態テキスト */}
      <div className="ml-4 text-center">
        <div className="text-lg font-semibold text-gray-800">
          {isCalculating ? 'Dロジック計算中...' : '計算完了'}
        </div>
        {isCalculating && (
          <div className="text-sm text-gray-600 mt-1">
            ダンスインザダーク基準100点で指数化中
          </div>
        )}
      </div>
    </div>
  );
};

export default DLogicOrb; 