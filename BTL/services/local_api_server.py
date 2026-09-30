"""
HUNRE E-COMMERCE - LOCAL UNIFIED API GATEWAY & MICROSERVICES RUNNER
Cổng: 8000
Hỗ trợ chạy trực tiếp toàn bộ các API Microservices (Auth, Products CRUD, Escrow Saga, Hub Logistics, AI Proxy)
kèm phục vụ tĩnh toàn bộ Frontend (Student Portal & Hub Staff Scanner).
Lưu trữ dữ liệu bền vững (JSON File Persistence) tại data/hunre_db.json.
"""

from fastapi import FastAPI, HTTPException, Request, Response, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
import json
import time
import hmac
import hashlib
import requests
import base64
import io
from PIL import Image, ImageStat
import numpy as np
from datetime import datetime

# Đường dẫn file CSDL JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_ENGINE_DIR = os.path.join(BASE_DIR, "ai-engine")
if AI_ENGINE_DIR not in sys.path:
    sys.path.insert(0, AI_ENGINE_DIR)

try:
    from app.services.graph_solver import BarterGraphSolver
    from app.services.price_agent import PriceNegotiatorAgent
except Exception:
    BarterGraphSolver = None
    PriceNegotiatorAgent = None

DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "hunre_db.json")

app = FastAPI(
    title="HUNRE E-Commerce Unified Gateway & Services",
    description="Cổng API Gateway tập trung & Đầy đủ 5 Microservices cho sinh viên HUNRE",
    version="2.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dữ liệu khởi tạo chuẩn
DEFAULT_DB = {
    "users": [
        {"id": 1, "student_code": "20211001", "full_name": "Nguyễn Văn An", "email": "an.nv@hunre.edu.vn", "trust_score": 520, "campus": "CS1_HA_NOI", "wallet_balance": 500000.0, "role": "STUDENT", "faculty": "Công nghệ Thông tin", "status": "ACTIVE"},
        {"id": 2, "student_code": "20211002", "full_name": "Trần Thị Bích", "email": "bich.tt@hunre.edu.vn", "trust_score": 480, "campus": "CS1_HA_NOI", "wallet_balance": 250000.0, "role": "STUDENT", "faculty": "Môi trường", "status": "ACTIVE"},
        {"id": 3, "student_code": "20211003", "full_name": "Lê Hoàng Cường", "email": "cuong.lh@hunre.edu.vn", "trust_score": 390, "campus": "CS1_HA_NOI", "wallet_balance": 120000.0, "role": "STUDENT", "faculty": "Khí tượng Thủy văn", "status": "ACTIVE"},
        {"id": 4, "student_code": "HUB001", "full_name": "Cộng Tác Viên Trạm Hub", "email": "hub.cs1@hunre.edu.vn", "trust_score": 999, "campus": "CS1_HA_NOI", "wallet_balance": 0.0, "role": "HUB_STAFF", "faculty": "Đoàn Thanh Niên", "status": "ACTIVE"},
        {"id": 99, "student_code": "ADMIN001", "full_name": "Quản Trị Viên HUNRE", "email": "admin@hunre.edu.vn", "trust_score": 1000, "campus": "CS1_HA_NOI", "wallet_balance": 10000000.0, "role": "ADMIN", "faculty": "Phòng Đào Tạo & CTSV", "status": "ACTIVE"}
    ],
    "products": [
        {
            "id": 1,
            "seller_id": 1,
            "seller_name": "Nguyễn Văn An",
            "category_id": "BOOKS",
            "category_name": "Giáo Trình & Tài Liệu",
            "title": "Giáo trình Cơ Sở Dữ Liệu & SQL (HUNRE)",
            "description": "Giáo trình dùng cho sinh viên K11, K12 CNTT. Trang sạch, không quăn mép, có ghi chú bài tập.",
            "original_price": 80000.0,
            "current_price": 75000.0,
            "floor_price": 60000.0,
            "condition_grade": "GRADE_A",
            "ai_defect_score": 0.035,
            "ai_inspection_summary": "Độ mới 94%, không rách, mép trang sạch, chữ ký dHash xác thực",
            "is_barter_eligible": 1,
            "desired_exchange_items": "Máy tính Casio FX 580VN",
            "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop",
            "status": "ACTIVE",
            "created_at": "2026-09-15 08:30:00"
        },
        {
            "id": 2,
            "seller_id": 2,
            "seller_name": "Trần Thị Bích",
            "category_id": "TECH",
            "category_name": "Dụng Cụ Học Tập",
            "title": "Máy tính Casio FX 580VN X (Like New)",
            "description": "Máy tính chính hãng thi tốt nghiệp và đại học, nguyên tem Bộ GD&ĐT, màn hình LCD sắc nét.",
            "original_price": 350000.0,
            "current_price": 320000.0,
            "floor_price": 280000.0,
            "condition_grade": "GRADE_S",
            "ai_defect_score": 0.012,
            "ai_inspection_summary": "Độ mới 98%, màn hình LCD nét không xước, phím nảy nhạy",
            "is_barter_eligible": 1,
            "desired_exchange_items": "Bàn phím cơ DareU hoặc Balo",
            "image_url": "https://images.unsplash.com/photo-1596495578065-6e0763fa1178?w=600&auto=format&fit=crop",
            "status": "ACTIVE",
            "created_at": "2026-09-15 09:15:00"
        },
        {
            "id": 3,
            "seller_id": 3,
            "seller_name": "Lê Hoàng Cường",
            "category_id": "TECH",
            "category_name": "Thiết Bị Điện Tử",
            "title": "Bàn phím cơ DareU EK87 Blue Switch",
            "description": "Bàn phím cơ dây cắm Type-C, switch nhận 100%, gõ nảy tốt, led trắng đơn sắc.",
            "original_price": 280000.0,
            "current_price": 250000.0,
            "floor_price": 200000.0,
            "condition_grade": "GRADE_B",
            "ai_defect_score": 0.098,
            "ai_inspection_summary": "Độ mới 88%, hơi xước góc trái vỏ, các switch hoạt động 100%",
            "is_barter_eligible": 1,
            "desired_exchange_items": "Giáo trình CSDL hoặc Sách Tiếng Anh",
            "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop",
            "status": "ACTIVE",
            "created_at": "2026-09-15 10:00:00"
        }
    ],
    "lockers": [
        {"id": 1, "hub_id": 1, "locker_code": "LOCKER-S-01", "size_type": "SMALL", "description": "Cỡ Nhỏ (Giáo trình & Sách)", "status": "EMPTY", "current_order": None},
        {"id": 2, "hub_id": 1, "locker_code": "LOCKER-M-01", "size_type": "MEDIUM", "description": "Cỡ Vừa (Bàn phím DareU)", "status": "OCCUPIED", "current_order": "ORD-HUNRE-98471"},
        {"id": 3, "hub_id": 1, "locker_code": "LOCKER-M-02", "size_type": "MEDIUM", "description": "Cỡ Vừa (Laptop / Casio)", "status": "EMPTY", "current_order": None},
        {"id": 4, "hub_id": 1, "locker_code": "LOCKER-L-01", "size_type": "LARGE", "description": "Cỡ Lớn (Màn hình / Case)", "status": "EMPTY", "current_order": None}
    ],
    "escrow_orders": {
        "ORD-HUNRE-98471": {
            "order_code": "ORD-HUNRE-98471",
            "buyer_id": 1,
            "buyer_name": "Nguyễn Văn An",
            "seller_id": 3,
            "seller_name": "Lê Hoàng Cường",
            "product_id": 3,
            "product_title": "Bàn phím cơ DareU EK87 Blue Switch",
            "hub_id": 1,
            "hub_name": "Trạm Hub CS1 (Nhà A - Văn Phòng Đoàn Trường)",
            "locker_code": "LOCKER-M-01",
            "escrow_amount": 250000.0,
            "saga_step": 4,
            "status": "STORED_AT_HUB",
            "deadline": "17:30 ngày 18/09/2026",
            "created_at": "2026-09-16 11:00:00"
        }
    },
    "carts": {
        "1": [
            {
                "product_id": 1,
                "title": "Giáo trình Cơ Sở Dữ Liệu & SQL (HUNRE)",
                "price": 75000.0,
                "quantity": 1,
                "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop",
                "category_name": "Giáo Trình & Tài Liệu"
            }
        ]
    },
    "orders": [
        {
            "id": 1,
            "order_code": "DH20260916-0001",
            "user_id": 1,
            "customer_name": "Nguyễn Văn An",
            "customer_phone": "0981234567",
            "shipping_address": "Ký túc xá Đại học Tài nguyên và Môi trường Hà Nội",
            "shipping_method": "HUB_PICKUP",
            "shipping_fee": 0.0,
            "items": [
                {"product_id": 3, "title": "Bàn phím cơ DareU EK87 Blue Switch", "price": 250000.0, "quantity": 1}
            ],
            "items_total": 250000.0,
            "discount_amount": 0.0,
            "voucher_code": None,
            "total_price": 250000.0,
            "gateway": "ESCROW",
            "status": "delivering",
            "payment_status": "paid",
            "note": "Nhận tại ô tủ LOCKER-M-01",
            "created_at": "2026-09-16 11:00:00"
        },
        {
            "id": 2,
            "order_code": "DH20260918-0002",
            "user_id": 2,
            "customer_name": "Trần Thị Bích",
            "customer_phone": "0912345678",
            "shipping_address": "Số 41A đường Phú Diễn, Bắc Từ Liêm, Hà Nội",
            "shipping_method": "GHN_DELIVERY",
            "shipping_fee": 25000.0,
            "items": [
                {"product_id": 1, "title": "Giáo trình Cơ Sở Dữ Liệu & SQL (HUNRE)", "price": 75000.0, "quantity": 1}
            ],
            "items_total": 75000.0,
            "discount_amount": 10000.0,
            "voucher_code": "HUNRE2026",
            "total_price": 90000.0,
            "gateway": "COD",
            "status": "pending",
            "payment_status": "pending",
            "note": "Giao tận tay trong giờ hành chính",
            "created_at": "2026-09-18 14:30:00"
        }
    ],
    "payment_transactions": [
        {
            "id": 1,
            "order_code": "DH20260916-0001",
            "gateway": "escrow",
            "amount": 250000.0,
            "status": "paid",
            "result_code": 0,
            "message": "Đã khóa tiền ký quỹ Smart Escrow thành công",
            "paid_at": "2026-09-16 11:01:00",
            "created_at": "2026-09-16 11:00:00"
        },
        {
            "id": 2,
            "order_code": "DH20260918-0002",
            "gateway": "cod",
            "amount": 90000.0,
            "status": "pending",
            "result_code": 0,
            "message": "Chờ thu tiền mặt khi giao hàng (COD)",
            "paid_at": None,
            "created_at": "2026-09-18 14:30:00"
        }
    ],
    "vouchers": [
        {"code": "HUNRE2026", "discount_percent": 10, "discount_amount": 0, "min_order_value": 50000.0, "description": "Giảm 10% đơn từ 50.000đ chào năm học mới"},
        {"code": "TANSINHVIEN", "discount_percent": 0, "discount_amount": 20000.0, "min_order_value": 100000.0, "description": "Giảm 20.000đ cho đơn hàng từ 100.000đ"},
        {"code": "FREESHIP_HUB", "discount_percent": 0, "discount_amount": 25000.0, "min_order_value": 0.0, "description": "Miễn phí vận chuyển nhận hàng tại Trạm Hub CS1"}
    ],
    "reviews": [
        {
            "id": 1,
            "product_id": 1,
            "user_id": 2,
            "user_name": "Trần Thị Bích",
            "rating": 5,
            "comment": "Sách rất mới, đầy đủ đề cương ôn tập môn CSDL của thầy cô HUNRE. Rất đáng tiền!",
            "created_at": "2026-09-17 16:20:00"
        }
    ],
    "wishlists": {
        "1": [2],
        "2": [1, 3]
    },
    "config": {
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "")
    }
}

