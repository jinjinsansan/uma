'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Crown, Send, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useChatStore } from '../../store/chatStore';
import DLogoChatAnimation from '../animation/DLogoChatAnimation';

export default function DLogicChatInterface() {
  const { messages, isLoading, addMessage } = useChatStore();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [showDLogo, setShowDLogo] = useState(false);
  const [dLogoScore, setDLogoScore] = useState(0);

  // メッセージが追加されたときに自動スクロール
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // メッセージ送信（バックエンドAPI連携版）
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');

    // ユーザーメッセージを追加
    addMessage({
      type: 'user',
      content: userMessage,
    });

    // ローディング開始
    const { setLoading } = useChatStore.getState();
    setLoading(true);

    try {
      // バックエンドAPIにリクエスト
      const response = await fetch('http://localhost:8001/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          history: messages.map(m => ({
            role: m.type === 'user' ? 'user' : 'assistant',
            content: m.content
          }))
        }),
      });

      if (!response.ok) {
        throw new Error('API request failed');
      }

      const data = await response.json();
      
      // D-Logic分析結果の場合、スコアを抽出してアニメーション表示
      const scoreMatch = data.response?.match(/【総合評価】(\d+\.?\d*)点/);
      if (scoreMatch) {
        const score = parseFloat(scoreMatch[1]);
        setDLogoScore(score);
        setShowDLogo(true);
      }

      // AI応答を追加
      addMessage({
        type: 'ai',
        content: data.response || '申し訳ございません。応答を生成できませんでした。',
      });
    } catch (error) {
      console.error('Chat API error:', error);
      
      // エラー時はフォールバック応答を使用
      const fallbackResponse = generateDLogicResponse(userMessage);
      addMessage({
        type: 'ai',
        content: fallbackResponse,
      });
    } finally {
      setLoading(false);
    }
  };

  // Enter キーでの送信
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // D-Logic AI のフォールバック応答（API失敗時用）
  const generateDLogicResponse = (userMessage: string): string => {
    // 既存の固定応答ロジックを維持
    const lowerMessage = userMessage.toLowerCase();
    
    const horseNames = ['ディープインパクト', 'オルフェーヴル', 'ダンスインザダーク'];
    const mentionedHorse = horseNames.find(horse => 
      lowerMessage.includes(horse.toLowerCase()) || userMessage.includes(horse)
    );
    
    if (mentionedHorse) {
      const scores = {
        'ディープインパクト': { total: 98.7, grade: 'SS (伝説級)' },
        'オルフェーヴル': { total: 89.4, grade: 'S (超一流)' },
        'ダンスインザダーク': { total: 100.0, grade: 'SS (基準馬)' }
      };
      
      const score = scores[mentionedHorse as keyof typeof scores];
      setDLogoScore(score.total);
      setShowDLogo(true);
      
      return `🐎 ${mentionedHorse} のD-Logic分析結果\n\n【総合評価】${score.total}点 - ${score.grade}`;
    }
    
    return '🤖 D-Logic AI へようこそ\n\n現在、API接続に問題が発生しています。しばらくお待ちください。';
  };

  return (
    <div className="h-full bg-gradient-to-b from-black via-gray-900 to-black text-white flex flex-col">
      {/* Dロゴアニメーション */}
      <DLogoChatAnimation 
        score={dLogoScore}
        isVisible={showDLogo}
        onAnimationComplete={() => setShowDLogo(false)}
      />
      
      {/* チャットメッセージエリア */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {/* 初期メッセージ */}
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-[#ffd700]/20 rounded-full mb-6">
              <Crown className="w-8 h-8 text-[#ffd700]" />
            </div>
            <h3 className="text-xl font-bold text-[#ffd700] mb-4">D-Logic AI Chat</h3>
            <p className="text-gray-300 mb-8 max-w-md mx-auto">
              D-Logic統合分析エンジン搭載<br />
              馬名を入力するだけで瞬時にD-Logic分析を実行
            </p>
            
            {/* サンプル質問 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              <button
                onClick={() => setInputValue('ディープインパクトの分析をお願いします')}
                className="glass-effect rounded-lg p-4 text-left hover:bg-[#ffd700]/10 transition-colors"
              >
                <div className="text-[#ffd700] font-semibold mb-1">馬名直接分析</div>
                <div className="text-sm text-gray-400">「ディープインパクトの分析をお願いします」</div>
              </button>
              
              <button
                onClick={() => setInputValue('今日のG1レースの予想は？')}
                className="glass-effect rounded-lg p-4 text-left hover:bg-[#ffd700]/10 transition-colors"
              >
                <div className="text-[#ffd700] font-semibold mb-1">レース相談</div>
                <div className="text-sm text-gray-400">「今日のG1レースの予想は？」</div>
              </button>
            </div>
          </div>
        )}

        {/* メッセージ一覧 */}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.type === 'user'
                  ? 'bg-[#ffd700] text-black'
                  : 'glass-effect border border-[#ffd700]/30'
              }`}
            >
              {message.type === 'ai' && (
                <div className="flex items-center mb-2">
                  <Crown className="w-4 h-4 text-[#ffd700] mr-2" />
                  <span className="text-xs text-[#ffd700] font-semibold">D-Logic AI</span>
                </div>
              )}
              <div className="whitespace-pre-line">{message.content}</div>
              <div className={`text-xs mt-2 ${
                message.type === 'user' ? 'text-black/70' : 'text-gray-400'
              }`}>
                {message.timestamp.toLocaleTimeString('ja-JP', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </div>
            </div>
          </div>
        ))}

        {/* ローディング表示 */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="glass-effect border border-[#ffd700]/30 rounded-lg px-4 py-3">
              <div className="flex items-center mb-2">
                <Crown className="w-4 h-4 text-[#ffd700] mr-2" />
                <span className="text-xs text-[#ffd700] font-semibold">D-Logic AI</span>
              </div>
              <div className="flex items-center">
                <Loader2 className="w-4 h-4 text-[#ffd700] animate-spin mr-2" />
                <span className="text-gray-300">分析中...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 入力エリア */}
      <div className="border-t border-[#ffd700]/30 p-4">
        <div className="flex items-center space-x-3">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="馬名や競馬について何でもお聞きください..."
              className="w-full bg-gray-800/50 border border-[#ffd700]/30 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-[#ffd700] focus:ring-1 focus:ring-[#ffd700]"
            />
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="bg-[#ffd700] hover:bg-[#ffd700]/90 disabled:bg-gray-600 disabled:cursor-not-allowed text-black p-3 rounded-lg transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        
        <div className="text-xs text-gray-400 mt-2 text-center">
          D-Logic統合分析エンジン | 959,620レコード完全分析対応
        </div>
      </div>
    </div>
  );
}