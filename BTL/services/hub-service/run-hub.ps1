param([switch]$Demo)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path -LiteralPath 'vendor/autoload.php')) {
    composer install --no-interaction --prefer-dist
    if ($LASTEXITCODE -ne 0) { throw 'Không cài được thư viện PHP.' }
}
if ($Demo) {
    php scripts/setup-demo.php
    if ($LASTEXITCODE -ne 0) { throw 'Không tạo được dữ liệu demo.' }
    $env:DB_CONNECTION = 'sqlite'
    $env:DB_DATABASE = Join-Path $PSScriptRoot 'storage/demo.sqlite'
    if (!$env:HUB_QR_SECRET) { $env:HUB_QR_SECRET = (php -r 'echo bin2hex(random_bytes(32));') }
    Write-Host 'DEMO riêng: không dùng DB MySQL, không kết nối tiền ký quỹ thật.'
    Write-Host 'Nhân viên: hub.cs1@hunre.edu.vn | Người bán: seller@hunre.edu.vn | Người mua: buyer@hunre.edu.vn'
    Write-Host 'Mật khẩu demo: password | Mã đơn: ORD-DEMO-1, ORD-DEMO-2, ORD-DEMO-3'
}
Write-Host 'Hub Staff: http://127.0.0.1:8004/staff/'
Write-Host 'QR sinh viên: http://127.0.0.1:8004/pages/hub-qr.html'
php -S 127.0.0.1:8004 -t public public/dev-router.php
