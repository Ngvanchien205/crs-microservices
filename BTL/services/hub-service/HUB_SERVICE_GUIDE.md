# Phạm vi công việc Hub Service — HUNRE E-Commerce

Thư mục dự án hiện tại: `C:\O2O\crs-microservices\BTL`.
Backend Hub được triển khai bằng **Laravel 12**, PHP 8.2+, cổng 8004.
Không thay cổng hay nội dung `docker-compose.yml` gốc. Nhánh làm việc: `feature/hub-laravel`; chưa commit/push.

## 1. Những phần trực tiếp thuộc công việc của bạn

- `C:\O2O\crs-microservices\BTL\services\hub-service\app\Http\Controllers\HubController.php`: danh sách trạm, tình trạng locker, xem đơn, phát QR, check-in/check-out. Kiểm tra chủ đơn, trạng thái, cơ sở Hub; transaction và row lock; không giải ngân.
- `C:\O2O\crs-microservices\BTL\services\hub-service\app\Services\DynamicQREngine.php`: HMAC-SHA256 rút gọn 16 ký tự, gắn mã đơn + ID chủ đơn + loại bàn giao + cửa sổ 30 giây. Chỉ chấp nhận cửa sổ hiện tại, không nhận cửa sổ trước đó.
- `C:\O2O\crs-microservices\BTL\services\hub-service\app\Http\Controllers\HubAuthController.php`: đăng nhập bằng password_hash của bảng users, phiên Bearer 8 giờ, đăng xuất/thu hồi phiên.
- `C:\O2O\crs-microservices\BTL\services\hub-service\app\Http\Middleware\HubAuthenticate.php`: xác thực token băm SHA-256 trong DB và nạp vai trò từ users ở mỗi request; không tin role/user_id do trình duyệt tự khai.
- `C:\O2O\crs-microservices\BTL\services\hub-service\app\Providers\AppServiceProvider.php`: giới hạn đăng nhập 5 lần/phút/IP, API 120 lần/phút/token.
- `C:\O2O\crs-microservices\BTL\services\hub-service\routes\api.php`: hợp đồng API. Giữ các endpoint scan-checkin/scan-checkout và alias checkin/checkout để nối giao diện.
- `C:\O2O\crs-microservices\BTL\services\hub-service\bootstrap\app.php`, `public\index.php`, `artisan`, `composer.json`, `composer.lock`, `config\`: bộ khởi động và cấu hình Laravel thật; thay entry PHP demo cũ.
- `C:\O2O\crs-microservices\BTL\frontend\hub-staff-portal\index.html`: giao diện nhân viên, đăng nhập, chọn trạm, tình trạng tủ, chọn kích cỡ, đọc/dán QR, gửi/nhận hàng. Không báo thành công khi API lỗi. Camera đọc QR nếu trình duyệt hỗ trợ BarcodeDetector, nếu không có thì dùng nội dung QR thủ công.
- `C:\O2O\crs-microservices\BTL\frontend\hub-staff-portal\css\style.css`: giao diện trạm, dùng lại stylesheet hiện có.
- `C:\O2O\crs-microservices\BTL\frontend\student-portal\pages\hub-qr.html`: màn hình sinh viên đăng nhập Hub và lấy QR đúng vai trò SELLER/BUYER, tự cập nhật khi hết cửa sổ. QR được vẽ SVG trong backend, không gửi token ra dịch vụ QR bên ngoài.
- `C:\O2O\crs-microservices\BTL\frontend\student-portal\pages\escrow-order.html`: màn hình đơn hàng có QR nhận đồ; phần gọi Hub đã dùng phiên xác thực thay vì user_id=1 cố định và không hiển thị QR giả.
- `C:\O2O\crs-microservices\BTL\services\hub-service\tests\HubTest.php`, `phpunit.xml`: kiểm thử tự động trên SQLite in-memory, không chạm DB dùng chung.
- `C:\O2O\crs-microservices\BTL\services\hub-service\scripts\smoke-test.ps1`: kiểm thử HTTP thật; chỉ dành cho tài khoản và đơn DEMO.

## 2. Các phần liên quan nhưng không thuộc quyền xử lý nghiệp vụ của Hub

- `C:\O2O\crs-microservices\BTL\shared\database-init\init-schema.sql`: schema dùng chung. Hub đọc users/hubs/escrow_orders, đọc và cập nhật lockers; cập nhật trạng thái, locker_id và updated_at của escrow_orders.
- `C:\O2O\crs-microservices\BTL\shared\database-init\zz-hub-service.sql`: migration bổ sung hub_access_tokens và hub_events. Tên zz bảo đảm chạy sau init-schema khi MySQL khởi tạo lần đầu. Không xóa/sửa bảng cũ.
- `C:\O2O\crs-microservices\BTL\gateway\nginx.conf`: chuyển `/api/v1/hub` đến `hub-service:8004`; phục vụ `/staff/` và trang sinh viên. Prefix hiện có đã bao phủ endpoint mới nên không cần đổi Gateway.
- `C:\O2O\crs-microservices\BTL\services\escrow-service\app\Http\Controllers\EscrowController.php`: thiết kế Laravel cho tạo đơn/ký quỹ/giải ngân. Hub chỉ tiếp nhận đơn ESCROW_LOCKED và bàn giao sang INSPECTING_AT_HUB. Escrow chịu trách nhiệm RELEASED/DISPUTED/REFUNDED và sổ cái.
- `C:\O2O\crs-microservices\BTL\services\escrow-service\public\index.php`: **entry hiện đang là demo JSON**, chưa phải Laravel dùng MySQL. Đơn tạo ở demo Escrow chưa tự xuất hiện trong DB của Hub Laravel.
- `C:\O2O\crs-microservices\BTL\services\auth-service\app\Http\Controllers\AuthController.php` và `public\index.php`: tài khoản, vai trò và đăng nhập chung. Token demo hiện có chưa thể dùng làm bằng chứng xác thực cho Hub. Hub có endpoint đăng nhập riêng dùng users/password_hash; tích hợp SSO chung cần nhóm Auth cung cấp hợp đồng token thật.
- `C:\O2O\crs-microservices\BTL\services\product-service\`: quản lý món đồ/tồn kho; Hub không sửa giá, trạng thái sản phẩm hay thuật toán định giá trong phạm vi này.
- `C:\O2O\crs-microservices\BTL\services\ai-engine\`: có thể hỗ trợ thẩm định ảnh trước/sau bàn giao; không cần cho luồng Hub hiện tại.
- `C:\O2O\crs-microservices\BTL\docker-compose.yml`: điều phối MySQL và Hub. `docker-compose.hub.yml` là file bổ sung cấp bí mật QR, không đổi cấu hình cổng gốc.
- `C:\O2O\crs-microservices\BTL\run-dev.ps1` và `services\local_api_server.py`: chế độ demo Python cũ, **không chạy Hub Laravel mới**. Không dùng cách này để chứng minh backend Hub Laravel.
- Thư mục `shared\postman` được ghi trong cây thiết kế nhưng chưa có collection hiện hữu trong bản checkout lúc kiểm tra. Bộ request Hub mới có tại `shared\postman\HUNRE-Hub.postman_collection.json`.

## 3. Những chức năng đã hoàn thiện

1. Tra cứu trạm và ô tủ theo Hub; giữ response `data` và `lockers`, `current_order`, `description`.
2. Đăng nhập/đăng xuất bằng users của DB, xác thực Bearer và phân quyền STUDENT/HUB_STAFF/ADMIN. Nhân viên được thao tác các Hub cùng campus; ADMIN được thao tác mọi campus. Chưa có bảng phân công từng trạm cụ thể.
3. Phát QR cho đúng người bán/người mua, đúng trạng thái đơn. Sinh SVG cục bộ, trả `qr_image_url` dạng data URI.
4. Check-in: ESCROW_LOCKED → STORED_AT_HUB; gán tủ EMPTY đúng Hub và kích cỡ yêu cầu, chuyển OCCUPIED.
5. Check-out: STORED_AT_HUB → INSPECTING_AT_HUB; chỉ trả trống đúng locker liên kết với đơn, xóa locker_id trên đơn.
6. Ghi hub_events với đơn/tủ/nhân viên/hành động/thời điểm, cùng transaction. Ghi nhật ký lỗi thì cả cập nhật tủ và đơn bị rollback.
7. Từ chối QR hết hạn, sai chữ ký, sai ID chủ đơn, sai loại QR, sai campus, quét lặp, trạng thái không hợp lệ, hết tủ hoặc liên kết tủ bị sai.
8. Giao diện hiển thị lỗi thật; chống bấm lặp; escape dữ liệu khi hiển thị locker; camera có fallback nhập QR thủ công.

QR động giảm thời gian dùng lại ảnh chụp nhưng **không thể bảo đảm chống chuyển tiếp trong cùng cửa sổ 30 giây**. Nhân viên vẫn phải kiểm tra danh tính khi bàn giao. Đây là quản lý tủ phần mềm, chưa có tích hợp khóa IoT. Chưa có service worker/manifest nên không gọi giao diện là PWA offline hoàn chỉnh.

## 4. Chạy ngay bản Hub demo độc lập

```powershell
cd C:\O2O\crs-microservices\BTL\services\hub-service
.\run-hub.ps1 -Demo
```

- Nhân viên: `http://127.0.0.1:8004/staff/`
- Sinh viên: `http://127.0.0.1:8004/pages/hub-qr.html`
- Tài khoản nhân viên: `hub.cs1@hunre.edu.vn`; người bán: `seller@hunre.edu.vn`; người mua: `buyer@hunre.edu.vn`.
- Mật khẩu demo: `password`. Chỉ dùng demo cục bộ, không đưa ra Internet.
- Đơn ban đầu: ORD-DEMO-1, ORD-DEMO-2, ORD-DEMO-3, đã ở ESCROW_LOCKED.
- DB riêng: `C:\O2O\crs-microservices\BTL\services\hub-service\storage\demo.sqlite`. Script giữ nguyên dữ liệu nếu đã có, không reset.
- Người bán đăng nhập trang QR, chọn SELLER, tạo QR cho đơn. Nhân viên đăng nhập trang staff, dán nội dung QR/quét camera, check-in. Người mua đăng nhập trang QR, chọn BUYER, lấy QR mới. Nhân viên check-out.
- Trang staff và trang sinh viên dùng hai khóa sessionStorage riêng để không ghi đè phiên của nhau. Dùng trang hub-qr độc lập để demo; trang escrow-order còn phụ thuộc service Escrow khác.
- Chạy script ở terminal riêng khi muốn kiểm tra HTTP: `.\scripts\smoke-test.ps1`. Script chuyển ORD-DEMO-1 sang INSPECTING_AT_HUB; lần sau dùng `-OrderCode ORD-DEMO-2` hoặc đơn mới, không chạy reset.

