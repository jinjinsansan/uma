'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { X, Gift, Clock, Users } from 'lucide-react';
// import { UserService } from '@/services/userService';

interface LineAddFriendPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onTicketClaimed: () => void;
}

export default function LineAddFriendPopup({ isOpen, onClose, onTicketClaimed }: LineAddFriendPopupProps) {
  const { data: session } = useSession();
  const [step, setStep] = useState<'intro' | 'qr' | 'verification' | 'success' | 'error'>('intro');
  const [verificationCode, setVerificationCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // LINEアカウント情報（環境変数から取得）
  const LINE_ACCOUNT_ID = process.env.NEXT_PUBLIC_LINE_ACCOUNT_ID || '@082thmrq';
  const LINE_ADD_URL = `https://line.me/R/ti/p/${LINE_ACCOUNT_ID}`;

  // ランダムな検証コードを生成（実際の運用時はサーバーサイドで管理）
  const generateVerificationCode = () => {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
  };

  useEffect(() => {
    if (isOpen && step === 'intro') {
      // ポップアップが開かれた時に検証コードを生成
      setVerificationCode(generateVerificationCode());
    }
  }, [isOpen, step]);

  const handleAddFriend = () => {
    setStep('qr');
  };

  const handleVerification = async () => {
    if (!session?.user?.email) {
      setErrorMessage('ユーザー情報が取得できません');
      setStep('error');
      return;
    }

    setIsLoading(true);
    try {
      // 実際の運用時はLINE Messaging APIと連携してチケットを付与
      // ここではデモ用に直接API呼び出し
      const userId = 1; // 実際はセッションからユーザーIDを取得
      const lineUserId = `demo_${Date.now()}`; // 実際はLINEから取得
      
      // await UserService.addLineTicket(userId, lineUserId);
      console.log('LINE ticket would be added for user:', userId, lineUserId);
      
      setStep('success');
      onTicketClaimed();
    } catch (error) {
      console.error('LINE連携エラー:', error);
      setErrorMessage('延長チケットの付与に失敗しました');
      setStep('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl max-w-md w-full p-6 relative border border-gray-700">
        {/* 閉じるボタン */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <X size={24} />
        </button>

        {/* イントロ画面 */}
        {step === 'intro' && (
          <div className="text-center">
            <div className="mb-6">
              <Gift className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">
                LINE友達追加で3日間延長！
              </h2>
              <p className="text-gray-400">
                D-Logic AI公式LINEを友達追加すると<br />
                無料トライアル期間が3日間延長されます
              </p>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-center space-x-4 text-sm">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-yellow-500" />
                  <span className="text-yellow-500">+3日間</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Gift className="w-4 h-4 text-green-500" />
                  <span className="text-green-500">延長チケット</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={handleAddFriend}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                LINE友達追加して延長チケットをもらう
              </button>
              <button
                onClick={handleSkip}
                className="w-full text-gray-400 hover:text-white transition-colors"
              >
                後で追加する
              </button>
            </div>
          </div>
        )}

        {/* QRコード画面 */}
        {step === 'qr' && (
          <div className="text-center">
            <h2 className="text-2xl font-bold text-white mb-4">
              LINE友達追加
            </h2>
            <p className="text-gray-400 mb-6">
              QRコードを読み取るか、ボタンをクリックして<br />
              D-Logic AI公式LINEを友達追加してください
            </p>

            {/* QRコード表示エリア */}
            <div className="bg-white rounded-lg p-4 mb-6 mx-auto w-48 h-48 flex items-center justify-center">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(LINE_ADD_URL)}`}
                alt="LINE友達追加QRコード"
                className="w-full h-full object-contain"
                onError={(e) => {
                  // QRコード生成に失敗した場合のフォールバック
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.parentElement!.innerHTML = `
                    <div class="text-center">
                      <div class="text-6xl mb-2">📱</div>
                      <div class="text-black text-xs">QRコード</div>
                      <div class="text-black text-xs font-bold">${LINE_ACCOUNT_ID}</div>
                    </div>
                  `;
                }}
              />
            </div>

            <div className="space-y-3">
              <a
                href={LINE_ADD_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                LINEアプリで友達追加
              </a>
              
              <div className="bg-gray-800 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-2">
                  友達追加後、以下のコードをLINEで送信してください：
                </p>
                <div className="bg-gray-700 rounded px-3 py-2 font-mono text-yellow-400">
                  {verificationCode}
                </div>
              </div>

              <button
                onClick={handleVerification}
                disabled={isLoading}
                className="w-full bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-600 text-black font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                {isLoading ? '確認中...' : '友達追加完了・延長チケット受け取り'}
              </button>

              <button
                onClick={() => setStep('intro')}
                className="w-full text-gray-400 hover:text-white transition-colors"
              >
                戻る
              </button>
            </div>
          </div>
        )}

        {/* 成功画面 */}
        {step === 'success' && (
          <div className="text-center">
            <div className="mb-6">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <Gift className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-green-500 mb-2">
                延長チケット獲得！
              </h2>
              <p className="text-gray-400">
                無料トライアル期間が3日間延長されました<br />
                引き続きD-Logic AIをお楽しみください
              </p>
            </div>

            <div className="bg-green-900/30 border border-green-600 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-center space-x-2 text-green-400">
                <Clock className="w-5 h-5" />
                <span className="font-bold">トライアル期間 +3日間延長</span>
              </div>
            </div>

            <button
              onClick={onClose}
              className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-3 px-6 rounded-lg transition-colors duration-200"
            >
              閉じる
            </button>
          </div>
        )}

        {/* エラー画面 */}
        {step === 'error' && (
          <div className="text-center">
            <div className="mb-6">
              <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <X className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-red-500 mb-2">
                エラーが発生しました
              </h2>
              <p className="text-gray-400">
                {errorMessage || '延長チケットの付与に失敗しました'}
              </p>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => setStep('qr')}
                className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                もう一度試す
              </button>
              <button
                onClick={onClose}
                className="w-full text-gray-400 hover:text-white transition-colors"
              >
                閉じる
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}