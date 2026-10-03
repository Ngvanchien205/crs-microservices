param([string]$BaseUrl='http://127.0.0.1:8004',[string]$OrderCode='ORD-DEMO-1')
$ErrorActionPreference='Stop'
$api="$BaseUrl/api/v1/hub"
function Login-Demo([string]$email) {
    $body=@{email=$email;password='password'} | ConvertTo-Json
    (Invoke-RestMethod "$api/auth/login" -Method Post -ContentType 'application/json' -Body $body).token
}
function Assert-Hub([bool]$condition,[string]$message) { if(!$condition){throw $message} }
$staff=Login-Demo 'hub.cs1@hunre.edu.vn'
$seller=Login-Demo 'seller@hunre.edu.vn'
$buyer=Login-Demo 'buyer@hunre.edu.vn'
try {
    foreach($path in @('/staff/','/staff/css/style.css','/pages/hub-qr.html','/css/style.css','/up')) {
        $response=Invoke-WebRequest "$BaseUrl$path"
        Assert-Hub ($response.StatusCode -eq 200) "Không tải được $path"
        Write-Host "PASS tải trang/tài nguyên: $path"
    }
    $order=Invoke-RestMethod "$api/orders/$OrderCode" -Headers @{Authorization="Bearer $staff"}
    Assert-Hub ($order.order.status -eq 'ESCROW_LOCKED') 'Đơn demo đã xử lý. Dùng ORD-DEMO-2/3 hoặc đơn demo mới; không reset dữ liệu tự động.'
    $qr=Invoke-RestMethod "$api/orders/$OrderCode/dynamic-qr?role=SELLER" -Headers @{Authorization="Bearer $seller"}
    $body=@{qr_payload=$qr.data.qr_payload;scan_type='CHECKIN';size_type='MEDIUM'} | ConvertTo-Json
    $checkin=Invoke-RestMethod "$api/checkin" -Method Post -ContentType 'application/json' -Headers @{Authorization="Bearer $staff"} -Body $body
    Assert-Hub ($checkin.status -eq 'STORED_AT_HUB') 'Check-in sai trạng thái.'
    Assert-Hub ($checkin.locker.status -eq 'OCCUPIED') 'Ô tủ chưa chiếm dụng.'
    Write-Host "PASS check-in: $OrderCode -> $($checkin.locker_code)"
    $qr=Invoke-RestMethod "$api/orders/$OrderCode/dynamic-qr?role=BUYER" -Headers @{Authorization="Bearer $buyer"}
    $body=@{qr_payload=$qr.data.qr_payload;scan_type='CHECKOUT'} | ConvertTo-Json
    $checkout=Invoke-RestMethod "$api/checkout" -Method Post -ContentType 'application/json' -Headers @{Authorization="Bearer $staff"} -Body $body
    Assert-Hub ($checkout.status -eq 'INSPECTING_AT_HUB') 'Check-out sai trạng thái.'
    Assert-Hub ($checkout.locker.status -eq 'EMPTY') 'Ô tủ chưa trả trống.'
    Write-Host "PASS check-out: $OrderCode -> INSPECTING_AT_HUB, ô tủ EMPTY"
    Write-Host 'HTTP smoke test đạt. Chỉ tác động đơn demo, không giải ngân tiền.'
} finally {
    foreach($token in @($staff,$seller,$buyer)) {
        try { Invoke-RestMethod "$api/auth/logout" -Method Post -Headers @{Authorization="Bearer $token"} | Out-Null } catch { Write-Warning 'Không thu hồi được một phiên kiểm thử.' }
    }
}
