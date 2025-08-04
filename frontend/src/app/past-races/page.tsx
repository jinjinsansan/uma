import G1RacesPage from '@/components/pages/G1RacesPage'
import AuthGuard from '@/components/auth/AuthGuard'

export default function PastRaces() {
  return (
    <AuthGuard requireAuth={true}>
      <G1RacesPage />
    </AuthGuard>
  )
}

export const metadata = {
  title: '過去レースD-Logic体験 | 競馬予想AI',
  description: '歴史に残る名レースでD-Logic分析を体験。実際の結果と照らし合わせて精度を確認できます。',
}