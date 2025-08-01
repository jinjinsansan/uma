'use client';

import React from 'react';
import { DLogicCalculationResult, DLogicService } from '../../services/dLogicService';

interface DLogicResultDisplayProps {
  result: DLogicCalculationResult;
  onClose?: () => void;
}

const DLogicResultDisplay: React.FC<DLogicResultDisplayProps> = ({ result, onClose }) => {
  if (!result || !result.horses) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-lg">
        <div className="text-center text-gray-500">
          <div className="text-2xl mb-2">📊</div>
          <p>Dロジック計算結果がありません</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg max-w-4xl mx-auto">
      {/* ヘッダー */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-800">
            Dロジック分析結果
          </h2>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          )}
        </div>
        
        {/* 計算概要 */}
        <div className="bg-blue-50 p-4 rounded-lg mb-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="font-semibold text-blue-800">計算方法</div>
              <div className="text-blue-600">{result.calculation_method}</div>
            </div>
            <div>
              <div className="font-semibold text-blue-800">基準馬</div>
              <div className="text-blue-600">{result.base_horse}</div>
            </div>
            <div>
              <div className="font-semibold text-blue-800">基準スコア</div>
              <div className="text-blue-600">{result.base_score}点</div>
            </div>
            <div>
              <div className="font-semibold text-blue-800">評価項目</div>
              <div className="text-blue-600">{result.sql_data_utilization}</div>
            </div>
          </div>
        </div>

        {/* 統計サマリー */}
        <div className="bg-green-50 p-4 rounded-lg mb-6">
          <h3 className="font-semibold text-green-800 mb-2">レース統計</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="font-medium text-green-700">出走頭数</div>
              <div className="text-green-600">{result.calculation_summary.total_horses}頭</div>
            </div>
            <div>
              <div className="font-medium text-green-700">平均スコア</div>
              <div className="text-green-600">{result.calculation_summary.average_score.toFixed(1)}点</div>
            </div>
            <div>
              <div className="font-medium text-green-700">最高スコア</div>
              <div className="text-green-600">{result.calculation_summary.top_score.toFixed(1)}点</div>
            </div>
            <div>
              <div className="font-medium text-green-700">最低スコア</div>
              <div className="text-green-600">{result.calculation_summary.bottom_score.toFixed(1)}点</div>
            </div>
          </div>
        </div>
      </div>

      {/* 馬別結果 */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">馬別Dロジック指数</h3>
        
        {result.horses.map((horse, index) => (
          <div key={horse.horse_id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
                  index === 0 ? 'bg-yellow-500' : 
                  index === 1 ? 'bg-gray-400' : 
                  index === 2 ? 'bg-orange-500' : 'bg-gray-300'
                }`}>
                  {index + 1}
                </div>
                <div>
                  <div className="font-semibold text-gray-800">{horse.horse_name}</div>
                  <div className="text-sm text-gray-500">ID: {horse.horse_id}</div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {horse.d_logic_score.toFixed(1)}点
                </div>
                <div className="text-sm text-gray-500">
                  {DLogicService.getScoreLevel(horse.d_logic_score)}
                </div>
              </div>
            </div>

            {/* 詳細スコア */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
              {Object.entries(horse.detailed_analysis.detailed_scores).map(([key, score]) => (
                <div key={key} className="text-center p-2 bg-gray-50 rounded">
                  <div className="text-xs text-gray-600 mb-1">
                    {key === 'basic_ability' ? '基本能力' :
                     key === 'environment_adaptation' ? '環境適応' :
                     key === 'human_factors' ? '人的要因' :
                     key === 'bloodline_physique' ? '血統・体質' :
                     key === 'racing_style' ? '競走スタイル' : key}
                  </div>
                  <div className="font-semibold text-gray-800">{score.toFixed(1)}</div>
                  <div className="text-xs text-gray-500">
                    {DLogicService.getDetailedScoreLevel(score)}
                  </div>
                </div>
              ))}
            </div>

            {/* SQL分析結果 */}
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-sm font-medium text-blue-800 mb-2">SQL分析結果</div>
              <div className="text-sm text-blue-700">
                {DLogicService.generateSQLAnalysisSummary(horse.detailed_analysis.sql_analysis)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 計算詳細 */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-semibold text-gray-800 mb-2">計算詳細</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <div>• 計算方法: {result.horses[0]?.detailed_analysis.calculation_details.calculation_method}</div>
          <div>• 基準馬: {result.horses[0]?.detailed_analysis.calculation_details.base_horse}</div>
          <div>• 基準スコア: {result.horses[0]?.detailed_analysis.calculation_details.base_score}点</div>
          <div>• SQL活用: {result.horses[0]?.detailed_analysis.calculation_details.sql_data_utilization}</div>
        </div>
      </div>
    </div>
  );
};

export default DLogicResultDisplay; 