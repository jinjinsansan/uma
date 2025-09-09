# Windows Defenderファイアウォール規則設定スクリプト
# PowerShellを管理者権限で実行してください

Write-Host "PostgreSQL用ファイアウォール規則を設定します..." -ForegroundColor Green

# 受信規則の追加（WSL2からのアクセス許可）
New-NetFirewallRule -DisplayName "PostgreSQL for WSL2 (Inbound)" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5432 `
    -Action Allow `
    -Profile Any `
    -Description "Allow PostgreSQL access from WSL2"

# 送信規則の追加（念のため）
New-NetFirewallRule -DisplayName "PostgreSQL for WSL2 (Outbound)" `
    -Direction Outbound `
    -Protocol TCP `
    -LocalPort 5432 `
    -Action Allow `
    -Profile Any `
    -Description "Allow PostgreSQL outbound for WSL2"

Write-Host "✅ ファイアウォール規則が追加されました" -ForegroundColor Green

# 規則の確認
Write-Host "`n現在のPostgreSQL関連規則:" -ForegroundColor Yellow
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*PostgreSQL*"} | `
    Format-Table DisplayName, Enabled, Direction, Action

Write-Host "`n設定完了！WSL2からPostgreSQLに接続できるようになりました。" -ForegroundColor Green