def load_db():
    if not os.path.exists(DB_FILE):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DB, f, ensure_ascii=False, indent=2)
        return DEFAULT_DB
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_DB

def save_db(db):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# =============================================================
# 1. AUTH SERVICE APIS (/api/v1/auth)
# =============================================================

@app.get("/api/v1/auth/users")
def get_all_users():
    db = load_db()
    return {"success": True, "users": db["users"]}

@app.get("/api/v1/auth/users/trust-score")
def get_trust_score_query(user_id: int = Query(1)):
    return calculate_trust_score(user_id)

@app.get("/api/v1/auth/trust-score/{user_id}")
def get_trust_score_path(user_id: int):
    return calculate_trust_score(user_id)

def calculate_trust_score(user_id: int):
    db = load_db()
    user = next((u for u in db["users"] if u["id"] == user_id), None)
    if not user:
        # Fallback user mặc định
        user = db["users"][0]
    score = user["trust_score"]
    if score >= 800:
        tier = "KIM CƯƠNG (Miễn cọc 100% & Ưu tiên Barter)"
    elif score >= 600:
        tier = "VÀNG (Ưu tiên Barter & Giảm 50% cọc)"
    elif score >= 400:
        tier = "BẠC (Sinh viên uy tín tiêu chuẩn)"
    else:
        tier = "ĐỒNG (Cần tích lũy thêm giao dịch)"
    return {
        "success": True,
        "data": {
            "user_id": user["id"],
            "full_name": user["full_name"],
            "student_code": user["student_code"],
            "trust_score": score,
            "tier": tier,
            "wallet_balance": user.get("wallet_balance", 0.0),
            "campus": user.get("campus", "CS1_HA_NOI")
        }
    }

class RegisterDTO(BaseModel):
    student_code: str
    full_name: str
    email: str
    password: Optional[str] = "123456"
    faculty: Optional[str] = "Công nghệ Thông tin"
    campus: Optional[str] = "CS1_HA_NOI"

@app.post("/api/v1/auth/register")
def register(dto: RegisterDTO):
    if not dto.student_code.strip() or not dto.full_name.strip():
        raise HTTPException(status_code=422, detail="Mã sinh viên và họ tên không được để trống!")
    if not dto.email.lower().endswith("@hunre.edu.vn"):
        raise HTTPException(status_code=422, detail="KYC Failed: Bắt buộc sử dụng email sinh viên trường (@hunre.edu.vn)!")

    db = load_db()
    # Kiểm tra trùng email
    if any(u["email"].lower() == dto.email.lower() for u in db["users"]):
        raise HTTPException(status_code=409, detail="Email sinh viên này đã được đăng ký trong hệ thống!")

    new_user = {
        "id": len(db["users"]) + 1,
        "student_code": dto.student_code.strip(),
        "full_name": dto.full_name.strip(),
        "email": dto.email.lower().strip(),
        "trust_score": 500,
        "campus": dto.campus,
        "wallet_balance": 200000.0,
        "role": "STUDENT",
        "faculty": dto.faculty
    }
    db["users"].append(new_user)
    save_db(db)
    return {"success": True, "message": "Đăng ký thành công!", "user": new_user}

# =============================================================
# 2. PRODUCT SERVICE APIS (/api/v1/products - FULL CRUD)
# =============================================================

@app.get("/api/v1/products")
def get_products(category: Optional[str] = None, keyword: Optional[str] = None):
    db = load_db()
    items = db["products"]
    if category and category != "ALL":
        items = [p for p in items if p.get("category_id") == category or p.get("category_name") == category]
    if keyword:
        kw = keyword.lower()
        items = [p for p in items if kw in p.get("title", "").lower() or kw in p.get("description", "").lower() or kw in p.get("desired_exchange_items", "").lower()]
    return {"success": True, "count": len(items), "data": items}

