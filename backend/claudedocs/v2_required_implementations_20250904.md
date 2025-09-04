# V2システム リリースに必要な実装リスト
## 作成日: 2025年9月4日 19:00

## 現状確認
- ✅ Supabaseテーブル構成は完備
  - `v2_columns`: コラムデータ（access_type, required_points含む）
  - `v2_column_reads`: 閲覧記録用
  - `v2_column_views`: ビュー数記録用
  - `v2_user_points`: ユーザーポイント管理
  - `v2_point_transactions`: ポイント取引履歴
- ✅ 管理画面でコラムのポイント設定可能
- ✅ フロントエンドにaccess_type定義済み

## 🔴 必須実装項目（リリース前）

### 1. コラムポイント消費機能の実装
#### バックエンドAPI作成
```python
# /mnt/e/dev/Cusor/chatbot/uma/backend/api/v2/column.py (新規作成)
from fastapi import APIRouter, HTTPException, Depends
from services.v2.points_service import V2PointsService

router = APIRouter(prefix="/api/v2/column", tags=["v2-column"])

@router.post("/view/{column_id}")
async def view_column_with_points(
    column_id: str,
    user_id: str = Depends(get_current_user)
):
    # 1. コラム情報取得
    column = supabase.table("v2_columns").select("*").eq("id", column_id).single().execute()
    
    # 2. アクセスタイプ確認
    if column.data["access_type"] == "point_required":
        required_points = column.data["required_points"]
        
        # 3. 既読チェック（既に読んでいれば課金しない）
        existing_read = supabase.table("v2_column_reads")\
            .select("*")\
            .eq("column_id", column_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not existing_read.data:
            # 4. ポイント消費処理
            points_service = V2PointsService()
            try:
                await points_service.use_points(
                    user_id=user_id,
                    amount=required_points,
                    transaction_type="column_view",
                    description=f"コラム閲覧: {column.data['title']}",
                    related_entity_id=column_id
                )
                
                # 5. 閲覧記録保存
                supabase.table("v2_column_reads").insert({
                    "column_id": column_id,
                    "user_id": user_id,
                    "read_at": datetime.now().isoformat()
                }).execute()
                
            except InsufficientPointsError:
                return {"error": "ポイントが不足しています", "required": required_points}
    
    # 6. ビュー数更新
    supabase.table("v2_column_views").insert({
        "column_id": column_id,
        "user_id": user_id,
        "viewed_at": datetime.now().isoformat()
    }).execute()
    
    return {"success": True, "content": column.data}
```

#### フロントエンド修正
```tsx
// /src/app/v2/column/[id]/page.tsx の修正
const fetchColumn = async () => {
  // 管理者APIではなく、ポイント消費APIを使用
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v2/column/view/${columnId}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session?.user?.email}`
      }
    }
  );
  
  const data = await response.json();
  
  if (data.error === 'ポイントが不足しています') {
    setAccessDenied(true);
    setAccessMessage(`このコラムを閲覧するには${data.required}ポイントが必要です`);
    return;
  }
  
  setColumn(data.content);
};
```

### 2. 楽観的ロック（同時実行制御）の実装
```python
# /services/v2/points_service.py の修正
async def use_points(self, user_id: str, amount: int, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # トランザクション開始
            # 現在のポイントとバージョンを取得
            current = supabase.table("v2_user_points")\
                .select("current_points, version")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            if not current.data:
                raise UserNotFoundError()
            
            current_points = current.data["current_points"]
            current_version = current.data.get("version", 0)
            
            if current_points < amount:
                raise InsufficientPointsError()
            
            new_points = current_points - amount
            
            # バージョンチェック付き更新
            result = supabase.table("v2_user_points")\
                .update({
                    "current_points": new_points,
                    "total_spent": current.data["total_spent"] + amount,
                    "version": current_version + 1,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("user_id", user_id)\
                .eq("version", current_version)\  # 楽観的ロック
                .execute()
            
            if not result.data:
                # バージョン不一致 = 他で更新された
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))  # リトライ間隔
                    continue
                raise ConcurrencyError("ポイント更新に失敗しました")
            
            # トランザクション記録
            await self._record_transaction(user_id, -amount, new_points, **kwargs)
            return result.data[0]
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
```

### 3. ポイント履歴表示画面の実装
```tsx
// /src/components/v2/PointsHistory.tsx (新規作成)
import React, { useState, useEffect } from 'react';
import { v2ApiClient } from '@/lib/v2/api-client';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ArrowUpCircle, ArrowDownCircle, Clock } from 'lucide-react';

interface PointTransaction {
  id: string;
  amount: number;
  transaction_type: string;
  description: string;
  balance_after: number;
  created_at: string;
}

