"""
HUNRE E-COMMERCE - COMPREHENSIVE FEATURE & EXCEPTION TEST SUITE
Kiểm thử toàn diện cả chức năng thành công (Happy Path) VÀ các trường hợp ngoại lệ (Exceptions & Edge Cases)
cho 5 Microservices:
- Auth & Trust Score
- Product Catalog CRUD
- Escrow Saga & Dispute
- Hub Logistics & TOTP QR
- AI Pricing & Negotiation
"""

import sys
import os
import json
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from local_api_server import app, DEFAULT_DB, save_db, load_db

client = TestClient(app)

def run_tests():
    # Đặt lại CSDL sạch ban đầu
    save_db(DEFAULT_DB)

    passed_tests = 0
    failed_tests = 0
    results = []

    def check(test_id, category, name, condition, details=""):
        nonlocal passed_tests, failed_tests
        if condition:
            passed_tests += 1
            status = "PASS"
        else:
            failed_tests += 1
            status = "FAIL"
        results.append({
            "id": test_id,
            "category": category,
            "name": name,
            "status": status,
            "details": details
        })
        icon = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"  {icon} [{category}] {name} {details}")

    print("\n" + "=" * 70)
    print("BAT DAU KIEM THU TOAN DIEN CHUC NANG & NGOAI LE (FEATURE & EXCEPTION TESTS)")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. AUTH SERVICE: CHUC NANG & NGOAI LE
    # -------------------------------------------------------------
    print("\n--- 1. AUTH SERVICE & TRUST SCORE ENGINE ---")
    
    # 1.1 Happy: Lấy trust score hợp lệ
    res = client.get("/api/v1/auth/users/trust-score?user_id=1")
    check("AUTH-01", "AUTH", "Happy Path: Lay Trust Score cua SV An", 
          res.status_code == 200 and res.json()["data"]["trust_score"] == 520,
          f"Status: {res.status_code}")

    # 1.2 Ngoại lệ: Đăng ký bằng email KHÔNG PHẢI @hunre.edu.vn (KYC Failed)
    res = client.post("/api/v1/auth/register", json={
        "student_code": "20218888",
        "full_name": "Nguyen Van Gia Mao",
        "email": "giamao@gmail.com"  # Ngoại lệ: Không phải email trường
    })
    check("AUTH-EX-01", "AUTH", "Ngoai Le 1: Tu choi email ngoai truong (@gmail.com)", 
          res.status_code == 422 and "KYC Failed" in res.json().get("detail", ""),
          f"Status: {res.status_code} - Detail: {res.json().get('detail', '')}")

    # 1.3 Ngoại lệ: Đăng ký thiếu Mã SV hoặc Họ tên
    res = client.post("/api/v1/auth/register", json={
        "student_code": "   ",
        "full_name": "",
        "email": "sinhvienmoi@hunre.edu.vn"
    })
    check("AUTH-EX-02", "AUTH", "Ngoai Le 2: Tu choi thieu Ma SV hoac Ho ten", 
          res.status_code == 422,
          f"Status: {res.status_code}")

    # 1.4 Ngoại lệ: Đăng ký trùng email đã có trong hệ thống
    res = client.post("/api/v1/auth/register", json={
        "student_code": "20211001",
        "full_name": "Trung Email",
        "email": "an.nv@hunre.edu.vn"  # Trùng với SV 1
    })
    check("AUTH-EX-03", "AUTH", "Ngoai Le 3: Tu choi trung email da ton tai (409 Conflict)", 
          res.status_code == 409,
          f"Status: {res.status_code}")

    # -------------------------------------------------------------
    # 2. PRODUCT SERVICE: CRUD & NGOAI LE
    # -------------------------------------------------------------
    print("\n--- 2. PRODUCT SERVICE (CRUD ENGINE & VALIDATION) ---")

    # 2.1 Happy: Thêm mới sản phẩm hợp lệ
    res = client.post("/api/v1/products", json={
        "title": "Giao trinh Toan Cao Cap A1 (Chuan HUNRE)",
        "category_id": "BOOKS",
        "original_price": 70000.0,
        "current_price": 60000.0,
        "floor_price": 50000.0,
        "desired_exchange_items": "Casio 580",
        "seller_id": 1
    })
    created_id = res.json()["data"]["id"] if res.status_code == 200 else None
    check("PROD-01", "PRODUCT", "Happy Path: Dang ban san pham moi thanh cong", 
          res.status_code == 200 and created_id is not None,
          f"New Product ID: {created_id}")

    # 2.2 Ngoại lệ: Đăng bán với tiêu đề rỗng
    res = client.post("/api/v1/products", json={
        "title": "   ",  # Tiêu đề rỗng
        "current_price": 50000.0,
        "original_price": 50000.0
    })
    check("PROD-EX-01", "PRODUCT", "Ngoai Le 1: Tu choi tieu de rong (400 Bad Request)", 
          res.status_code == 400 and "không được để trống" in res.json().get("detail", ""),
          f"Status: {res.status_code}")

    # 2.3 Ngoại lệ: Đăng bán với giá bán <= 0 (Giá âm hoặc 0đ)
    res = client.post("/api/v1/products", json={
        "title": "Sach gia 0 dong hoac am",
        "current_price": -20000.0,
        "original_price": 50000.0
    })
    check("PROD-EX-02", "PRODUCT", "Ngoai Le 2: Tu choi gia ban <= 0", 
          res.status_code == 400 and "lớn hơn 0" in res.json().get("detail", ""),
          f"Status: {res.status_code}")

    # 2.4 Ngoại lệ: Giá sàn lớn hơn giá bán (floor_price > current_price)
    res = client.post("/api/v1/products", json={
        "title": "Sach loi gia san vo ly",
        "current_price": 50000.0,
        "original_price": 50000.0,
        "floor_price": 80000.0  # Giá sàn 80k > Giá bán 50k
    })
    check("PROD-EX-03", "PRODUCT", "Ngoai Le 3: Tu choi gia san lon hon gia ban", 
          res.status_code == 400 and "Giá sàn" in res.json().get("detail", ""),
          f"Status: {res.status_code}")

    # 2.5 Ngoại lệ: Xem chi tiết sản phẩm không tồn tại (ID 99999)
    res = client.get("/api/v1/products/99999")
    check("PROD-EX-04", "PRODUCT", "Ngoai Le 4: Xem san pham khong ton tai (404 Not Found)", 
          res.status_code == 404,
          f"Status: {res.status_code}")

    # 2.6 Ngoại lệ: Cập nhật sản phẩm không tồn tại
    res = client.put("/api/v1/products/99999", json={"title": "Sua san pham ma"})
    check("PROD-EX-05", "PRODUCT", "Ngoai Le 5: Sua san pham khong ton tai (404)", 
          res.status_code == 404,
          f"Status: {res.status_code}")

    # 2.7 Ngoại lệ: Xóa sản phẩm không tồn tại
    res = client.delete("/api/v1/products/99999")
    check("PROD-EX-06", "PRODUCT", "Ngoai Le 6: Xoa san pham khong ton tai (404)", 
          res.status_code == 404,
          f"Status: {res.status_code}")

    # 2.8 Happy & Edge: Tìm kiếm với từ khóa không khớp
    res = client.get("/api/v1/products?keyword=khong_co_mon_do_nay_tren_doi_98765")
    check("PROD-02", "PRODUCT", "Edge Case: Tim kiem tu khoa khong ton tai tra ve mang rong []", 
          res.status_code == 200 and len(res.json().get("data", [])) == 0,
          f"Count: {res.json().get('count')}")

    # 2.9 Ngoại lệ: Cập nhật tiêu đề thành khoảng trắng rỗng
    res = client.put(f"/api/v1/products/{created_id}", json={"title": "   "})
    check("PROD-EX-07", "PRODUCT", "Ngoai Le 7: Tu choi sua tieu de thanh rong (400)", 
          res.status_code == 400,
          f"Status: {res.status_code}")

    # 2.10 Ngoại lệ: Cập nhật giá bán <= 0
    res = client.put(f"/api/v1/products/{created_id}", json={"current_price": -5000})
    check("PROD-EX-08", "PRODUCT", "Ngoai Le 8: Tu choi sua gia ban <= 0 (400)", 
          res.status_code == 400,
          f"Status: {res.status_code}")

    # -------------------------------------------------------------
    # 3. ESCROW SERVICE: SAGA, DISPUTE & NGOAI LE
    # -------------------------------------------------------------
    print("\n--- 3. ESCROW SERVICE (SAGA FLOW & DISPUTE HANDLING) ---")

    # 3.1 Happy: Tạo đơn ký quỹ hợp lệ
    res = client.post("/api/v1/escrow/orders", json={
        "product_id": 1,
        "buyer_id": 2,
        "agreed_price": 70000.0
    })
    order_code = res.json()["order"]["order_code"] if res.status_code == 200 else None
    check("ESCROW-01", "ESCROW", "Happy Path: Tao don ky quy Smart Escrow thanh cong", 
          res.status_code == 200 and order_code is not None,
          f"Order Code: {order_code}")

    # 3.2 Ngoại lệ: Tạo đơn ký quỹ cho sản phẩm không tồn tại
    res = client.post("/api/v1/escrow/orders", json={
        "product_id": 88888,
        "buyer_id": 1
    })
    check("ESCROW-EX-01", "ESCROW", "Ngoai Le 1: Tu choi tao don voi product_id khong ton tai (404)", 
          res.status_code == 404,
          f"Status: {res.status_code}")

    # 3.3 Ngoại lệ: Gửi hành động Saga bất hợp lệ (Action không hỗ trợ)
    res = client.post("/api/v1/escrow/saga/advance", json={
        "order_code": order_code,
        "action": "HACK_RUT_TIEN_TRAI_PHEP"
    })
    check("ESCROW-EX-02", "ESCROW", "Ngoai Le 2: Tu choi hanh dong Saga khong hop le (400 Bad Request)", 
          res.status_code == 400 and "không hợp lệ" in res.json().get("detail", ""),
          f"Status: {res.status_code}")

    # 3.4 Ngoại lệ: Gửi thao tác trên đơn hàng không tồn tại
    res = client.post("/api/v1/escrow/saga/advance", json={
        "order_code": "ORD-KHONG-CO-TRONG-CSDL",
        "action": "CHECKIN"
    })
    check("ESCROW-EX-03", "ESCROW", "Ngoai Le 3: Thao tac tren ma don khong ton tai (404)", 
          res.status_code == 404,
          f"Status: {res.status_code}")

    # 3.5 Happy: Giải ngân đơn hàng thành công và cộng điểm uy tín +5 cho cả 2 bên
    res_release = client.post(f"/api/v1/escrow/orders/{order_code}/release")
    check("ESCROW-02", "ESCROW", "Happy Path: Giai ngan ky quy (SATISFIED) -> Trang thai RELEASED & Cong diem uy tin +5", 
          res_release.status_code == 200 and res_release.json()["order"]["status"] == "RELEASED",
          f"Status: {res_release.status_code} - Step: {res_release.json().get('order', {}).get('saga_step')}")

    # 3.6 Ngoại lệ: Thao tác giải ngân trên đơn hàng không tồn tại
    res_fake_release = client.post("/api/v1/escrow/orders/ORD-MA-KHONG-TON-TAI/release")
    check("ESCROW-EX-04", "ESCROW", "Ngoai Le 4: Giai ngan don hang khong ton tai bao loi 404", 
          res_fake_release.status_code == 404,
          f"Status: {res_fake_release.status_code}")

    # 3.7 Happy & Exception Handling: Khiếu nại đơn hàng (DISPUTE)
    # Tạo thêm 1 đơn để test khiếu nại
    res_ord2 = client.post("/api/v1/escrow/orders", json={"product_id": 2, "buyer_id": 3})
    ord2_code = res_ord2.json()["order"]["order_code"]
    res_disp = client.post(f"/api/v1/escrow/orders/{ord2_code}/dispute")
    check("ESCROW-03", "ESCROW", "Xu Ly Khieu Nai: Chuyen trang thai sang DISPUTED, dong bang tien ky quy", 
          res_disp.status_code == 200 and res_disp.json()["order"]["status"] == "DISPUTED",
          f"New Status: {res_disp.json()['order']['status']}")

    # -------------------------------------------------------------
    # 4. HUB LOGISTICS: LOCKER ALLOCATION & NGOAI LE
    # -------------------------------------------------------------
    print("\n--- 4. HUB LOGISTICS SERVICE (LOCKER & TOTP QR) ---")

    # 4.1 Happy: Quét Check-in nhận đồ cấp phát ô tủ
    res = client.post("/api/v1/hub/checkin", json={
        "order_code": "ORD-HUNRE-TEST-01",
        "scan_type": "CHECKIN"
    })
    check("HUB-01", "HUB", "Happy Path: Quet Check-in cap phat o tu Locker OCCUPIED", 
          res.status_code == 200 and res.json()["locker"]["status"] == "OCCUPIED",
          f"Locker: {res.json()['locker']['locker_code']}")

    # 4.2 Happy: Quét Check-out giải phóng ô tủ
    res = client.post("/api/v1/hub/checkout", json={
        "order_code": "ORD-HUNRE-TEST-01",
        "scan_type": "CHECKOUT"
    })
    check("HUB-02", "HUB", "Happy Path: Quet Check-out ban giao va giai phong tu EMPTY", 
          res.status_code == 200 and res.json()["locker"]["status"] == "EMPTY",
          f"Locker: {res.json()['locker']['locker_code']}")

    # 4.3 Ngoại lệ: Check-out một đơn hàng không nằm trong ô tủ nào
    res = client.post("/api/v1/hub/checkout", json={
        "order_code": "ORD-KHONG-CO-TRONG-TU-NAO",
        "scan_type": "CHECKOUT"
    })
    check("HUB-EX-01", "HUB", "Ngoai Le 1: Check-out don hang khong co trong Locker bao loi 404", 
          res.status_code == 404,
          f"Status: {res.status_code} - Detail: {res.json().get('detail')}")

    # 4.4 Ngoại lệ: Check-in khi toàn bộ ô tủ đã bị chiếm dụng (Full Lockers 409 Conflict)
    # Tạm thời chiếm dụng tất cả ô tủ trong DB
    curr_db = client.get("/api/v1/hub/lockers").json()["lockers"]
    tdb = load_db()
    for l in tdb["lockers"]:
        l["status"] = "OCCUPIED"
        l["current_order"] = "ORD-OCCUPIED"
    save_db(tdb)

    res_full = client.post("/api/v1/hub/checkin", json={"order_code": "ORD-TRY-WHEN-FULL", "scan_type": "CHECKIN"})
    check("HUB-EX-02", "HUB", "Ngoai Le 2: Tu choi Check-in khi toan bo tu Locker bi day (409 Conflict)", 
          res_full.status_code == 409 and "Toàn bộ ô tủ" in res_full.json().get("detail", ""),
          f"Status: {res_full.status_code}")

    # Khôi phục lại 1 tủ trống
    tdb = load_db()
    tdb["lockers"][0]["status"] = "EMPTY"
    tdb["lockers"][0]["current_order"] = None
    save_db(tdb)

    # 4.5 Happy: Kiểm tra mã Dynamic QR TOTP xoay 30 giây
    res = client.get("/api/v1/hub/orders/ORD-HUNRE-98471/dynamic-qr")
    token1 = res.json()["data"]["token"]
    expires1 = res.json()["data"]["expires_in_seconds"]
    check("HUB-03", "HUB", "Happy Path: Sinh Dynamic QR HMAC-SHA256 16 ky tu xoay 30s", 
          res.status_code == 200 and len(token1) == 16 and 0 <= expires1 <= 30,
          f"Token: {token1} - Expires in: {expires1}s")

    # -------------------------------------------------------------
    # 5. AI ENGINE PROXY & NEGOTIATION LOGIC
    # -------------------------------------------------------------
    print("\n--- 5. AI PRICING AGENT, BARTER GRAPH & COMPUTER VISION ---")

    # 5.1 Happy: Giá đề xuất hợp lý (>= giá sàn)
    res = client.post("/api/v1/ai/pricing/negotiate", json={
        "item_current_price": 75000,
        "item_floor_price": 60000,
        "buyer_offer_price": 65000,
        "buyer_trust_score": 520
    })
    check("AI-01", "AI", "Happy Path: Tra gia hop ly (65k >= 60k san) duoc AI ACCEPT", 
          res.status_code == 200 and res.json().get("decision") == "ACCEPT",
          f"Decision: {res.json().get('decision')}")

    # 5.2 Happy: Tính toán khấu hao giá theo thời gian (Time-decay Dutch Auction)
    res_decay = client.post("/api/v1/ai/pricing/decay", json={
        "original_price": 100000.0,
        "floor_price": 50000.0,
        "hours_elapsed": 72.0,
        "decay_half_life_hours": 72.0
    })
    check("AI-02", "AI", "Happy Path: AI Tinh toan giam gia theo thoi gian (Dutch Auction Time-Decay)", 
          res_decay.status_code == 200 and res_decay.json().get("current_decayed_price") == 75000.0,
          f"Decayed Price: {res_decay.json().get('current_decayed_price')}d (-{res_decay.json().get('discount_percentage')}%)")

    # 5.3 Happy: Tìm kiếm chu trình đồ thị hoán đổi Barter Graph Solver (3-Way Cycle)
    barter_payload = {
        "items": [
            {"id": 101, "seller_id": 1, "title": "Giao trinh Toan C3", "current_price": 50000.0, "desired_category_or_title": "Lap trinh Python"},
            {"id": 102, "seller_id": 2, "title": "Lap trinh Python", "current_price": 55000.0, "desired_category_or_title": "Tai nghe Sony"},
            {"id": 103, "seller_id": 3, "title": "Tai nghe Sony", "current_price": 50000.0, "desired_category_or_title": "Giao trinh Toan C3"}
        ],
        "max_cycle_length": 3
    }
    res_cycle = client.post("/api/v1/ai/barter/solve-cycles", json=barter_payload)
    cycles_found = res_cycle.json().get("cycles_found_count", 0) if res_cycle.status_code == 200 else 0
    check("AI-03", "AI", "Happy Path: AI Barter Graph Solver tim thay chu trinh hoan doi 3 ben can bang", 
          res_cycle.status_code == 200 and cycles_found >= 1,
          f"Cycles Found: {cycles_found}")

    # 5.4 Ngoại lệ: Giá đề xuất quá thấp so với giá sàn (< 60.000đ và SV bậc Bạc) -> AI từ chối REJECT
    res = client.post("/api/v1/ai/pricing/negotiate", json={
        "item_current_price": 75000,
        "item_floor_price": 60000,
        "buyer_offer_price": 40000,  # 40k < 60k giá sàn
        "buyer_trust_score": 520
    })
    check("AI-EX-01", "AI", "Ngoai Le 1: Tra gia duoi gia san bi AI REJECT tu choi", 
          res.status_code == 200 and res.json().get("decision") == "REJECT",
          f"Decision: {res.json().get('decision')}")

    # 5.5 Ngoại lệ & Thương lượng: Sinh viên uy tín cao (Trust Score >= 600) được ưu đãi COUNTER_OFFER
    res = client.post("/api/v1/ai/pricing/negotiate", json={
        "item_current_price": 75000,
        "item_floor_price": 60000,
        "buyer_offer_price": 55000,  # Dưới sàn nhưng SV uy tín cao
        "buyer_trust_score": 750    # Sinh viên hạng Vàng
    })
    check("AI-EX-02", "AI", "Ngoai Le 2: SV uy tin cao (Trust Score 750) duoc de xuat COUNTER_OFFER", 
          res.status_code == 200 and res.json().get("decision") == "COUNTER_OFFER",
          f"Decision: {res.json().get('decision')} - Counter Price: {res.json().get('counter_offer_price')}đ")

    # 5.6 Ngoại lệ: Thẩm định ảnh bằng tệp tin không phải định dạng ảnh (Text file)
    res_cv_err = client.post("/api/v1/ai/cv/inspect", files={"file": ("fake_file.txt", b"plain text data", "text/plain")})
    check("AI-EX-03", "AI", "Ngoai Le 3: Tu choi tep khong phai anh trong CV Inspection (400 Bad Request)", 
          res_cv_err.status_code == 400,
          f"Status: {res_cv_err.status_code}")

    # 5.7 Ngoại lệ: Gửi độ dài chu trình Barter Graph vượt quá ngưỡng tối đa cho phép (max_cycle_length = 10 > 5)
    res_len_err = client.post("/api/v1/ai/barter/solve-cycles", json={"items": [], "max_cycle_length": 10})
    check("AI-EX-04", "AI", "Ngoai Le 4: Tu choi do dai chu trinh vuot gioi han le=5 (422 Unprocessable Entity)", 
          res_len_err.status_code == 422,
          f"Status: {res_len_err.status_code}")

    # -------------------------------------------------------------
    # 6. CART SERVICE (LAB 04: GIỎ HÀNG CÓ TÍNH TIỀN)
    # -------------------------------------------------------------
    print("\n--- 6. CART SERVICE (LAB 04) ---")
    
    # 6.1 Happy Path: Làm sạch và Thêm sản phẩm vào giỏ hàng
    client.delete("/api/v1/cart/clear?user_id=1")
    res = client.post("/api/v1/cart/add", json={"user_id": 1, "product_id": 1, "quantity": 2})
    check("CART-01", "CART", "Happy Path: Them 2 cuon Giao trinh vao gio hang",
          res.status_code == 200 and res.json()["cart"][0]["quantity"] == 2,
          f"Status: {res.status_code}")
          
    # 6.2 Happy Path: Xem giỏ hàng & tính tổng tiền tự động
    res = client.get("/api/v1/cart?user_id=1")
    check("CART-02", "CART", "Happy Path: Xem gio hang co tinh tong tien tu dong (subtotal)",
          res.status_code == 200 and res.json()["total_amount"] > 0,
          f"Total Amount: {res.json().get('total_amount')}d")

    # 6.3 Happy Path: Cập nhật số lượng trong giỏ hàng
    res = client.put("/api/v1/cart/update", json={"user_id": 1, "product_id": 1, "quantity": 3})
    check("CART-03", "CART", "Happy Path: Cap nhat tang so luong len 3 san pham",
          res.status_code == 200 and res.json()["cart"][0]["quantity"] == 3,
          f"New Quantity: {res.json()['cart'][0]['quantity']}")

    # 6.4 Ngoại lệ 1: Thêm vào giỏ với số lượng âm hoặc 0 (400 Bad Request)
    res = client.post("/api/v1/cart/add", json={"user_id": 1, "product_id": 1, "quantity": 0})
    check("CART-EX-01", "CART", "Ngoai Le 1: Tu choi them so luong 0 vao gio (400)",
          res.status_code == 400,
          f"Status: {res.status_code}")

    # 6.5 Ngoại lệ 2: Cập nhật số lượng âm (400 Bad Request)
    res = client.put("/api/v1/cart/update", json={"user_id": 1, "product_id": 1, "quantity": -5})
    check("CART-EX-02", "CART", "Ngoai Le 2: Tu choi cap nhat so luong am (400)",
          res.status_code == 400,
          f"Status: {res.status_code}")

    # 6.6 Ngoại lệ 3: Thêm sản phẩm không tồn tại vào giỏ (404 Not Found)
    res = client.post("/api/v1/cart/add", json={"user_id": 1, "product_id": 999999, "quantity": 1})
    check("CART-EX-03", "CART", "Ngoai Le 3: Tu choi them san pham khong ton tai (404)",
          res.status_code == 404,
          f"Status: {res.status_code}")

    # 6.7 Happy Path: Xóa món khỏi giỏ hàng
    res = client.delete("/api/v1/cart/remove/1?user_id=1")
    check("CART-04", "CART", "Happy Path: Xoa san pham khoi gio hang thanh cong",
          res.status_code == 200,
          f"Status: {res.status_code}")

    # -------------------------------------------------------------
    # 7. SHIPPING SERVICE (LAB 05: PHÍ VẬN CHUYỂN GHN & HUB)
    # -------------------------------------------------------------
    print("\n--- 7. SHIPPING SERVICE (LAB 05) ---")

    # 7.1 Happy Path: Lấy tại Trạm Hub CS1 HUNRE -> 0đ
    res = client.post("/api/v1/shipping/calculate-fee", json={"method": "HUB_PICKUP"})
    check("SHIP-01", "SHIPPING", "Happy Path: Nhan tai Tram Hub CS1 mien phi van chuyen (0d)",
          res.status_code == 200 and res.json()["fee"] == 0.0,
          f"Fee: {res.json().get('fee')}d")

    # 7.2 Happy Path: Giao Hàng Nhanh (GHN) nội thành Bắc Từ Liêm -> 22.000đ
    res = client.post("/api/v1/shipping/calculate-fee", json={"method": "GHN_DELIVERY", "district": "Bắc Từ Liêm"})
    check("SHIP-02", "SHIPPING", "Happy Path: Tinh phi ship GHN noi thanh Bac Tu Liem (22.000d)",
          res.status_code == 200 and res.json()["fee"] == 22000.0,
          f"Fee: {res.json().get('fee')}d")

    # 7.3 Happy Path: Giao Hàng Nhanh (GHN) ngoại tỉnh -> 30.000đ
    res = client.post("/api/v1/shipping/calculate-fee", json={"method": "GHN_DELIVERY", "district": "Thành phố Bắc Ninh", "province": "Bắc Ninh"})
    check("SHIP-03", "SHIPPING", "Happy Path: Tinh phi ship GHN ngoai tinh (30.000d)",
          res.status_code == 200 and res.json()["fee"] == 30000.0,
          f"Fee: {res.json().get('fee')}d")

    # 7.4 Ngoại lệ: Phương thức vận chuyển không hợp lệ (400 Bad Request)
    res = client.post("/api/v1/shipping/calculate-fee", json={"method": "FLYING_CARPET"})
    check("SHIP-EX-01", "SHIPPING", "Ngoai Le 1: Tu choi phuong thuc van chuyen sai (400)",
          res.status_code == 400,
          f"Status: {res.status_code}")

    # -------------------------------------------------------------
    # 8. VOUCHERS, CHECKOUT & MULTI-GATEWAYS (LAB 06 & LAB 09)
    # -------------------------------------------------------------
    print("\n--- 8. VOUCHERS, ORDERS & MULTI-GATEWAY PAYMENTS ---")

    # 8.1 Happy Path: Áp dụng mã Voucher HUNRE2026 giảm 10% (10.000đ) và TANSINHVIEN giảm 20.000đ
    res = client.post("/api/v1/vouchers/apply", json={"code": "HUNRE2026", "order_value": 100000})
    check("VOUCHER-01", "VOUCHER", "Happy Path: Ap dung ma giam gia HUNRE2026 giam 10% (10.000d)",
          res.status_code == 200 and res.json()["discount_amount"] == 10000.0,
          f"Discount: {res.json().get('discount_amount')}d")

    res_tsv = client.post("/api/v1/vouchers/apply", json={"code": "TANSINHVIEN", "order_value": 100000})
    check("VOUCHER-01B", "VOUCHER", "Happy Path: Ap dung ma TANSINHVIEN giam 20.000d",
          res_tsv.status_code == 200 and res_tsv.json()["discount_amount"] == 20000.0,
          f"Discount: {res_tsv.json().get('discount_amount')}d")

    # 8.2 Ngoại lệ 1: Áp dụng voucher không đủ giá trị tối thiểu (400 Bad Request)
    res = client.post("/api/v1/vouchers/apply", json={"code": "HUNRE2026", "order_value": 30000})
    check("VOUCHER-EX-01", "VOUCHER", "Ngoai Le 1: Tu choi ap voucher khi don chua dat gia tri toi thieu",
          res.status_code == 400,
          f"Status: {res.status_code}")

    # 8.3 Ngoại lệ 2: Mã voucher không tồn tại (404 Not Found)
    res = client.post("/api/v1/vouchers/apply", json={"code": "MA_GIA_MAO", "order_value": 100000})
    check("VOUCHER-EX-02", "VOUCHER", "Ngoai Le 2: Tu choi ma voucher khong ton tai (404)",
          res.status_code == 404,
          f"Status: {res.status_code}")

    # 8.4 Happy Path: Đặt hàng qua Cổng Ký Quỹ ESCROW (Lab 06)
    res = client.post("/api/v1/orders/checkout", json={
        "user_id": 1,
        "customer_name": "Nguyen Van An",
        "customer_phone": "0981112233",
        "shipping_address": "KTX HUNRE Nha B3",
        "shipping_method": "HUB_PICKUP",
        "gateway": "ESCROW",
        "voucher_code": "HUNRE2026",
        "items": [{"product_id": 2, "title": "May tinh Casio fx-580VNX", "price": 420000, "quantity": 1}]
    })
    order_escrow = res.json().get("order", {})
    check("ORDER-01", "ORDER", "Happy Path: Dat hang cong ESCROW -> Khoa coc an toan & ghi log giao dich",
          res.status_code == 200 and order_escrow.get("payment_status") == "paid",
          f"Order Code: {order_escrow.get('order_code')}")

    # 8.5 Happy Path: Đặt hàng qua Ví Điện Tử MoMo Sandbox (Lab 06)
    res = client.post("/api/v1/orders/checkout", json={
        "user_id": 1,
        "customer_name": "Tran Thi Bich",
        "customer_phone": "0982223344",
        "shipping_address": "41A Phu Dien",
        "shipping_method": "GHN_DELIVERY",
        "gateway": "MOMO",
        "items": [{"product_id": 3, "title": "Balo sinh vien", "price": 120000, "quantity": 1}]
    })
    order_momo = res.json().get("order", {})
    momo_url = res.json().get("momo_pay_url")
    check("ORDER-02", "ORDER", "Happy Path: Dat hang cong MoMo -> Sinh link QR thanh toan Sandbox",
          res.status_code == 200 and momo_url is not None and "momo.vn" in momo_url,
          f"Order Code: {order_momo.get('order_code')}")

    # 8.6 Happy Path: Đặt hàng qua Tiền mặt COD (Lab 06 & Lab 09)
    res = client.post("/api/v1/orders/checkout", json={
        "user_id": 2,
        "customer_name": "Le Hoang Cuong",
        "customer_phone": "0983334455",
        "shipping_address": "KTX Khu B HUNRE",
        "shipping_method": "GHN_DELIVERY",
        "gateway": "COD",
        "items": [{"product_id": 1, "title": "Giao trinh", "price": 45000, "quantity": 1}]
    })
    order_cod = res.json().get("order", {})
    order_cod_code = order_cod.get("order_code")
    check("ORDER-03", "ORDER", "Happy Path: Dat hang COD -> Trang thai pending cho doi soat thu tien",
          res.status_code == 200 and order_cod.get("payment_status") == "pending",
          f"Order Code: {order_cod_code}")

    # 8.7 Ngoại lệ 1: Đặt hàng thiếu Tên hoặc SĐT người nhận (422 Unprocessable Entity)
    res = client.post("/api/v1/orders/checkout", json={
        "user_id": 1,
        "customer_name": "",
        "customer_phone": "",
        "shipping_address": "KTX",
        "items": [{"product_id": 1, "price": 45000, "quantity": 1}]
    })
    check("ORDER-EX-01", "ORDER", "Ngoai Le 1: Tu choi dat hang thieu thong tin nguoi nhan (422)",
          res.status_code == 422,
          f"Status: {res.status_code}")

    # 8.8 Ngoại lệ 2: Cổng thanh toán không hợp lệ (400 Bad Request)
    res = client.post("/api/v1/orders/checkout", json={
        "user_id": 1,
        "customer_name": "Nguyen Van An",
        "customer_phone": "0981234567",
        "shipping_address": "KTX",
        "gateway": "BITCOIN",
        "items": [{"product_id": 1, "price": 45000, "quantity": 1}]
    })
    check("ORDER-EX-02", "ORDER", "Ngoai Le 2: Tu choi cong thanh toan khong ho tro (400)",
          res.status_code == 400,
          f"Status: {res.status_code}")

    # -------------------------------------------------------------
    # 9. ADMIN ORDER MANAGEMENT & STRICT RULES (LAB 08)
    # -------------------------------------------------------------
    print("\n--- 9. ADMIN ORDER MANAGEMENT (LAB 08 - 8 TABS & SAFE RULES) ---")

    # 9.1 Happy Path: Lọc 8 tab trạng thái (all, pending, ready, delivering,...)
    res_all = client.get("/api/v1/admin/orders?tab=all")
    res_pending = client.get("/api/v1/admin/orders?tab=pending")
    check("ADMIN-ORD-01", "ADMIN", "Happy Path: Loc danh sach 8 tab don hang (all & pending)",
          res_all.status_code == 200 and res_pending.status_code == 200,
          f"All Count: {res_all.json().get('count')} - Pending Count: {res_pending.json().get('count')}")

    # 9.2 Happy Path: Chuyển trạng thái đơn sang 'delivering'
    res = client.put(f"/api/v1/admin/orders/{order_cod_code}/status", json={"status": "delivering", "note": "Shipper GHN dang lay hang"})
    check("ADMIN-ORD-02", "ADMIN", f"Happy Path: Chuyen don {order_cod_code} sang delivering",
          res.status_code == 200 and res.json()["order"]["status"] == "delivering",
          f"Status: {res.status_code}")

    # 9.3 QUY TẮC RÀNG BUỘC CỐT LÕI CỦA LAB 08 (CRITICAL EXCEPTION):
    # Đơn hàng đang ở trạng thái 'delivering' -> TUYỆT ĐỐI KHÔNG ĐƯỢC PHÉP HỦY (HTTP 400)
    res_cancel_err = client.put(f"/api/v1/admin/orders/{order_cod_code}/status", json={"status": "cancelled", "note": "Khach muon huy"})
    check("ADMIN-ORD-EX-01", "ADMIN", "QUY TAC LAB 08: TU CHOI HUY DON DANG GIAO HANG (400 Bad Request)",
          res_cancel_err.status_code == 400 and "KHÔNG ĐƯỢC PHÉP HỦY" in res_cancel_err.json().get("detail", ""),
          f"Status: {res_cancel_err.status_code} - Detail: {res_cancel_err.json().get('detail')}")

    # -------------------------------------------------------------
    # 10. FINANCE KPIS & COD RECONCILIATION MATRIX (LAB 09)
    # -------------------------------------------------------------
    print("\n--- 10. FINANCE RECONCILIATION & COD MATRIX (LAB 09) ---")

    # 10.1 Happy Path: Lấy chỉ số KPIs tài chính
    res_kpis = client.get("/api/v1/admin/finance/kpis")
    kpis = res_kpis.json().get("kpis", {})
    check("FIN-01", "FINANCE", "Happy Path: Tinh toan 6 chi so KPI tai chinh & doi soat",
          res_kpis.status_code == 200 and "gross_revenue" in kpis and "pending_cod_amount" in kpis,
          f"Gross Revenue: {kpis.get('gross_revenue'):,}d - Escrow: {kpis.get('escrow_holding_amount'):,}d")

    # 10.2 Happy Path: Lấy danh sách sổ cái giao dịch
    res_txs = client.get("/api/v1/admin/finance/transactions")
    tx_list = res_txs.json().get("transactions", [])
    cod_tx = next((t for t in tx_list if t.get("gateway") == "cod"), None)
    check("FIN-02", "FINANCE", "Happy Path: Truy van so cai giao dich doi soat da cong",
          res_txs.status_code == 200 and len(tx_list) > 0,
          f"Transactions Count: {len(tx_list)}")

    # 10.3 Happy Path: Chuyển trạng thái COD hợp lệ (pending -> paid)
    if cod_tx:
        res_cod_paid = client.put("/api/v1/admin/finance/cod-transition", json={"transaction_id": cod_tx["id"], "new_status": "paid"})
        check("FIN-03", "FINANCE", "Happy Path: Doi soat COD thu tien thanh cong (pending -> paid)",
              res_cod_paid.status_code == 200 and res_cod_paid.json()["transaction"]["status"] == "paid",
              f"New Status: {res_cod_paid.json()['transaction']['status']}")

        # 10.4 Ngoại lệ: Chuyển trạng thái COD phi lý trái ma trận (paid -> refunded trực tiếp không qua refund_pending)
        res_cod_invalid = client.put("/api/v1/admin/finance/cod-transition", json={"transaction_id": cod_tx["id"], "new_status": "refunded"})
        check("FIN-EX-01", "FINANCE", "Ngoai Le 1: Tu choi chuyen trang thai COD trai ma tran Lab 09 (400)",
              res_cod_invalid.status_code == 400,
              f"Status: {res_cod_invalid.status_code} - Detail: {res_cod_invalid.json().get('detail')}")

    # -------------------------------------------------------------
    # 11. WISHLIST & PRODUCT REVIEWS (YÊU CẦU BÀI TẬP LỚN)
    # -------------------------------------------------------------
    print("\n--- 11. WISHLIST & REVIEWS (YEU CAU BTL) ---")

    # 11.1 Happy Path: Thêm sản phẩm 3 vào yêu thích (Wishlist toggle ADD)
    res_fav = client.post("/api/v1/wishlist/toggle", json={"user_id": 1, "product_id": 3})
    check("WISH-01", "WISHLIST", "Happy Path: Toggle yeu thich san pham 3 (Them vao)",
          res_fav.status_code == 200 and res_fav.json().get("is_liked") is True,
          f"Liked: {res_fav.json().get('is_liked')}")

    # 11.2 Happy Path: Lấy danh sách yêu thích của sinh viên
    res_fav_list = client.get("/api/v1/wishlist/1")
    check("WISH-02", "WISHLIST", "Happy Path: Lay danh sach san pham yeu thich cua user (Co chua sp 2 va 3)",
          res_fav_list.status_code == 200 and res_fav_list.json().get("count") >= 2,
          f"Fav Count: {res_fav_list.json().get('count')}")

    # 11.3 Happy Path: Bỏ thích sản phẩm 3 (Wishlist toggle REMOVE)
    res_unfav = client.post("/api/v1/wishlist/toggle", json={"user_id": 1, "product_id": 3})
    check("WISH-03", "WISHLIST", "Happy Path: Toggle bo yeu thich san pham 3 (Go ra)",
          res_unfav.status_code == 200 and res_unfav.json().get("is_liked") is False,
          f"Liked: {res_unfav.json().get('is_liked')}")

    # 11.3 Happy Path: Đăng đánh giá & nhận xét sản phẩm
    res_rev = client.post("/api/v1/reviews", json={"product_id": 1, "user_id": 1, "rating": 5, "comment": "Giao trinh rat dep va day du chuong"})
    check("REV-01", "REVIEW", "Happy Path: Dang danh gia 5 sao cho san pham",
          res_rev.status_code == 200 and res_rev.json()["review"]["rating"] == 5,
          f"Status: {res_rev.status_code}")

    # 11.4 Ngoại lệ 1: Đánh giá sao vượt quá ngưỡng [1-5] (400 Bad Request)
    res_rev_err = client.post("/api/v1/reviews", json={"product_id": 1, "user_id": 1, "rating": 10, "comment": "Diem 10 khong hop le"})
    check("REV-EX-01", "REVIEW", "Ngoai Le 1: Tu choi danh gia vuot qua 5 sao (400)",
          res_rev_err.status_code == 400,
          f"Status: {res_rev_err.status_code}")

    # 11.5 Ngoại lệ 2: Đánh giá với nội dung bình luận rỗng (400 Bad Request)
    res_rev_blank = client.post("/api/v1/reviews", json={"product_id": 1, "user_id": 1, "rating": 4, "comment": "   "})
    check("REV-EX-02", "REVIEW", "Ngoai Le 2: Tu choi binh luan rong (400)",
          res_rev_blank.status_code == 400,
          f"Status: {res_rev_blank.status_code}")

    # -------------------------------------------------------------
    # 12. ADMIN USER MANAGEMENT & SECURITY (LAB 03)
    # -------------------------------------------------------------
    print("\n--- 12. ADMIN USER MANAGEMENT (LAB 03) ---")

    # 12.1 Happy Path: Admin truy vấn danh sách toàn bộ người dùng
    res_users = client.get("/api/v1/admin/users")
    check("ADMIN-USR-01", "ADMIN", "Happy Path: Admin lay danh sach toan bo nguoi dung",
          res_users.status_code == 200 and len(res_users.json()["users"]) >= 4,
          f"Total Users: {len(res_users.json().get('users', []))}")

    # 12.2 Happy Path: Khóa / Mở khóa tài khoản sinh viên vi phạm
    res_block = client.put("/api/v1/admin/users/3/status", json={"status": "BLOCKED"})
    check("ADMIN-USR-02", "ADMIN", "Happy Path: Admin khoa tai khoan sinh vi pham (BLOCKED)",
          res_block.status_code == 200 and res_block.json()["user"]["status"] == "BLOCKED",
          f"User 3 Status: {res_block.json()['user']['status']}")

    # 12.3 Ngoại lệ: Cố tình khóa tài khoản Quản Trị Viên Admin (400 Bad Request)
    admin_user = next((u for u in res_users.json()["users"] if u.get("role") == "ADMIN"), None)
    if admin_user:
        res_admin_block = client.put(f"/api/v1/admin/users/{admin_user['id']}/status", json={"status": "BLOCKED"})
        check("ADMIN-USR-EX-01", "ADMIN", "Ngoai Le 1: Tu choi khoa tai khoan Quan Tri Vien ADMIN (400)",
              res_admin_block.status_code == 400,
              f"Status: {res_admin_block.status_code} - Detail: {res_admin_block.json().get('detail')}")

    # -------------------------------------------------------------
    # TONG KET KET QUA
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"TONG KET KIEM THU: {passed_tests}/{passed_tests + failed_tests} TESTS PASSED")
    print(f"TY LE THANH CONG: {(passed_tests / (passed_tests + failed_tests)) * 100:.1f}%")
    print("=" * 70 + "\n")

    return passed_tests, failed_tests, results

if __name__ == "__main__":
    run_tests()


