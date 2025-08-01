/**
 * Dロジック連携サービス
 * ダンスインザダーク基準100点の指数計算APIとの連携
 */

export interface DLogicCalculationRequest {
  race_code: string;
  race_data: any;
  calculation_type?: string;
}

export interface DLogicCalculationResult {
  race_code: string;
  calculation_time: string;
  horses: Array<{
    horse_id: string;
    horse_name: string;
    d_logic_score: number;
    base_horse: string;
  }>;
  base_horse: string;
  base_score: number;
  status: string;
  message: string;
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
   * Dロジック計算実行
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
} 