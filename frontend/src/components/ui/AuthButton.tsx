'use client';

import { useSession, signIn, signOut } from 'next-auth/react';
import Link from 'next/link';

export default function AuthButton() {
  const { data: session, status } = useSession();

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
        <span className="text-white text-sm">
          {session.user?.name || session.user?.email}
        </span>
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