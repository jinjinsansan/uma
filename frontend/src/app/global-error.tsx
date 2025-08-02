'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Global application error:', error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="text-center">
              <div className="text-red-500 text-6xl mb-4">🚨</div>
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                重大なエラーが発生しました
              </h1>
              <p className="text-gray-600 mb-6">
                アプリケーションで予期しないエラーが発生しました。
              </p>
              <div className="space-y-3">
                <button
                  onClick={reset}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  再試行
                </button>
                <button
                  onClick={() => window.location.href = '/'}
                  className="w-full bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  ホームに戻る
                </button>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
} 