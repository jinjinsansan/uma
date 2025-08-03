import type { Metadata } from 'next'
import './globals.css'
import { Noto_Sans_JP } from 'next/font/google'

const notoSansJP = Noto_Sans_JP({
  subsets: ['latin'],
  weight: ['300', '400', '500', '700'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'D-Logic AI - 革命的競馬予想システム',
  description: '959,620レコードの膨大なデータとAI技術を融合した次世代D-Logic分析エンジン。ダンスインザダーク基準100点による科学的で客観的な12項目評価システム。',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className={notoSansJP.className}>{children}</body>
    </html>
  )
}
