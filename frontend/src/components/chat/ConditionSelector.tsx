import { useState } from 'react';
import { motion } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import { api } from '../../lib/api';

interface ConditionSelectorProps {
  onComplete: () => void;
}

const CONDITIONS = [
  { 
    id: '1_running_style', 
    name: '脚質', 
    description: '逃げ、先行、差し、追込の適性',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    selectedBgColor: 'bg-blue-100',
    selectedBorderColor: 'border-blue-500',
    hoverBgColor: 'hover:bg-blue-100'
  },
  { 
    id: '2_course_direction', 
    name: '右周り・左周り複勝率', 
    description: 'コース回り方向別成績',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    selectedBgColor: 'bg-green-100',
    selectedBorderColor: 'border-green-500',
    hoverBgColor: 'hover:bg-green-100'
  },
  { 
    id: '3_distance_category', 
    name: '距離毎複勝率', 
    description: '1000-1200m、1400m、1600m、1800-2000m、2200m、2000-2400m、2500m、2400-3000m、3000-3600m',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    selectedBgColor: 'bg-purple-100',
    selectedBorderColor: 'border-purple-500',
    hoverBgColor: 'hover:bg-purple-100'
  },
  { 
    id: '4_interval_category', 
    name: '出走間隔毎複勝率', 
    description: '連闘、中1、中2、中3-4、中5-8、中9-12、中13以上',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    selectedBgColor: 'bg-orange-100',
    selectedBorderColor: 'border-orange-500',
    hoverBgColor: 'hover:bg-orange-100'
  },
  { 
    id: '5_course_specific', 
    name: 'コース毎複勝率', 
    description: '競馬場・芝ダート・距離の組み合わせ',
    bgColor: 'bg-pink-50',
    borderColor: 'border-pink-200',
    selectedBgColor: 'bg-pink-100',
    selectedBorderColor: 'border-pink-500',
    hoverBgColor: 'hover:bg-pink-100'
  },
  { 
    id: '6_horse_count', 
    name: '出走頭数毎複勝率', 
    description: '7頭以下、8-12頭、13-16頭、16-17頭、16-18頭',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    selectedBgColor: 'bg-indigo-100',
    selectedBorderColor: 'border-indigo-500',
    hoverBgColor: 'hover:bg-indigo-100'
  },
  { 
    id: '7_track_condition', 
    name: '馬場毎複勝率', 
    description: '良、重、やや重、不良',
    bgColor: 'bg-teal-50',
    borderColor: 'border-teal-200',
    selectedBgColor: 'bg-teal-100',
    selectedBorderColor: 'border-teal-500',
    hoverBgColor: 'hover:bg-teal-100'
  },
  { 
    id: '8_season_category', 
    name: '季節毎複勝率', 
    description: '1-3月、4-6月、7-9月、10-12月',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    selectedBgColor: 'bg-yellow-100',
    selectedBorderColor: 'border-yellow-500',
    hoverBgColor: 'hover:bg-yellow-100'
  },
];

