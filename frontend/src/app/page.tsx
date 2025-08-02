'use client';

import ChatInterface from '../components/chat/ChatInterface';
import StarParticles from '../components/animation/StarParticles';
import GradientBackground from '../components/animation/GradientBackground';

export default function Home() {
  return (
    <main className="min-h-screen relative overflow-hidden" style={{ backgroundColor: '#ffffff' }}>
      <GradientBackground />
      <StarParticles />
      <ChatInterface />
    </main>
  );
}
