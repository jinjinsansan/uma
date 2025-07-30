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
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
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

  const getLastMessageContent = (): string => {
    if (messages.length === 0) return '';
    const lastMessage = messages[messages.length - 1];
    return lastMessage.content || '';
  };

  // キーボード表示の検出
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth <= 768;
      const viewportHeight = window.visualViewport?.height || window.innerHeight;
      const isKeyboardOpen = isMobile && viewportHeight < window.innerHeight * 0.8;
      
      setIsKeyboardVisible(isKeyboardOpen);
    };

    // ビューポートの変更を監視
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleResize);
    } else {
      window.addEventListener('resize', handleResize);
    }

    return () => {
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleResize);
      } else {
        window.removeEventListener('resize', handleResize);
      }
    };
  }, []);

  // 球体の位置を動的に調整
  useEffect(() => {
    if (messages.length > 0 && !isKeyboardVisible) {
      // 会話が始まったら画面上部に移動（キーボードが表示されていない場合のみ）
      const timer = setTimeout(() => {
        setOrbPosition('top');
      }, 1000); // 1秒後に移動開始
      
      return () => clearTimeout(timer);
    } else if (isKeyboardVisible) {
      // キーボードが表示されている場合は球体を非表示
      setOrbPosition('center');
    } else {
      // メッセージがない場合は中央に戻す
      setOrbPosition('center');
    }
  }, [messages.length, isKeyboardVisible]);

  // メッセージが追加されたときに自動スクロール
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="min-h-screen flex flex-col relative">
      {/* ビューポートの調整 */}
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
      
      <header className="flex justify-between items-center p-4 sm:p-6">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Zap className="w-6 h-6 sm:w-8 sm:h-8 text-orange-500" />
            <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
              OracleAI
            </h1>
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="bg-yellow-500 text-white px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg font-semibold shadow-lg text-sm sm:text-base"
        >
          Premium会員
        </motion.button>
      </header>

      {/* 動的な位置の球体（キーボード表示時は非表示） */}
      {!isKeyboardVisible && (
        <motion.div 
          className="fixed z-10 pointer-events-none"
          style={{
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
          animate={{
            top: orbPosition === 'center' ? '75vh' : '15vh', // 初期位置を75vhに変更
            opacity: isKeyboardVisible ? 0 : 1,
          }}
          transition={{
            duration: 1.5,
            ease: "easeInOut",
          }}
        >
          <AnimatedOrb 
            confidence={getOrbConfidence()} 
            isProcessing={isLoading} 
            lastMessage={getLastMessageContent()}
          />
        </motion.div>
      )}

      {/* スクロール可能なチャットエリア */}
      <main 
        className={`flex-1 flex flex-col items-center px-4 sm:px-6 pb-20 sm:pb-32 chat-main ${
          isKeyboardVisible ? 'keyboard-visible' : ''
        }`}
        style={{ 
          paddingTop: orbPosition === 'center' && !isKeyboardVisible ? '20px' : '80px',
          minHeight: isKeyboardVisible ? '50vh' : 'auto',
          maxHeight: isKeyboardVisible ? '50vh' : 'none',
          overflow: isKeyboardVisible ? 'auto' : 'visible'
        }}
      >
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

      {/* 入力エリア（キーボード表示時の位置調整） */}
      <div 
        className={`fixed left-0 right-0 p-3 sm:p-6 bg-white/90 backdrop-blur-md border-t border-gray-200 z-20 shadow-lg transition-all duration-300 input-area ${
          isKeyboardVisible ? 'keyboard-visible' : ''
        }`}
        style={{
          paddingBottom: isKeyboardVisible ? 'env(safe-area-inset-bottom)' : '1rem',
          maxHeight: isKeyboardVisible ? '40vh' : 'auto'
        }}
      >
        <MessageInput onShowConditions={() => setShowConditions(true)} />
      </div>
    </div>
  );
}