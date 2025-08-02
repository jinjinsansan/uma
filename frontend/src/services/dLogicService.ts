/**
 * Dロジック連携サービス
 * ダンスインザダーク基準100点の指数計算APIとの連携
 * 多次元Dロジック計算エンジン対応
 */

export interface DLogicCalculationRequest {
  race_code: string;
  race_data: any;
  calculation_type?: string;
}

export interface DLogicDetailedScore {
  basic_ability: number;
  environment_adaptation: number;
  human_factors: number;
  bloodline_physique: number;
  racing_style: number;
}

export interface DLogicSQLAnalysis {
  distance_analysis: {
    score: number;
    description: string;
    sql_fields_used: string[];
  };
  track_condition_analysis: {
    score: number;
    description: string;
    sql_fields_used: string[];
  };
  weather_analysis: {
    score: number;
    description: string;
    sql_fields_used: string[];
  };
  jockey_compatibility: {
    score: number;
    description: string;
    sql_fields_used: string[];
  };
  bloodline_evaluation: {
    score: number;
    description: string;
    sql_fields_used: string[];
  };
}

export interface DLogicCalculationResult {
  race_code: string;
  calculation_time: string;
  horses: Array<{
    horse_id: string;
    horse_name: string;
    d_logic_score: number;
    detailed_analysis: {
      total_score: number;
      base_score: number;
      detailed_scores: DLogicDetailedScore;
      sql_analysis: DLogicSQLAnalysis;
      calculation_details: {
        calculation_method: string;
        base_horse: string;
        base_score: number;
        sql_data_utilization: string;
        weight_distribution: any;
      };
    };
  }>;
  calculation_method: string;
  base_horse: string;
  base_score: number;
  sql_data_utilization: string;
  calculation_summary: {
    total_horses: number;
    average_score: number;
    top_score: number;
    bottom_score: number;
  };
  status: string;
  message: string;
}

export interface KnowledgeBaseData {
  dance_in_the_dark_data: any;
  sql_evaluation_criteria: any;
  d_logic_weights: any;
}

export class DLogicService {
  private static readonly API_BASE_URL = 'http://localhost:8000/api/d-logic';

  /**
   * Dロジック計算APIの健全性チェック
   */
  static async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/health`);
      return response.ok;
    } catch (error) {
      console.error('DロジックAPI健全性チェックエラー:', error);
      return false;
    }
  }

  /**
   * 多次元Dロジック計算実行
   */
  static async calculateDLogic(request: DLogicCalculationRequest): Promise<DLogicCalculationResult> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Dロジック計算APIエラー: ${response.status}`);
      }

      const result = await response.json();
      return result as DLogicCalculationResult;
    } catch (error) {
      console.error('Dロジック計算エラー:', error);
      throw error;
    }
  }

  /**
   * ダンスインザダーク基準100点の指数計算
   */
  static async calculateDanceInTheDarkBased(request: DLogicCalculationRequest): Promise<DLogicCalculationResult> {
    const dLogicRequest = {
      ...request,
      calculation_type: 'dance_in_the_dark_based'
    };
    return this.calculateDLogic(dLogicRequest);
  }

  /**
   * ナレッジベース情報取得
   */
  static async getKnowledgeBase(): Promise<KnowledgeBaseData> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/knowledge-base`);
      
      if (!response.ok) {
        throw new Error(`ナレッジベース取得APIエラー: ${response.status}`);
      }

      const result = await response.json();
      return result.knowledge_base as KnowledgeBaseData;
    } catch (error) {
      console.error('ナレッジベース取得エラー:', error);
      throw error;
    }
  }

  /**
   * 単一馬の詳細分析
   */
  static async analyzeSingleHorse(horseData: any): Promise<any> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/analyze-horse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(horseData),
      });

      if (!response.ok) {
        throw new Error(`単一馬分析APIエラー: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('単一馬分析エラー:', error);
      throw error;
    }
  }

  /**
   * Dロジックスコアの評価レベル取得
   */
  static getScoreLevel(score: number): string {
    if (score >= 90) return 'S級';
    if (score >= 80) return 'A級';
    if (score >= 70) return 'B級';
    if (score >= 60) return 'C級';
    return 'D級';
  }

  /**
   * 詳細スコアの評価レベル取得
   */
  static getDetailedScoreLevel(score: number): string {
    if (score >= 90) return '優秀';
    if (score >= 80) return '良好';
    if (score >= 70) return '普通';
    if (score >= 60) return '要注意';
    return '危険';
  }

  /**
   * SQL分析結果の要約生成
   */
  static generateSQLAnalysisSummary(sqlAnalysis: DLogicSQLAnalysis): string {
    const analyses = [
      { name: '距離適性', score: sqlAnalysis.distance_analysis.score, desc: sqlAnalysis.distance_analysis.description },
      { name: '馬場適性', score: sqlAnalysis.track_condition_analysis.score, desc: sqlAnalysis.track_condition_analysis.description },
      { name: '天候適性', score: sqlAnalysis.weather_analysis.score, desc: sqlAnalysis.weather_analysis.description },
      { name: '騎手相性', score: sqlAnalysis.jockey_compatibility.score, desc: sqlAnalysis.jockey_compatibility.description },
      { name: '血統評価', score: sqlAnalysis.bloodline_evaluation.score, desc: sqlAnalysis.bloodline_evaluation.description }
    ];

    const strengths = analyses.filter(a => a.score >= 85).map(a => a.name);
    const weaknesses = analyses.filter(a => a.score < 70).map(a => a.name);

    let summary = '';
    if (strengths.length > 0) {
      summary += `強み: ${strengths.join(', ')}。`;
    }
    if (weaknesses.length > 0) {
      summary += `課題: ${weaknesses.join(', ')}。`;
    }
    if (summary === '') {
      summary = 'バランスの取れた能力分布です。';
    }

    return summary;
  }
} 