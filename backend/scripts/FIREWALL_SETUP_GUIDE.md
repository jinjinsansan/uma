# Windows Defenderファイアウォール設定ガイド

## 🔧 GUI操作での設定手順

### 1. Windows Defenderファイアウォールを開く
1. Windowsキー + R
2. `wf.msc` と入力してEnter
3. 「セキュリティが強化されたWindows Defenderファイアウォール」が開きます

### 2. 受信規則の追加
1. 左側メニューの「受信の規則」をクリック
2. 右側の「新しい規則...」をクリック
3. 規則の種類: 「ポート」を選択 → 次へ
4. プロトコルとポート:
   - 「TCP」を選択
   - 「特定のローカルポート」: `5432` を入力
   - 次へ
5. 操作: 「接続を許可する」を選択 → 次へ
6. プロファイル: すべてチェック（ドメイン、プライベート、パブリック） → 次へ
7. 名前:
   - 名前: `PostgreSQL for WSL2`
   - 説明: `Allow PostgreSQL access from WSL2 (port 5432)`
   - 完了

### 3. 送信規則の追加（オプション）
同様の手順で「送信の規則」も追加できます（通常は不要）

## 🚀 PowerShellでの簡単設定

管理者権限でPowerShellを開いて以下のコマンドを実行：

```powershell
# 受信規則の追加
New-NetFirewallRule -DisplayName "PostgreSQL for WSL2" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow

# 規則の確認
Get-NetFirewallRule -DisplayName "PostgreSQL for WSL2"
```

## ✅ 設定確認方法

### Windows側で確認
```powershell
# PowerShellで規則を確認
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*PostgreSQL*"}
```

### WSL2側で確認
```bash
# 接続テスト
python3 /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/simple_pckeiba_test.py
```

## 🔐 より安全な設定（推奨）

特定のIPアドレス範囲のみ許可する場合：

```powershell
# WSL2のIPアドレス範囲（172.16.0.0/12）のみ許可
New-NetFirewallRule -DisplayName "PostgreSQL for WSL2 (Secure)" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5432 `
    -Action Allow `
    -RemoteAddress 172.16.0.0/12 `
    -Description "Allow PostgreSQL from WSL2 subnet only"
```

## ❌ 規則の削除方法

不要になった場合の削除：

```powershell
# PowerShellで削除
Remove-NetFirewallRule -DisplayName "PostgreSQL for WSL2"
```

または、GUIで：
1. Windows Defenderファイアウォールを開く
2. 「受信の規則」から「PostgreSQL for WSL2」を右クリック
3. 「削除」を選択

## 📝 注意事項

- ファイアウォール規則は永続的に保存されます
- PC再起動後も有効です
- PostgreSQLサービスの再起動は不要です
- pg_hba.confの設定（0.0.0.0/0許可）はそのままで大丈夫です

## 🧪 動作テスト

設定後、以下のスクリプトで接続確認：

```bash
cd /mnt/e/dev/Cusor/chatbot/uma/backend/scripts
python3 simple_pckeiba_test.py
```

成功すると以下のような表示：
```
✅ 接続成功！
nvd_ra テーブルのレコード数: 315,509
```