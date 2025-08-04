/**
 * ユーザー管理サービス
 * Google OAuth認証後のユーザー情報管理
 */

export interface User {
  id: number;
  google_id: string;
  email: string;
  name: string;
  image_url?: string;
  subscription_type: 'free' | 'premium';
  total_queries_used: number;
  free_trial_end_date?: string;
  premium_end_date?: string;
  daily_queries_remaining: number;
}

export interface UserQuota {
  can_use: boolean;
  subscription_status: 'free_trial' | 'premium' | 'expired';
  daily_remaining: number;
  today_usage: number;
  free_trial_end?: string;
  premium_end?: string;
}

export interface QueryUsage {
  user_id: number;
  query_type: 'horse_analysis' | 'race_analysis' | 'general_chat';
  query_text: string;
  response_text: string;
  processing_time_ms: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class UserService {
  /**
   * ユーザー登録/取得
   */
  static async registerOrGetUser(userData: {
    google_id: string;
    email: string;
    name: string;
    image_url?: string;
  }): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/users/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      throw new Error(`ユーザー登録に失敗しました: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * ユーザー情報取得
   */
  static async getUserInfo(userId: number): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/users/info/${userId}`);

    if (!response.ok) {
      throw new Error(`ユーザー情報の取得に失敗しました: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 使用制限チェック
   */
  static async checkUserQuota(userId: number): Promise<UserQuota> {
    const response = await fetch(`${API_BASE_URL}/api/users/quota/${userId}`);

    if (!response.ok) {
      throw new Error(`使用制限の確認に失敗しました: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 使用回数消費
   */
  static async useQuota(queryData: QueryUsage): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/use-quota`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(queryData),
    });

    if (!response.ok) {
      throw new Error(`使用回数の記録に失敗しました: ${response.statusText}`);
    }
  }

  /**
   * LINE友達追加で延長チケット追加
   */
  static async addLineTicket(userId: number, lineUserId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/line/add-ticket/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ line_user_id: lineUserId }),
    });

    if (!response.ok) {
      throw new Error(`LINE延長チケットの追加に失敗しました: ${response.statusText}`);
    }
  }

  /**
   * 残り使用回数をフォーマット
   */
  static formatRemainingQueries(quota: UserQuota): string {
    if (quota.subscription_status === 'premium') {
      return '無制限';
    } else if (quota.subscription_status === 'free_trial') {
      return `${quota.daily_remaining}回/日`;
    } else {
      return 'トライアル期間終了';
    }
  }

  /**
   * サブスクリプション状態をフォーマット
   */
  static formatSubscriptionStatus(quota: UserQuota): string {
    switch (quota.subscription_status) {
      case 'premium':
        return 'プレミアム会員';
      case 'free_trial':
        return '無料トライアル中';
      case 'expired':
        return 'トライアル期間終了';
      default:
        return '不明';
    }
  }

  /**
   * トライアル終了日をフォーマット
   */
  static formatTrialEndDate(endDate?: string): string {
    if (!endDate) return '不明';
    
    const date = new Date(endDate);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays <= 0) {
      return '期間終了';
    } else if (diffDays === 1) {
      return '明日まで';
    } else {
      return `あと${diffDays}日`;
    }
  }
}