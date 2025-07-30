import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Loader2 } from 'lucide-react';
import { useChatStore } from '../../store/chatStore';
import { api } from '../../lib/api';

interface MessageInputProps {
  onShowConditions: () => void;
}

export default function MessageInput({ onShowConditions }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { addMessage, setLoading, isLoading } = useChatStore();

  // キーボード表示の検出
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth <= 768;
      const viewportHeight = window.visualViewport?.height || window.innerHeight;
      const isKeyboardOpen = isMobile && viewportHeight < window.innerHeight * 0.8;
      
      setIsKeyboardVisible(isKeyboardOpen);
    };

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

  // 入力フィールドにフォーカスを当てる（キーボード表示時は遅延）
  useEffect(() => {
    if (!isLoading && !isSubmitting) {
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, isKeyboardVisible ? 100 : 0);
      
      return () => clearTimeout(timer);
    }
  }, [isLoading, isSubmitting, isKeyboardVisible]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSubmitting) return;

    const userMessage = input.trim();
    setInput('');
    setIsSubmitting(true);

    // ユーザーメッセージを即座に追加
    addMessage({
      type: 'user',
      content: userMessage,
    });

    // AIの応答を少し遅延させて自然な会話感を演出
    setTimeout(async () => {
      setLoading(true);

      try {
        // まずバックエンドサーバーの状態を確認
        const isServerHealthy = await api.healthCheck();
        if (!isServerHealthy) {
          throw new Error('バックエンドサーバーが起動していません。サーバーを起動してから再度お試しください。');
        }

        const response = await api.chat(userMessage);
        
        // AIメッセージを滑らかに追加
        addMessage({
          type: 'ai',
          content: response.message,
        });

        if (response.type === 'conditions') {
          // 条件選択を少し遅延させて自然な流れを作る
          setTimeout(() => {
            onShowConditions();
          }, 1000);
        }
      } catch (error) {
        console.error('Chat error:', error);
        
        // エラーメッセージを取得
        const errorMessage = error instanceof Error ? error.message : '不明なエラーが発生しました。';
        
        addMessage({
          type: 'ai',
          content: `エラーが発生しました: ${errorMessage}`,
        });
      } finally {
        setLoading(false);
        setIsSubmitting(false);
      }
    }, 300); // 300msの遅延で自然な会話感を演出
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center space-x-2 sm:space-x-4">
      <motion.input
        ref={inputRef}
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="今日のレースの予想は？"
        disabled={isLoading || isSubmitting}
        className={`flex-1 px-3 py-2.5 sm:px-4 sm:py-3 rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 text-base sm:text-base ${
          isKeyboardVisible ? 'text-lg' : 'text-sm sm:text-base'
        }`}
        style={{
          fontSize: isKeyboardVisible ? '16px' : undefined, // iOSでズームを防ぐ
        }}
        whileFocus={{ scale: 1.02 }}
        transition={{ duration: 0.2 }}
      />
      <motion.button
        type="submit"
        disabled={!input.trim() || isSubmitting || isLoading}
        className={`p-2.5 sm:p-3 bg-green-500 text-white rounded-full hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg transition-all duration-200 flex-shrink-0 ${
          isKeyboardVisible ? 'p-3' : 'p-2.5 sm:p-3'
        }`}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        {isSubmitting || isLoading ? (
          <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
        ) : (
          <Send className="w-4 h-4 sm:w-5 sm:h-5" />
        )}
      </motion.button>
    </form>
  );
}