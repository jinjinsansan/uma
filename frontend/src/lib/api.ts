import { Condition } from '../types/race';
import { ChatResponse } from '../types/chat';

export interface PredictionResult {
  horses: any[];
  confidence: 'high' | 'medium' | 'low';
  selectedConditions: string[];
  calculationTime: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  // 8条件の一覧取得
  async getConditions(): Promise<Condition[]> {
    const response = await fetch(`${API_BASE_URL}/conditions`);
    if (!response.ok) {
      throw new Error('Failed to fetch conditions');
    }
    return response.json();
  },

  // レース予想実行
  async predict(raceId: string, selectedConditions: string[]): Promise<PredictionResult> {
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
      throw new Error('Failed to predict race');
    }
    return response.json();
  },

  // チャットボット応答
  async chat(message: string, raceInfo?: string): Promise<ChatResponse> {
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
      throw new Error('Failed to get chat response');
    }
    return response.json();
  },
};