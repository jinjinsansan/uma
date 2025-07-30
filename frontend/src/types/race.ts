export interface Race {
  id: string;
  name: string;
  date: string;
  venue: string;
  distance: number;
  surface: 'turf' | 'dirt';
  horseCount: number;
}

export interface Horse {
  id: string;
  name: string;
  baseScore: number;
  finalScore?: number;
  rank?: number;
  confidence?: 'high' | 'medium' | 'low';
}

export interface PredictionResult {
  horses: Horse[];
  confidence: 'high' | 'medium' | 'low';
  selectedConditions: string[];
  calculationTime: string;
  analysis?: string;
  dataSource?: {
    source: string;
    description: string;
    last_update?: string;
  };
}

export interface Condition {
  id: string;
  name: string;
  description: string;
  priority?: number;
}

export type ConfidenceLevel = 'waiting' | 'chatting' | 'high' | 'medium' | 'low' | 'processing';