## 5. Chạy Laravel với MySQL của nhóm

1. Cài thư viện: `composer install` tại thư mục Hub. Sao chép `.env.example` sang `.env`, điền HUB_QR_SECRET ngẫu nhiên ít nhất 32 ký tự và thông tin DB. Không commit `.env` hoặc vendor.
2. MySQL local của Compose: host 127.0.0.1, port 3307, database hunre_ecommerce. Hub trong Docker: host mysql, port 3306 (Compose gốc đã khai báo).
3. DB mới: các script trong shared/database-init được MySQL chạy khi volume khởi tạo lần đầu. DB đã có volume: phải chạy riêng zz-hub-service.sql, vì MySQL không tự chạy lại init scripts. Không xóa volume để áp dụng migration.

```powershell
cd C:\O2O\crs-microservices\BTL
docker compose up -d mysql
# Chờ MySQL sẵn sàng, áp dụng migration bổ sung vào DB có sẵn:
Get-Content -Raw .\shared\database-init\zz-hub-service.sql | docker compose exec -T mysql mysql -uroot -proot hunre_ecommerce
$env:HUB_QR_SECRET = (php -r 'echo bin2hex(random_bytes(32));')
docker compose -f docker-compose.yml -f docker-compose.hub.yml up -d --build hub-service
```

