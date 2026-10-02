# TÀI LIỆU PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG (UML & SYSTEM ARCHITECTURE)
## Đề Tài: Sàn Giao Dịch & Trao Đổi Đồ Dùng Học Tập Sinh Viên HUNRE (Mô Hình O2O & AI)
- **Trường:** Đại học Tài nguyên và Môi trường Hà Nội (HUNRE)
- **Khoa:** Công Nghệ Thông Tin
- **Môn học:** Phân tích & Thiết kế Hệ thống Thông tin / Công nghệ Phần mềm

---

## 1. SƠ ĐỒ KIẾN TRÚC HỆ THỐNG (MICROSERVICES ARCHITECTURE DIAGRAM)

Hệ thống được thiết kế theo kiến trúc Microservices chuẩn Enterprise, đóng gói hoàn chỉnh bằng Docker & Docker Compose:

```mermaid
graph TB
    subgraph Clients["TẦNG CLIENT (GIAO DIỆN NGƯỜI DÙNG)"]
        SP["Student Portal (Sàn SV O2O)"]
        AP["Admin Portal (Quản trị & Đối soát)"]
        HP["Hub Staff PWA (Máy quét QR Locker)"]
    end

    subgraph Gateway["TẦNG API GATEWAY & REVERSE PROXY (CỔNG 8000)"]
        NGX["Nginx API Gateway / Static Server"]
    end

    subgraph Services["TẦNG MICROSERVICES BACKEND"]
        AUTH["Auth Service (Port 8001)<br/>- KYC @hunre.edu.vn<br/>- Trust Score Engine"]
        PROD["Product Service (Port 8002)<br/>- CRUD Sản phẩm & Danh mục<br/>- Wishlist & Reviews"]
        ESCROW["Smart Escrow Service (Port 8003)<br/>- Saga Orchestrator<br/>- Đóng băng & Giải ngân cọc"]
        HUB["Hub Logistics Service (Port 8004)<br/>- Dynamic QR TOTP 30s<br/>- Quản lý Smart Locker"]
        AI["AI Engine (Port 8005)<br/>- Gemini Multimodal Vision<br/>- Barter Graph Solver<br/>- Dutch Auction Time-Decay"]
    end

    subgraph Storage["TẦNG DỮ LIỆU & CACHE"]
        DB[("MySQL 8.0 (Port 3307)<br/>hunre_ecommerce")]
        REDIS[("Redis 7.0 (Port 6379)<br/>TOTP Cache & Rate Limit")]
    end

    SP -->|HTTP/Port 8000| NGX
    AP -->|HTTP/Port 8000| NGX
    HP -->|HTTP/Port 8000| NGX

    NGX -->|/api/v1/auth| AUTH
    NGX -->|/api/v1/products| PROD
    NGX -->|/api/v1/escrow| ESCROW
    NGX -->|/api/v1/hub| HUB
    NGX -->|/api/v1/ai| AI

    AUTH --> DB
    PROD --> DB
    ESCROW --> DB
    HUB --> DB
    HUB --> REDIS
    ESCROW --> REDIS
```

---

## 2. SƠ ĐỒ CA SỬ DỤNG (USE CASE DIAGRAM)

### 2.1. Phân loại tác nhân (Actors)
1. **Sinh viên HUNRE (Student):** Vừa đóng vai trò Người mua (Buyer) vừa là Người bán (Seller).
2. **Nhân viên Trạm Hub (Hub Staff):** Đoàn Thanh niên trực trạm bàn giao đồ và vận hành ô tủ thông minh.
3. **Quản trị viên (Admin):** Quản lý đối soát tài chính, đơn hàng, khóa tài khoản vi phạm.
4. **Hệ thống AI (AI Service Agent):** Thẩm định ảnh đồ cũ 4 tiêu chí, gợi ý giá, giải thuật toán hoán đổi đồ.

