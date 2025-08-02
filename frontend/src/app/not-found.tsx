'use client';

import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
        <div className="text-center">
          <div className="text-gray-400 text-6xl mb-4">404</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            ページが見つかりません
          </h1>
          <p className="text-gray-600 mb-6">
            お探しのページは存在しないか、移動された可能性があります。
          </p>
          <Link
            href="/"
            className="inline-block w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            ホームに戻る
          </Link>
        </div>
      </div>
    </div>
  );
} 