import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "UmaOracle AI - 競馬予想チャットボット",
  description: "JRAの過去データ + 独自計算式 + LLMを組み合わせた競馬予想チャットボット",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
