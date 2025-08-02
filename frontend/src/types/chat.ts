export interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  raceInfo?: string;
  conditions?: string[];
  predictionResult?: PredictionResult;
}

export interface PredictionResult {
  confidence: 'high' | 'medium' | 'low';
  selectedHorses?: SelectedHorse[];
  analysis?: string;
  dataSource?: {
    source: string;
    description: string;
  };
}

export interface SelectedHorse {
  number: number;
  name: string;
  jockey?: string;
  trainer?: string;
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