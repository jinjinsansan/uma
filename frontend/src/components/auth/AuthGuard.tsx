'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export default function AuthGuard({ children, requireAuth = true }: AuthGuardProps) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    if (status === 'loading') return; // セッション読み込み中

    if (requireAuth) {
      if (!session) {
        // 未認証の場合はログインページにリダイレクト
        router.push('/auth/signin');
        return;
      }
    }

    setIsAuthorized(true);
  }, [session, status, router, requireAuth]);

  // セッション読み込み中
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-yellow-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">認証状態を確認中...</p>
        </div>
      </div>
    );
  }

  // 認証が必要だが未認証
  if (requireAuth && !session) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-white text-2xl mb-4">ログインが必要です</h1>
          <p className="text-gray-400 mb-8">このページにアクセスするにはGoogleアカウントでログインしてください。</p>
          <button
            onClick={() => router.push('/auth/signin')}
            className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold px-6 py-3 rounded-lg transition-colors duration-200"
          >
            ログインページへ
          </button>
        </div>
      </div>
    );
  }

  // 認証完了またはauth不要
  if (isAuthorized) {
    return <>{children}</>;
  }

  return null;
}