```mermaid
graph LR
    Student((Sinh viên HUNRE))
    Staff((Nhân viên Trạm Hub))
    Admin((Quản trị viên))
    AISystem((Hệ thống AI))

    subgraph PhânHệSinhViên["PHÂN HỆ GIAO DỊCH SINH VIÊN"]
        UC1[Đăng ký & KYC Email @hunre.edu.vn]
        UC2[Đăng bán đồ dùng & Thẩm định AI]
        UC3[Xem danh mục & Tìm kiếm sản phẩm]
        UC4[Thương lượng & Đàm phán giá tự động]
        UC5[Tạo đơn Ký quỹ Smart Escrow]
        UC6[Tham gia Chu trình Đổi đồ Barter Graph]
        UC7[Lấy mã Dynamic QR nhận đồ]
    end

    subgraph PhânHệTramHub["PHÂN HỆ TRẠM HUB LOGISTICS"]
        UC8[Quét QR Check-in nhận đồ từ người bán]
        UC9[Phân bổ & Mở ô tủ Smart Locker]
        UC10[Quét QR Check-out bàn giao đồ cho người mua]
        UC11[Xác nhận bàn giao & Giải phóng ô tủ]
    end

    subgraph PhânHệQuanTri["PHÂN HỆ QUẢN TRỊ & ĐỐI SOÁT"]
        UC12[Quản lý & Khóa tài khoản vi phạm]
        UC13[Xử lý đơn hàng 8 Tab trạng thái]
        UC14[Đối soát Tài chính & Ma trận COD]
        UC15[Trọng tài xử lý Khiếu nại Dispute]
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    Student --> UC6
    Student --> UC7

    UC2 -.->|<<include>>| AISystem
    UC4 -.->|<<include>>| AISystem
    UC6 -.->|<<include>>| AISystem

    Staff --> UC8
    Staff --> UC9
    Staff --> UC10
    Staff --> UC11

    Admin --> UC12
    Admin --> UC13
    Admin --> UC14
    Admin --> UC15
```

---

## 3. SƠ ĐỒ THỰC THỂ LIÊN KẾT (ENTITY RELATIONSHIP DIAGRAM - ERD)

```mermaid
erDiagram
    USERS ||--o{ PRODUCTS : "đăng bán"
    USERS ||--o{ ESCROW_ORDERS : "mua / bán"
    USERS ||--o{ ESCROW_LEDGER : "ghi sổ số dư"
    CATEGORIES ||--o{ PRODUCTS : "phân loại"
    PRODUCTS ||--o{ PRODUCT_IMAGES : "chứa hình ảnh"
    HUBS ||--o{ LOCKERS : "quản lý ô tủ"
    HUBS ||--o{ ESCROW_ORDERS : "điểm trung chuyển"
    LOCKERS ||--o{ ESCROW_ORDERS : "lưu trữ hàng"
    ESCROW_ORDERS ||--o{ ESCROW_LEDGER : "phát sinh giao dịch"
    ESCROW_ORDERS ||--o| DISPUTES : "khiếu nại"
    BARTER_CYCLES ||--o{ BARTER_CYCLE_NODES : "chứa các mắt xích"
    PRODUCTS ||--o{ BARTER_CYCLE_NODES : "tham gia đổi"

    USERS {
        bigint id PK
        string student_code UK
        string full_name
        string email UK
        int trust_score
        enum role "STUDENT, HUB_STAFF, ADMIN"
        decimal wallet_balance
        decimal escrow_locked_balance
    }

    CATEGORIES {
        int id PK
        string name
        string slug UK
    }

    PRODUCTS {
        bigint id PK
        bigint seller_id FK
        int category_id FK
        string title
        decimal original_price
        decimal current_price
        decimal floor_price
        string condition_grade "GRADE_S, A, B, C"
        float ai_defect_score
        string desired_exchange_items
        string status
    }

    HUBS {
        int id PK
        string name
        string campus "CS1_HA_NOI, CS2"
        string location_detail
    }

    LOCKERS {
        int id PK
        int hub_id FK
        string locker_code UK
        enum status "EMPTY, OCCUPIED, MAINTENANCE"
    }

    ESCROW_ORDERS {
        bigint id PK
        string order_code UK
        bigint buyer_id FK
        bigint seller_id FK
        bigint product_id FK
        int hub_id FK
        int locker_id FK
        decimal escrow_amount
        enum status "INITIATED, ESCROW_LOCKED, STORED_AT_HUB, RELEASED, DISPUTED"
    }

    ESCROW_LEDGER {
        bigint id PK
        bigint order_id FK
        bigint user_id FK
        enum transaction_type "HOLD_DEPOSIT, RELEASE_TO_SELLER, REFUND"
        decimal amount
        string idempotency_key UK
    }
```

