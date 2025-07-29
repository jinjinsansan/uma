import { useState } from 'react';
import { motion } from 'framer-motion';
import { Send } from 'lucide-react';
import { useChatStore } from '../../store/chatStore';
import { api } from '../../lib/api';

interface MessageInputProps {
  onShowConditions?: () => void;
}

export default function MessageInput({ onShowConditions }: MessageInputProps) {
  const [input, setInput] = useState('');
  const { addMessage, setLoading } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    addMessage({
      type: 'user',
      content: userMessage,
    });

    setLoading(true);

    try {
      const response = await api.chat(userMessage);
      
      addMessage({
        type: 'ai',
        content: response.message,
        raceInfo: response.data?.raceInfo,
      });

      // 条件選択が必要な場合
      if (response.type === 'conditions') {
        onShowConditions?.();
      }
    } catch (error) {
      console.error('Chat error:', error);
      addMessage({
        type: 'ai',
        content: '申し訳ございません。エラーが発生しました。もう一度お試しください。',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex space-x-2">
      <motion.input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="今日のレースの予想は？"
        className="flex-1 px-4 py-3 bg-white/10 backdrop-blur-sm text-white placeholder-white/60 rounded-lg border border-white/20 focus:outline-none focus:border-white/40"
        whileFocus={{ scale: 1.02 }}
        transition={{ duration: 0.2 }}
      />
      <motion.button
        type="submit"
        className="px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-400 transition-colors"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Send size={20} />
      </motion.button>
    </form>
  );
}