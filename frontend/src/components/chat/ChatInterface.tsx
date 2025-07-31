import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';
import AnimatedOrb from '../animation/AnimatedOrb';
import MessageList from './MessageList';
import ConditionSelector from './ConditionSelector';
import { useChatStore } from '../../store/chatStore';
import { ConfidenceLevel } from '../../types/race';
// 新しいコンポーネントをインポート（既存のimport文は変更しない）
import { ImprovedChatInput } from './ImprovedChatInput';
// Phase 2: レース選択ボタンをインポート
import RaceSelectionButton from '../navigation/RaceSelectionButton';

export default function ChatInterface() {
  const { messages, isLoading, selectedConditions } = useChatStore();
  const [showConditions, setShowConditions] = useState(false);
  const [orbPosition, setOrbPosition] = useState<'center' | 'top'>('center');
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  const [isConditionsSelected, setIsConditionsSelected] = useState(false);
  const [isPredictionResult, setIsPredictionResult] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const getOrbConfidence = (): ConfidenceLevel => {
    if (isLoading) return 'processing';
    if (messages.length === 0) return 'waiting'; // Initial state: waiting
    
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.predictionResult) {
      return lastMessage.predictionResult.confidence || 'medium';
    }
    
    // If there are user messages and no prediction result yet, it's chatting
    if (messages.some(msg => msg.type === 'user')) {
      return 'chatting';
    }
    
    return 'waiting';
  };

  const getLastMessageContent = (): string => {
    if (messages.length === 0) return '';
    const lastMessage = messages[messages.length - 1];
    return lastMessage.content || '';
  };

  // 8条件選択時のアニメーション
  useEffect(() => {
    console.log('=== ChatInterface 8条件選択アニメーション ===');
    console.log('selectedConditions:', selectedConditions);
    console.log('selectedConditions.length:', selectedConditions.length);
    console.log('isConditionsSelected:', isConditionsSelected);
    
    if (selectedConditions.length === 4) {
      console.log('🎯 4つの条件が選択されました。アニメーション開始');
      setIsConditionsSelected(true);
      
      // 0.6秒後にアニメーション完了（AnimatedOrbと合わせる）
      setTimeout(() => {
        console.log('✅ アニメーション完了');
        setIsConditionsSelected(false);
      }, 600);
    } else {
      // 条件が4つ未満の場合はアニメーションをリセット
      console.log('🔄 条件が4つ未満のためアニメーションをリセット');
      setIsConditionsSelected(false);
    }
  }, [selectedConditions]);

  // 予想結果表示時のアニメーション
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.predictionResult && !isPredictionResult) {
      console.log('🎯 予想結果表示時のアニメーション開始');
      setIsPredictionResult(true);
      
      // 10秒後にアニメーション完了（AnimatedOrbと合わせる）
      const timer = setTimeout(() => {
        console.log('🔄 10秒経過、予想結果アニメーション完了');
        setIsPredictionResult(false);
      }, 10000);
      
      // クリーンアップ関数を追加
      return () => {
        console.log('🧹 ChatInterface 予想結果アニメーションのクリーンアップ');
        clearTimeout(timer);
      };
    }
  }, [messages, isPredictionResult]);

  // キーボード表示の検出
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth <= 768;
      const viewportHeight = window.visualViewport?.height || window.innerHeight;
      const isKeyboardOpen = isMobile && viewportHeight < window.innerHeight * 0.8;
      
      setIsKeyboardVisible(isKeyboardOpen);
    };

    // ビューポートの変更を監視
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleResize);
    } else {
      window.addEventListener('resize', handleResize);
    }

    return () => {
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleResize);
      } else {
        window.removeEventListener('resize', handleResize);
      }
    };
  }, []);

  // 球体の位置を動的に調整
  useEffect(() => {
    if (messages.length > 0 && !isKeyboardVisible) {
      // 会話が始まったら画面上部に移動（キーボードが表示されていない場合のみ）
      const timer = setTimeout(() => {
        setOrbPosition('top');
      }, 1000); // 1秒後に移動開始
      
      return () => clearTimeout(timer);
    } else if (isKeyboardVisible) {
      // キーボードが表示されている場合は球体を非表示
      setOrbPosition('center');
    } else {
      // メッセージがない場合は中央に戻す
      setOrbPosition('center');
    }
  }, [messages.length, isKeyboardVisible]);

  // メッセージが追加されたときに自動スクロール
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="h-screen flex flex-col relative bg-white overflow-hidden">
      {/* ビューポートの調整 */}
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
      
      <header className="flex justify-between items-center p-4 sm:p-6 bg-white flex-shrink-0">
        <div className="flex items-center space-x-2">
          <Zap className="w-6 h-6 sm:w-8 sm:h-8 text-orange-500" />
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
            OracleAI
          </h1>
        </div>
        <div className="flex items-center space-x-3">
          {/* Phase 2: レース選択ボタンを追加 */}
          <RaceSelectionButton />
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-yellow-500 text-white px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg font-semibold shadow-lg text-sm sm:text-base"
          >
            Premium会員
          </motion.button>
        </div>
      </header>

      {/* 動的な位置の球体（キーボード表示時は非表示） */}
      {!isKeyboardVisible && (
        <motion.div 
          className="fixed z-10 pointer-events-none"
          style={{
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
          animate={{
            top: orbPosition === 'center' ? '25vh' : '10vh', // 球体の位置を上部に調整
            opacity: isKeyboardVisible ? 0 : 1,
          }}
          transition={{
            duration: 1.5,
            ease: "easeInOut",
          }}
        >
          <AnimatedOrb 
            confidence={getOrbConfidence()} 
            isProcessing={isLoading} 
            lastMessage={getLastMessageContent()}
            isConditionsSelected={isConditionsSelected}
            isPredictionResult={isPredictionResult}
          />
        </motion.div>
      )}

      {/* スクロール可能なチャットエリア */}
      <main 
        className="flex-1 flex flex-col items-center px-4 sm:px-6 overflow-y-auto"
        style={{ 
          paddingTop: orbPosition === 'center' && !isKeyboardVisible ? '20px' : '80px',
          paddingBottom: '200px' // チャット入力エリアの高さ分の余白
        }}
      >
        <div className="w-full max-w-2xl">
          <MessageList messages={messages} />
          <div ref={messagesEndRef} />
        </div>

        {showConditions && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="w-full max-w-4xl mt-6"
          >
            <ConditionSelector onComplete={() => setShowConditions(false)} />
          </motion.div>
        )}
      </main>

      {/* 新しいチャット入力エリア（境界線を完全に削除） */}
      <div 
        className="fixed bottom-8 left-0 right-0 p-3 sm:p-6 bg-white z-20"
        style={{
          paddingBottom: 'env(safe-area-inset-bottom)'
        }}
      >
        <ImprovedChatInput 
          onShowConditions={() => setShowConditions(true)}
          placeholder="競馬について何でもお気軽にお聞きください..."
        />
      </div>

      {/* 下部の空白エリア */}
      <div className="h-8 sm:h-12 bg-white"></div>
    </div>
  );
}