---

## 4. CÁC SƠ ĐỒ TUẦN TỰ NGHIỆP VỤ (SEQUENCE DIAGRAMS)

### 4.1. Luồng Thẩm Định Hình Ảnh AI 4 Tiêu Chí & Tự Động Điền Form Đăng Bán
```mermaid
sequenceDiagram
    actor SinhVien as Sinh viên (Người bán)
    participant UI as Student Portal (Frontend)
    participant GW as Nginx Gateway (Port 8000)
    participant AI as AI Engine (Port 8005)
    participant Gemini as Google Gemini Multimodal API
    participant ProdSvc as Product Service (Port 8002)
    participant DB as MySQL DB

    SinhVien->>UI: Tải ảnh chụp thực tế đồ dùng lên
    UI->>GW: POST /api/v1/ai/cv/inspect (Multipart Image)
    GW->>AI: Chuyển tiếp ảnh
    AI->>AI: Phân tích Gradient sắc nét gx/gy & tỷ lệ hao mòn defect_ratio
    AI->>Gemini: Gửi Prompt 4 câu hỏi + Base64 ảnh
    Gemini-->>AI: Trả về JSON (Tên đồ, % độ mới, Giá mới thị trường, Định giá & Giá sàn)
    AI-->>GW: Trả kết quả 4 tiêu chí + chữ ký số dHash
    GW-->>UI: Hiển thị Thẻ Thẩm Định AI
    UI->>UI: Tự động điền 100% dữ liệu vào Form Đăng Bán
    SinhVien->>UI: Bấm "Đăng Bán Lên Sàn Chợ HUNRE"
    UI->>GW: POST /api/v1/products (Thông tin sản phẩm)
    GW->>ProdSvc: Ghi nhận sản phẩm
    ProdSvc->>DB: INSERT INTO products (Status = ACTIVE)
    ProdSvc-->>UI: Thông báo đăng bài thành công
```

### 4.2. Luồng Ký Quỹ Thông Minh Smart Escrow & Giao Nhận O2O Tại Trạm Hub
```mermaid
sequenceDiagram
    actor Buyer as Sinh viên Mua
    actor Seller as Sinh viên Bán
    actor Staff as Nhân viên Trạm Hub
    participant Escrow as Escrow Service
    participant HubSvc as Hub Logistics Service
    participant Locker as Smart Locker (Nhà A)
    participant Ledger as Sổ cái Ký quỹ (MySQL)

    Buyer->>Escrow: 1. Đặt mua sản phẩm & Ký quỹ tiền cọc
    Escrow->>Ledger: Đóng băng tiền cọc (HOLD_DEPOSIT) -> Trạng thái ESCROW_LOCKED
    Escrow-->>Seller: Thông báo: Mang đồ ra gửi tại Trạm Hub CS1

    Seller->>Staff: 2. Mang đồ ra Hub xuất trình mã gửi
    Staff->>HubSvc: Quét mã Check-in
    HubSvc->>Locker: Mở ô tủ trống (Trạng thái: OCCUPIED)
    HubSvc->>Escrow: Cập nhật: Đồ đã lưu tủ (STORED_AT_HUB)
    
    Buyer->>Staff: 3. Đến Hub mở Dynamic QR TOTP (xoay vòng 30s)
    Staff->>HubSvc: Quét xác thực TOTP Check-out
    HubSvc->>Locker: Mở ô tủ cho người mua lấy đồ kiểm tra
    
    alt Người mua hài lòng với tình trạng đồ
        Buyer->>Escrow: Bấm "Xác nhận hài lòng"
        Escrow->>Ledger: Giải ngân 100% tiền cọc cho Người bán (RELEASE_TO_SELLER)
        Escrow->>Escrow: Cộng +5 Điểm Uy Tín (Trust Score) cho cả 2 bên
        HubSvc->>Locker: Giải phóng ô tủ (Trạng thái: EMPTY)
    else Hàng lỗi / không đúng mô tả
        Buyer->>Escrow: Gửi yêu cầu Khiếu nại (DISPUTE)
        Escrow->>Escrow: Đóng băng tiền, chuyển Admin/Trạm Hub hoàn cọc 100%
    end
```

