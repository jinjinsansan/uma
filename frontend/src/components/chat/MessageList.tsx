import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import { Message } from '../../types/chat';

export default function MessageList() {
  const { messages } = useChatStore();

  const renderMessage = (message: Message) => {
    const isUser = message.type === 'user';
    
    return (
      <motion.div
        key={message.id}
        className={`mb-4 ${isUser ? 'text-right' : 'text-left'}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className={`inline-block max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-white/10 backdrop-blur-sm text-white'
        }`}>
          <p className="text-sm">{message.content}</p>
          {message.raceInfo && (
            <p className="text-xs opacity-70 mt-1">レース: {message.raceInfo}</p>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <div className="space-y-4 max-h-96 overflow-y-auto">
      <AnimatePresence>
        {messages.map(renderMessage)}
      </AnimatePresence>
    </div>
  );
}