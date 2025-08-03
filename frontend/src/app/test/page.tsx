export default function TestPage() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#0a0a0a', 
      color: '#ffffff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column'
    }}>
      <h1 style={{ 
        fontSize: '4rem', 
        fontWeight: '900',
        color: '#ffd700',
        textShadow: '0 0 30px rgba(255, 215, 0, 0.6)',
        fontFamily: 'Arial Black, sans-serif',
        marginBottom: '2rem'
      }}>
        D
      </h1>
      <h2 style={{ fontSize: '2rem', marginBottom: '1rem' }}>
        D-Logic AI Test Page
      </h2>
      <p style={{ color: '#cccccc' }}>
        フロントエンドサーバーが正常に動作しています
      </p>
      <div style={{ marginTop: '2rem' }}>
        <a href="/" style={{ 
          backgroundColor: '#ffd700',
          color: '#0a0a0a',
          padding: '12px 24px',
          borderRadius: '8px',
          textDecoration: 'none',
          fontWeight: 'bold'
        }}>
          TOPページに戻る
        </a>
      </div>
    </div>
  );
}