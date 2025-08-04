'use client';

import { useSession, signIn, signOut } from 'next-auth/react';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { UserService, type User, type UserQuota } from '@/services/userService';

export default function AuthButton() {
  const { data: session, status } = useSession();
  const [user, setUser] = useState<User | null>(null);
  const [quota, setQuota] = useState<UserQuota | null>(null);

  // Google OAuth認証成功後にユーザー登録/取得
  useEffect(() => {
    if (session?.user) {
      const registerUser = async () => {
        try {
          const userData = await UserService.registerOrGetUser({
            google_id: session.user.email || '', // セッションにはgoogle_idがないためemailを使用
            email: session.user.email || '',
            name: session.user.name || '',
            image_url: session.user.image || undefined,
          });
          setUser(userData);
          
          // 使用制限情報も取得
          const quotaData = await UserService.checkUserQuota(userData.id);
          setQuota(quotaData);
        } catch (error) {
          console.error('ユーザー登録/取得エラー:', error);
        }
      };
      
      registerUser();
    }
  }, [session]);

  if (status === 'loading') {
    return (
      <div className="bg-gray-700 px-4 py-2 rounded-lg">
        <div className="animate-pulse h-4 w-16 bg-gray-600 rounded"></div>
      </div>
    );
  }

  if (session) {
    return (
      <div className="flex items-center space-x-3">
        {session.user?.image && (
          <img
            src={session.user.image}
            alt="プロフィール"
            className="w-8 h-8 rounded-full border border-gray-600"
          />
        )}
        <div className="flex flex-col">
          <span className="text-white text-sm">
            {session.user?.name || session.user?.email}
          </span>
          {quota && (
            <div className="flex items-center space-x-2 text-xs">
              <span className={`${
                quota.subscription_status === 'premium' ? 'text-yellow-400' :
                quota.subscription_status === 'free_trial' ? 'text-green-400' :
                'text-red-400'
              }`}>
                {UserService.formatSubscriptionStatus(quota)}
              </span>
              <span className="text-gray-400">
                残り: {UserService.formatRemainingQueries(quota)}
              </span>
              {quota.free_trial_end && quota.subscription_status === 'free_trial' && (
                <span className="text-orange-400">
                  ({UserService.formatTrialEndDate(quota.free_trial_end)})
                </span>
              )}
            </div>
          )}
        </div>
        <button
          onClick={() => signOut()}
          className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded-lg text-sm transition-colors duration-200"
        >
          ログアウト
        </button>
      </div>
    );
  }

  return (
    <Link
      href="/auth/signin"
      className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold px-4 py-2 rounded-lg transition-colors duration-200"
    >
      ログイン
    </Link>
  );
}