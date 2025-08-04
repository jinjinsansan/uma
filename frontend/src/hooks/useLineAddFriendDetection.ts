import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { UserService } from '@/services/userService';

interface UseLineAddFriendDetectionOptions {
  // ユーザーがログインしてから何秒後にポップアップを表示するか
  delaySeconds?: number;
  // 一度閉じた後、何時間後に再表示するか
  reshowHours?: number;
}

export function useLineAddFriendDetection(options: UseLineAddFriendDetectionOptions = {}) {
  const { delaySeconds = 30, reshowHours = 24 } = options;
  const { data: session, status } = useSession();
  const [shouldShowPopup, setShouldShowPopup] = useState(false);
  const [userQuota, setUserQuota] = useState<any>(null);

  useEffect(() => {
    if (status !== 'authenticated' || !session?.user) return;

    const checkAndShowPopup = async () => {
      try {
        // ローカルストレージで表示履歴をチェック
        const lastShownKey = `line_popup_last_shown_${session.user.email}`;
        const lastShown = localStorage.getItem(lastShownKey);
        
        if (lastShown) {
          const lastShownTime = new Date(lastShown);
          const now = new Date();
          const hoursSinceLastShow = (now.getTime() - lastShownTime.getTime()) / (1000 * 60 * 60);
          
          if (hoursSinceLastShow < reshowHours) {
            return; // まだ再表示時間に達していない
          }
        }

        // ユーザーの使用制限情報を取得
        const userId = 1; // 実際はセッションから取得
        const quota = await UserService.checkUserQuota(userId);
        setUserQuota(quota);

        // 無料トライアル中かつLINE友達追加していない場合のみ表示
        if (quota.subscription_status === 'free_trial') {
          // LINE友達追加済みかチェック（実際のAPIで確認）
          const hasLineTicket = false; // 実際はAPIで確認
          
          if (!hasLineTicket) {
            // 指定秒数後にポップアップ表示
            setTimeout(() => {
              setShouldShowPopup(true);
            }, delaySeconds * 1000);
          }
        }
      } catch (error) {
        console.error('LINE友達追加ポップアップ判定エラー:', error);
      }
    };

    checkAndShowPopup();
  }, [session, status, delaySeconds, reshowHours]);

  const hidePopup = () => {
    setShouldShowPopup(false);
    
    // 表示履歴をローカルストレージに保存
    if (session?.user?.email) {
      const lastShownKey = `line_popup_last_shown_${session.user.email}`;
      localStorage.setItem(lastShownKey, new Date().toISOString());
    }
  };

  const onTicketClaimed = () => {
    setShouldShowPopup(false);
    
    // チケット獲得済みフラグを設定（今後表示しない）
    if (session?.user?.email) {
      const claimedKey = `line_ticket_claimed_${session.user.email}`;
      localStorage.setItem(claimedKey, 'true');
    }
  };

  return {
    shouldShowPopup,
    hidePopup,
    onTicketClaimed,
    userQuota
  };
}