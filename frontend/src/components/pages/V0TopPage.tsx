"use client"

import type React from "react"
import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "../ui/button"
import { Crown, Star, Bot, UserPlus, MessageCircle, Rocket } from "lucide-react"

export default function V0TopPage() {
  const [showLogo, setShowLogo] = useState(true)
  const [showMain, setShowMain] = useState(false)

  useEffect(() => {
    // 3秒後にメインページを表示
    const timer = setTimeout(() => {
      setShowLogo(false)
      setTimeout(() => setShowMain(true), 500)
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  if (showLogo) {
    return <LogoAnimation />
  }

  return (
    <div
      className={`min-h-screen bg-[#0a0a0a] text-white transition-opacity duration-500 ${showMain ? "opacity-100" : "opacity-0"}`}
    >
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-screen" data-version="v3-fixed">
        {/* メインロゴ - 修正版 */}
        <div className="text-center mb-20">
          <h1 className="text-[#ffd700] text-6xl md:text-8xl lg:text-9xl font-bold mb-10 animate-gentle-pulse">D-Logic</h1>
          <p className="text-gray-300 text-lg md:text-xl mb-0">独自ロジックで全ての馬をAIが指数化</p>
        </div>

        {/* キャッチコピー - 修正版 */}
        <div className="text-center mb-20 max-w-5xl px-4">
          <p className="text-[#ffd700] text-lg md:text-xl lg:text-2xl font-semibold leading-relaxed">
            959,620レコード、109,426頭、82,738レースの巨大データベースと
            <br />
            リアルタイムデータを用いて独自開発のAIが競馬予想に役立つ指数を出力
          </p>
        </div>

        {/* ナビゲーションボタン */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl w-full px-4">
          <NavigationButton
            icon={<Crown className="w-8 h-8" />}
            title="本日の開催レース"
            description="リアルタイムデータによる本日の開催レース情報"
            href="/today-races"
          />

          <NavigationButton
            icon={<Star className="w-8 h-8" />}
            title="過去レースD-Logic体験"
            description="過去のG1レースでD-Logic分析を体験"
            href="/past-races"
          />

          <NavigationButton
            icon={<Bot className="w-8 h-8" />}
            title="D-Logic AI"
            description="AI搭載チャット馬名直接入力分析対応"
            href="/d-logic-ai"
          />

          <NavigationButton 
            icon={<UserPlus className="w-8 h-8" />} 
            title="会員登録" 
            description="無料体験・有料プラン・LINE連携特典あり" 
            href="/register" 
          />

          <NavigationButton
            icon={<MessageCircle className="w-8 h-8" />}
            title="お問い合わせ"
            description="D-Logic公式LINE サポート・質問"
            href="https://line.me/R/ti/p/@dlogic"
            external
          />

          <NavigationButton
            icon={<Rocket className="w-8 h-8" />}
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
            Powered by D-Logic Analysis Engine | 959,620 Records | 71 Years of Data
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

interface NavigationButtonProps {
  icon: React.ReactNode
  title: string
  description: string
  href: string
  disabled?: boolean
  external?: boolean
}

function NavigationButton({ icon, title, description, href, disabled = false, external = false }: NavigationButtonProps) {
  const handleClick = () => {
    if (disabled) return
    
    if (external) {
      window.open(href, '_blank', 'noopener noreferrer')
    } else {
      window.location.href = href
    }
  }

  const buttonContent = (
    <Button
      variant="outline"
      className={`
        w-full h-[140px] p-4 flex flex-col items-center justify-center text-center
        bg-gray-900/50 border-[#ffd700]/30 hover:border-[#ffd700] 
        hover:bg-[#ffd700]/10 transition-all duration-300 rounded-lg
        ${disabled ? "opacity-50 cursor-not-allowed" : "hover:scale-[1.02]"}
      `}
      disabled={disabled}
      onClick={handleClick}
    >
      <div className="text-[#ffd700] mb-2">{icon}</div>
      <h3 className="text-white font-semibold text-base mb-1">{title}</h3>
      {description && <p className="text-gray-400 text-xs leading-tight px-2">{description}</p>}
    </Button>
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