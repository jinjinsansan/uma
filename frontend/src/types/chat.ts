export interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  raceInfo?: string;
  conditions?: string[];
  predictionResult?: any;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  selectedConditions: string[];
  currentRace?: string;
}

export interface ChatResponse {
  message: string;
  type: 'text' | 'conditions' | 'prediction';
  data?: any;
}