---

## 5. SƠ ĐỒ CHUYỂN TRẠNG THÁI (STATE MACHINE DIAGRAM)

```mermaid
stateDiagram-v2
    [*] --> INITIATED: Người mua khởi tạo đơn hàng
    INITIATED --> ESCROW_LOCKED: Khóa tiền cọc thành công (Ví điện tử / Ký quỹ)
    INITIATED --> CANCELLED: Hủy trước khi nạp cọc

    ESCROW_LOCKED --> STORED_AT_HUB: Người bán gửi đồ vào ô tủ Smart Locker
    ESCROW_LOCKED --> CANCELLED: Người bán quá hạn gửi đồ (Hoàn tiền mua)

    STORED_AT_HUB --> BUYER_CHECKOUT: Người mua quét TOTP QR nhận đồ kiểm tra

    BUYER_CHECKOUT --> RELEASED: Người mua hài lòng -> Giải ngân cho người bán (+5 Trust Score)
    BUYER_CHECKOUT --> DISPUTED: Phát hiện trầy xước/hư hỏng -> Đóng băng tiền

    DISPUTED --> REFUNDED: Trọng tài Trạm Hub duyệt hoàn tiền 100% cho người mua
    DISPUTED --> RELEASED: Thương lượng thành công / Giải ngân

    RELEASED --> [*]
    REFUNDED --> [*]
    CANCELLED --> [*]
```

---

## 6. SƠ ĐỒ HOẠT ĐỘNG (ACTIVITY DIAGRAM)

```mermaid
flowchart TD
    Start([Bắt đầu]) --> Step1[Người bán chụp ảnh sản phẩm thực tế]
    Step1 --> Step2[AI Vision quét ảnh & đánh giá 4 tiêu chí]
    Step2 --> Step3[Hệ thống tự động điền Form & Người bán xác nhận đăng]
    Step3 --> Step4[Người mua duyệt danh mục / đàm phán giá với AI]
    Step4 --> Step5{Người bán chấp nhận giá?}
    Step5 -- Không --> Step4
    Step5 -- Có --> Step6[Người mua tạo đơn & Khóa tiền ký quỹ Smart Escrow]
    Step6 --> Step7[Người bán mang đồ đến Trạm Hub CS1/CS2]
    Step7 --> Step8[Nhân viên Hub quét Check-in, cất đồ vào Smart Locker]
    Step8 --> Step9[Người mua nhận thông báo & mã Dynamic QR TOTP 30s]
    Step9 --> Step10[Người mua đến Hub xuất trình QR để nhận đồ kiểm tra]
    Step10 --> Step11{Đồ có đúng như mô tả AI không?}
    Step11 -- Có --> Step12[Người mua bấm Xác nhận hài lòng]
    Step12 --> Step13[Hệ thống giải ngân cho người bán & cộng điểm Trust Score]
    Step11 -- Không --> Step14[Gửi yêu cầu Khiếu nại Dispute tại bàn Hub]
    Step14 --> Step15[Nhân viên Hub đối soát hoàn cọc 100% cho người mua]
    Step13 --> End([Kết thúc giao dịch an toàn])
    Step15 --> End
```
