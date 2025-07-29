import { create } from 'zustand';
import { Message, ChatState } from '../types/chat';
import { ConfidenceLevel } from '../types/race';

interface ChatStore extends ChatState {
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  addMessageWithDelay: (message: Omit<Message, 'id' | 'timestamp'>, delay?: number) => void;
  setLoading: (loading: boolean) => void;
  setSelectedConditions: (conditions: string[]) => void;
  setCurrentRace: (race: string) => void;
  clearMessages: () => void;
  updateLastMessage: (content: string) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isLoading: false,
  selectedConditions: [],
  currentRace: undefined,

  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date(),
    };
    set((state) => ({
      messages: [...state.messages, newMessage],
    }));
  },

  addMessageWithDelay: (message, delay = 500) => {
    setTimeout(() => {
      const newMessage: Message = {
        ...message,
        id: Date.now().toString(),
        timestamp: new Date(),
      };
      set((state) => ({
        messages: [...state.messages, newMessage],
      }));
    }, delay);
  },

  updateLastMessage: (content: string) => {
    set((state) => {
      if (state.messages.length === 0) return state;
      
      const updatedMessages = [...state.messages];
      const lastMessage = updatedMessages[updatedMessages.length - 1];
      
      if (lastMessage) {
        lastMessage.content = content;
      }
      
      return { messages: updatedMessages };
    });
  },

  setLoading: (loading) => {
    set({ isLoading: loading });
  },

  setSelectedConditions: (conditions) => {
    set({ selectedConditions: conditions });
  },

  setCurrentRace: (race) => {
    set({ currentRace: race });
  },

  clearMessages: () => {
    set({ messages: [] });
  },
}));