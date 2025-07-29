import { useState } from 'react';
import { motion } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import { Condition } from '../../types/race';

const CONDITIONS: Condition[] = [
  {
    id: '1_running_style',
    name: '脚質',
    description: '逃げ、先行、差し、追込の適性',
  },
  {
    id: '2_course_direction',
    name: '右周り・左周り複勝率',
    description: 'コース回り方向別成績',
  },
  {
    id: '3_distance_category',
    name: '距離毎複勝率',
    description: '1000-3600mの距離別成績',
  },
  {
    id: '4_interval_category',
    name: '出走間隔毎複勝率',
    description: '連闘、中1、中2、中3-4、中5-8、中9-12、中13以上',
  },
  {
    id: '5_course_specific',
    name: 'コース毎複勝率',
    description: '競馬場・芝ダート・距離の組み合わせ',
  },
  {
    id: '6_horse_count',
    name: '出走頭数毎複勝率',
    description: '7頭以下、8-12頭、13-16頭、16-17頭、16-18頭',
  },
  {
    id: '7_track_condition',
    name: '馬場毎複勝率',
    description: '良、重、やや重、不良',
  },
  {
    id: '8_season_category',
    name: '季節毎複勝率',
    description: '1-3月、4-6月、7-9月、10-12月',
  },
];

export default function ConditionSelector() {
  const { selectedConditions, setSelectedConditions } = useChatStore();
  const [selected, setSelected] = useState<string[]>([]);

  const handleConditionClick = (conditionId: string) => {
    if (selected.includes(conditionId)) {
      setSelected(selected.filter(id => id !== conditionId));
    } else if (selected.length < 4) {
      setSelected([...selected, conditionId]);
    }
  };

  const handleConfirm = () => {
    if (selected.length === 4) {
      setSelectedConditions(selected);
      // ここで予想処理を実行
    }
  };

  const getPriorityLabel = (conditionId: string) => {
    const index = selected.indexOf(conditionId);
    if (index === -1) return null;
    
    const labels = ['1st', '2nd', '3rd', '4th'];
    return labels[index];
  };

  return (
    <motion.div
      className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <h3 className="text-white text-lg font-semibold mb-4">
        8条件から4つを選択してください（優先順位付き）
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {CONDITIONS.map((condition) => {
          const isSelected = selected.includes(condition.id);
          const priority = getPriorityLabel(condition.id);
          
          return (
            <motion.button
              key={condition.id}
              onClick={() => handleConditionClick(condition.id)}
              className={`p-3 rounded-lg text-left transition-all ${
                isSelected
                  ? 'bg-blue-500 text-white'
                  : 'bg-white/5 text-white hover:bg-white/10'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm">{condition.name}</div>
                  <div className="text-xs opacity-70">{condition.description}</div>
                </div>
                {priority && (
                  <div className="bg-white/20 px-2 py-1 rounded text-xs font-bold">
                    {priority}
                  </div>
                )}
              </div>
            </motion.button>
          );
        })}
      </div>

      <div className="flex justify-between items-center">
        <div className="text-white/70 text-sm">
          選択済み: {selected.length}/4
        </div>
        
        <motion.button
          onClick={handleConfirm}
          disabled={selected.length !== 4}
          className={`px-6 py-2 rounded-lg font-semibold ${
            selected.length === 4
              ? 'bg-green-500 text-white hover:bg-green-400'
              : 'bg-gray-500 text-gray-300 cursor-not-allowed'
          }`}
          whileHover={selected.length === 4 ? { scale: 1.05 } : {}}
          whileTap={selected.length === 4 ? { scale: 0.95 } : {}}
        >
          予想実行
        </motion.button>
      </div>
    </motion.div>
  );
}