export default function ConditionSelector({ onComplete }: ConditionSelectorProps) {
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const { addMessage, setLoading, setSelectedConditions: setStoreSelectedConditions } = useChatStore();

  const handleConditionClick = (conditionId: string) => {
    if (selectedConditions.includes(conditionId)) {
      const newSelected = selectedConditions.filter(id => id !== conditionId);
      setSelectedConditions(newSelected);
      setStoreSelectedConditions(newSelected);
    } else if (selectedConditions.length < 4) {
      const newSelected = [...selectedConditions, conditionId];
      setSelectedConditions(newSelected);
      setStoreSelectedConditions(newSelected);
    }
  };

  const getPriorityLabel = (index: number) => {
    const labels = ['1位', '2位', '3位', '4位'];
    return labels[index] || '';
  };

  const getWeightPercentage = (index: number) => {
    const weights = [40, 30, 20, 10];
    return weights[index] || 0;
  };

  const getConfidenceText = (confidence: string) => {
    switch (confidence) {
      case 'high': return '高信頼度';
      case 'medium': return '中信頼度';
      case 'low': return '低信頼度';
      default: return '中信頼度';
    }
  };

  const handleConfirm = async () => {
    if (selectedConditions.length === 0) return;

    setLoading(true);
    addMessage({
      type: 'ai',
      content: '選択された条件で予想を実行しています...',
    });

    try {
      const response = await api.predict('sample_race', selectedConditions);
      
      // バックエンドから返された信頼度を使用
      const confidence = response.confidence || 'medium';
      
      // 予想結果のテキストを生成
      const resultText = `🏆 予想結果 (${getConfidenceText(confidence)})\n\n${response.horses.map((horse, index) => {
        const rank = index + 1;
        const score = horse.final_score || horse.base_score || 0;
        const rankEmoji = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `${rank}位`;
        return `${rankEmoji} ${horse.name} (指数: ${score.toFixed(1)}点)`;
      }).join('\n')}\n\n${response.analysis ? `\n📝 詳細解説:\n${response.analysis}` : ''}\n\n⏱️ 計算時間: ${new Date().toLocaleTimeString()}`;

      addMessage({
        type: 'ai',
        content: resultText,
        predictionResult: {
          ...response,
          confidence
        }
      });
    } catch (error) {
      console.error('Prediction error:', error);
      addMessage({
        type: 'ai',
        content: '予想の実行中にエラーが発生しました。もう一度お試しください。',
      });
    } finally {
      setLoading(false);
      onComplete();
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-4 sm:p-6 border border-gray-200">
      <h3 className="text-lg sm:text-xl font-bold text-gray-800 mb-4 sm:mb-6 text-center">
        予想条件を選択してください（最大4つ）
      </h3>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-3 mb-4 sm:mb-6">
        {CONDITIONS.map((condition) => {
          const isSelected = selectedConditions.includes(condition.id);
          const selectedIndex = selectedConditions.indexOf(condition.id);
          
          return (
            <motion.button
              key={condition.id}
              onClick={() => handleConditionClick(condition.id)}
              className={`p-3 sm:p-4 rounded-lg border-2 transition-all ${
                isSelected
                  ? `${condition.selectedBgColor} ${condition.selectedBorderColor} text-gray-800`
                  : `${condition.bgColor} ${condition.borderColor} text-gray-700 ${condition.hoverBgColor}`
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="text-center">
                <div className="flex items-center justify-center">
                  <h4 className="text-xs sm:text-sm font-bold leading-tight">{condition.name}</h4>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {selectedConditions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 sm:mb-6 p-3 sm:p-4 bg-blue-50 rounded-lg"
        >
          <h4 className="font-semibold text-blue-800 mb-2 text-sm sm:text-base">選択された条件:</h4>
          <div className="space-y-1 sm:space-y-2">
            {selectedConditions.map((conditionId, index) => {
              const condition = CONDITIONS.find(c => c.id === conditionId);
              return (
                <div key={conditionId} className="flex justify-between items-center">
                  <span className="text-blue-700 text-xs sm:text-sm">{condition?.name}</span>
                </div>
              );
            })}
          </div>
          <div className="mt-2 p-2 bg-green-50 rounded border border-green-200">
            <p className="text-xs text-green-700">
              📊 TFJV実データを使用した高精度予想
            </p>
          </div>
        </motion.div>
      )}

      <div className="flex justify-center">
        <motion.button
          onClick={handleConfirm}
          disabled={selectedConditions.length === 0}
          className={`px-6 py-3 rounded-lg font-semibold text-white transition-all ${
            selectedConditions.length === 0
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
          whileHover={selectedConditions.length > 0 ? { scale: 1.05 } : {}}
          whileTap={selectedConditions.length > 0 ? { scale: 0.95 } : {}}
        >
          予想実行
        </motion.button>
      </div>
    </div>
  );
}