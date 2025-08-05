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
        // テスト用：認証済みユーザーには常に表示（開発時のみ）
        console.log('LINE popup check - authenticated user:', session.user.email);
        
        // ローカルストレージで表示履歴をチェック
        const lastShownKey = `line_popup_last_shown_${session.user.email}`;
        const lastShown = typeof window !== 'undefined' ? localStorage.getItem(lastShownKey) : null;
        
        // テスト用：常に表示（24時間制限を無視）
        console.log('Showing LINE popup after', delaySeconds, 'seconds');
        
        // 指定秒数後にポップアップ表示
        setTimeout(() => {
          setShouldShowPopup(true);
        }, delaySeconds * 1000);
      } catch (error) {
        console.error('LINE友達追加ポップアップ判定エラー:', error);
        // エラーが発生してもポップアップは表示する（テスト用）
        setTimeout(() => {
          setShouldShowPopup(true);
        }, delaySeconds * 1000);
      }
    };

    checkAndShowPopup();
  }, [session, status, delaySeconds, reshowHours]);

  const hidePopup = () => {
    setShouldShowPopup(false);
    
    // 表示履歴をローカルストレージに保存
    if (session?.user?.email && typeof window !== 'undefined') {
      const lastShownKey = `line_popup_last_shown_${session.user.email}`;
      localStorage.setItem(lastShownKey, new Date().toISOString());
    }
  };

  const onTicketClaimed = () => {
    setShouldShowPopup(false);
    
    // チケット獲得済みフラグを設定（今後表示しない）
    if (session?.user?.email && typeof window !== 'undefined') {
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