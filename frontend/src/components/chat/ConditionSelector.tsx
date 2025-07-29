import { useState } from 'react';
import { motion } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import { api } from '../../lib/api';

interface ConditionSelectorProps {
  onComplete: () => void;
}

const CONDITIONS = [
  { id: '1_running_style', name: '脚質', description: '逃げ、先行、差し、追込の適性' },
  { id: '2_course_direction', name: '右周り・左周り複勝率', description: 'コース回り方向別成績' },
  { id: '3_distance_category', name: '距離毎複勝率', description: '1000-1200m、1400m、1600m、1800-2000m、2200m、2000-2400m、2500m、2400-3000m、3000-3600m' },
  { id: '4_interval_category', name: '出走間隔毎複勝率', description: '連闘、中1、中2、中3-4、中5-8、中9-12、中13以上' },
  { id: '5_course_specific', name: 'コース毎複勝率', description: '競馬場・芝ダート・距離の組み合わせ' },
  { id: '6_horse_count', name: '出走頭数毎複勝率', description: '7頭以下、8-12頭、13-16頭、16-17頭、16-18頭' },
  { id: '7_track_condition', name: '馬場毎複勝率', description: '良、重、やや重、不良' },
  { id: '8_season_category', name: '季節毎複勝率', description: '1-3月、4-6月、7-9月、10-12月' },
];

export default function ConditionSelector({ onComplete }: ConditionSelectorProps) {
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const { addMessage, setLoading } = useChatStore();

  const handleConditionClick = (conditionId: string) => {
    if (selectedConditions.includes(conditionId)) {
      setSelectedConditions(selectedConditions.filter(id => id !== conditionId));
    } else if (selectedConditions.length < 4) {
      setSelectedConditions([...selectedConditions, conditionId]);
    }
  };

  const getPriorityLabel = (index: number) => {
    const labels = ['1st', '2nd', '3rd', '4th'];
    return labels[index];
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
      
      // 予想指数に基づいて信頼度を決定
      const avgScore = response.horses.reduce((sum, horse) => 
        sum + (horse.finalScore || horse.baseScore), 0) / response.horses.length;
      
      let confidence: 'high' | 'medium' | 'low';
      if (avgScore >= 80) {
        confidence = 'high';
      } else if (avgScore >= 60) {
        confidence = 'medium';
      } else {
        confidence = 'low';
      }
      
      const resultText = `予想結果:\n${response.horses.map((horse, index) => 
        `${index + 1}位: ${horse.name} (指数: ${horse.finalScore || horse.baseScore})`
      ).join('\n')}`;

      addMessage({
        type: 'ai',
        content: resultText,
        predictionResult: {
          ...response,
          confidence
        }
      });
    } catch (error) {
      addMessage({
        type: 'ai',
        content: '予想の実行中にエラーが発生しました。',
      });
    } finally {
      setLoading(false);
      onComplete();
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-200">
      <h3 className="text-xl font-bold text-gray-800 mb-4 text-center">
        予想条件を選択してください（最大4つ）
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {CONDITIONS.map((condition) => {
          const isSelected = selectedConditions.includes(condition.id);
          const selectedIndex = selectedConditions.indexOf(condition.id);
          
          return (
            <motion.button
              key={condition.id}
              onClick={() => handleConditionClick(condition.id)}
              className={`p-4 rounded-xl border-2 transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 text-blue-800'
                  : 'border-gray-200 bg-gray-50 text-gray-700 hover:border-gray-300 hover:bg-gray-100'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="text-left">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">{condition.name}</h4>
                  {isSelected && (
                    <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full">
                      {getPriorityLabel(selectedIndex)}
                    </span>
                  )}
                </div>
                <p className="text-sm opacity-75">{condition.description}</p>
              </div>
            </motion.button>
          );
        })}
      </div>

      <div className="flex justify-center">
        <motion.button
          onClick={handleConfirm}
          disabled={selectedConditions.length === 0}
          className="px-8 py-3 bg-blue-600 text-white rounded-full font-semibold disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          予想実行
        </motion.button>
      </div>
    </div>
  );
}