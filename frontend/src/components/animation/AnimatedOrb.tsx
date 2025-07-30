import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { ConfidenceLevel } from '../../types/race';

interface AnimatedOrbProps {
  confidence: ConfidenceLevel;
  isProcessing?: boolean;
  lastMessage?: string;
  isConditionsSelected?: boolean;
  isPredictionResult?: boolean;
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
    background: 'radial-gradient(circle at 30% 30%, #ff6b6b 0%, #ff8e8e 25%, #ffa5a5 50%, #ffb3b3 75%, #ffc0c0 100%)',
    shadow: '0 0 60px rgba(255, 107, 107, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
  }
};

// デフォルトのグリーン色
const DEFAULT_GREEN = {
  background: 'radial-gradient(circle at 30% 30%, #4ade80 0%, #22c55e 25%, #16a34a 50%, #15803d 75%, #166534 100%)',
  shadow: '0 0 50px rgba(0, 0, 0, 0.15), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)'
};

// ランダムな色の配列（より明るく美しい色）
const RANDOM_COLORS = [
  { background: 'radial-gradient(circle at 30% 30%, #ff6b6b 0%, #ff8e8e 25%, #ffa5a5 50%, #ffb3b3 75%, #ffc0c0 100%)', shadow: '0 0 60px rgba(255, 107, 107, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)' },
  { background: 'radial-gradient(circle at 30% 30%, #4ecdc4 0%, #44a08d 25%, #3a8b7a 50%, #307667 75%, #266154 100%)', shadow: '0 0 60px rgba(78, 205, 196, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)' },
  { background: 'radial-gradient(circle at 30% 30%, #45b7d1 0%, #3a9bb8 25%, #2f7f9f 50%, #246386 75%, #19476d 100%)', shadow: '0 0 60px rgba(69, 183, 209, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)' },
  { background: 'radial-gradient(circle at 30% 30%, #96ceb4 0%, #7fb8a0 25%, #68a28c 50%, #518c78 75%, #3a7664 100%)', shadow: '0 0 60px rgba(150, 206, 180, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)' },
  { background: 'radial-gradient(circle at 30% 30%, #feca57 0%, #ff9ff3 25%, #54a0ff 50%, #5f27cd 75%, #341f97 100%)', shadow: '0 0 60px rgba(254, 202, 87, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)' },
  { background: 'radial-gradient(circle at 30% 30%, #ff9ff3 0%, #f368e0 25%, #e056fd 50%, #c44569 75%, #a55eea 100%)', shadow: '0 0 60px rgba(255, 159, 243, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)' },
  { background: 'radial-gradient(circle at 30% 30%, #54a0ff 0%, #2e86de 25%, #0c2461 50%, #1e3799 75%, #4a69bd 100%)', shadow: '0 0 60px rgba(84, 160, 255, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)' },
  { background: 'radial-gradient(circle at 30% 30%, #5f27cd 0%, #341f97 25%, #0c2461 50%, #1e3799 75%, #4a69bd 100%)', shadow: '0 0 60px rgba(95, 39, 205, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)' }
];