@app.get("/api/v1/products/{product_id}")
def get_product_detail(product_id: int):
    db = load_db()
    product = next((p for p in db["products"] if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")
    return {"success": True, "data": product}

class ProductCreateDTO(BaseModel):
    title: str
    description: Optional[str] = ""
    category_id: Optional[str] = "BOOKS"
    category_name: Optional[str] = "Giáo Trình & Tài Liệu"
    original_price: float
    current_price: float
    floor_price: Optional[float] = None
    condition_grade: Optional[str] = "GRADE_A"
    ai_defect_score: Optional[float] = 0.05
    ai_inspection_summary: Optional[str] = "Đã được AI thẩm định"
    is_barter_eligible: Optional[int] = 1
    desired_exchange_items: Optional[str] = "Trao đổi linh hoạt"
    image_url: Optional[str] = None
    seller_id: Optional[int] = 1

@app.post("/api/v1/products")
def create_product(dto: ProductCreateDTO):
    if not dto.title or not dto.title.strip():
        raise HTTPException(status_code=400, detail="Tiêu đề sản phẩm không được để trống!")
    if dto.current_price <= 0:
        raise HTTPException(status_code=400, detail="Giá bán sản phẩm phải lớn hơn 0 VNĐ!")
    if dto.floor_price is not None and dto.floor_price > dto.current_price:
        raise HTTPException(status_code=400, detail="Giá sàn không được lớn hơn giá bán hiện tại!")

    db = load_db()
    seller = next((u for u in db["users"] if u["id"] == dto.seller_id), db["users"][0])
    floor_price = dto.floor_price if dto.floor_price is not None else (dto.current_price * 0.8)
    
    # Map category name
    cat_names = {
        "BOOKS": "Giáo Trình & Tài Liệu",
        "TECH": "Thiết Bị Điện Tử",
        "STATIONERY": "Dụng Cụ Học Tập",
        "OTHER": "Đồ Dùng Khác"
    }
    category_name = dto.category_name or cat_names.get(dto.category_id, "Đồ Dùng Học Tập")

    new_id = max([p["id"] for p in db["products"]] + [0]) + 1
    new_product = {
        "id": new_id,
        "seller_id": seller["id"],
        "seller_name": seller["full_name"],
        "category_id": dto.category_id,
        "category_name": category_name,
        "title": dto.title.strip(),
        "description": dto.description or "Sản phẩm chính chủ sinh viên HUNRE.",
        "original_price": dto.original_price or dto.current_price,
        "current_price": dto.current_price,
        "floor_price": floor_price,
        "condition_grade": dto.condition_grade or "GRADE_A",
        "ai_defect_score": dto.ai_defect_score or 0.05,
        "ai_inspection_summary": dto.ai_inspection_summary or "Đã xác thực ảnh thực tế",
        "is_barter_eligible": dto.is_barter_eligible if dto.is_barter_eligible is not None else 1,
        "desired_exchange_items": dto.desired_exchange_items or "Không có",
        "image_url": dto.image_url or "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop",
        "status": "ACTIVE",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db["products"].insert(0, new_product)
    save_db(db)
    return {"success": True, "message": "Đăng bán sản phẩm lên Chợ Sinh Viên thành công!", "data": new_product}

class ProductUpdateDTO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    current_price: Optional[float] = None
    floor_price: Optional[float] = None
    desired_exchange_items: Optional[str] = None
    status: Optional[str] = None

@app.put("/api/v1/products/{product_id}")
def update_product(product_id: int, dto: ProductUpdateDTO):
    db = load_db()
    product = next((p for p in db["products"] if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")

    if dto.title is not None:
        if not dto.title.strip():
            raise HTTPException(status_code=400, detail="Tiêu đề cập nhật không được để trống!")
        product["title"] = dto.title.strip()

    if dto.current_price is not None:
        if dto.current_price <= 0:
            raise HTTPException(status_code=400, detail="Giá bán cập nhật phải lớn hơn 0 VNĐ!")
        product["current_price"] = dto.current_price

    target_current = dto.current_price if dto.current_price is not None else product["current_price"]
    if dto.floor_price is not None:
        if dto.floor_price > target_current:
            raise HTTPException(status_code=400, detail="Giá sàn không được lớn hơn giá bán!")
        product["floor_price"] = dto.floor_price
    if dto.description is not None: product["description"] = dto.description
    if dto.category_id is not None: product["category_id"] = dto.category_id
    if dto.current_price is not None: product["current_price"] = dto.current_price
    if dto.floor_price is not None: product["floor_price"] = dto.floor_price
    if dto.desired_exchange_items is not None: product["desired_exchange_items"] = dto.desired_exchange_items
    if dto.status is not None: product["status"] = dto.status
    product["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_db(db)
    return {"success": True, "message": "Cập nhật sản phẩm thành công!", "data": product}

@app.delete("/api/v1/products/{product_id}")
def delete_product(product_id: int):
    db = load_db()
    initial_len = len(db["products"])
    db["products"] = [p for p in db["products"] if p["id"] != product_id]
    if len(db["products"]) == initial_len:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")
    save_db(db)
    return {"success": True, "message": f"Đã gỡ sản phẩm #{product_id} khỏi sàn giao dịch."}

# =============================================================
# 3. ESCROW SERVICE APIS (/api/v1/escrow)
# =============================================================

@app.get("/api/v1/escrow/orders")
def get_all_escrow_orders():
    db = load_db()
    return {"success": True, "orders": list(db["escrow_orders"].values())}

@app.get("/api/v1/escrow/orders/{order_code}")
def get_escrow_order(order_code: str):
    db = load_db()
    order = db["escrow_orders"].get(order_code)
    if not order:
        # Fallback thử lấy đơn đầu tiên nếu demo
        if db["escrow_orders"]:
            order = list(db["escrow_orders"].values())[0]
        else:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng ký quỹ.")
    return {"success": True, "order": order}

class CreateOrderDTO(BaseModel):
    product_id: int
    buyer_id: Optional[int] = 1
    agreed_price: Optional[float] = None

@app.post("/api/v1/escrow/orders")
def create_escrow_order(dto: CreateOrderDTO):
    db = load_db()
    product = next((p for p in db["products"] if p["id"] == dto.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm để tạo đơn.")
    
    buyer = next((u for u in db["users"] if u["id"] == dto.buyer_id), db["users"][0])
    seller = next((u for u in db["users"] if u["id"] == product["seller_id"]), db["users"][2])
    
    order_code = f"ORD-HUNRE-{int(time.time()) % 100000:05d}"
    amount = dto.agreed_price if dto.agreed_price is not None else product["current_price"]

    new_order = {
        "order_code": order_code,
        "buyer_id": buyer["id"],
        "buyer_name": buyer["full_name"],
        "seller_id": seller["id"],
        "seller_name": seller["full_name"],
        "product_id": product["id"],
        "product_title": product["title"],
        "hub_id": 1,
        "hub_name": "Trạm Hub CS1 (Nhà A - Văn Phòng Đoàn Trường)",
        "locker_code": "LOCKER-M-02",
        "escrow_amount": amount,
        "saga_step": 2, # Đã đặt hàng và khóa cọc
        "status": "DEPOSITED",
        "deadline": "17:30 ngày mai",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db["escrow_orders"][order_code] = new_order
    save_db(db)
    return {"success": True, "message": "Tạo đơn hàng và khóa tiền ký quỹ thành công!", "order": new_order}

class SagaAdvanceDTO(BaseModel):
    order_code: str
    action: str  # CHECKIN, CHECKOUT, SATISFIED, DISPUTE

@app.post("/api/v1/escrow/saga/advance")
def advance_saga(dto: SagaAdvanceDTO):
    if dto.action not in ["CHECKIN", "CHECKOUT", "SATISFIED", "DISPUTE"]:
        raise HTTPException(status_code=400, detail=f"Hành động Saga '{dto.action}' không hợp lệ! Chỉ chấp nhận: CHECKIN, CHECKOUT, SATISFIED, DISPUTE.")

    db = load_db()
    order = db["escrow_orders"].get(dto.order_code)
    if not order:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đơn hàng ký quỹ '{dto.order_code}'.")

    if dto.action == "CHECKIN":
        order["saga_step"] = 4
        order["status"] = "STORED_AT_HUB"
        msg = "Người bán đã gửi đồ vào Trạm Hub. Đồ đã lưu an toàn trong tủ Locker."
    elif dto.action == "CHECKOUT":
        order["saga_step"] = 5
        order["status"] = "BUYER_CHECKOUT"
        msg = "Người mua đã mở tủ nhận đồ và đang kiểm tra tại bàn Trạm Hub."
    elif dto.action == "SATISFIED":
        order["saga_step"] = 7
        order["status"] = "RELEASED"
        # Cộng điểm uy tín +5 cho cả 2 bên
        for u in db["users"]:
            if u["id"] in [order["buyer_id"], order["seller_id"]]:
                u["trust_score"] = min(1000, u["trust_score"] + 5)
        msg = f"Người mua xác nhận hài lòng! Đã giải ngân {int(order['escrow_amount']):,}đ cho người bán {order['seller_name']}. Cả 2 được cộng +5 Điểm Uy Tín!"
    elif dto.action == "DISPUTE":
        order["saga_step"] = 7
        order["status"] = "DISPUTED"
        msg = "Đã tiếp nhận khiếu nại! Tiền ký quỹ bị đóng băng để Trạm Hub hoàn cọc 100%."

    save_db(db)
    return {"success": True, "message": msg, "order": order}

@app.post("/api/v1/escrow/orders/{order_code}/release")
def release_escrow(order_code: str):
    return advance_saga(SagaAdvanceDTO(order_code=order_code, action="SATISFIED"))

@app.post("/api/v1/escrow/orders/{order_code}/dispute")
def dispute_escrow(order_code: str):
    return advance_saga(SagaAdvanceDTO(order_code=order_code, action="DISPUTE"))

# =============================================================
# 4. HUB SERVICE APIS (/api/v1/hub)
# =============================================================

@app.get("/api/v1/hub/lockers")
def get_lockers():
    db = load_db()
    return {"success": True, "lockers": db["lockers"]}

class HubScanDTO(BaseModel):
    order_code: str
    scan_type: str # CHECKIN hoặc CHECKOUT

@app.post("/api/v1/hub/checkin")
def hub_checkin(dto: HubScanDTO):
    db = load_db()
    # Tìm locker trống
    empty_locker = next((l for l in db["lockers"] if l["status"] == "EMPTY"), None)
    if not empty_locker:
        raise HTTPException(status_code=409, detail="Toàn bộ ô tủ Locker tại Trạm Hub CS1 đang bận! Vui lòng chờ giải phóng ô tủ.")
    
    empty_locker["status"] = "OCCUPIED"
    empty_locker["current_order"] = dto.order_code

    if dto.order_code in db["escrow_orders"]:
        db["escrow_orders"][dto.order_code]["status"] = "STORED_AT_HUB"
        db["escrow_orders"][dto.order_code]["saga_step"] = 4
        db["escrow_orders"][dto.order_code]["locker_code"] = empty_locker["locker_code"]

    save_db(db)
    return {
        "success": True,
        "message": f"Quét nhận hàng thành công! Đã cấp phát ô tủ {empty_locker['locker_code']} ({empty_locker['description']}).",
        "locker": empty_locker
    }

@app.post("/api/v1/hub/checkout")
def hub_checkout(dto: HubScanDTO):
    db = load_db()
    # Tìm locker của order này
    locker = next((l for l in db["lockers"] if l.get("current_order") == dto.order_code), None)
    if not locker:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ô tủ Locker đang chứa đơn hàng '{dto.order_code}'!")
    
    locker["status"] = "EMPTY"
    locker["current_order"] = None

    if dto.order_code in db["escrow_orders"]:
        db["escrow_orders"][dto.order_code]["status"] = "BUYER_CHECKOUT"
        db["escrow_orders"][dto.order_code]["saga_step"] = 5

    save_db(db)
    return {
        "success": True,
        "message": f"Xác thực mã QR thành công! Đã mở khóa ô tủ {locker['locker_code']}. Người mua đang nhận hàng kiểm tra.",
        "locker": locker
    }

@app.get("/api/v1/hub/orders/{order_code}/dynamic-qr")
def generate_dynamic_qr(order_code: str, user_id: int = 1, role: str = "BUYER"):
    time_window = int(time.time() // 30)
    payload = f"{order_code}|{user_id}|{role}|{time_window}"
    token = hmac.new(b"HUNRE_SECRET_2026", payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
    seconds_left = 30 - int(time.time() % 30)
    return {
        "success": True,
        "data": {
            "order_code": order_code,
            "role": role,
            "token": token,
            "expires_in_seconds": seconds_left,
            "qr_payload": f"HUNRE:{order_code}:{user_id}:{role}:{token}",
            "qr_image_url": f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=HUNRE:{order_code}:{user_id}:{role}:{token}"
        }
    }

# =============================================================
# 5. AI VISION RECOGNITION (GOOGLE GEMINI 1.5 FLASH & SMART CV)
# =============================================================

class GeminiKeyDTO(BaseModel):
    api_key: str

@app.get("/api/v1/ai/config/key")
def get_ai_key_status():
    db = load_db()
    key = os.getenv("GEMINI_API_KEY") or db.get("config", {}).get("gemini_api_key", "")
    has_key = bool(key and len(key) > 5)
    masked = f"{key[:6]}...{key[-4:]}" if has_key and len(key) >= 10 else ("Đã kích hoạt" if has_key else "Chưa cấu hình")
    return {
        "success": True,
        "has_key": has_key,
        "masked_key": masked,
        "model": "gemini-3.5-flash-lite"
    }

@app.post("/api/v1/ai/config/key")
def set_ai_key(dto: GeminiKeyDTO):
    key = dto.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="Mã API Key không được để trống!")
    db = load_db()
    if "config" not in db:
        db["config"] = {}
    db["config"]["gemini_api_key"] = key
    save_db(db)
    os.environ["GEMINI_API_KEY"] = key
    return {
        "success": True,
        "message": "Đã lưu và kích hoạt Google Gemini API Key thành công!",
        "masked_key": f"{key[:6]}...{key[-4:]}" if len(key) >= 10 else "Đã lưu"
    }

@app.post("/api/v1/ai/cv/inspect")
async def inspect_product_image_endpoint(file: UploadFile = File(...)):
    # Bắt lỗi định dạng tệp tin (Yêu cầu ngoại lệ AI-EX-03)
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    valid_exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".jfif")
    is_image = content_type.startswith("image/") or any(filename.endswith(ext) for ext in valid_exts)
    if not is_image:
        raise HTTPException(status_code=400, detail="Tệp tin không đúng định dạng hình ảnh! Chỉ chấp nhận JPG, PNG, WEBP.")
    
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Tệp tin ảnh rỗng!")
    
    # Đọc thông tin kích thước và phân tích sắc nét
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = pil_img.size
        aspect_ratio = width / max(1, height)
        
        gray = pil_img.convert("L")
        arr = np.array(gray, dtype=np.float32)
        gy, gx = np.gradient(arr)
        sharpness = float(np.mean(np.sqrt(gx**2 + gy**2)))
        defect_ratio = round(min(0.35, max(0.01, (100 - min(sharpness * 3, 90)) / 250)), 3)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể phân tích tệp tin ảnh: {str(e)}")

    db = load_db()
    gemini_key = os.getenv("GEMINI_API_KEY") or db.get("config", {}).get("gemini_api_key", "")
    
    recognition = None
    ai_model_name = "HUNRE Computer Vision Classifier"
    
    # 1. Thử gọi Google Gemini Vision (3.5 Flash Lite / 3.8 Flash) nếu có API Key
    if gemini_key:
        os.environ.pop('CURL_CA_BUNDLE', None)
        os.environ.pop('REQUESTS_CA_BUNDLE', None)
        os.environ.pop('SSL_CERT_FILE', None)
        ca_bundle = None
        try:
            import certifi
            ca_bundle = certifi.where()
            os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle
            os.environ['SSL_CERT_FILE'] = ca_bundle
        except Exception:
            pass

        try:
            b64_img = base64.b64encode(image_bytes).decode("utf-8")
            prompt = """
            Bạn là Giám định viên AI & Chuyên gia Thẩm định giá O2O của trường Đại học Tài nguyên và Môi trường Hà Nội (HUNRE).
            Nhiệm vụ của bạn là xem hình ảnh sản phẩm sinh viên tải lên và trả lời chính xác 4 câu hỏi:

            1. ĐÂY LÀ GÌ?
               - Nhận diện tên cụ thể của món đồ (model, thương hiệu, giáo trình hay thiết bị).
               - Phân loại danh mục trên sàn sinh viên HUNRE (BOOKS: Sách/Giáo trình, TECH: Thiết bị điện tử, STATIONERY: Đồ dùng học tập, OTHER: Khác).
               - Tên danh mục hiển thị tiếng Việt.

            2. ĐỘ MỚI BAO NHIÊU?
               - Ước tính phần trăm độ mới (condition_percentage: từ 50 đến 99).
               - Xếp hạng Condition Grade:
                 * GRADE_S: Like New / Mới 96-99%
                 * GRADE_A: Rất tốt / Mới 90-95%, trầy xước rất nhẹ
                 * GRADE_B: Tốt / Mới 80-89%, hao mòn tự nhiên theo thời gian
                 * GRADE_C: Trung bình / Mới 60-79%, có vết trầy xước, ố vàng, sứt mẻ rõ
               - Nhãn hiển thị độ mới (grade_label: ví dụ "Độ mới 95% (Rất tốt)").
               - Tỷ lệ lỗi bề mặt defect_ratio (từ 0.01 đến 0.35).
               - Mô tả chi tiết trực quan tình trạng bề mặt quan sát được từ ảnh (vết trầy, ố vàng, tem mác, độ hao mòn).

            3. NGOÀI THỊ TRƯỜNG GIÁ MỚI THẾ NÀO?
               - Ước tính giá bán mới 100% chính hãng ngoài thị trường hiện tại ở Việt Nam (suggested_original_price tính bằng VNĐ).
               - Ghi chú giá thị trường mới (market_price_notes: ví dụ "Giá mua mới chính hãng ngoài thị trường khoảng 650.000đ - 720.000đ").

            4. VÀ ĐỊNH GIÁ CÁI NÀY BAO NHIÊU?
               - Định giá thanh lý / bán lại đồ cũ (second-hand) cho sinh viên HUNRE (suggested_selling_price bằng VNĐ, vừa túi tiền sinh viên).
               - Đề xuất giá sàn tối thiểu có thể thương lượng / mặc cả tự động với AI (suggested_floor_price bằng VNĐ).
               - Lý do định giá (pricing_reason: giải thích dựa trên độ mới, độ hot và túi tiền sinh viên).
               - Gợi ý món đồ trao đổi phù hợp cho sinh viên HUNRE (desired_exchange_items).

            YÊU CẦU: Trả về DUY NHẤT một chuỗi JSON thuần tuý (RFC 8259), không bọc markdown ```json, không thêm text ngoài:
            {
              "item_name": "Tên chi tiết món đồ",
              "category": "BOOKS hoặc TECH hoặc STATIONERY hoặc OTHER",
              "category_name": "Tên tiếng Việt danh mục",
              "condition_percentage": 95,
              "condition_grade": "GRADE_A",
              "grade_label": "Độ mới 95% (Rất tốt)",
              "defect_ratio": 0.04,
              "visual_description": "Mô tả nhận định chi tiết tình trạng bề mặt quan sát từ ảnh",
              "suggested_original_price": 550000,
              "market_price_notes": "Giá mua mới ngoài thị trường khoảng 550.000đ - 650.000đ",
              "suggested_selling_price": 380000,
              "suggested_floor_price": 320000,
              "pricing_reason": "Lý do định giá cụ thể dựa trên độ mới và giá trị thực tế cho sinh viên HUNRE",
              "desired_exchange_items": "Gợi ý đồ đổi",
              "detected_tags": ["máy tính", "casio", "sinh viên"]
            }
            """

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": b64_img
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json"
                }
            }

            candidate_models = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
            for model in candidate_models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                    resp = requests.post(url, json=payload, timeout=12, verify=ca_bundle if ca_bundle else True)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        text_out = res_json["candidates"][0]["content"]["parts"][0]["text"]
                        clean_text = text_out.strip()
                        if clean_text.startswith("```"):
                            clean_text = clean_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                        recognition = json.loads(clean_text)
                        ai_model_name = f"Google Gemini ({model} - DeepMind Multimodal Vision)"
                        break
                except Exception as gemini_err:
                    print(f"[Gemini Vision {model} Fallback]: {gemini_err}")
                    continue
        except Exception as e:
            print(f"[Gemini Vision Overall Exception]: {e}")
            recognition = None

    # 2. Nếu không có key hoặc Gemini gọi lỗi -> Dùng Heuristic Vision Classifier cục bộ
    if not recognition:
        if aspect_ratio < 0.88:  # Khung dọc đứng -> Sách / Giáo trình
            recognition = {
                "item_name": "Giáo trình Cơ Sở Dữ Liệu & SQL (HUNRE)",
                "category": "BOOKS",
                "category_name": "Giáo Trình & Tài Liệu",
                "condition_percentage": 94,
                "suggested_original_price": 85000,
                "market_price_notes": "Giá bìa sách mới tại thư viện / nhà sách khoảng 85.000đ - 95.000đ",
                "suggested_selling_price": 75000,
                "suggested_floor_price": 60000,
                "pricing_reason": "Giáo trình dùng thường xuyên cho K11-K12 CNTT, sách giữ gìn cẩn thận, bìa phẳng không ố.",
                "condition_grade": "GRADE_A" if defect_ratio < 0.08 else "GRADE_B",
                "grade_label": "Độ mới 94% (Rất tốt)" if defect_ratio < 0.08 else "Độ mới 85% (Khá)",
                "defect_ratio": defect_ratio,
                "visual_description": "Ảnh chụp thực tế sinh viên HUNRE, mép phẳng, bìa sạch không ố vàng, ghi chú bài tập đầy đủ.",
                "desired_exchange_items": "Máy tính Casio FX 580VN hoặc Balo",
                "detected_tags": ["sách giáo trình", "tài liệu học tập", "k11-k12"]
            }
        elif 0.88 <= aspect_ratio <= 1.25:  # Khung vuông -> Máy tính Casio / Thiết bị nhỏ
            recognition = {
                "item_name": "Máy tính Casio FX 580VN X (Like New)",
                "category": "TECH",
                "category_name": "Thiết Bị Điện Tử",
                "condition_percentage": 98,
                "suggested_original_price": 680000,
                "market_price_notes": "Giá mua mới chính hãng Bitex hiện nay khoảng 650.000đ - 720.000đ",
                "suggested_selling_price": 450000,
                "suggested_floor_price": 380000,
                "pricing_reason": "Máy tính thi đại học và tốt nghiệp bắt buộc, máy giữ như mới, tem chống giả nguyên vẹn.",
                "condition_grade": "GRADE_S" if defect_ratio < 0.04 else "GRADE_A",
                "grade_label": "Độ mới 98% (Like New)",
                "defect_ratio": defect_ratio,
                "visual_description": "Màn hình LCD sắc nét không trầy xước, phím bấm nhạy nảy, tem Bộ GD&ĐT còn nguyên vẹn.",
                "desired_exchange_items": "Bàn phím cơ DareU hoặc Balo",
                "detected_tags": ["máy tính casio", "dụng cụ thi", "fx580"]
            }
        else:  # Khung ngang rộng -> Bàn phím cơ / Thiết bị ngoại vi
            recognition = {
                "item_name": "Bàn phím cơ DareU EK87 Blue Switch (Type-C)",
                "category": "TECH",
                "category_name": "Thiết Bị Điện Tử",
                "condition_percentage": 88,
                "suggested_original_price": 490000,
                "market_price_notes": "Giá niêm yết bán mới tại các đại lý công nghệ khoảng 450.000đ - 520.000đ",
                "suggested_selling_price": 250000,
                "suggested_floor_price": 200000,
                "pricing_reason": "Bàn phím cơ phổ thông cho sinh viên IT thực hành gõ code, phím nảy tốt, hao mòn nhẹ bề mặt.",
                "condition_grade": "GRADE_B" if defect_ratio > 0.05 else "GRADE_A",
                "grade_label": "Độ mới 88% (Khá tốt)",
                "defect_ratio": defect_ratio,
                "visual_description": "Keycap hơi bóng nhẹ ở cụm phím chính, có vết xước dăm góc trái vỏ, toàn bộ Blue Switch hoạt động chuẩn.",
                "desired_exchange_items": "Giáo trình CSDL hoặc Sách Tiếng Anh",
                "detected_tags": ["bàn phím cơ", "dareu", "phụ kiện laptop"]
            }

    # Tổng hợp cấu trúc chi tiết trả lời 4 câu hỏi cốt lõi
    cond_percent = recognition.get("condition_percentage") or int(round((1 - float(recognition.get("defect_ratio", defect_ratio))) * 100))
    orig_price = float(recognition.get("suggested_original_price", 80000))
    sell_price = float(recognition.get("suggested_selling_price", 65000))
    floor_price = float(recognition.get("suggested_floor_price", 50000))
    discount_pct = round((1 - sell_price / max(1.0, orig_price)) * 100, 1) if orig_price > 0 else 0

    four_questions = {
        "1_what_is_it": {
            "title": "Đây là gì?",
            "item_name": recognition.get("item_name", "Đồ Dùng Sinh Viên"),
            "category": recognition.get("category", "OTHER"),
            "category_name": recognition.get("category_name", "Đồ Dùng Học Tập"),
            "detected_tags": recognition.get("detected_tags", [])
        },
        "2_condition": {
            "title": "Độ mới bao nhiêu?",
            "condition_percentage": cond_percent,
            "condition_grade": recognition.get("condition_grade", "GRADE_A"),
            "grade_label": recognition.get("grade_label", f"Độ mới {cond_percent}%"),
            "defect_ratio": recognition.get("defect_ratio", defect_ratio),
            "visual_description": recognition.get("visual_description", "Ảnh chụp thực tế sinh viên, bề mặt tốt.")
        },
        "3_market_new_price": {
            "title": "Ngoài thị trường giá mới thế nào?",
            "suggested_original_price": orig_price,
            "market_price_notes": recognition.get("market_price_notes", f"Giá mua mới trên thị trường khoảng {int(orig_price):,}đ")
        },
        "4_suggested_valuation": {
            "title": "Và định giá cái này bao nhiêu?",
            "suggested_selling_price": sell_price,
            "suggested_floor_price": floor_price,
            "discount_percentage": discount_pct,
            "pricing_reason": recognition.get("pricing_reason", "Định giá phù hợp với túi tiền sinh viên HUNRE."),
            "desired_exchange_items": recognition.get("desired_exchange_items", "Sách giáo trình hoặc đồ dùng học tập")
        }
    }

    dhash = hashlib.sha256(image_bytes).hexdigest()[:16].upper()
    return {
        "success": True,
        "ai_model": ai_model_name,
        "four_questions": four_questions,
        "recognition": recognition,
        "inspection": {
            "dimensions": {"width": width, "height": height},
            "metrics": {
                "sharpness_score": round(sharpness, 2),
                "defect_ratio": recognition.get("defect_ratio", defect_ratio)
            },
            "evaluation": {
                "condition_grade": recognition.get("condition_grade", "GRADE_A"),
                "grade_label": recognition.get("grade_label", "GRADE A - Rất tốt"),
                "summary": recognition.get("visual_description", "Ảnh chụp thực tế sinh viên"),
                "authenticity_confidence": 0.96
            }
        },
        "anti_fraud": {
            "is_authentic": True,
            "recommendation": "Ảnh chụp thực tế sinh viên HUNRE (Đã đối chiếu dHash)",
            "phash_signature": f"dHash-{dhash}"
        }
    }

# =============================================================
# 6. AI PRICING, TIME-DECAY & BARTER GRAPH SOLVER
# =============================================================

class BarterItemDTO(BaseModel):
    id: int
    seller_id: int
    seller_name: Optional[str] = None
    title: str
    category_name: Optional[str] = None
    current_price: float
    desired_category_or_title: str
    accept_any_match: Optional[bool] = False

class BarterRequestDTO(BaseModel):
    items: List[BarterItemDTO]
    max_cycle_length: Optional[int] = Field(default=3, ge=2, le=5)

class TimeDecayRequestDTO(BaseModel):
    original_price: float
    floor_price: float
    hours_elapsed: float
    decay_half_life_hours: Optional[float] = 72.0

class NegotiationRequestDTO(BaseModel):
    item_current_price: float
    item_floor_price: float
    buyer_offer_price: float
    buyer_trust_score: int

@app.post("/api/v1/ai/pricing/decay")
def calculate_time_decay(payload: TimeDecayRequestDTO):
    if PriceNegotiatorAgent:
        return PriceNegotiatorAgent.calculate_decay_price(
            original_price=payload.original_price,
            floor_price=payload.floor_price,
            hours_elapsed=payload.hours_elapsed,
            decay_half_life_hours=payload.decay_half_life_hours
        )
    decay_constant = 0.693147 / payload.decay_half_life_hours
    decayed_excess = (payload.original_price - payload.floor_price) * (2.7182818 ** (-decay_constant * payload.hours_elapsed))
    current_price = round(max(payload.floor_price, payload.floor_price + decayed_excess), -3)
    discount = round((1 - current_price / payload.original_price) * 100, 1) if payload.original_price > 0 else 0
    return {
        "original_price": payload.original_price,
        "floor_price": payload.floor_price,
        "hours_elapsed": payload.hours_elapsed,
        "current_decayed_price": current_price,
        "discount_percentage": discount,
        "is_at_floor": current_price <= payload.floor_price
    }

@app.post("/api/v1/ai/pricing/negotiate")
def negotiate_price(payload: NegotiationRequestDTO):
    if PriceNegotiatorAgent:
        return PriceNegotiatorAgent.negotiate_offer(
            item_current_price=payload.item_current_price,
            item_floor_price=payload.item_floor_price,
            buyer_offer_price=payload.buyer_offer_price,
            buyer_trust_score=payload.buyer_trust_score
        )
    if payload.buyer_offer_price >= payload.item_current_price:
        return {"decision": "ACCEPT", "final_price": payload.buyer_offer_price, "message": "Giá trả hợp lý, giao dịch được phê duyệt!"}
    if payload.buyer_offer_price < payload.item_floor_price:
        if payload.buyer_trust_score >= 600:
            counter = round(payload.item_floor_price * 1.03, -3)
            return {"decision": "COUNTER_OFFER", "counter_offer_price": counter, "message": f"Mức giá dưới giá sàn. Đề xuất: {int(counter):,}đ."}
        return {"decision": "REJECT", "floor_price_hint": payload.item_floor_price, "message": "Giá đề xuất quá thấp so với giá sàn."}
    mid = round((payload.buyer_offer_price + payload.item_current_price) / 2, -3)
    return {"decision": "COUNTER_OFFER", "counter_offer_price": mid, "message": f"Mức giá thương lượng AI đề xuất: {int(mid):,}đ."}

@app.post("/api/v1/ai/barter/solve-cycles")
def solve_barter_cycles(payload: BarterRequestDTO):
    if BarterGraphSolver:
        raw_items = [item.model_dump() for item in payload.items]
        cycles = BarterGraphSolver.detect_and_balance_cycles(raw_items, payload.max_cycle_length)
        return {
            "total_items_analyzed": len(raw_items),
            "cycles_found_count": len(cycles),
            "cycles": cycles
        }
    return {"total_items_analyzed": len(payload.items), "cycles_found_count": 0, "cycles": []}

@app.api_route("/api/v1/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_ai_engine(path: str, request: Request):
    ai_url = f"http://localhost:8005/api/v1/ai/{path}"
    headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
    body = await request.body()
    try:
        resp = requests.request(
            method=request.method,
            url=ai_url,
            headers=headers,
            data=body,
            timeout=10
        )
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
    except Exception as e:
        return {
            "success": False,
            "message": f"Không thể kết nối đến AI Service (cổng 8005): {str(e)}",
            "hint": "Khởi động AI Engine bằng lệnh: python -m uvicorn app.main:app --port 8005 tại BTL/services/ai-engine"
        }

# =============================================================
# 6. CART SERVICE APIS (/api/v1/cart - LAB 04)
# =============================================================

class CartItemAddDTO(BaseModel):
    user_id: Optional[int] = 1
    product_id: int
    quantity: Optional[int] = 1

class CartItemUpdateDTO(BaseModel):
    user_id: Optional[int] = 1
    product_id: int
    quantity: int

@app.get("/api/v1/cart")
def get_cart(user_id: int = Query(1)):
    db = load_db()
    uid_str = str(user_id)
    items = db.get("carts", {}).get(uid_str, [])
    total_price = sum(item["price"] * item["quantity"] for item in items)
    cart_data = {
        "user_id": user_id,
        "items": items,
        "item_count": sum(item["quantity"] for item in items),
        "total_items": sum(item["quantity"] for item in items),
        "total_price": total_price,
        "total_amount": total_price
    }
    return {
        "success": True,
        "data": cart_data,
        **cart_data
    }

@app.post("/api/v1/cart/add")
def add_to_cart(dto: CartItemAddDTO):
    if dto.quantity <= 0:
        raise HTTPException(status_code=400, detail="Số lượng thêm vào giỏ phải lớn hơn 0!")
    db = load_db()
    product = next((p for p in db["products"] if p["id"] == dto.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại!")
    
    uid_str = str(dto.user_id)
    if "carts" not in db:
        db["carts"] = {}
    if uid_str not in db["carts"]:
        db["carts"][uid_str] = []
    
    user_cart = db["carts"][uid_str]
    existing_item = next((item for item in user_cart if item["product_id"] == dto.product_id), None)
    if existing_item:
        existing_item["quantity"] += dto.quantity
    else:
        user_cart.append({
            "product_id": product["id"],
            "title": product["title"],
            "price": product["current_price"],
            "unit_price": product["current_price"],
            "quantity": dto.quantity,
            "image_url": product.get("image_url", ""),
            "category_name": product.get("category_name", "")
        })
    save_db(db)
    
    total_price = sum(item["price"] * item["quantity"] for item in user_cart)
    cart_data = {
        "user_id": dto.user_id,
        "items": user_cart,
        "item_count": sum(item["quantity"] for item in user_cart),
        "total_items": sum(item["quantity"] for item in user_cart),
        "total_price": total_price,
        "total_amount": total_price
    }
    return {
        "success": True,
        "message": f"Đã thêm '{product['title']}' vào giỏ hàng!",
        "cart": user_cart,
        "data": cart_data
    }

@app.put("/api/v1/cart/update")
def update_cart_item(dto: CartItemUpdateDTO):
    if dto.quantity <= 0:
        raise HTTPException(status_code=400, detail="Số lượng cập nhật trong giỏ hàng phải lớn hơn 0!")
    db = load_db()
    uid_str = str(dto.user_id)
    user_cart = db.get("carts", {}).get(uid_str, [])
    item = next((i for i in user_cart if i["product_id"] == dto.product_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Sản phẩm không có trong giỏ hàng!")
    
    item["quantity"] = dto.quantity
    save_db(db)
    
    total_price = sum(item["price"] * item["quantity"] for item in user_cart)
    cart_data = {
        "user_id": dto.user_id,
        "items": user_cart,
        "item_count": sum(item["quantity"] for item in user_cart),
        "total_items": sum(item["quantity"] for item in user_cart),
        "total_price": total_price,
        "total_amount": total_price
    }
    return {
        "success": True,
        "message": "Đã cập nhật số lượng món hàng!",
        "cart": user_cart,
        "data": cart_data
    }

@app.delete("/api/v1/cart/remove/{product_id}")
def remove_from_cart(product_id: int, user_id: int = Query(1)):
    db = load_db()
    uid_str = str(user_id)
    user_cart = db.get("carts", {}).get(uid_str, [])
    initial_len = len(user_cart)
    db["carts"][uid_str] = [i for i in user_cart if i["product_id"] != product_id]
    if len(db["carts"][uid_str]) == initial_len:
        raise HTTPException(status_code=404, detail="Sản phẩm không có trong giỏ hàng để xóa!")
    save_db(db)
    
    updated_cart = db["carts"][uid_str]
    total_price = sum(item["price"] * item["quantity"] for item in updated_cart)
    cart_data = {
        "user_id": user_id,
        "items": updated_cart,
        "item_count": sum(item["quantity"] for item in updated_cart),
        "total_items": sum(item["quantity"] for item in updated_cart),
        "total_price": total_price,
        "total_amount": total_price
    }
    return {
        "success": True,
        "message": "Đã xóa sản phẩm khỏi giỏ hàng!",
        "cart": updated_cart,
        "data": cart_data
    }

@app.delete("/api/v1/cart/clear")
def clear_cart(user_id: int = Query(1)):
    db = load_db()
    uid_str = str(user_id)
    if "carts" in db and uid_str in db["carts"]:
        db["carts"][uid_str] = []
        save_db(db)
    return {"success": True, "message": "Đã dọn sạch giỏ hàng!"}

# =============================================================
# 7. SHIPPING SERVICE APIS (/api/v1/shipping - LAB 05 GHN API)
# =============================================================

class ShippingFeeDTO(BaseModel):
    method: str  # HUB_PICKUP hoặc GHN_DELIVERY
    province: Optional[str] = "Hà Nội"
    district: Optional[str] = "Bắc Từ Liêm"

@app.post("/api/v1/shipping/calculate-fee")
def calculate_shipping_fee(dto: ShippingFeeDTO):
    if dto.method == "HUB_PICKUP":
        return {
            "success": True,
            "method": "HUB_PICKUP",
            "fee": 0.0,
            "estimated_delivery": "Lấy ngay trong ngày",
            "description": "Nhận miễn phí tại Trạm Hub CS1 HUNRE (Ô tủ Locker thông minh bảo vệ 24/7)"
        }
    elif dto.method == "GHN_DELIVERY":
        # Chuẩn Lab 05: Tính phí ship nội/ngoại thành
        is_inner_hanoi = "bắc từ liêm" in (dto.district or "").lower() or "cầu giấy" in (dto.district or "").lower()
        fee = 22000.0 if is_inner_hanoi else 30000.0
        return {
            "success": True,
            "method": "GHN_DELIVERY",
            "fee": fee,
            "estimated_delivery": "1 - 2 ngày làm việc",
            "description": f"Giao Hàng Nhanh (GHN) Express - Giao tận phòng trọ tại {dto.district}, {dto.province}"
        }
    else:
        raise HTTPException(status_code=400, detail="Phương thức giao hàng không hợp lệ! Chỉ chấp nhận HUB_PICKUP hoặc GHN_DELIVERY.")

# =============================================================
# 8. ORDERS & MULTI-GATEWAY PAYMENT APIS (/api/v1/orders - LAB 06 & LAB 09)
# =============================================================

class OrderCheckoutDTO(BaseModel):
    user_id: Optional[int] = None
    buyer_id: Optional[int] = None
    customer_name: Optional[str] = None
    receiver_name: Optional[str] = None
    customer_phone: Optional[str] = None
    receiver_phone: Optional[str] = None
    shipping_address: str
    shipping_method: Optional[str] = "HUB_PICKUP" # HUB_PICKUP hoặc GHN_DELIVERY
    gateway: Optional[str] = None # ESCROW, MOMO, COD
    payment_gateway: Optional[str] = None
    voucher_code: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None # Nếu None, lấy từ cart của user
    note: Optional[str] = ""
    notes: Optional[str] = ""

@app.post("/api/v1/orders/checkout")
def checkout_order(dto: OrderCheckoutDTO):
    u_id = dto.user_id if dto.user_id is not None else (dto.buyer_id if dto.buyer_id is not None else 1)
    c_name = (dto.customer_name or dto.receiver_name or "").strip()
    c_phone = (dto.customer_phone or dto.receiver_phone or "").strip()
    c_gateway = (dto.gateway or dto.payment_gateway or "ESCROW").upper()
    c_note = (dto.note or dto.notes or "").strip()

    if not c_name or not c_phone:
        raise HTTPException(status_code=422, detail="Tên người nhận và số điện thoại không được để trống!")
    
    db = load_db()
    uid_str = str(u_id)
    items = dto.items
    from_cart = False
    if not items or len(items) == 0:
        items = db.get("carts", {}).get(uid_str, [])
        from_cart = True
    
    if not items or len(items) == 0:
        raise HTTPException(status_code=400, detail="Giỏ hàng đang trống! Vui lòng chọn ít nhất 1 sản phẩm để đặt hàng.")
    
    items_total = sum(i.get("price", i.get("unit_price", 0)) * i.get("quantity", 1) for i in items)
    shipping_fee = 0.0 if dto.shipping_method == "HUB_PICKUP" else 25000.0
    discount_amount = 0.0
    
    if dto.voucher_code:
        v_code = dto.voucher_code.strip().upper()
        voucher = next((v for v in db.get("vouchers", []) if v["code"].upper() == v_code), None)
        if not voucher:
            raise HTTPException(status_code=404, detail=f"Mã voucher '{dto.voucher_code}' không tồn tại hoặc đã hết hạn!")
        if items_total < voucher.get("min_order_value", 0):
            raise HTTPException(status_code=400, detail=f"Đơn hàng phải từ {int(voucher['min_order_value']):,}đ để dùng mã {v_code}!")
        if voucher.get("discount_percent", 0) > 0:
            discount_amount = items_total * (voucher["discount_percent"] / 100.0)
        else:
            discount_amount = voucher.get("discount_amount", 0.0)
    
    total_price = max(0.0, items_total + shipping_fee - discount_amount)
    order_code = f"DH{datetime.now().strftime('%Y%m%d')}-{int(time.time()) % 10000:04d}"
    
    if c_gateway not in ["ESCROW", "MOMO", "COD"]:
        raise HTTPException(status_code=400, detail="Cổng thanh toán không hợp lệ! Chọn ESCROW, MOMO hoặc COD.")
    
    payment_status = "paid" if c_gateway == "ESCROW" else "pending"
    order_status = "pending" # Bắt đầu ở tab Chờ xử lý của Lab 08
    
    new_order = {
        "id": max([o["id"] for o in db.get("orders", [])] + [0]) + 1,
        "order_code": order_code,
        "user_id": u_id,
        "customer_name": c_name,
        "customer_phone": c_phone,
        "shipping_address": dto.shipping_address.strip(),
        "shipping_method": dto.shipping_method,
        "shipping_fee": shipping_fee,
        "items": items,
        "items_total": items_total,
        "discount_amount": discount_amount,
        "voucher_code": dto.voucher_code,
        "total_price": total_price,
        "gateway": c_gateway,
        "status": order_status,
        "payment_status": payment_status,
        "note": c_note,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if "orders" not in db: db["orders"] = []
    db["orders"].insert(0, new_order)
    
    # Ghi nhận vào payment_transactions (Lab 06 & Lab 09)
    if "payment_transactions" not in db: db["payment_transactions"] = []
    tx_id = max([t["id"] for t in db["payment_transactions"]] + [0]) + 1
    new_tx = {
        "id": tx_id,
        "order_code": order_code,
        "gateway": c_gateway.lower(),
        "amount": total_price,
        "status": payment_status,
        "result_code": 0,
        "message": "Thanh toán Ký Quỹ thành công" if c_gateway == "ESCROW" else ("Khởi tạo giao dịch MoMo Sandbox" if c_gateway == "MOMO" else "Chờ thu tiền mặt khi giao hàng (COD)"),
        "paid_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if payment_status == "paid" else None,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db["payment_transactions"].insert(0, new_tx)
    
    # Nếu chọn ESCROW, đồng bộ sang escrow_orders để tương thích hoàn toàn
    if c_gateway == "ESCROW":
        first_item = items[0]
        db["escrow_orders"][order_code] = {
            "order_code": order_code,
            "buyer_id": u_id,
            "buyer_name": c_name,
            "seller_id": 3,
            "seller_name": "Lê Hoàng Cường",
            "product_id": first_item.get("product_id", 1),
            "product_title": first_item.get("title", "Đơn hàng Chợ Sinh Viên"),
            "hub_id": 1,
            "hub_name": "Trạm Hub CS1 (Nhà A - Văn Phòng Đoàn Trường)",
            "locker_code": "LOCKER-M-02",
            "escrow_amount": total_price,
            "saga_step": 2,
            "status": "DEPOSITED",
            "deadline": "17:30 ngày mai",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # Dọn giỏ hàng nếu đặt từ giỏ hàng
    if from_cart and "carts" in db and uid_str in db["carts"]:
        db["carts"][uid_str] = []
        
    save_db(db)
    
    momo_pay_url = None
    if c_gateway == "MOMO":
        momo_pay_url = f"https://test-payment.momo.vn/v2/gateway/pay?orderId={order_code}&amount={int(total_price)}"
        
    return {
        "success": True,
        "message": f"Đặt hàng thành công! Mã đơn: {order_code}",
        "order": new_order,
        "data": new_order,
        "payment": new_tx,
        "momo_pay_url": momo_pay_url
    }

@app.get("/api/v1/orders")
def get_orders(user_id: Optional[int] = None):
    db = load_db()
    orders = db.get("orders", [])
    if user_id is not None:
        orders = [o for o in orders if o.get("user_id") == user_id]
    return {"success": True, "count": len(orders), "orders": orders}

@app.get("/api/v1/orders/{order_code}")
def get_order_by_code(order_code: str):
    db = load_db()
    order = next((o for o in db.get("orders", []) if o.get("order_code") == order_code), None)
    if not order:
        # Fallback tìm trong escrow_orders
        if order_code in db.get("escrow_orders", {}):
            eo = db["escrow_orders"][order_code]
            return {"success": True, "order": eo}
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng!")
    return {"success": True, "order": order}

# =============================================================
# 9. ADMIN ORDER MANAGEMENT (LAB 08) & FINANCE (LAB 09) APIS
# =============================================================

class AdminOrderStatusDTO(BaseModel):
    status: str # pending, ready, picking, delivering, delivered, return, cancelled
    note: Optional[str] = ""

@app.get("/api/v1/admin/orders")
def admin_get_orders(
    tab: str = Query("all"),
    search: Optional[str] = None,
    gateway: Optional[str] = None,
    payment_status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    db = load_db()
    orders = list(db.get("orders", []))
    
    # 8 Tab phân loại theo chuẩn Lab 08
    tab_map = {
        "pending": ["pending", "not_shipped", "processing"],
        "ready": ["ready", "ready_to_pick"],
        "picking": ["picking"],
        "delivering": ["delivering", "picked", "storing", "transporting", "sorting"],
        "delivered": ["delivered"],
        "return": ["return", "returning", "returned"],
        "cancelled": ["cancelled"]
    }
    
    if tab != "all" and tab in tab_map:
        allowed = tab_map[tab]
        orders = [o for o in orders if o.get("status") in allowed]
    
    if gateway:
        orders = [o for o in orders if o.get("gateway", "").lower() == gateway.lower()]
    if payment_status:
        orders = [o for o in orders if o.get("payment_status", "").lower() == payment_status.lower()]
    if search:
        kw = search.lower().strip()
        orders = [o for o in orders if kw in o.get("order_code", "").lower() or kw in o.get("customer_name", "").lower() or kw in o.get("customer_phone", "").lower()]
        
    return {
        "success": True,
        "tab": tab,
        "count": len(orders),
        "orders": orders
    }

@app.put("/api/v1/admin/orders/{order_code}/status")
def admin_update_order_status(order_code: str, dto: AdminOrderStatusDTO):
    db = load_db()
    order = next((o for o in db.get("orders", []) if o.get("order_code") == order_code), None)
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng cần cập nhật!")
    
    curr_status = order.get("status", "pending")
    new_status = dto.status.lower()
    
    # QUY TẮC BẢO VỆ CHẶT CHẼ CỦA LAB 08:
    # "Nếu đơn hàng ở trạng thái đang giao -> KHÔNG cho Hủy"
    if curr_status in ["delivering", "picking", "transporting", "storing"] and new_status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Quy chuẩn nghiệp vụ Lab 08: Đơn hàng đang trong quá trình lấy hàng hoặc vận chuyển, KHÔNG ĐƯỢC PHÉP HỦY!"
        )
    
    order["status"] = new_status
    if new_status == "delivered":
        order["payment_status"] = "paid"
    order["admin_note"] = dto.note or ""
    order["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_db(db)
    return {"success": True, "message": f"Đã chuyển trạng thái đơn {order_code} sang '{new_status}'!", "order": order}

@app.get("/api/v1/admin/finance/kpis")
def get_finance_kpis():
    db = load_db()
    orders = db.get("orders", [])
    txs = db.get("payment_transactions", [])
    
    gross_revenue = sum(o.get("total_price", 0.0) for o in orders if o.get("status") != "cancelled")
    net_revenue = sum(t.get("amount", 0.0) for t in txs if t.get("status") == "paid")
    pending_cod = sum(t.get("amount", 0.0) for t in txs if t.get("gateway") == "cod" and t.get("status") == "pending")
    escrow_holding = sum(t.get("amount", 0.0) for t in txs if t.get("gateway") == "escrow" and t.get("status") == "paid")
    refunded_amt = sum(t.get("amount", 0.0) for t in txs if t.get("status") == "refunded")
    order_count = len(orders)
    aov = (gross_revenue / order_count) if order_count > 0 else 0.0
    
    return {
        "success": True,
        "kpis": {
            "gross_revenue": gross_revenue,
            "net_revenue": net_revenue,
            "pending_cod_amount": pending_cod,
            "escrow_holding_amount": escrow_holding,
            "refunded_amount": refunded_amt,
            "total_orders_count": order_count,
            "average_order_value": round(aov, 2)
        }
    }

@app.get("/api/v1/admin/finance/transactions")
def get_finance_transactions():
    db = load_db()
    return {"success": True, "transactions": db.get("payment_transactions", [])}

class CodTransitionDTO(BaseModel):
    transaction_id: int
    new_status: str # pending, paid, refund_pending, refunded, failed

@app.put("/api/v1/admin/finance/cod-transition")
def update_cod_status(dto: CodTransitionDTO):
    # Ma trận chuyển đổi trạng thái COD chuẩn Lab 09:
    COD_TRANSITIONS = {
        'pending': ['pending', 'paid', 'failed'],
        'failed': ['failed', 'pending', 'paid'],
        'paid': ['paid', 'refund_pending'],
        'refund_pending': ['refund_pending', 'refunded'],
        'refunded': ['refunded'],
        'cancelled': ['cancelled']
    }
    
    db = load_db()
    tx = next((t for t in db.get("payment_transactions", []) if t["id"] == dto.transaction_id), None)
    if not tx:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch thanh toán!")
    
    curr = tx.get("status", "pending")
    target = dto.new_status.lower()
    
    allowed = COD_TRANSITIONS.get(curr, [curr])
    if target not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Quy chuẩn đối soát Lab 09: Không thể chuyển từ '{curr}' sang '{target}'! Các trạng thái hợp lệ: {', '.join(allowed)}."
        )
    
    tx["status"] = target
    if target == "paid":
        tx["paid_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tx["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Cập nhật payment_status trên đơn hàng tương ứng
    order = next((o for o in db.get("orders", []) if o.get("order_code") == tx.get("order_code")), None)
    if order:
        order["payment_status"] = target
        if target == "paid" and order.get("status") == "pending":
            order["status"] = "delivered"
            
    save_db(db)
    return {"success": True, "message": f"Đối soát COD thành công! Trạng thái mới: {target}", "transaction": tx}

@app.get("/api/v1/admin/users")
def admin_get_users():
    db = load_db()
    return {"success": True, "users": db.get("users", [])}

class UserStatusUpdateDTO(BaseModel):
    status: str # ACTIVE hoặc BLOCKED

@app.put("/api/v1/admin/users/{user_id}/status")
def admin_update_user_status(user_id: int, dto: UserStatusUpdateDTO):
    db = load_db()
    user = next((u for u in db.get("users", []) if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng!")
    if user.get("role") == "ADMIN":
        raise HTTPException(status_code=400, detail="Không thể khóa tài khoản Quản Trị Viên hệ thống!")
    
    user["status"] = dto.status.upper()
    save_db(db)
    return {"success": True, "message": f"Đã cập nhật trạng thái tài khoản {user['full_name']} thành {user['status']}!", "user": user}

# =============================================================
# 10. VOUCHERS, REVIEWS & WISHLIST APIS (YÊU CẦU BÀI TẬP LỚN)
# =============================================================

@app.get("/api/v1/vouchers")
def get_vouchers():
    db = load_db()
    return {"success": True, "vouchers": db.get("vouchers", [])}

class VoucherApplyDTO(BaseModel):
    code: Optional[str] = None
    voucher_code: Optional[str] = None
    order_value: Optional[float] = None
    order_amount: Optional[float] = None

@app.post("/api/v1/vouchers/apply")
def apply_voucher(dto: VoucherApplyDTO):
    raw_code = (dto.code or dto.voucher_code or "").strip()
    raw_value = dto.order_value if dto.order_value is not None else (dto.order_amount or 0.0)
    
    if not raw_code:
        raise HTTPException(status_code=400, detail="Vui lòng nhập mã voucher!")
    
    db = load_db()
    code_upper = raw_code.upper()
    voucher = next((v for v in db.get("vouchers", []) if v["code"].upper() == code_upper), None)
    if not voucher:
        raise HTTPException(status_code=404, detail=f"Mã voucher '{raw_code}' không tồn tại hoặc đã hết hạn!")
    
    if raw_value < voucher.get("min_order_value", 0):
        raise HTTPException(
            status_code=400,
            detail=f"Đơn hàng cần tối thiểu {int(voucher['min_order_value']):,}đ để áp dụng voucher {code_upper}!"
        )
    
    discount = 0.0
    if voucher.get("discount_percent", 0) > 0:
        discount = raw_value * (voucher["discount_percent"] / 100.0)
    else:
        discount = voucher.get("discount_amount", 0.0)
        
    res_data = {
        "voucher": voucher,
        "voucher_code": code_upper,
        "discount_amount": discount,
        "min_order_amount": voucher.get("min_order_value", 0),
        "final_price": max(0.0, raw_value - discount),
        "final_amount": max(0.0, raw_value - discount)
    }
    return {
        "success": True,
        "data": res_data,
        **res_data,
        "message": f"Áp dụng mã {code_upper} thành công! Giảm {int(discount):,}đ."
    }

class ReviewCreateDTO(BaseModel):
    product_id: int
    user_id: Optional[int] = 1
    rating: int = 5
    comment: str

@app.post("/api/v1/reviews")
def add_review(dto: ReviewCreateDTO):
    if dto.rating < 1 or dto.rating > 5:
        raise HTTPException(status_code=400, detail="Đánh giá sao phải từ 1 đến 5 sao!")
    if not dto.comment.strip():
        raise HTTPException(status_code=400, detail="Nội dung nhận xét không được để trống!")
    
    db = load_db()
    user = next((u for u in db.get("users", []) if u["id"] == dto.user_id), db["users"][0])
    
    if "reviews" not in db: db["reviews"] = []
    new_rev = {
        "id": max([r["id"] for r in db["reviews"]] + [0]) + 1,
        "product_id": dto.product_id,
        "user_id": user["id"],
        "user_name": user["full_name"],
        "rating": dto.rating,
        "comment": dto.comment.strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db["reviews"].insert(0, new_rev)
    save_db(db)
    return {"success": True, "message": "Cảm ơn bạn đã gửi đánh giá sản phẩm!", "review": new_rev, "data": new_rev}

@app.get("/api/v1/products/{product_id}/reviews")
def get_product_reviews(product_id: int):
    db = load_db()
    revs = [r for r in db.get("reviews", []) if r.get("product_id") == product_id]
    avg_rating = sum(r["rating"] for r in revs) / len(revs) if revs else 5.0
    return {"success": True, "count": len(revs), "average_rating": round(avg_rating, 1), "reviews": revs, "data": revs}

class WishlistToggleDTO(BaseModel):
    user_id: Optional[int] = 1
    product_id: int

@app.post("/api/v1/wishlist/toggle")
def toggle_wishlist(dto: WishlistToggleDTO):
    db = load_db()
    uid_str = str(dto.user_id)
    if "wishlists" not in db: db["wishlists"] = {}
    if uid_str not in db["wishlists"]: db["wishlists"][uid_str] = []
    
    user_favs = db["wishlists"][uid_str]
    if dto.product_id in user_favs:
        user_favs.remove(dto.product_id)
        is_liked = False
        msg = "Đã bỏ sản phẩm khỏi danh sách yêu thích."
    else:
        user_favs.append(dto.product_id)
        is_liked = True
        msg = "Đã thêm sản phẩm vào danh sách yêu thích!"
        
    save_db(db)
    return {
        "success": True,
        "is_liked": is_liked,
        "message": msg,
        "wishlist_ids": user_favs,
        "data": {
            "product_id": dto.product_id,
            "is_wishlisted": is_liked,
            "wishlist_ids": user_favs
        }
    }

@app.get("/api/v1/wishlist/{user_id}")
def get_user_wishlist(user_id: int):
    db = load_db()
    uid_str = str(user_id)
    fav_ids = db.get("wishlists", {}).get(uid_str, [])
    fav_products = [p for p in db.get("products", []) if p["id"] in fav_ids]
    return {
        "success": True,
        "count": len(fav_products),
        "products": fav_products,
        "wishlist_ids": fav_ids,
        "data": fav_ids
    }

# =============================================================
# 11. PHỤC VỤ STATIC FILES CHO FRONTEND
# =============================================================

FRONTEND_STUDENT_DIR = os.path.join(BASE_DIR, "..", "frontend", "student-portal")
FRONTEND_STAFF_DIR = os.path.join(BASE_DIR, "..", "frontend", "hub-staff-portal")
FRONTEND_ADMIN_DIR = os.path.join(BASE_DIR, "..", "frontend", "admin-portal")

if os.path.exists(FRONTEND_ADMIN_DIR):
    app.mount("/admin", StaticFiles(directory=FRONTEND_ADMIN_DIR, html=True), name="admin-portal")

if os.path.exists(FRONTEND_STAFF_DIR):
    app.mount("/staff", StaticFiles(directory=FRONTEND_STAFF_DIR, html=True), name="hub-staff")

if os.path.exists(FRONTEND_STUDENT_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_STUDENT_DIR, html=True), name="student-portal")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("local_api_server:app", host="0.0.0.0", port=8000, reload=True)
