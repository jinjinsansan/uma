import React, { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../../store/chatStore';
import { api } from '../../lib/api';

interface QuickAction {
  id: string;
  text: string;
  displayText: string;
  emoji: string;
}

const quickActions: QuickAction[] = [
  {
    id: 'today-race',
    text: '今日のレースの予想を教えて',
    displayText: '今日のレース予想',
    emoji: '🏇'
  },
  {
    id: 'eight-conditions',
    text: '8条件計算について詳しく教えて',
    displayText: '8条件について',
    emoji: '📊'
  },
  {
    id: 'winning-tips',
    text: '競馬で勝つためのコツを教えて',
    displayText: '勝つためのコツ',
    emoji: '💡'
  },
  {
    id: 'accuracy-rate',
    text: '過去の的中率はどれくらいですか？',
    displayText: '的中率について',
    emoji: '📈'
  },
  {
    id: 'betting-strategy',
    text: 'おすすめの馬券の買い方を教えて',
    displayText: '馬券の買い方',
    emoji: '🎯'
  }
];

interface ImprovedChatInputProps {
  onSendMessage?: (message: string) => void;
  placeholder?: string;
  maxLength?: number;
  disabled?: boolean;
  onShowConditions?: () => void;
}

export const ImprovedChatInput: React.FC<ImprovedChatInputProps> = ({
  onSendMessage,
  placeholder = "競馬について何でもお気軽にお聞きください... 詳しい分析や予想をお手伝いします！",
  maxLength = 2000,
  disabled = false,
  onShowConditions
}) => {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { addMessage, setLoading, isLoading } = useChatStore();

  // Auto-resize textarea
  const autoResize = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const newHeight = Math.min(textareaRef.current.scrollHeight, 200);
      textareaRef.current.style.height = newHeight + 'px';
    }
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    autoResize();
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle quick action click
  const handleQuickActionClick = (action: QuickAction) => {
    setMessage(action.text);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
    autoResize();
  };

  // Handle send message
  const handleSendMessage = async () => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending || disabled) return;

    setIsSending(true);

    try {
      // ユーザーメッセージを即座に追加
      addMessage({
        type: 'user',
        content: trimmedMessage,
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

          const response = await api.chat(trimmedMessage);
          
          // AIメッセージを滑らかに追加
          addMessage({
            type: 'ai',
            content: response.message,
          });

          if (response.type === 'conditions' && onShowConditions) {
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
        }
      }, 300); // 300msの遅延で自然な会話感を演出

      // Clear input after successful send
      setMessage('');
      autoResize();

    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  // Character count color
  const getCharCountColor = () => {
    const count = message.length;
    if (count > maxLength * 0.9) return 'text-red-500';
    if (count > maxLength * 0.75) return 'text-yellow-500';
    return 'text-gray-400';
  };

  useEffect(() => {
    autoResize();
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Quick Actions */}
      <div className="flex flex-wrap gap-3 mb-4">
        {quickActions.map((action) => (
          <button
            key={action.id}
            onClick={() => handleQuickActionClick(action)}
            disabled={disabled}
            className="bg-gray-50 border border-gray-200 hover:bg-gray-100 hover:border-gray-300 
                     px-4 py-3 rounded-lg text-sm font-medium text-gray-700 transition-all duration-200 
                     hover:transform hover:-translate-y-0.5 hover:shadow-md active:transform active:translate-y-0
                     disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:transform-none
                     flex items-center gap-2"
          >
            <span>{action.emoji}</span>
            <span>{action.displayText}</span>
          </button>
        ))}
      </div>

      {/* Main Input Container */}
      <div className="relative">
        <div className="border-2 border-gray-200 focus-within:border-blue-500 focus-within:shadow-lg 
                      focus-within:shadow-blue-500/10 rounded-xl bg-white transition-all duration-300 
                      hover:shadow-md overflow-hidden">
          
          {/* Input Area */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder={placeholder}
            maxLength={maxLength}
            disabled={disabled || isSending}
            rows={1}
            className="w-full min-h-[60px] max-h-[200px] px-4 py-4 border-none outline-none 
                     resize-none text-base leading-6 placeholder-gray-400 disabled:opacity-50
                     disabled:cursor-not-allowed overflow-y-auto"
          />

          {/* Footer */}
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex justify-between items-center">
            {/* Shortcuts and Counter */}
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <div className="hidden sm:flex items-center gap-1">
                <kbd className="bg-gray-200 border border-gray-300 rounded px-2 py-0.5 text-xs font-mono">Shift</kbd>
                <span>+</span>
                <kbd className="bg-gray-200 border border-gray-300 rounded px-2 py-0.5 text-xs font-mono">Enter</kbd>
                <span>で改行</span>
              </div>
              <div className="hidden sm:flex items-center gap-1">
                <kbd className="bg-gray-200 border border-gray-300 rounded px-2 py-0.5 text-xs font-mono">Enter</kbd>
                <span>で送信</span>
              </div>
              <span className={`text-xs ${getCharCountColor()}`}>
                {message.length}/{maxLength}
              </span>
            </div>

            {/* Send Button */}
            <button
              onClick={handleSendMessage}
              disabled={!message.trim() || isSending || disabled}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                       text-white font-semibold px-5 py-2.5 rounded-lg transition-all duration-200
                       hover:transform hover:-translate-y-0.5 hover:shadow-lg hover:shadow-green-600/30
                       active:transform active:translate-y-0 flex items-center gap-2 relative overflow-hidden"
            >
              {isSending ? (
                <>
                  <span>送信中...</span>
                  <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                </>
              ) : (
                <>
                  <span>送信</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                  </svg>
                </>
              )}
              
              {/* Shimmer effect during sending */}
              {isSending && (
                <div className="absolute inset-0 -top-full bg-gradient-to-r from-transparent via-white/30 to-transparent 
                              animate-shimmer"></div>
              )}
            </button>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 1s infinite;
        }
      `}</style>
    </div>
  );
};

export default ImprovedChatInput; 