export default function AnimatedOrb({ 
  confidence, 
  isProcessing, 
  lastMessage, 
  isConditionsSelected = false,
  isPredictionResult = false 
}: AnimatedOrbProps) {
  const [currentConfidence, setCurrentConfidence] = useState<ConfidenceLevel>('waiting');
  const [isColorChanging, setIsColorChanging] = useState(false);
  const [colorChangeProgress, setColorChangeProgress] = useState(0);
  const [pulseMode, setPulseMode] = useState<'normal' | 'racing' | 'prediction' | 'conditions' | 'result'>('normal');
  const [isOrbTopic, setIsOrbTopic] = useState(false);
  const [orbAnimationKey, setOrbAnimationKey] = useState(0);
  const [currentRandomColor, setCurrentRandomColor] = useState<typeof RANDOM_COLORS[0] | null>(null);
  const [isShrinking, setIsShrinking] = useState(false);
  const [isExpanding, setIsExpanding] = useState(false);

  useEffect(() => {
    setCurrentConfidence(confidence);
    
    // 球体に関する話題かどうかを判定
    const orbKeywords = [
      '球体', 'ボール', '球', 'オーブ', 'orb', '丸い', '円', '玉', '球体の', 'ボールの',
      '球の', 'オーブの', '球体が', 'ボールが', '球が', 'オーブが', '球体は', 'ボールは',
      '球は', 'オーブは', '球体を', 'ボールを', '球を', 'オーブを', '球体に', 'ボールに',
      '球に', 'オーブに', '球体で', 'ボールで', '球で', 'オーブで', '球体と', 'ボールと',
      '球と', 'オーブと', '球体も', 'ボールも', '球も', 'オーブも', '球体や', 'ボールや',
      '球や', 'オーブや', '球体の色', 'ボールの色', '球の色', 'オーブの色', '球体の動き',
      'ボールの動き', '球の動き', 'オーブの動き', '球体の大きさ', 'ボールの大きさ',
      '球の大きさ', 'オーブの大きさ', '球体の形', 'ボールの形', '球の形', 'オーブの形',
      '球体の位置', 'ボールの位置', '球の位置', 'オーブの位置', '球体の変化', 'ボールの変化',
      '球の変化', 'オーブの変化', '球体のアニメーション', 'ボールのアニメーション',
      '球のアニメーション', 'オーブのアニメーション', '球体の演出', 'ボールの演出',
      '球の演出', 'オーブの演出', '球体の効果', 'ボールの効果', '球の効果', 'オーブの効果'
    ];
    
    const isOrbRelated = lastMessage ? orbKeywords.some(keyword => 
      lastMessage.toLowerCase().includes(keyword.toLowerCase())
    ) : false;
    
    setIsOrbTopic(isOrbRelated);
    
    // 球体に関する話題が検出されたらアニメーションキーを更新
    if (isOrbRelated) {
      setOrbAnimationKey(prev => prev + 1);
    }
    
    // パルスモードを設定
    if (confidence === 'high' || confidence === 'medium' || confidence === 'low') {
      setPulseMode('prediction');
    } else if (confidence === 'chatting') {
      // チャット中は競馬関連の話題かどうかを判定
      const racingKeywords = [
        '競馬', 'レース', '馬', '騎手', '調教師', '血統', '距離', '馬場', '芝', 'ダート',
        '単勝', '複勝', '馬連', '馬単', '三連複', '三連単', 'ワイド', '枠連',
        '1着', '2着', '3着', '着差', 'タイム', '上がり', '上がり3F', '上がり4F',
        '人気', 'オッズ', '本命', '対抗', '穴', '穴馬', '逃げ', '先行', '差し', '追込',
        '右回り', '左回り', '重', '良', '稍重', '不良', '東京', '阪神', '京都', '中山',
        '新潟', '福島', '小倉', '札幌', '函館', '中京', '名古屋', '金沢', '高知',
        'ディープインパクト', 'シンボリルドルフ', 'オグリキャップ', 'トウカイテイオー',
        'メジロマックイーン', 'ナリタブライアン', 'サイレンススズカ', 'エルコンドルパサー'
      ];
      
      const isRacingTopic = lastMessage && racingKeywords.some(keyword => 
        lastMessage.toLowerCase().includes(keyword.toLowerCase())
      );
      
      setPulseMode(isRacingTopic ? 'racing' : 'normal');
    } else {
      setPulseMode('normal');
    }
  }, [confidence, lastMessage]);

  // 8条件選択時のアニメーション
  useEffect(() => {
    if (isConditionsSelected) {
      // 他のアニメーションをリセット
      setIsExpanding(false);
      setCurrentRandomColor(null);
      setIsShrinking(true);
      setPulseMode('conditions');
      // アニメーションキーを強制的に更新
      setOrbAnimationKey(prev => prev + 1);
      
      // 0.6秒後に縮小アニメーション完了
      setTimeout(() => {
        setIsShrinking(false);
        setPulseMode('normal');
      }, 600);
    } else {
      // 条件が選択されていない場合は状態をリセット
      setIsShrinking(false);
      if (pulseMode === 'conditions') {
        setPulseMode('normal');
      }
    }
  }, [isConditionsSelected]);

  // 予想結果表示時のアニメーション
  useEffect(() => {
    if (isPredictionResult && !isConditionsSelected) { // 8条件選択時は実行しない
      // ランダムな色を選択
      const randomColor = RANDOM_COLORS[Math.floor(Math.random() * RANDOM_COLORS.length)];
      setCurrentRandomColor(randomColor);
      
      // 拡大アニメーション開始
      setIsExpanding(true);
      setPulseMode('result');
      
      // 3秒後に元のグリーン色に戻す
      const timer = setTimeout(() => {
        setCurrentRandomColor(null);
        setIsExpanding(false);
        setPulseMode('normal');
        // 信頼度もリセット
        setCurrentConfidence('waiting');
      }, 3000);
      
      // クリーンアップ関数を追加
      return () => clearTimeout(timer);
    }
  }, [isPredictionResult, isConditionsSelected]);

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
    // 予想結果表示時のランダム色（スムーズな変化）
    if (currentRandomColor) {
      return {
        background: currentRandomColor.background,
        boxShadow: currentRandomColor.shadow,
        transition: 'all 0.8s ease-in-out'
      };
    }
    
    // 球体に関する話題の場合は特別な色を適用
    if (isOrbTopic) {
      return {
        background: 'radial-gradient(circle at 30% 30%, #ff6b6b 0%, #ff8e8e 25%, #ffa5a5 50%, #ffb3b3 75%, #ffc0c0 100%)',
        boxShadow: '0 0 60px rgba(255, 107, 107, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4), 0 20px 40px rgba(0, 0, 0, 0.25), inset 0 -10px 20px rgba(0, 0, 0, 0.15)',
        transition: 'all 0.5s ease-in-out'
      };
    }
    
    // 予想指数出力時のみ信頼度に応じた色を適用（currentRandomColorがnullの場合のみ）
    if ((currentConfidence === 'high' || currentConfidence === 'medium' || currentConfidence === 'low') && !currentRandomColor) {
      if (isColorChanging) {
        // 色変化中のアニメーション（よりスムーズに）
        const baseColor = DEFAULT_GREEN;
        
        const targetColor = CONFIDENCE_COLORS[currentConfidence as keyof typeof CONFIDENCE_COLORS];
        
        // より滑らかな色の変化
        return {
          background: colorChangeProgress > 0.3 ? targetColor.background : baseColor.background,
          boxShadow: colorChangeProgress > 0.3 ? targetColor.shadow : baseColor.shadow,
          transition: 'all 0.3s ease-in-out'
        };
      } else {
        // 色変化完了後
        const targetColor = CONFIDENCE_COLORS[currentConfidence as keyof typeof CONFIDENCE_COLORS];
        return {
          background: targetColor.background,
          boxShadow: targetColor.shadow,
          transition: 'all 0.5s ease-in-out'
        };
      }
    }
    
    // デフォルトはグリーン色（予想結果表示後は確実にここに戻る）
    return {
      background: DEFAULT_GREEN.background,
      boxShadow: DEFAULT_GREEN.shadow,
      transition: 'all 0.5s ease-in-out'
    };
  };

  const getPulseAnimation = () => {
    // 8条件選択時の縮小アニメーション（最優先）
    if (isShrinking) {
      return {
        scale: [1, 0.3, 0.1, 0.02],
      };
    }
    
    // 予想結果表示時の拡大アニメーション（8条件選択時以外）
    if (isExpanding && !isShrinking) {
      return {
        scale: [0.02, 2.0, 1.5, 1],
      };
    }
    
    // 球体に関する話題の場合は特別なアニメーション
    if (isOrbTopic) {
      return {
        scale: [1, 1.2, 0.9, 1.1, 1],
        y: [0, -20, 20, -10, 0],
      };
    }
    
    switch (pulseMode) {
      case 'racing':
        return {
          scale: [1, 1.3, 0.8, 1.2, 1],
        };
      case 'prediction':
        return {
          scale: [1, 1.4, 0.7, 1.3, 1],
        };
      case 'conditions':
        // 8条件選択時：高速縮小（より劇的に）
        return {
          scale: [1, 0.3, 0.1, 0.02],
        };
      case 'result':
        // 予想結果表示時：高速拡大（より劇的に）
        return {
          scale: [0.02, 2.0, 1.5, 1],
        };
      default:
        // 通常時：緩やかな伸び縮み
        return {
          scale: [1, 1.15, 1],
        };
    }
  };

  const getPulseTransition = () => {
    // 8条件選択時の高速縮小（より高速に）
    if (isShrinking) {
      return {
        duration: 0.6,
        repeat: 0,
        ease: "easeInOut",
      };
    }
    
    // 予想結果表示時の高速拡大（より高速に）
    if (isExpanding) {
      return {
        duration: 0.6,
        repeat: 0,
        ease: "easeInOut",
      };
    }
    
    // 球体に関する話題の場合は特別なトランジション
    if (isOrbTopic) {
      return {
        duration: 2.0,
        repeat: 1,
        ease: "easeInOut",
      };
    }
    
    switch (pulseMode) {
      case 'racing':
        // 競馬関連話題時：心臓のドキドキスピード
        return {
          duration: 1.2,
          repeat: 1,
          ease: "easeInOut",
        };
      case 'prediction':
        // 予想指数出力時：心臓のドキドキスピード
        return {
          duration: 1.5,
          repeat: 1,
          ease: "easeInOut",
        };
      case 'conditions':
        // 8条件選択時：高速縮小（より高速に）
        return {
          duration: 0.6,
          repeat: 0,
          ease: "easeInOut",
        };
      case 'result':
        // 予想結果表示時：高速拡大（より高速に）
        return {
          duration: 0.6,
          repeat: 0,
          ease: "easeInOut",
        };
      default:
        // 通常時：緩やかな伸び縮み
        return {
          duration: 6,
          repeat: Infinity,
          ease: "easeInOut",
        };
    }
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
          // console.log('🚀 アニメーション開始 - key:', orbAnimationKey);
        }}
        onAnimationComplete={() => {
          // console.log('✅ アニメーション完了 - key:', orbAnimationKey);
        }}
      />
    </div>
  );
}