# D-Logic AI ユーザーデータベース設計

## テーブル構成

### 1. users テーブル
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    image_url TEXT,
    subscription_type ENUM('free', 'premium') DEFAULT 'free',
    free_trial_start_date DATETIME,
    free_trial_end_date DATETIME,
    premium_start_date DATETIME,
    premium_end_date DATETIME,
    total_queries_used INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2. user_queries テーブル（使用履歴）
```sql
CREATE TABLE user_queries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    query_type ENUM('horse_analysis', 'race_analysis', 'general_chat') NOT NULL,
    query_text TEXT,
    response_text LONGTEXT,
    processing_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 3. user_payments テーブル（決済履歴）
```sql
CREATE TABLE user_payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    payment_provider ENUM('stripe', 'paypal') NOT NULL,
    payment_intent_id VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'JPY',
    subscription_period INT, -- 月数
    status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 4. line_users テーブル（LINE連携）
```sql
CREATE TABLE line_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    line_user_id VARCHAR(255) UNIQUE NOT NULL,
    tickets_received INT DEFAULT 0,
    friend_added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## 使用制限ルール

### 無料会員
- 初回登録時：7日間無料
- LINE友達追加：+3日間延長チケット
- 1日あたり5回まで馬名分析可能
- レース分析は無制限（過去レースのみ）

### 有料会員
- 月額料金：1,980円
- 馬名分析：無制限
- レース分析：無制限（未来レース含む）
- 優先サポート

## API エンドポイント設計

### 認証関連
- `GET /api/auth/user` - ユーザー情報取得
- `POST /api/auth/register` - 初回登録（Google OAuth後）

### 使用制限チェック
- `GET /api/user/quota` - 残り使用回数確認
- `POST /api/user/use-quota` - 使用回数消費

### 決済関連
- `POST /api/payments/create-subscription` - サブスクリプション作成
- `GET /api/payments/history` - 決済履歴取得

### LINE連携
- `POST /api/line/link` - LINEアカウント連携
- `POST /api/line/add-ticket` - 延長チケット付与