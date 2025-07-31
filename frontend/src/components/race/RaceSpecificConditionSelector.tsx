import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trophy, MapPin, Calendar, Clock } from 'lucide-react';
import RaceAnimatedOrb from './RaceAnimatedOrb';
import { ConfidenceLevel } from '../../types/race';

interface Race {
  race_code: string;
  kaisai_nen: string;
  kaisai_gappi: string;
  keibajo_code: string;
  keibajo_name: string;
  race_bango: string;
  kyosomei_hondai: string;
  kyori: string;
  track_code: string;
  hasso_jikoku: string;
  shusso_tosu: string;
  formatted_date: string;
  formatted_time: string;
}

interface RaceSpecificConditionSelectorProps {
  selectedRace: Race;
  onBack: () => void;
}

// 8条件の定義（既存システムと同じ）
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

export default function RaceSpecificConditionSelector({ selectedRace, onBack }: RaceSpecificConditionSelectorProps) {
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConditionsSelected, setIsConditionsSelected] = useState(false);
  const [isPredictionResult, setIsPredictionResult] = useState(false);
  const [lastMessage, setLastMessage] = useState('');

  // 球体アニメーション用の状態
  const [confidence, setConfidence] = useState<ConfidenceLevel>('waiting');

  // 条件選択の処理
  const handleConditionClick = (conditionId: string) => {
    if (selectedConditions.includes(conditionId)) {
      const newSelected = selectedConditions.filter(id => id !== conditionId);
      setSelectedConditions(newSelected);
    } else if (selectedConditions.length < 4) {
      setSelectedConditions([...selectedConditions, conditionId]);
    }
  };

  // 4条件選択完了時のアニメーション
  useEffect(() => {
    if (selectedConditions.length === 4) {
      setIsConditionsSelected(true);
      
      // 0.6秒後にアニメーション完了
      setTimeout(() => {
        setIsConditionsSelected(false);
      }, 600);
    } else {
      setIsConditionsSelected(false);
    }
  }, [selectedConditions]);

  // 予想実行の処理
  const handlePrediction = async () => {
    if (selectedConditions.length !== 4) return;

    setIsLoading(true);
    setConfidence('processing');

    try {
      // 予想処理のシミュレーション（実際のAPI呼び出しは後で実装）
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 予想結果の表示
      setIsPredictionResult(true);
      setConfidence('medium'); // 仮の信頼度
      setLastMessage(`選択されたレース「${selectedRace.kyosomei_hondai}」で予想を実行しました。`);
      
      // 10秒後にアニメーション完了
      setTimeout(() => {
        setIsPredictionResult(false);
        setConfidence('waiting');
      }, 10000);
      
    } catch (error) {
      console.error('Prediction error:', error);
      setConfidence('waiting');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 relative">
      {/* 球体アニメーション */}
      <div className="fixed bottom-4 right-4 z-10">
        <RaceAnimatedOrb
          confidence={confidence}
          isProcessing={isLoading}
          lastMessage={lastMessage}
          isConditionsSelected={isConditionsSelected}
          isPredictionResult={isPredictionResult}
        />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-800 transition-colors mb-4"
          >
            <span className="mr-2">←</span>
            レース選択に戻る
          </button>
          
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex items-center mb-4">
              <Trophy className="w-6 h-6 text-yellow-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-800">
                レース専用8条件選択
              </h1>
            </div>
            
            {/* レース情報 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center">
                <MapPin className="w-5 h-5 text-gray-500 mr-2" />
                <span className="text-gray-700">{selectedRace.keibajo_name}</span>
              </div>
              <div className="flex items-center">
                <Calendar className="w-5 h-5 text-gray-500 mr-2" />
                <span className="text-gray-700">{selectedRace.formatted_date}</span>
              </div>
              <div className="flex items-center">
                <Clock className="w-5 h-5 text-gray-500 mr-2" />
                <span className="text-gray-700">{selectedRace.formatted_time}</span>
              </div>
              <div className="flex items-center">
                <span className="text-gray-700 font-medium">{selectedRace.kyori}m</span>
              </div>
            </div>
            
            <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
              <h2 className="font-bold text-yellow-800 text-lg mb-2">
                {selectedRace.kyosomei_hondai}
              </h2>
              <p className="text-yellow-700 text-sm">
                このレースで8条件を使った予想を体験しましょう
              </p>
            </div>
          </div>
        </div>

        {/* 8条件選択エリア */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-6 text-center">
            予想条件を選択してください（最大4つ）
          </h3>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-6">
            {CONDITIONS.map((condition) => {
              const isSelected = selectedConditions.includes(condition.id);
              const selectedIndex = selectedConditions.indexOf(condition.id);
              
              return (
                <motion.button
                  key={condition.id}
                  onClick={() => handleConditionClick(condition.id)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    isSelected
                      ? `${condition.selectedBgColor} ${condition.selectedBorderColor} text-gray-800`
                      : `${condition.bgColor} ${condition.borderColor} text-gray-700 ${condition.hoverBgColor}`
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="text-center">
                    {isSelected && (
                      <div className="absolute -top-2 -right-2 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                        {selectedIndex + 1}
                      </div>
                    )}
                    <h4 className="text-sm font-bold leading-tight">{condition.name}</h4>
                    <p className="text-xs text-gray-600 mt-1">{condition.description}</p>
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* 選択された条件の表示 */}
          {selectedConditions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-blue-50 rounded-lg"
            >
              <h4 className="font-semibold text-blue-800 mb-3">選択された条件:</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {selectedConditions.map((conditionId, index) => {
                  const condition = CONDITIONS.find(c => c.id === conditionId);
                  return (
                    <div key={conditionId} className="flex items-center">
                      <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-2">
                        {index + 1}
                      </span>
                      <span className="text-blue-700 text-sm">{condition?.name}</span>
                    </div>
                  );
                })}
              </div>
              <div className="mt-3 p-2 bg-green-50 rounded border border-green-200">
                <p className="text-xs text-green-700">
                  📊 TFJV実データを使用した高精度予想
                </p>
              </div>
            </motion.div>
          )}

          {/* 予想実行ボタン */}
          <div className="flex justify-center">
            <motion.button
              onClick={handlePrediction}
              disabled={selectedConditions.length !== 4 || isLoading}
              className={`px-8 py-4 rounded-lg font-semibold text-white transition-all ${
                selectedConditions.length !== 4 || isLoading
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
              whileHover={selectedConditions.length === 4 && !isLoading ? { scale: 1.05 } : {}}
              whileTap={selectedConditions.length === 4 && !isLoading ? { scale: 0.95 } : {}}
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                  予想実行中...
                </div>
              ) : (
                '予想実行'
              )}
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
} 