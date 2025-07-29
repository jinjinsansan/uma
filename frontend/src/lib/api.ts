import { Condition } from '../types/race';
import { ChatResponse } from '../types/chat';

export interface PredictionResult {
  horses: any[];
  confidence: 'high' | 'medium' | 'low';
  selectedConditions: string[];
  calculationTime: string;
  analysis?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://uma-i30n.onrender.com';

// エラーメッセージを生成する関数
const createErrorMessage = (error: any, endpoint: string): string => {
  console.error(`API Error (${endpoint}):`, error);
  
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    return `バックエンドサーバーに接続できません。サーバーが起動しているか確認してください。`;
  }
  
  if (error.message.includes('Failed to fetch')) {
    return `ネットワークエラーが発生しました。インターネット接続を確認してください。`;
  }
  
  if (error.status === 404) {
    return `APIエンドポイントが見つかりません。`;
  }
  
  if (error.status === 500) {
    return `サーバー内部エラーが発生しました。`;
  }
  
  return `エラーが発生しました: ${error.message || '不明なエラー'}`;
};

export const api = {
  // 8条件の一覧取得
  async getConditions(): Promise<Condition[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/conditions`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      throw new Error(createErrorMessage(error, 'getConditions'));
    }
  },

  // レース予想実行
  async predict(raceId: string, selectedConditions: string[]): Promise<PredictionResult> {
    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          race_id: raceId,
          selected_conditions: selectedConditions,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      throw new Error(createErrorMessage(error, 'predict'));
    }
  },

  // チャットボット応答
  async chat(message: string, raceInfo?: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          race_info: raceInfo,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      throw new Error(createErrorMessage(error, 'chat'));
    }
  },

  // バックエンドサーバーの状態確認
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  },
};