Giữ bí mật này ổn định trong cấu hình triển khai; không tạo lại mỗi lần restart production. Tài khoản MySQL root/root trong Compose là demo; production cần tài khoản giới hạn quyền, secret manager, HTTPS và web server/process manager phù hợp thay cho PHP development server.

Để mở giao diện qua Nginx, chạy Gateway/các dependencies của cấu hình hiện có. Địa chỉ: `http://localhost:8000/staff/`, `http://localhost:8000/pages/hub-qr.html`, API `http://localhost:8000/api/v1/hub`.
**Điều kiện tích hợp:** nhóm Escrow phải thực sự tạo đơn ESCROW_LOCKED trong MySQL dùng chung. Hub mới không đọc tệp JSON demo của Escrow và không tự tạo giao dịch tài chính.

## 6. API và dữ liệu gửi

- POST `/api/v1/hub/auth/login`: email, password → token, user, expires_at.
- POST `/api/v1/hub/auth/logout`: Bearer → thu hồi phiên.
- GET `/api/v1/hub/stations`: danh sách trạm, công khai.
- GET `/api/v1/hub/lockers/{hubId}` hoặc `/lockers?hub_id=1`: Bearer nhân viên/admin.
- GET `/api/v1/hub/orders/{orderCode}`: nhân viên cùng campus hoặc buyer/seller của đơn.
- GET `/api/v1/hub/orders/{orderCode}/dynamic-qr?role=SELLER|BUYER`: Bearer chủ đơn. user_id cũ vẫn nhận nhưng phải trùng người đăng nhập.
- POST `/api/v1/hub/checkin` hoặc `/scan-checkin`: Bearer nhân viên; DTO cũ gồm order_code, seller_id, token, size_type tùy chọn. Có thể gửi qr_payload thay cho ba trường đầu. scan_type CHECKIN nếu có.
- POST `/api/v1/hub/checkout` hoặc `/scan-checkout`: Bearer nhân viên; order_code, buyer_id, token; hoặc qr_payload. scan_type CHECKOUT nếu có.

