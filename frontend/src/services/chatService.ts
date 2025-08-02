/**
 * チャットサービス
 * OpenAI統合チャット機能
 */

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatResponse {
  status: string;
  message: string;
  has_d_logic?: boolean;
  race_info?: any;
  d_logic_result?: any;
  matching_races?: any[];
}

export class ChatService {
  private static readonly API_BASE_URL = 'http://localhost:8002/api';

  /**
   * チャットメッセージを送信
   */
  static async sendMessage(message: string, history: ChatMessage[] = []): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          history: history.map(msg => ({
            role: msg.role,
            content: msg.content
          }))
        }),
      });

      if (!response.ok) {
        throw new Error(`チャットAPIエラー: ${response.status}`);
      }

      const result: ChatResponse = await response.json();
      return result;
    } catch (error) {
      console.error('チャット送信エラー:', error);
      return {
        status: 'error',
        message: '申し訳ございません。チャット処理中にエラーが発生しました。',
        has_d_logic: false
      };
    }
  }

  /**
   * レース関連のメッセージかどうかを判定
   */
  static isRaceRelatedMessage(message: string): boolean {
    const raceKeywords = [
      '指数', 'Dロジック', 'レース', '東京', '京都', '阪神', '中山', '新潟',
      '福島', '小倉', '札幌', '函館', '中京', '金沢', '佐賀', '門別',
      '1R', '2R', '3R', '4R', '5R', '6R', '7R', '8R', '9R', '10R', '11R', '12R'
    ];
    
    return raceKeywords.some(keyword => message.includes(keyword));
  }

  /**
   * Dロジック計算リクエストかどうかを判定
   */
  static isDLogicRequest(message: string): boolean {
    const dLogicKeywords = [
      'Dロジック', 'Dロジックで', '指数を出して', '指数計算', 'ダンスインザダーク'
    ];
    
    return dLogicKeywords.some(keyword => message.includes(keyword));
  }

  /**
   * メッセージの種類を判定
   */
  static getMessageType(message: string): 'race_request' | 'd_logic_request' | 'general' {
    if (this.isDLogicRequest(message)) {
      return 'd_logic_request';
    } else if (this.isRaceRelatedMessage(message)) {
      return 'race_request';
    } else {
      return 'general';
    }
  }
} 