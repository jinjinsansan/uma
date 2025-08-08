"use client"

import type React from "react"
import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "../ui/button"
import { Crown, Star, Bot, UserPlus, MessageCircle, Rocket } from "lucide-react"
import AuthButton from "../ui/AuthButton"

interface DatabaseStats {
  total_records: number;
  total_horses: number;
  total_races: number;
  years_span: number;
}

export default function V0TopPageFixed() {
  const [showLogo, setShowLogo] = useState(false)  // 3秒アニメーション無効化
  const [showMain, setShowMain] = useState(true)   // 直接メイン画面表示
  const [isMounted, setIsMounted] = useState(false)
  const [databaseStats, setDatabaseStats] = useState<DatabaseStats | null>(null);
  const [statsText, setStatsText] = useState('959,620レコード、109,426頭、82,738レースの巨大データベース');

  useEffect(() => {
    setIsMounted(true)
    // 3秒アニメーションを無効化してメイン画面を直接表示
  }, [])

  useEffect(() => {
    // データベース統計を取得
    const fetchDatabaseStats = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/stats/database');
        const data = await response.json();
        
        if (data.status === 'success' || data.status === 'fallback') {
          const newStatsText = `${data.display_text.records}レコード、${data.display_text.horses}頭、${data.display_text.races}レースの巨大データベース`;
          setDatabaseStats(data.database_stats);
          setStatsText(newStatsText);
        }
      } catch (error) {
        // フォールバック値を使用（エラーは表示しない）
      }
    };

    fetchDatabaseStats();
    
    // 5分ごとに更新
    const interval = setInterval(fetchDatabaseStats, 300000);
    return () => clearInterval(interval);
  }, [])

  // 3秒アニメーション完全無効化 - 直接メイン画面表示
  if (!isMounted) {
    return null  // ローディング中
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black text-white relative overflow-hidden">
      {/* 認証ボタン - 右上に配置 */}
      <div className="absolute top-4 right-4 z-10">
        <AuthButton />
      </div>
      
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-screen">
        {/* V0メインロゴ - レスポンシブ最適化版 */}
        <div className="text-center mb-12 md:mb-20">
          <h1 className="text-6xl sm:text-8xl md:text-12xl lg:text-14xl xl:text-16xl font-bold mb-6 md:mb-10 bg-gradient-to-r from-[#ffd700] to-[#ffed4e] bg-[length:400%_400%] animate-gradient-flow bg-clip-text text-transparent px-2">
            D-Logic
          </h1>
          <p className="text-gray-300 text-base md:text-lg lg:text-xl mb-0 px-4">独自ロジックで全ての馬をAIが指数化</p>
        </div>

        {/* キャッチコピー - レスポンシブ最適化版 */}
        <div className="text-center mb-12 md:mb-20 max-w-5xl px-4">
          <p className="text-[#ffd700] text-lg md:text-xl lg:text-2xl font-semibold leading-relaxed">
            {statsText}と
            <br />
            リアルタイムデータを用いて独自開発のAIが競馬予想に役立つ指数を出力
          </p>
        </div>

        {/* ナビゲーションボタン - 完全修正版 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl w-full px-4">
          <NavigationButtonFixed
            icon={<Crown className="w-6 h-6" />}
            title="本日の開催レース"
            description="リアルタイムデータによる本日の開催レース情報"
            href="/today-races"
          />

          <NavigationButtonFixed
            icon={<Star className="w-6 h-6" />}
            title="過去レースD-Logic体験"
            description="過去のG1レースでD-Logic分析を体験"
            href="/past-races"
          />

          <NavigationButtonFixed
            icon={<Bot className="w-6 h-6" />}
            title="D-Logic AI"
            description="AI搭載チャット馬名直接入力分析対応"
            href="/d-logic-ai"
          />

          <NavigationButtonFixed 
            icon={<UserPlus className="w-6 h-6" />} 
            title="会員登録" 
            description="無料体験・有料プラン・LINE連携特典あり" 
            href="/register" 
          />

          <NavigationButtonFixed
            icon={<MessageCircle className="w-6 h-6" />}
            title="お問い合わせ"
            description="D-Logic公式LINE サポート・質問"
            href="https://line.me/R/ti/p/@dlogic"
            external
          />

          <NavigationButtonFixed
            icon={<Rocket className="w-6 h-6" />}
            title="プレミアム"
            description="近日公開予定"
            href="/premium"
            disabled
          />
        </div>

        {/* Footer */}
        <footer className="mt-20 text-center text-gray-400 text-sm">
          <p>&copy; 2025 D-Logic AI. All rights reserved.</p>
          <p className="mt-2">
            Powered by D-Logic Analysis Engine | {databaseStats ? `${databaseStats.total_records.toLocaleString()} Records` : '1,050,000+ Records'} | 71 Years of Data
          </p>
        </footer>
      </div>
    </div>
  )
}

function LogoAnimation() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center">
      {/* 大きなD - 激しく点滅 */}
      <div className="text-[#ffd700] text-[20rem] md:text-[25rem] lg:text-[30rem] font-bold mb-8 animate-intense-flash leading-none">
        D
      </div>

      {/* D-Logic テキスト - 点滅しない */}
      <div className="text-[#ffd700] text-6xl md:text-7xl lg:text-8xl font-bold">D-Logic</div>
    </div>
  )
}

interface NavigationButtonFixedProps {
  icon: React.ReactNode
  title: string
  description: string
  href: string
  disabled?: boolean
  external?: boolean
}

function NavigationButtonFixed({ icon, title, description, href, disabled = false, external = false }: NavigationButtonFixedProps) {
  const handleClick = () => {
    if (disabled) return
    
    if (external) {
      if (typeof window !== 'undefined') {
        window.open(href, '_blank', 'noopener noreferrer')
      }
    } else {
      if (typeof window !== 'undefined') {
        window.location.href = href
      }
    }
  }

  const buttonContent = (
    <div
      className={`
        w-full h-[120px] sm:h-[130px] md:h-[140px] p-4 sm:p-5 md:p-6 flex flex-col items-center justify-center text-center
        bg-gradient-to-br from-gray-900/80 to-gray-800/80 border border-[#ffd700]/40 md:border-2
        hover:border-[#ffd700] hover:bg-gradient-to-br hover:from-[#ffd700]/10 hover:to-[#ffed4e]/10 
        transition-all duration-300 rounded-xl cursor-pointer backdrop-blur-sm
        hover:shadow-[0_0_30px_rgba(255,215,0,0.3)] hover:scale-[1.02]
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
      onClick={handleClick}
    >
      <div className="text-[#ffd700] mb-2">{icon}</div>
      <h3 className="text-white font-semibold text-sm mb-1">{title}</h3>
      {description && <p className="text-gray-400 text-xs leading-tight px-1">{description}</p>}
    </div>
  )

  // 外部リンクの場合はLinkでラップしない
  if (external || disabled) {
    return buttonContent
  }

  // 内部リンクの場合はNext.js Linkでラップ
  return (
    <Link href={href} className="block">
      {buttonContent}
    </Link>
  )
}