```json
{"qr_payload":"HUNRE:ORD-DEMO-2:1:SELLER:0123456789ABCDEF","scan_type":"CHECKIN","size_type":"MEDIUM"}
```

Token ví dụ trên chỉ minh họa, không phải chữ ký hợp lệ. Dùng mã thực tế từ trang QR.
Giữ `success`, `message`, `locker` dạng object và bổ sung `locker_code`, `status`, `order_code`, `instruction`. Không trả thành công giả để tương thích API demo thiếu QR/xác thực: client cần cập nhật theo giao diện đã sửa.
Mã lỗi: 400 QR sai/hết hạn; 401 chưa đăng nhập; 403 sai quyền/chủ đơn/campus; 404 thiếu đơn/trạm; 409 xung đột trạng thái hoặc ô tủ; 422 dữ liệu sai; 429 vượt giới hạn.

## 7. Kiểm thử và giới hạn xác minh

```powershell
cd C:\O2O\crs-microservices\BTL\services\hub-service
composer test
php artisan route:list --path=hub
.\scripts\smoke-test.ps1 -OrderCode ORD-DEMO-1
```

PHPUnit sử dụng DB SQLite in-memory tách biệt; bao phủ login/logout/expiry/rate-limit, phân quyền, chủ đơn, QR, tủ và rollback. HTTP smoke test dùng SQLite demo riêng. Chưa kiểm chứng tranh chấp row lock trên MySQL thực, Docker build hay tích hợp toàn hệ thống khi Docker daemon chưa chạy. Chưa kiểm thử camera trên thiết bị vật lý. Không coi smoke tải HTML/CSS là đã kiểm thử UI bằng trình duyệt hoàn chỉnh.

Kết quả kiểm tra ngày 03/10/2026: PHP 8.5.9 local; Laravel 12.69.3; PHPUnit 12 ca đạt. Đã chạy HTTP smoke thành công cho ORD-DEMO-1, nên đơn này hiện ở INSPECTING_AT_HUB; dùng ORD-DEMO-2 hoặc ORD-DEMO-3 để thử tiếp. Đã kiểm tra cú pháp JavaScript của ba trang liên quan. Quy trình bootstrap tham khảo [tài liệu Laravel](https://api.laravel.com/docs/12.x/Illuminate/Foundation/Configuration/ApplicationBuilder.html).
