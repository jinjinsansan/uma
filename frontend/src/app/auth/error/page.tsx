'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Suspense } from 'react';

function AuthErrorContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const error = searchParams?.get('error') || null;

  const getErrorMessage = (error: string | null) => {
    switch (error) {
      case 'Configuration':
        return 'サーバー設定に問題があります。しばらく待ってから再度お試しください。';
      case 'AccessDenied':
        return 'アクセスが拒否されました。適切な権限がありません。';
      case 'Verification':
        return 'メール認証に失敗しました。再度お試しください。';
      case 'Default':
        return '認証中に予期しないエラーが発生しました。';
      default:
        return 'ログインに失敗しました。再度お試しください。';
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-500 mb-2">
            D-Logic AI
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            認証エラー
          </h2>
        </div>

        <div className="bg-gray-900 p-8 rounded-xl border border-red-500">
          <div className="text-center space-y-4">
            <div className="text-red-400 text-6xl mb-4">⚠️</div>
            <p className="text-white text-lg font-medium">
              {getErrorMessage(error)}
            </p>
            <p className="text-gray-400 text-sm">
              エラーコード: {error || 'Unknown'}
            </p>
          </div>
        </div>

        <div className="flex flex-col space-y-4">
          <Link
            href="/auth/signin"
            className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-3 px-4 rounded-lg text-center transition-colors duration-200"
          >
            再度ログインを試す
          </Link>
          <Link
            href="/"
            className="w-full border border-gray-600 text-white hover:bg-gray-800 font-bold py-3 px-4 rounded-lg text-center transition-colors duration-200"
          >
            トップページへ戻る
          </Link>
        </div>

        <div className="text-center">
          <p className="text-gray-500 text-sm">
            問題が続く場合は、しばらく時間をおいて再度お試しください。
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AuthError() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white">読み込み中...</div>
      </div>
    }>
      <AuthErrorContent />
    </Suspense>
  );
}