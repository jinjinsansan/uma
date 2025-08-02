import { motion } from 'framer-motion';
import { Message, SelectedHorse } from '../../types/chat';
import { User, Bot } from 'lucide-react';
import { useState, useEffect } from 'react';

interface MessageListProps {
  messages: Message[];
}

interface TypingMessageProps {
  message: Message;
  index: number;
}

function TypingMessage({ message, index }: TypingMessageProps) {
  const [displayedContent, setDisplayedContent] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (message.type === 'ai') {
      setIsTyping(true);
      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex < message.content.length) {
          setDisplayedContent(message.content.slice(0, currentIndex + 1));
          currentIndex++;
        } else {
          setIsTyping(false);
          clearInterval(interval);
        }
      }, 30); // タイピング速度を調整

      return () => clearInterval(interval);
    } else {
      setDisplayedContent(message.content);
      setIsTyping(false);
    }
  }, [message.content, message.type]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`flex items-start space-x-2 max-w-[85%] sm:max-w-[75%] ${
          message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
        }`}
      >
        {/* アバター */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          message.type === 'user' 
            ? 'bg-blue-500' 
            : 'bg-gradient-to-br from-green-400 to-blue-500'
        }`}>
          {message.type === 'user' ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>

        {/* メッセージ内容 */}
        <div
          className={`px-4 py-2 rounded-2xl text-sm sm:text-base ${
            message.type === 'user'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          <div className="whitespace-pre-wrap break-words">
            {displayedContent}
            {isTyping && message.type === 'ai' && (
              <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse" />
            )}
          </div>
          
          {/* 予想結果の表示 */}
          {message.predictionResult && !isTyping && (
            <div className="mt-3 p-3 bg-white/80 rounded-lg border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-600">
                  予想結果
                </span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  message.predictionResult.confidence === 'high' 
                    ? 'bg-green-100 text-green-800'
                    : message.predictionResult.confidence === 'medium'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {message.predictionResult.confidence === 'high' ? '高信頼度' :
                   message.predictionResult.confidence === 'medium' ? '中信頼度' : '低信頼度'}
                </span>
              </div>
              
              <div className="space-y-2">
                {message.predictionResult.selectedHorses?.map((horse: SelectedHorse, idx: number) => (
                  <div key={idx} className="flex items-center justify-between text-xs">
                    <span className="font-medium">{horse.name}</span>
                    <span className="text-gray-600">{horse.number}番</span>
                  </div>
                ))}
              </div>
              
              {message.predictionResult.analysis && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <p className="text-xs text-gray-600">
                    {message.predictionResult.analysis}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center text-gray-500">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-4"
        >
          <div className="w-16 h-16 mx-auto bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
            <Bot className="w-8 h-8 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              OracleAI へようこそ！
            </h3>
            <p className="text-sm text-gray-500 max-w-md">
              競馬予想について何でもお聞きください。<br />
              今日のレースの予想や、特定のレースについて質問できます。
            </p>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-4 w-full">
      {messages.map((message, index) => (
        <TypingMessage key={index} message={message} index={index} />
      ))}
    </div>
  );
}