import { create } from 'zustand';
import { Message, ChatState } from '../types/chat';
import { ConfidenceLevel } from '../types/race';

interface ChatStore extends ChatState {
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setLoading: (loading: boolean) => void;
  setSelectedConditions: (conditions: string[]) => void;
  setCurrentRace: (race: string) => void;
  clearMessages: () => void;
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