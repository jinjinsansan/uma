'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import DLogicChatInterface from '../../components/chat/DLogicChatInterface';
import AuthGuard from '@/components/auth/AuthGuard';
import LineAddFriendPopup from '@/components/line/LineAddFriendPopup';
import { useLineAddFriendDetection } from '@/hooks/useLineAddFriendDetection';

export default function DLogicAIPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { shouldShowPopup, hidePopup, onTicketClaimed } = useLineAddFriendDetection({
    delaySeconds: 45, // D-Logic AI使用中45秒後に表示
  });

  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-gradient-to-b from-black via-gray-900 to-black">
      {/* Header */}
      <header className="bg-gray-900/50 border-b border-[#ffd700]/30">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <span className="text-[#ffd700] text-2xl font-bold">D</span>
            <span className="text-xl font-bold text-[#ffd700]">D-Logic AI</span>
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-6">
            <Link href="/today-races" className="outline-button px-4 py-2 text-sm">
              本日のレース
            </Link>
            <Link href="/past-races" className="outline-button px-4 py-2 text-sm">
              過去レース体験
            </Link>
            <Link href="/register" className="outline-button px-4 py-2 text-sm">
              会員登録
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden text-[#ffd700] p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-gray-900 border-t border-[#ffd700]/30">
            <nav className="container mx-auto px-4 py-4 flex flex-col space-y-3">
              <Link 
                href="/today-races" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                本日のレース
              </Link>
              <Link 
                href="/past-races" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                過去レース体験
              </Link>
              <Link 
                href="/register" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                会員登録
              </Link>
            </nav>
          </div>
        )}
      </header>

        {/* Main Content - Full Height Chat */}
        <main className="h-[calc(100vh-80px)]">
          <DLogicChatInterface />
        </main>
      </div>
      
      {/* LINE友達追加ポップアップ */}
      <LineAddFriendPopup
        isOpen={shouldShowPopup}
        onClose={hidePopup}
        onTicketClaimed={onTicketClaimed}
      />
    </AuthGuard>
  );
}