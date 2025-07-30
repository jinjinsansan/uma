import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Zap, Crown } from 'lucide-react';
import AnimatedOrb from '../animation/AnimatedOrb';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ConditionSelector from './ConditionSelector';
import { useChatStore } from '../../store/chatStore';
import { ConfidenceLevel } from '../../types/race';

export default function ChatInterface() {
  const { messages, isLoading, selectedConditions } = useChatStore();
  const [showConditions, setShowConditions] = useState(false);
  const [orbPosition, setOrbPosition] = useState<'center' | 'top'>('center');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const getOrbConfidence = (): ConfidenceLevel => {
    if (isLoading) return 'processing';
    if (messages.length === 0) return 'waiting'; // Initial state: waiting
    
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.predictionResult) {
      return lastMessage.predictionResult.confidence || 'medium';
    }
    
    // If there are user messages and no prediction result yet, it's chatting
    if (messages.some(msg => msg.type === 'user')) {
      return 'chatting';
    }
    
    return 'waiting';
  };

  // 球体の位置を動的に調整
  useEffect(() => {
    if (messages.length > 0) {
      // 会話が始まったら画面上部に移動
      const timer = setTimeout(() => {
        setOrbPosition('top');
      }, 1000); // 1秒後に移動開始
      
      return () => clearTimeout(timer);
    } else {
      // メッセージがない場合は中央に戻す
      setOrbPosition('center');
    }
  }, [messages.length]);

  // メッセージが追加されたときに自動スクロール
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="min-h-screen flex flex-col relative">
      <header className="flex justify-between items-center p-6">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Zap className="w-8 h-8 text-orange-500" />
            <h1 className="text-2xl font-bold text-gray-800">
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

      {/* 動的な位置の球体 */}
      <motion.div 
        className="fixed left-1/2 transform -translate-x-1/2 z-10 pointer-events-none"
        animate={{
          top: orbPosition === 'center' ? '50%' : '20%',
          y: orbPosition === 'center' ? '-50%' : '-50%',
        }}
        transition={{
          duration: 1.5,
          ease: "easeInOut",
        }}
      >
        <AnimatedOrb confidence={getOrbConfidence()} isProcessing={isLoading} />
      </motion.div>

      {/* スクロール可能なチャットエリア */}
      <main className="flex-1 flex flex-col items-center px-6 pb-20" style={{ paddingTop: orbPosition === 'center' ? '20px' : '120px' }}>
        <div className="w-full max-w-2xl">
          <MessageList messages={messages} />
          <div ref={messagesEndRef} />
        </div>

        {showConditions && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="w-full max-w-4xl mt-6"
          >
            <ConditionSelector onComplete={() => setShowConditions(false)} />
          </motion.div>
        )}
      </main>

      <div className="fixed bottom-0 left-0 right-0 p-3 sm:p-6 bg-white/80 backdrop-blur-sm border-t border-gray-200 z-20">
        <MessageInput onShowConditions={() => setShowConditions(true)} />
      </div>
    </div>
  );
}