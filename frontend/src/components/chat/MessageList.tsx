import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Message } from '../../types/chat';

interface MessageListProps {
  messages: Message[];
}

interface TypingMessageProps {
  content: string;
  type: 'user' | 'ai';
  raceInfo?: string;
}

function TypingMessage({ content, type, raceInfo }: TypingMessageProps) {
  const [displayedContent, setDisplayedContent] = useState('');
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    if (type === 'ai') {
      let index = 0;
      const interval = setInterval(() => {
        if (index < content.length) {
          setDisplayedContent(content.slice(0, index + 1));
          index++;
        } else {
          setIsTyping(false);
          clearInterval(interval);
        }
      }, 30); // タイピング速度を調整

      return () => clearInterval(interval);
    } else {
      setDisplayedContent(content);
      setIsTyping(false);
    }
  }, [content, type]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`flex ${type === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-xl px-4 py-3 rounded-2xl ${
          type === 'user'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-800'
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {displayedContent}
          {isTyping && type === 'ai' && (
            <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse" />
          )}
        </p>
        {raceInfo && !isTyping && (
          <p className="text-xs opacity-75 mt-1">{raceInfo}</p>
        )}
      </div>
    </motion.div>
  );
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-4 min-h-full">
      <AnimatePresence mode="wait">
        {messages.map((message, index) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ 
              duration: 0.4, 
              ease: "easeOut",
              delay: index * 0.1 // メッセージ間の遅延
            }}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-xl px-4 py-3 rounded-2xl ${
                message.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              {message.raceInfo && (
                <p className="text-xs opacity-75 mt-1">{message.raceInfo}</p>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}