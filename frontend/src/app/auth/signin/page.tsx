'use client';

import { signIn, getSession } from 'next-auth/react';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

export default function SignIn() {
  const [isLoading, setIsLoading] = useState(false);
  const [showDLogo, setShowDLogo] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // D-Logoを3秒間表示してからログイン画面を表示
    const timer = setTimeout(() => {
      setShowDLogo(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      const result = await signIn('google', {
        callbackUrl: '/',
        redirect: false
      });
      
      if (result?.error) {
        console.error('サインインエラー:', result.error);
      } else {
        router.push('/');
      }
    } catch (error) {
      console.error('サインインに失敗しました:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (showDLogo) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse">
            <div className="text-6xl md:text-8xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 mb-4">
              D
            </div>
          </div>
          <div className="text-yellow-400 text-lg font-medium">
            D-Logic AI
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-500 mb-2">
            D-Logic AI
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            会員ログイン
          </h2>
          <p className="text-gray-300 text-sm">
            競馬予想AIの世界へようこそ
          </p>
        </div>

        <div className="bg-gray-900 p-8 rounded-xl border border-gray-800">
          <div className="space-y-6">
            <button
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full flex items-center justify-center px-4 py-3 border border-gray-600 rounded-lg bg-white text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900 mr-2"></div>
                  サインイン中...
                </div>
              ) : (
                <div className="flex items-center">
                  <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Googleでサインイン
                </div>
              )}
            </button>

            <div className="text-center">
              <p className="text-gray-400 text-sm">
                サインインすることで、
                <a href="/terms" className="text-yellow-400 hover:underline">利用規約</a>
                および
                <a href="/privacy" className="text-yellow-400 hover:underline">プライバシーポリシー</a>
                に同意したものとみなします。
              </p>
            </div>
          </div>
        </div>

        <div className="text-center">
          <p className="text-gray-500 text-sm">
            ※ Googleアカウントで簡単にご利用いただけます
          </p>
        </div>
      </div>
    </div>
  );
}