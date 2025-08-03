'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    agreeToTerms: false
  });

  const [step, setStep] = useState(1); // 1: 登録, 2: LINE特典案内
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: 実際の登録処理を実装
    setStep(2);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-gray-900 to-black">
      {/* Header */}
      <header className="bg-bg-secondary border-b border-border-primary">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <span className="d-logo-small">D</span>
            <span className="text-xl font-bold text-gold-primary">会員登録</span>
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-6">
            <Link href="/today-races" className="outline-button px-4 py-2 text-sm">
              本日のレース
            </Link>
            <Link href="/d-logic-ai" className="outline-button px-4 py-2 text-sm">
              D-Logic AI
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden text-gold-primary p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-bg-tertiary border-t border-border-primary">
            <nav className="container mx-auto px-4 py-4 flex flex-col space-y-3">
              <Link 
                href="/today-races" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                本日のレース
              </Link>
              <Link 
                href="/d-logic-ai" 
                className="outline-button px-4 py-3 text-center text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                D-Logic AI
              </Link>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="relative py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-md mx-auto">

            {step === 1 && (
              <>
                {/* Hero Section */}
                <div className="text-center mb-8">
                  <h1 className="text-3xl font-bold text-gradient mb-4">
                    D-Logic会員登録
                  </h1>
                  <p className="text-secondary">
                    無料でD-Logic分析をお試しいただけます
                  </p>
                </div>

                {/* Benefits */}
                <div className="glass-effect rounded-lg p-6 mb-8">
                  <h2 className="text-lg font-bold text-gold-primary mb-4">無料会員特典</h2>
                  <ul className="space-y-3 text-sm text-secondary">
                    <li className="flex items-center space-x-2">
                      <span className="text-green-400">✓</span>
                      <span>過去レース分析：無制限</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="text-green-400">✓</span>
                      <span>本日レース分析：1日2回まで</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="text-green-400">✓</span>
                      <span>D-Logic AI チャット：基本機能</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="text-gold-primary">★</span>
                      <span>LINE友だち追加で3回分無料クーポン</span>
                    </li>
                  </ul>
                </div>

                {/* Registration Form */}
                <form onSubmit={handleSubmit} className="glass-effect rounded-lg p-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-primary mb-2">
                        お名前
                      </label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleInputChange}
                        required
                        className="w-full px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-primary focus:outline-none focus:border-gold-primary"
                        placeholder="山田太郎"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-primary mb-2">
                        メールアドレス
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        required
                        className="w-full px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-primary focus:outline-none focus:border-gold-primary"
                        placeholder="example@email.com"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-primary mb-2">
                        パスワード
                      </label>
                      <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleInputChange}
                        required
                        className="w-full px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-primary focus:outline-none focus:border-gold-primary"
                        placeholder="8文字以上"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-primary mb-2">
                        パスワード確認
                      </label>
                      <input
                        type="password"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleInputChange}
                        required
                        className="w-full px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-primary focus:outline-none focus:border-gold-primary"
                        placeholder="パスワードを再入力"
                      />
                    </div>

                    <div className="flex items-start space-x-2">
                      <input
                        type="checkbox"
                        name="agreeToTerms"
                        checked={formData.agreeToTerms}
                        onChange={handleInputChange}
                        required
                        className="mt-1"
                      />
                      <label className="text-sm text-secondary">
                        <Link href="/terms" className="text-gold-primary hover:underline">利用規約</Link>
                        および
                        <Link href="/privacy" className="text-gold-primary hover:underline">プライバシーポリシー</Link>
                        に同意します
                      </label>
                    </div>

                    <button
                      type="submit"
                      disabled={!formData.agreeToTerms}
                      className="w-full gold-button py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      無料会員登録
                    </button>
                  </div>
                </form>

                {/* Login Link */}
                <div className="text-center mt-6">
                  <p className="text-secondary text-sm">
                    すでにアカウントをお持ちですか？
                    <Link href="/login" className="text-gold-primary hover:underline ml-1">
                      ログイン
                    </Link>
                  </p>
                </div>
              </>
            )}

            {step === 2 && (
              <>
                {/* Success Message */}
                <div className="text-center mb-8">
                  <div className="text-6xl mb-4">🎉</div>
                  <h1 className="text-3xl font-bold text-gradient mb-4">
                    登録完了！
                  </h1>
                  <p className="text-secondary">
                    D-Logic会員へようこそ！
                  </p>
                </div>

                {/* LINE Special Offer */}
                <div className="glass-effect rounded-lg p-6 mb-6">
                  <div className="text-center mb-4">
                    <div className="text-4xl mb-2">📱</div>
                    <h2 className="text-xl font-bold text-gold-primary mb-2">
                      LINE友だち追加で特典！
                    </h2>
                    <p className="text-secondary text-sm mb-4">
                      D-Logic公式LINEを友だち追加すると<br />
                      <span className="text-gold-primary font-bold">3回分の無料分析クーポン</span>をプレゼント！
                    </p>
                  </div>

                  {/* QR Code Placeholder */}
                  <div className="bg-white p-4 rounded-lg mb-4 mx-auto w-48 h-48 flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <div className="text-4xl mb-2">📱</div>
                      <p className="text-sm">QRコード</p>
                      <p className="text-xs">（実装時に置き換え）</p>
                    </div>
                  </div>

                  <div className="text-center space-y-3">
                    <a
                      href="https://line.me/R/ti/p/@dlogic"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-4 rounded-lg transition-colors"
                    >
                      LINE友だち追加
                    </a>
                    
                    <button
                      onClick={() => window.location.href = '/d-logic-ai'}
                      className="block w-full outline-button py-3"
                    >
                      後で追加する（D-Logic AIへ）
                    </button>
                  </div>
                </div>

                {/* Instructions */}
                <div className="glass-effect rounded-lg p-4 text-sm text-secondary">
                  <h3 className="font-bold text-primary mb-2">クーポン受け取り方法</h3>
                  <ol className="space-y-1 list-decimal list-inside">
                    <li>上記ボタンでLINE友だち追加</li>
                    <li>自動返信でクーポンコードを受信</li>
                    <li>D-Logic AIでコードを入力して使用</li>
                  </ol>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}