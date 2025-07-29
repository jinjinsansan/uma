import { useState } from 'react';
import { motion } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import AnimatedOrb from '../animation/AnimatedOrb';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ConditionSelector from './ConditionSelector';
import { ConfidenceLevel } from '../../types/race';

export default function ChatInterface() {
  const { messages, isLoading, selectedConditions } = useChatStore();
  const [showConditions, setShowConditions] = useState(false);

  const getConfidenceLevel = (): ConfidenceLevel => {
    if (isLoading) return 'processing';
    if (messages.length === 0) return 'rainbow';
    
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.predictionResult) {
      return lastMessage.predictionResult.confidence || 'medium';
    }
    return 'rainbow';
  };

  return (
    <div className="flex flex-col h-screen">
      {/* ヘッダー */}
      <motion.header 
        className="flex justify-between items-center p-4 bg-black/20 backdrop-blur-sm"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-sm">🐎</span>
          </div>
          <h1 className="text-white text-xl font-bold">UmaOracle AI</h1>
        </div>
        <button className="px-4 py-2 bg-yellow-500 text-black rounded-lg font-semibold hover:bg-yellow-400 transition-colors">
          Premium会員
        </button>
      </motion.header>

      {/* メインコンテンツ */}
      <div className="flex-1 flex flex-col items-center justify-center p-4 relative">
        {/* 中央の球体 */}
        <motion.div
          className="mb-8"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <AnimatedOrb confidence={getConfidenceLevel()} isProcessing={isLoading} />
        </motion.div>

        {/* メッセージエリア */}
        <div className="w-full max-w-2xl">
          <MessageList />
          
          {/* 条件選択UI */}
          {showConditions && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
            >
              <ConditionSelector />
            </motion.div>
          )}
        </div>
      </div>

      {/* 入力エリア */}
      <div className="p-4 bg-black/20 backdrop-blur-sm">
        <MessageInput onShowConditions={() => setShowConditions(true)} />
      </div>
    </div>
  );
}