export function PointsHistory() {
  const [transactions, setTransactions] = useState<PointTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, [page]);

  const fetchHistory = async () => {
    try {
      const response = await v2ApiClient.getPointsHistory({
        page,
        limit: 20
      });
      
      if (page === 1) {
        setTransactions(response.data);
      } else {
        setTransactions(prev => [...prev, ...response.data]);
      }
      
      setHasMore(response.has_more);
    } catch (error) {
      console.error('履歴取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionIcon = (amount: number) => {
    return amount > 0 ? (
      <ArrowUpCircle className="w-5 h-5 text-green-500" />
    ) : (
      <ArrowDownCircle className="w-5 h-5 text-red-500" />
    );
  };

  const getTransactionTypeLabel = (type: string) => {
    const labels = {
      'initial_grant': '初回付与',
      'line_connection': 'LINE連携',
      'referral_bonus': '紹介ボーナス',
      'chat_create': 'チャット作成',
      'column_view': 'コラム閲覧',
      'admin_adjustment': '管理者調整'
    };
    return labels[type] || type;
  };

  return (
    <div className="bg-[#181A20] rounded-lg p-6 border border-[#2B3139]">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-5 h-5 text-[#F0B90B]" />
        <h3 className="text-lg font-semibold text-white">ポイント履歴</h3>
      </div>

      <div className="space-y-3">
        {transactions.map(transaction => (
          <div
            key={transaction.id}
            className="flex items-center justify-between p-3 bg-[#0B0E11] rounded-lg"
          >
            <div className="flex items-center gap-3">
              {getTransactionIcon(transaction.amount)}
              <div>
                <p className="text-sm font-medium text-white">
                  {transaction.description}
                </p>
                <p className="text-xs text-gray-400">
                  {getTransactionTypeLabel(transaction.transaction_type)} • 
                  {format(new Date(transaction.created_at), 'M/d HH:mm', { locale: ja })}
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <p className={`text-lg font-bold ${
                transaction.amount > 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                {transaction.amount > 0 ? '+' : ''}{transaction.amount} P
              </p>
              <p className="text-xs text-gray-400">
                残高: {transaction.balance_after} P
              </p>
            </div>
          </div>
        ))}
      </div>

      {hasMore && (
        <button
          onClick={() => setPage(prev => prev + 1)}
          className="w-full mt-4 py-2 text-sm text-[#F0B90B] hover:text-[#FCD535] transition-colors"
        >
          もっと見る
        </button>
      )}
    </div>
  );
}
```

### 4. マイページにポイント履歴タブを追加
```tsx
// /src/app/v2/my-account/page.tsx の修正
import { PointsHistory } from '@/components/v2/PointsHistory';

// タブ追加
const [activeTab, setActiveTab] = useState<'overview' | 'history' | 'referral'>('overview');

// レンダリング部分
<div className="flex gap-4 mb-6">
  <button
    onClick={() => setActiveTab('overview')}
    className={`px-4 py-2 rounded-lg ${
      activeTab === 'overview' ? 'bg-[#F0B90B] text-black' : 'bg-[#181A20] text-white'
    }`}
  >
    概要
  </button>
  <button
    onClick={() => setActiveTab('history')}
    className={`px-4 py-2 rounded-lg ${
      activeTab === 'history' ? 'bg-[#F0B90B] text-black' : 'bg-[#181A20] text-white'
    }`}
  >
    履歴
  </button>
  <button
    onClick={() => setActiveTab('referral')}
    className={`px-4 py-2 rounded-lg ${
      activeTab === 'referral' ? 'bg-[#F0B90B] text-black' : 'bg-[#181A20] text-white'
    }`}
  >
    友達紹介
  </button>
</div>

{activeTab === 'overview' && <PointsDisplay />}
{activeTab === 'history' && <PointsHistory />}
{activeTab === 'referral' && <ReferralSection />}
```

### 5. データベーススキーマ追加
```sql
-- v2_user_pointsテーブルにversion列を追加（楽観的ロック用）
ALTER TABLE v2_user_points 
ADD COLUMN version INTEGER DEFAULT 0;

-- インデックス追加（パフォーマンス改善）
CREATE INDEX idx_v2_column_reads_user_column 
ON v2_column_reads(user_id, column_id);

CREATE INDEX idx_v2_point_transactions_user_created 
ON v2_point_transactions(user_id, created_at DESC);
```

## 📋 実装チェックリスト

### 必須（リリース前）
- [ ] コラムポイント消費API実装（バックエンド）
- [ ] コラム閲覧時のポイント消費処理（フロントエンド）
- [ ] 楽観的ロック実装
- [ ] ポイント履歴表示コンポーネント作成
- [ ] マイページにポイント履歴タブ追加
- [ ] v2_user_pointsテーブルにversion列追加

### 推奨（リリース後1週間以内）
- [ ] 管理画面でのポイント手動調整機能
- [ ] ポイント統計ダッシュボード
- [ ] エラー時の詳細ログ記録

## 🚀 実装順序

1. **Day 1**: データベーススキーマ更新 + 楽観的ロック実装
2. **Day 2**: コラムポイント消費API実装
3. **Day 3**: ポイント履歴UI実装
4. **Day 4**: テスト + バグ修正
5. **Day 5**: リリース準備

## ⏱️ 推定工数

| タスク | 工数 |
|--------|------|
| コラムAPI実装 | 4時間 |
| 楽観的ロック | 2時間 |
| 履歴UI | 3時間 |
| マイページ改修 | 2時間 |
| テスト | 3時間 |
| **合計** | **14時間（2日）** |

---
作成者: Claude
作成日時: 2025-09-04 19:00