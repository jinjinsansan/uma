import { useState } from 'react';
import { motion } from 'framer-motion';
import { Horse, Crown } from 'lucide-react';
import AnimatedOrb from '../animation/AnimatedOrb';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ConditionSelector from './ConditionSelector';
import { useChatStore } from '../../store/chatStore';
import { ConfidenceLevel } from '../../types/race';

export default function ChatInterface() {
  const { messages, isLoading, selectedConditions } = useChatStore();
  const [showConditions, setShowConditions] = useState(false);

  const getOrbConfidence = (): ConfidenceLevel => {
    if (isLoading) return 'processing';
    if (messages.length === 0) return 'rainbow';
    if (selectedConditions.length > 0) return 'medium';
    return 'rainbow';
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* ヘッダー */}
      <header className="flex justify-between items-center p-6">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Horse className="w-8 h-8 text-orange-500" />
            <h1 className="text-2xl font-bold text-gray-800" style={{ fontFamily: 'Georgia, serif' }}>
              OracleAI
            </h1>
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="bg-yellow-500 text-white px-4 py-2 rounded-lg font-semibold shadow-lg"
        >
          Premium会員
        </motion.button>
      </header>

      {/* メインコンテンツ */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 pb-20">
        {/* 3D球体 */}
        <div className="mb-8">
          <AnimatedOrb confidence={getOrbConfidence()} isProcessing={isLoading} />
        </div>

        {/* メッセージリスト */}
        <div className="w-full max-w-2xl">
          <MessageList messages={messages} />
        </div>

        {/* 条件選択 */}
        {showConditions && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="w-full max-w-4xl mt-6"
          >
            <ConditionSelector onComplete={() => setShowConditions(false)} />
          </motion.div>
        )}
      </main>

      {/* 入力エリア */}
      <div className="fixed bottom-0 left-0 right-0 p-6 bg-white/80 backdrop-blur-sm border-t border-gray-200">
        <MessageInput onShowConditions={() => setShowConditions(true)} />
      </div>
    </div>
  );
}