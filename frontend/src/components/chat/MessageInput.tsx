import { useState } from 'react';
import { motion } from 'framer-motion';
import { Send } from 'lucide-react';
import { useChatStore } from '../../store/chatStore';
import { api } from '../../lib/api';

interface MessageInputProps {
  onShowConditions: () => void;
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
      // まずバックエンドサーバーの状態を確認
      const isServerHealthy = await api.healthCheck();
      if (!isServerHealthy) {
        throw new Error('バックエンドサーバーが起動していません。サーバーを起動してから再度お試しください。');
      }

      const response = await api.chat(userMessage);
      addMessage({
        type: 'ai',
        content: response.message,
      });

      if (response.type === 'conditions') {
        onShowConditions();
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
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center space-x-4">
      <motion.input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="今日のレースの予想は？"
        className="flex-1 px-4 py-3 rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-800"
        whileFocus={{ scale: 1.02 }}
      />
      <motion.button
        type="submit"
        disabled={!input.trim()}
        className="p-3 bg-green-500 text-white rounded-full hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <Send className="w-5 h-5" />
      </motion.button>
    </form>
  );
}