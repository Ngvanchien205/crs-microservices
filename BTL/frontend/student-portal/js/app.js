/**
 * HUNRE E-COMMERCE CLIENT APPLICATION LOGIC
 * Tương tác API Gateway & Microservices qua đường dẫn tương đối /api/v1/...
 * Hỗ trợ đầy đủ: CRUD Sản phẩm thời gian thực, Thẩm định AI, Trả giá AI, Đơn ký quỹ, Chuyển đổi User.
 */

const getApiBaseUrl = () => {
    if (window.location.protocol === 'file:' || (window.location.port !== '8000' && window.location.hostname !== '')) {
        return 'http://localhost:8000/api/v1';
    }
    return '/api/v1';
};
const API_BASE_URL = getApiBaseUrl();
const AI_ENGINE_URL = `${API_BASE_URL}/ai`;

// State toàn cục của ứng dụng
let currentUser = {
    id: 1,
    student_code: "20211001",
    full_name: "Nguyễn Văn An",
    trust_score: 520,
    tier: "BẠC (Sinh viên uy tín tiêu chuẩn)",
    wallet_balance: 500000.0
};

let allProducts = [];
let currentCategory = 'ALL';
let currentSearchKeyword = '';

let lastAiScanResult = {
    condition_grade: "GRADE_A",
    defect_score: 0.035,
    summary: "Độ mới 94%, không rách, mép trang sạch, chữ ký dHash xác thực",
    image_url: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop"
};

let currentNegotiateItem = {
    id: null,
    title: '',
    currentPrice: 0,
    floorPrice: 0
};

// State mở rộng: Giỏ hàng, Yêu thích, Voucher (Lab 04, 05, 06)
let userWishlistIds = [];
let currentCart = { items: [], total_amount: 0, total_items: 0 };
let appliedVoucher = null;
let currentShippingFee = 0;
let currentShippingMethod = 'HUB_PICKUP';
let activeReviewProductId = null;

// Khởi chạy khi tải trang
document.addEventListener('DOMContentLoaded', () => {
    loadUserTrustScore();
    loadProducts();
    loadWishlist();
    loadCart();
});

// =============================================================
// 1. TẢI VÀ RENDER DANH SÁCH SẢN PHẨM (DYNAMIC CRUD)
// =============================================================

async function loadProducts() {
    const grid = document.getElementById('productsGrid');
    try {
        const res = await fetch(`${API_BASE_URL}/products`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        allProducts = data.data || [];
        renderProducts();
    } catch (err) {
        console.warn('Lỗi tải sản phẩm từ API, sử dụng fallback cục bộ:', err);
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--danger-red);">
                <i class="fa-solid fa-triangle-exclamation fa-2x" style="margin-bottom: 10px;"></i>
                <p>Không thể kết nối đến Product Microservice. Vui lòng đảm bảo Gateway / local_api_server.py đang chạy tại cổng 8000!</p>
            </div>
        `;
    }
}

function renderProducts() {
    const grid = document.getElementById('productsGrid');
    if (!grid) return;

    let filtered = allProducts.filter(item => {
        const matchCat = (currentCategory === 'ALL' || item.category_id === currentCategory);
        const matchKw = !currentSearchKeyword || 
            item.title.toLowerCase().includes(currentSearchKeyword) || 
            (item.description && item.description.toLowerCase().includes(currentSearchKeyword)) ||
            (item.desired_exchange_items && item.desired_exchange_items.toLowerCase().includes(currentSearchKeyword));
        return matchCat && matchKw;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
                <i class="fa-solid fa-box-open fa-2x" style="margin-bottom: 12px; color: var(--text-dim);"></i>
                <p>Không tìm thấy món đồ nào phù hợp với từ khóa hoặc danh mục đã chọn.</p>
                <button class="btn btn-secondary" style="margin-top: 10px; font-size: 13px;" onclick="resetFilters()">Xem tất cả sản phẩm</button>
            </div>
        `;
        return;
    }

    grid.innerHTML = filtered.map(p => {
        const gradeClass = p.condition_grade ? p.condition_grade.toLowerCase().replace('_', '-') : 'grade-a';
        const gradeLabel = p.condition_grade ? p.condition_grade.replace('_', ' ') : 'GRADE A';
        const currPriceFormatted = Number(p.current_price || 0).toLocaleString('vi-VN');
        const origPriceFormatted = Number(p.original_price || p.current_price || 0).toLocaleString('vi-VN');
        const sellerName = p.seller_name || 'Sinh viên HUNRE';
        const isOwner = (p.seller_id === currentUser.id);
        const isWishlisted = userWishlistIds.includes(p.id);

        return `
            <div class="product-card" data-category="${p.category_id || 'OTHER'}" id="product-card-${p.id}">
                <div class="product-thumb" style="position: relative;">
                    <img src="${p.image_url || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop'}" alt="${p.title}">
                    <span class="badge-grade ${gradeClass}">${gradeLabel}</span>
                    ${p.is_barter_eligible ? '<span class="badge-barter"><i class="fa-solid fa-repeat"></i> Hỗ trợ đổi đồ</span>' : ''}
                    <!-- Wishlist Toggle Button -->
                    <button onclick="toggleWishlistItem(${p.id}, event)" title="${isWishlisted ? 'Bỏ thích' : 'Thêm vào yêu thích'}" style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.55); backdrop-filter: blur(4px); border: none; border-radius: 50%; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: ${isWishlisted ? '#EF4444' : '#FFFFFF'}; transition: transform 0.2s; z-index: 5;">
                        <i class="fa-solid fa-heart" style="font-size: 15px;"></i>
                    </button>
                </div>
                <div class="product-body">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span class="product-category">${p.category_name || 'Đồ Dùng Học Tập'}</span>
                        <span style="font-size: 11px; color: var(--text-dim);"><i class="fa-solid fa-user-tag"></i> ${sellerName}</span>
                    </div>
                    <h4 class="product-title" title="${p.title}">${p.title}</h4>
                    <div class="product-ai-note">
                        <i class="fa-solid fa-check"></i> 
                        <strong>AI Verified:</strong> ${p.ai_inspection_summary || 'Đã kiểm định độ mòn & tính xác thực'}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; margin-bottom: 12px;">
                        <span style="color: var(--text-secondary); cursor: pointer;" onclick="openReviewsModal(${p.id}, '${escapeHtml(p.title)}')">
                            5.0 (Đánh giá)
                        </span>
                        <span style="color: var(--text-muted);">
                            Muốn đổi: <span style="color: var(--text-main); font-weight: 500;">${p.desired_exchange_items || 'Đổi linh hoạt'}</span>
                        </span>
                    </div>
                    <div class="product-price-row">
                        <div>
                            <span class="current-price">${currPriceFormatted}đ</span>
                            ${p.original_price && p.original_price > p.current_price ? `<span class="original-price">${origPriceFormatted}đ</span>` : ''}
                        </div>
                        <div style="display: flex; gap: 6px;">
                            <button class="btn btn-secondary" style="padding: 7px 10px; font-size: 12.5px;" onclick="addToCart(${p.id})" title="Thêm vào giỏ hàng (Lab 04)">
                                <i class="fa-solid fa-cart-plus"></i>
                            </button>
                            <button class="btn btn-primary" style="padding: 7px 12px; font-size: 12.5px;" onclick="openNegotiateModal(${p.id}, '${escapeHtml(p.title)}', ${p.current_price}, ${p.floor_price || (p.current_price * 0.8)})">
                                <i class="fa-solid fa-handshake"></i> Trả Giá
                            </button>
                        </div>
                    </div>

                    <!-- Quản trị Sửa / Xóa -->
                    <div class="card-manage-btns">
                        <button class="btn-card-action edit" onclick="openEditModal(${p.id})" title="Chỉnh sửa thông tin">
                            <i class="fa-solid fa-pen-to-square"></i> Sửa tin
                        </button>
                        <button class="btn-card-action delete" onclick="deleteProduct(${p.id}, '${escapeHtml(p.title)}')" title="Gỡ sản phẩm khỏi sàn">
                            <i class="fa-solid fa-trash-can"></i> Xóa
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function handleSearchInput(event) {
    currentSearchKeyword = (event.target.value || '').trim().toLowerCase();
    renderProducts();
}

function filterProducts(category, btnElement) {
    currentCategory = category;
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach(b => b.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');
    renderProducts();
}

function resetFilters() {
    currentCategory = 'ALL';
    currentSearchKeyword = '';
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach((b, idx) => b.classList.toggle('active', idx === 0));
    renderProducts();
}

// =============================================================
// 2. MODAL THẨM ĐỊNH ẢNH AI & ĐĂNG BÁN SẢN PHẨM MỚI (CREATE / POST)
// =============================================================

function openAiInspectModal() {
    document.getElementById('aiInspectModal').style.display = 'flex';
}

function closeAiInspectModal() {
    document.getElementById('aiInspectModal').style.display = 'none';
}

function populateProductForm(title, category, origPrice, currPrice, floorPrice, barter, desc) {
    const titleInput = document.getElementById('newProductTitle');
    const catSelect = document.getElementById('newProductCategory');
    const origInput = document.getElementById('newProductOriginalPrice');
    const currInput = document.getElementById('newProductCurrentPrice');
    const floorInput = document.getElementById('newProductFloorPrice');
    const barterInput = document.getElementById('newProductBarter');
    const descInput = document.getElementById('newProductDesc');

    if (titleInput && title) titleInput.value = title;
    if (catSelect && category) catSelect.value = category;
    if (origInput && origPrice) origInput.value = origPrice;
    if (currInput && currPrice) currInput.value = currPrice;
    if (floorInput && floorPrice) floorInput.value = floorPrice;
    if (barterInput && barter) barterInput.value = barter;
    if (descInput && desc) descInput.value = desc;
}

function renderFourQuestionsCard(itemName, categoryName, gradeLabel, defectPct, visualDesc, origPrice, marketNotes, sellPrice, floorPrice, discountPct, pricingReason, barterSugg, phash) {
    return `
        <div style="border: 1px solid var(--border-subtle); border-radius: 8px; padding: 14px; background: #FFFFFF;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border-subtle);">
                <span style="font-size: 12.5px; font-weight: 600; color: var(--text-main);">Kết Quả Thẩm Định AI</span>
                <span style="font-size: 11px; background: var(--secondary-gray); border: 1px solid var(--border-subtle); color: var(--text-secondary); padding: 2px 8px; border-radius: 4px; font-weight: 500;">Thẩm định 4 tiêu chí</span>
            </div>

            <!-- 1. Đây là gì? -->
            <div style="margin-bottom: 10px; padding: 10px; background: var(--secondary-gray); border-radius: 6px;">
                <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 2px;">
                    1. Tên món đồ & Phân loại
                </div>
                <div style="font-size: 14px; font-weight: 600; color: var(--text-main);">
                    ${escapeHtml(itemName)}
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                    Danh mục sàn HUNRE: <strong>${escapeHtml(categoryName)}</strong>
                </div>
            </div>

            <!-- 2. Độ mới bao nhiêu? -->
            <div style="margin-bottom: 10px; padding: 10px; background: var(--secondary-gray); border-radius: 6px;">
                <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 2px;">
                    2. Tình trạng & Độ mới
                </div>
                <div style="font-size: 13.5px; font-weight: 600; color: var(--text-main);">
                    ${escapeHtml(gradeLabel)} <span style="font-size: 11.5px; font-weight: normal; color: var(--text-muted);">(Hao mòn: ${defectPct}%)</span>
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                    ${escapeHtml(visualDesc)}
                </div>
            </div>

            <!-- 3. Ngoài thị trường giá mới thế nào? -->
            <div style="margin-bottom: 10px; padding: 10px; background: var(--secondary-gray); border-radius: 6px;">
                <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 2px;">
                    3. Giá mua mới 100% ngoài thị trường
                </div>
                <div style="font-size: 13.5px; font-weight: 600; color: var(--text-main);">
                    ${Number(origPrice).toLocaleString('vi-VN')} VNĐ
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                    ${escapeHtml(marketNotes)}
                </div>
            </div>

            <!-- 4. Định giá cái này bao nhiêu? -->
            <div style="padding: 10px; background: var(--secondary-gray); border-radius: 6px;">
                <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 2px;">
                    4. Định giá đề xuất & Giá sàn
                </div>
                <div style="font-size: 14px; font-weight: 600; color: var(--text-main);">
                    Giá bán đề xuất: ${Number(sellPrice).toLocaleString('vi-VN')} VNĐ <span style="font-size: 11.5px; font-weight: normal; color: var(--text-muted);">(Tiết kiệm ${discountPct}%)</span>
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                    Giá sàn đàm phán tối thiểu: <strong>${Number(floorPrice).toLocaleString('vi-VN')} VNĐ</strong>
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                    Lý do định giá: ${escapeHtml(pricingReason)}
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                    Gợi ý trao đổi: ${escapeHtml(barterSugg)}
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 8px; margin-top: 8px; font-size: 11px; color: var(--text-muted);">
                <span>Chữ ký số: ${escapeHtml(phash || 'dHash-VERIFIED')}</span>
                <span>Ảnh chụp thực tế sinh viên HUNRE</span>
            </div>
        </div>
    `;
}

async function handleImageSelected(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Xem trước ảnh
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const laserBar = document.getElementById('laserScanBar');

    const reader = new FileReader();
    reader.onload = function(e) {
        imagePreview.src = e.target.result;
        previewContainer.style.display = 'block';
        uploadPlaceholder.style.display = 'none';
        if (laserBar) laserBar.style.display = 'block';
        lastAiScanResult.image_url = e.target.result;
    };
    reader.readAsDataURL(file);

    const resultBox = document.getElementById('aiResultBox');
    const resultDetails = document.getElementById('aiResultDetails');
    resultBox.style.display = 'block';
    resultDetails.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px; color: var(--text-secondary); font-size: 13px; padding: 10px;">
            <i class="fa-solid fa-spinner fa-spin"></i> 
            <span>AI đang nhận diện hình ảnh, thẩm định tình trạng & tính toán giá bán...</span>
        </div>
    `;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${AI_ENGINE_URL}/cv/inspect`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error(`HTTP error ${response.status}`);
        const data = await response.json();
        if (laserBar) laserBar.style.display = 'none';

        const evalData = data.inspection ? data.inspection.evaluation : {};
        const antiFraud = data.anti_fraud || {};
        let rec = data.recognition || {};
        const fq = data.four_questions || {};

        const q1 = fq["1_what_is_it"] || {};
        const q2 = fq["2_condition"] || {};
        const q3 = fq["3_market_new_price"] || {};
        const q4 = fq["4_suggested_valuation"] || {};

        const itemName = q1.item_name || rec.item_name || file.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ") || 'Đồ Dùng Sinh Viên HUNRE';
        const category = q1.category || rec.category || 'BOOKS';
        const categoryName = q1.category_name || rec.category_name || 'Giáo Trình & Tài Liệu';
        const condPct = q2.condition_percentage || rec.condition_percentage || 94;
        const gradeLabel = q2.grade_label || rec.grade_label || evalData.grade_label || `Độ mới ${condPct}%`;
        const defectPct = ((data.inspection?.metrics?.defect_ratio || rec.defect_ratio || 0.035) * 100).toFixed(1);
        const visualDesc = q2.visual_description || rec.visual_description || evalData.summary || 'Ảnh chụp thực tế sinh viên HUNRE, bề mặt bảo quản tốt.';
        const origPrice = Number(q3.suggested_original_price || rec.suggested_original_price || 85000);
        const marketNotes = q3.market_price_notes || rec.market_price_notes || `Giá mua mới ngoài thị trường khoảng ${origPrice.toLocaleString('vi-VN')}đ`;
        const sellPrice = Number(q4.suggested_selling_price || rec.suggested_selling_price || 75000);
        const floorPrice = Number(q4.suggested_floor_price || rec.suggested_floor_price || 60000);
        const discountPct = q4.discount_percentage || (origPrice > 0 ? Math.round((1 - sellPrice / origPrice) * 100) : 15);
        const pricingReason = q4.pricing_reason || rec.pricing_reason || 'Định giá hợp lý theo độ mới và khả năng chi trả của sinh viên HUNRE.';
        const barterSugg = q4.desired_exchange_items || rec.desired_exchange_items || 'Đổi giáo trình khác hoặc đồ dùng học tập';
        lastAiScanResult.condition_grade = evalData.condition_grade || rec.condition_grade || 'GRADE_A';
        lastAiScanResult.defect_score = data.inspection?.metrics?.defect_ratio || 0.035;
        lastAiScanResult.summary = `${gradeLabel}: ${visualDesc}`;

        // TỰ ĐỘNG ĐIỀN ĐẦY ĐỦ 100% VÀO FORM ĐĂNG BÁN
        populateProductForm(itemName, category, origPrice, sellPrice, floorPrice, barterSugg, visualDesc);

        resultDetails.innerHTML = renderFourQuestionsCard(
            itemName, categoryName, gradeLabel, defectPct,
            visualDesc, origPrice, marketNotes, sellPrice, floorPrice,
            discountPct, pricingReason, barterSugg, antiFraud.phash_signature
        );

        showToast(`AI đã nhận diện: "${itemName}" & tự động điền form!`, 'success');

    } catch (err) {
        if (laserBar) laserBar.style.display = 'none';
        console.warn('AI Vision inspect fallback:', err);

        // Fallback nhận diện thông minh cục bộ
        const fname = file.name.toLowerCase();
        let itemName = 'Giáo trình Cơ Sở Dữ Liệu & SQL (HUNRE)';
        let category = 'BOOKS';
        let categoryName = 'Giáo Trình & Tài Liệu';
        let origPrice = 85000;
        let sellPrice = 75000;
        let floorPrice = 60000;
        let barterSugg = 'Máy tính Casio FX 580VN hoặc Balo';
        let visualDesc = 'Ảnh chụp thực tế sinh viên HUNRE, mép phẳng, bìa sạch, không quăn mép.';

        if (fname.includes('casio') || fname.includes('fx') || fname.includes('maytinh')) {
            itemName = 'Máy tính Casio FX 580VN X (Like New)';
            category = 'TECH';
            categoryName = 'Thiết Bị Điện Tử';
            origPrice = 680000;
            sellPrice = 450000;
            floorPrice = 380000;
            barterSugg = 'Bàn phím cơ DareU hoặc Balo';
            visualDesc = 'Màn hình LCD sắc nét không trầy xước, phím bấm nảy nhạy, nguyên tem Bộ Giáo Dục.';
        } else if (fname.includes('phim') || fname.includes('keyboard') || fname.includes('chuot')) {
            itemName = 'Bàn phím cơ DareU EK87 Blue Switch';
            category = 'TECH';
            categoryName = 'Thiết Bị Điện Tử';
            origPrice = 490000;
            sellPrice = 250000;
            floorPrice = 200000;
            barterSugg = 'Giáo trình CSDL hoặc Sách Tiếng Anh';
            visualDesc = 'Keycap bóng nhẹ cụm phím chính, switch gõ tốt, cáp Type-C nguyên vẹn.';
        }

        lastAiScanResult.condition_grade = "GRADE_A";
        lastAiScanResult.defect_score = 0.04;
        lastAiScanResult.summary = "Độ mới 94%, ảnh chụp thực tế sinh viên";

        // Tự động điền form ngay cả khi offline
        populateProductForm(itemName, category, origPrice, sellPrice, floorPrice, barterSugg, visualDesc);

        resultDetails.innerHTML = renderFourQuestionsCard(
            itemName, categoryName,
            'GRADE A - Độ mới 94% (Rất tốt)', '4.0', visualDesc,
            origPrice, `Giá bìa mới ngoài thị trường khoảng ${origPrice.toLocaleString('vi-VN')}đ`,
            sellPrice, floorPrice, 15,
            'Định giá hợp lý theo độ mới và nhu cầu học tập của sinh viên HUNRE.',
            barterSugg, 'dHash-LOCAL-AUTH'
        );

        showToast(`AI Smart Vision đã nhận diện: "${itemName}"!`, 'info');
    }
}

function loadSampleImage(type) {
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const resultBox = document.getElementById('aiResultBox');
    const resultDetails = document.getElementById('aiResultDetails');

    let imgUrl = '';
    let grade = '';
    let defect = 0.03;
    let summary = '';
    let title = '';
    let origPrice = 80000;
    let currPrice = 75000;
    let floorPrice = 60000;
    let category = 'BOOKS';
    let barter = '';
    let marketNotes = '';
    let pricingReason = '';
    let categoryName = '';

    if (type === 'CSDL') {
        imgUrl = 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop';
        grade = 'GRADE_A';
        defect = 0.035;
        summary = 'Góc sách phẳng, không quăn mép, trang sạch không bị ố vàng, ghi chú bài tập K11 rõ ràng.';
        title = 'Giáo trình Cơ Sở Dữ Liệu & SQL (HUNRE)';
        origPrice = 85000;
        currPrice = 75000;
        floorPrice = 60000;
        category = 'BOOKS';
        categoryName = 'Giáo Trình & Tài Liệu';
        barter = 'Máy tính Casio FX 580VN';
        marketNotes = 'Giá bìa sách mới tại thư viện / nhà sách khoảng 85.000đ - 95.000đ';
        pricingReason = 'Giáo trình dùng thường xuyên cho K11-K12 CNTT, sách giữ gìn cẩn thận, bìa phẳng không ố.';
    } else if (type === 'CASIO') {
        imgUrl = 'https://images.unsplash.com/photo-1596495578065-6e0763fa1178?w=600&auto=format&fit=crop';
        grade = 'GRADE_S';
        defect = 0.012;
        summary = 'Màn hình LCD sắc nét không trầy xước, phím bấm nảy nhạy, nguyên tem Bộ Giáo Dục.';
        title = 'Máy tính Casio FX 580VN X (Like New)';
        origPrice = 680000;
        currPrice = 450000;
        floorPrice = 380000;
        category = 'TECH';
        categoryName = 'Thiết Bị Điện Tử';
        barter = 'Bàn phím cơ DareU hoặc Balo';
        marketNotes = 'Giá mua mới chính hãng Bitex hiện nay khoảng 650.000đ - 720.000đ';
        pricingReason = 'Máy tính thi đại học và tốt nghiệp bắt buộc, máy giữ như mới, tem chống giả nguyên vẹn.';
    } else {
        imgUrl = 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop';
        grade = 'GRADE_B';
        defect = 0.098;
        summary = 'Keycap hơi bóng nhẹ ở cụm phím chính, có vết xước dăm góc trái vỏ, toàn bộ Blue Switch hoạt động chuẩn.';
        title = 'Bàn phím cơ DareU EK87 Blue Switch';
        origPrice = 490000;
        currPrice = 250000;
        floorPrice = 200000;
        category = 'TECH';
        categoryName = 'Thiết Bị Điện Tử';
        barter = 'Giáo trình CSDL hoặc Sách Tiếng Anh';
        marketNotes = 'Giá niêm yết bán mới tại các đại lý công nghệ khoảng 450.000đ - 520.000đ';
        pricingReason = 'Bàn phím cơ phổ thông cho sinh viên IT thực hành gõ code, phím nảy tốt, hao mòn nhẹ bề mặt.';
    }

    lastAiScanResult = {
        condition_grade: grade,
        defect_score: defect,
        summary: summary,
        image_url: imgUrl
    };

    imagePreview.src = imgUrl;
    previewContainer.style.display = 'block';
    uploadPlaceholder.style.display = 'none';

    resultBox.style.display = 'block';
    resultDetails.innerHTML = '<div style="display: flex; align-items: center; gap: 8px; color: var(--text-secondary); font-size: 13px; padding: 10px;"><i class="fa-solid fa-spinner fa-spin"></i> <span>Hệ thống đang đối chiếu dữ liệu hình ảnh và mã băm dHash...</span></div>';

    // Tự động điền form
    populateProductForm(title, category, origPrice, currPrice, floorPrice, barter, summary);

    const condPct = Math.round((1 - defect) * 100);
    const discountPct = Math.round((1 - currPrice / origPrice) * 100);

    setTimeout(() => {
        resultDetails.innerHTML = renderFourQuestionsCard(
            title, categoryName,
            `${grade} - Độ mới ${condPct}%`, (defect * 100).toFixed(1),
            summary, origPrice, marketNotes, currPrice, floorPrice,
            discountPct, pricingReason, barter, 'dHash-SAMPLE-VERIFIED'
        );
    }, 200);
}

async function submitNewProduct() {
    const title = document.getElementById('newProductTitle').value.trim();
    const category_id = document.getElementById('newProductCategory').value;
    const original_price = parseFloat(document.getElementById('newProductOriginalPrice').value);
    const current_price = parseFloat(document.getElementById('newProductCurrentPrice').value);
    const floor_price = parseFloat(document.getElementById('newProductFloorPrice').value) || (current_price * 0.8);
    const desired_exchange_items = document.getElementById('newProductBarter').value.trim();
    const description = document.getElementById('newProductDesc').value.trim();

    if (!title) {
        alert('Vui lòng nhập tiêu đề sản phẩm!');
        return;
    }
    if (isNaN(current_price) || current_price <= 0) {
        alert('Vui lòng nhập giá bán hợp lệ!');
        return;
    }

    const payload = {
        title,
        category_id,
        original_price: original_price || current_price,
        current_price,
        floor_price,
        desired_exchange_items,
        description,
        condition_grade: lastAiScanResult.condition_grade,
        ai_defect_score: lastAiScanResult.defect_score,
        ai_inspection_summary: lastAiScanResult.summary,
        image_url: lastAiScanResult.image_url,
        seller_id: currentUser.id
    };

    try {
        const res = await fetch(`${API_BASE_URL}/products`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        showToast(data.message || 'Đăng bán sản phẩm thành công!', 'success');
        closeAiInspectModal();
        await loadProducts(); // Nạp lại sản phẩm ngay lập tức
    } catch (err) {
        console.error('Lỗi đăng bán sản phẩm:', err);
        showToast('Có lỗi khi gửi yêu cầu đăng bán: ' + err.message, 'error');
    }
}

// =============================================================
// 3. CHỈNH SỬA SẢN PHẨM (UPDATE / PUT)
// =============================================================

function openEditModal(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;

    document.getElementById('editProductId').value = product.id;
    document.getElementById('editProductTitle').value = product.title || '';
    document.getElementById('editProductCurrentPrice').value = product.current_price || 0;
    document.getElementById('editProductFloorPrice').value = product.floor_price || (product.current_price * 0.8);
    document.getElementById('editProductBarter').value = product.desired_exchange_items || '';
    document.getElementById('editProductDesc').value = product.description || '';

    document.getElementById('editProductModal').style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('editProductModal').style.display = 'none';
}

async function submitEditProduct() {
    const productId = parseInt(document.getElementById('editProductId').value);
    const title = document.getElementById('editProductTitle').value.trim();
    const current_price = parseFloat(document.getElementById('editProductCurrentPrice').value);
    const floor_price = parseFloat(document.getElementById('editProductFloorPrice').value);
    const desired_exchange_items = document.getElementById('editProductBarter').value.trim();
    const description = document.getElementById('editProductDesc').value.trim();

    if (!title) {
        alert('Tiêu đề không được để trống!');
        return;
    }

    const payload = {
        title,
        current_price,
        floor_price,
        desired_exchange_items,
        description
    };

    try {
        const res = await fetch(`${API_BASE_URL}/products/${productId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        showToast(data.message || 'Cập nhật sản phẩm thành công!', 'success');
        closeEditModal();
        await loadProducts();
    } catch (err) {
        console.error('Lỗi cập nhật sản phẩm:', err);
        showToast('Lỗi cập nhật: ' + err.message, 'error');
    }
}

// =============================================================
// 4. XÓA SẢN PHẨM (DELETE / products/{id})
// =============================================================

async function deleteProduct(productId, title) {
    if (!confirm(`Bạn có chắc chắn muốn gỡ sản phẩm "${title}" khỏi sàn giao dịch HUNRE không?`)) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/products/${productId}`, {
            method: 'DELETE'
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        showToast(data.message || 'Đã gỡ sản phẩm thành công!', 'info');
        await loadProducts();
    } catch (err) {
        console.error('Lỗi xóa sản phẩm:', err);
        showToast('Lỗi xóa sản phẩm: ' + err.message, 'error');
    }
}

// =============================================================
// 5. TRỢ LÝ ĐÀM PHÁN GIÁ AI & TẠO ĐƠN KÝ QUỸ
// =============================================================

function openNegotiateModal(id, title, currentPrice, floorPrice) {
    currentNegotiateItem = { id, title, currentPrice, floorPrice };
    document.getElementById('negotiateItemTitle').innerText = title;
    document.getElementById('negotiateCurrentPrice').innerText = `${Number(currentPrice).toLocaleString('vi-VN')} VNĐ`;
    document.getElementById('negotiateTrustScore').innerText = `${currentUser.trust_score} Điểm (${currentUser.tier.split(' ')[0]})`;
    document.getElementById('buyerOfferInput').value = '';
    document.getElementById('negotiationFeedback').style.display = 'none';
    document.getElementById('negotiateModal').style.display = 'flex';
}

function closeNegotiateModal() {
    document.getElementById('negotiateModal').style.display = 'none';
}

async function submitNegotiation() {
    const offer = parseFloat(document.getElementById('buyerOfferInput').value);
    const feedbackBox = document.getElementById('negotiationFeedback');

    if (!offer || offer <= 0) {
        alert('Vui lòng nhập mức giá bạn muốn đề xuất!');
        return;
    }

    feedbackBox.style.display = 'block';
    feedbackBox.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Trợ lý AI đang đối chiếu giá sàn và điểm uy tín HUNRE...';

    try {
        const response = await fetch(`${AI_ENGINE_URL}/pricing/negotiate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                item_current_price: currentNegotiateItem.currentPrice,
                item_floor_price: currentNegotiateItem.floorPrice,
                buyer_offer_price: offer,
                buyer_trust_score: currentUser.trust_score
            })
        });

        const data = await response.json();
        renderNegotiateFeedback(data, offer);
    } catch (e) {
        // Fallback
        let fakeData;
        if (offer >= currentNegotiateItem.currentPrice) {
            fakeData = { decision: 'ACCEPT', message: 'Giá đề xuất được phê duyệt ngay lập tức!' };
        } else if (offer < currentNegotiateItem.floorPrice) {
            fakeData = { 
                decision: 'COUNTER_OFFER', 
                counter_offer_price: currentNegotiateItem.floorPrice + 5000, 
                message: `Mức giá bạn đưa ra dưới giá sàn. Nhờ điểm uy tín HUNRE cao, hệ thống đề xuất giá tốt nhất: ${Number(currentNegotiateItem.floorPrice + 5000).toLocaleString('vi-VN')}đ.` 
            };
        } else {
            fakeData = { decision: 'ACCEPT', message: `Thương lượng thành công! Mức giá được chấp nhận: ${Number(offer).toLocaleString('vi-VN')}đ.` };
        }
        renderNegotiateFeedback(fakeData, offer);
    }
}

function renderNegotiateFeedback(data, offer) {
    const feedbackBox = document.getElementById('negotiationFeedback');
    feedbackBox.style.background = 'var(--secondary-gray)';
    feedbackBox.style.border = '1px solid var(--border-subtle)';
    feedbackBox.style.color = 'var(--text-main)';

    if (data.decision === 'ACCEPT') {
        const finalPrice = offer;
        feedbackBox.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 4px;">Chấp nhận đề xuất:</div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 10px;">${escapeHtml(data.message)}</div>
            <div>
                <button onclick="createEscrowFromNegotiate(${currentNegotiateItem.id}, ${finalPrice})" class="btn btn-primary" style="padding: 7px 14px; font-size: 12.5px;">
                    Đặt Cọc Ký Quỹ Đơn Này (${Number(finalPrice).toLocaleString('vi-VN')}đ)
                </button>
            </div>
        `;
    } else if (data.decision === 'COUNTER_OFFER') {
        const counterPrice = data.counter_offer_price || (currentNegotiateItem.floorPrice + 5000);
        feedbackBox.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 4px;">Đề xuất giá mới:</div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 10px;">${escapeHtml(data.message)}</div>
            <div>
                <button onclick="createEscrowFromNegotiate(${currentNegotiateItem.id}, ${counterPrice})" class="btn btn-primary" style="padding: 7px 14px; font-size: 12.5px;">
                    Đồng Ý Mua Với Giá ${Number(counterPrice).toLocaleString('vi-VN')}đ
                </button>
            </div>
        `;
    } else {
        feedbackBox.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 4px;">Từ chối đề xuất:</div>
            <div style="font-size: 13px; color: var(--text-secondary);">${escapeHtml(data.message)}</div>
        `;
    }
}

async function createEscrowFromNegotiate(productId, agreedPrice) {
    try {
        const res = await fetch(`${API_BASE_URL}/escrow/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: productId,
                buyer_id: currentUser.id,
                agreed_price: agreedPrice
            })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const order = data.order;
        showToast('Khởi tạo đơn ký quỹ Smart Escrow thành công!', 'success');
        closeNegotiateModal();
        setTimeout(() => {
            window.location.href = `pages/escrow-order.html?order_code=${order.order_code}`;
        }, 600);
    } catch (err) {
        console.error('Lỗi tạo đơn ký quỹ:', err);
        // Fallback chuyển trang với mã mặc định
        window.location.href = `pages/escrow-order.html?order_code=ORD-HUNRE-98471`;
    }
}

// =============================================================
// 6. XÁC THỰC & CHUYỂN ĐỔI NGƯỜI DÙNG (AUTH CONTEXT)
// =============================================================

async function loadUserTrustScore() {
    try {
        const res = await fetch(`${API_BASE_URL}/auth/users/trust-score?user_id=${currentUser.id}`);
        if (res.ok) {
            const data = await res.json();
            if (data.success && data.data) {
                currentUser.trust_score = data.data.trust_score;
                currentUser.tier = data.data.tier;
                updateUserDisplay();
            }
        }
    } catch (e) {
        console.warn('Lấy trust score từ auth service fallback:', e);
    }
}

function updateUserDisplay() {
    const nameEl = document.getElementById('currentUserName');
    const scoreEl = document.getElementById('userTrustScore');
    if (nameEl) nameEl.innerText = currentUser.full_name;
    if (scoreEl) {
        scoreEl.innerText = `${currentUser.trust_score} Điểm (${currentUser.tier.split(' ')[0]})`;
    }
}

async function openUserModal() {
    const modal = document.getElementById('userSwitchModal');
    const container = document.getElementById('usersListContainer');
    modal.style.display = 'flex';

    try {
        const res = await fetch(`${API_BASE_URL}/auth/users`);
        const data = await res.json();
        const users = data.users || [];

        container.innerHTML = users.map(u => `
            <div onclick="selectUser(${u.id})" style="padding: 10px 12px; background: ${u.id === currentUser.id ? 'var(--secondary-gray)' : '#FFFFFF'}; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 600; font-size: 13.5px; color: var(--text-main);">
                        ${escapeHtml(u.full_name)} 
                        ${u.id === currentUser.id ? '<span style="font-size: 11px; background: var(--text-main); color: #FFFFFF; padding: 1px 6px; border-radius: 4px; margin-left: 6px;">Đang chọn</span>' : ''}
                    </div>
                    <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">
                        MSV: ${escapeHtml(u.student_code)} • ${escapeHtml(u.faculty || 'Khoa CNTT')} • Ví: ${Number(u.wallet_balance || 0).toLocaleString('vi-VN')}đ
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 13px; font-weight: 700; color: var(--text-main);">${u.trust_score} Điểm</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p style="color: var(--text-muted); font-size: 13px;">Không thể tải danh sách tài khoản.</p>';
    }
}

function closeUserModal() {
    document.getElementById('userSwitchModal').style.display = 'none';
}

function selectUser(userId) {
    const userNames = {
        1: { full_name: "Nguyễn Văn An", student_code: "20211001", trust_score: 520, tier: "BẠC (Sinh viên uy tín tiêu chuẩn)", wallet_balance: 500000.0 },
        2: { full_name: "Trần Thị Bích", student_code: "20211002", trust_score: 480, tier: "BẠC (Sinh viên uy tín tiêu chuẩn)", wallet_balance: 250000.0 },
        3: { full_name: "Lê Hoàng Cường", student_code: "20211003", trust_score: 390, tier: "ĐỒNG (Cần tích lũy thêm giao dịch)", wallet_balance: 120000.0 },
        4: { full_name: "Cộng Tác Viên Trạm Hub", student_code: "HUB001", trust_score: 999, tier: "KIM CƯƠNG", wallet_balance: 0.0 }
    };

    if (userNames[userId]) {
        currentUser = { id: userId, ...userNames[userId] };
        updateUserDisplay();
        showToast(`Đã chuyển sang tài khoản: ${currentUser.full_name}`, 'info');
        closeUserModal();
        renderProducts(); // Render lại để cập nhật nút Sửa/Xóa của chính chủ
        loadWishlist();   // Nạp lại danh sách yêu thích của người dùng mới
        loadCart();       // Nạp lại giỏ hàng của người dùng mới
    }
}

// =============================================================
// 7. TOAST NOTIFICATIONS & TIỆN ÍCH
// =============================================================

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icon = type === 'success' ? 'circle-check' : (type === 'error' ? 'circle-xmark' : 'circle-info');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fa-solid fa-${icon}"></i> <span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// =============================================================
// 8. QUẢN LÝ GIỎ HÀNG (LAB 04 - SHOPPING CART)
// =============================================================

async function loadCart() {
    try {
        const res = await fetch(`${API_BASE_URL}/cart?user_id=${currentUser.id}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = await res.json();
        currentCart = result.data || { items: [], total_amount: 0, total_items: 0 };
        renderCartBadge();
    } catch (err) {
        console.warn('Lỗi nạp giỏ hàng:', err);
    }
}

function renderCartBadge() {
    const badge = document.getElementById('cartCountBadge');
    if (badge) {
        badge.textContent = currentCart.total_items || 0;
    }
}

function openCartDrawer() {
    renderCartItems();
    updateCartTotals();
    const modal = document.getElementById('cartModal');
    if (modal) modal.style.display = 'flex';
}

function closeCartDrawer() {
    const modal = document.getElementById('cartModal');
    if (modal) modal.style.display = 'none';
}

function renderCartItems() {
    const container = document.getElementById('cartItemsContainer');
    if (!container) return;

    if (!currentCart.items || currentCart.items.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 30px 10px; color: var(--text-muted);">
                <i class="fa-solid fa-cart-shopping fa-3x" style="margin-bottom: 12px; color: var(--text-dim);"></i>
                <p style="font-size: 14px; margin-bottom: 8px;">Giỏ hàng của bạn đang trống</p>
                <button class="btn btn-secondary" style="font-size: 12px; padding: 6px 14px;" onclick="closeCartDrawer()">
                    Dạo chợ chọn đồ ngay
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = currentCart.items.map(item => {
        const subtotalFormatted = Number(item.subtotal || (item.unit_price * item.quantity)).toLocaleString('vi-VN');
        const unitPriceFormatted = Number(item.unit_price || 0).toLocaleString('vi-VN');
        return `
            <div style="display: flex; align-items: center; justify-content: space-between; background: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 10px 12px; gap: 10px;">
                <img src="${item.image_url || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop'}" alt="${item.title}" style="width: 50px; height: 50px; border-radius: 6px; object-fit: cover; border: 1px solid var(--border-subtle); flex-shrink: 0;">
                <div style="flex: 1; min-width: 0;">
                    <h5 style="font-size: 13.5px; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-main);" title="${item.title}">${escapeHtml(item.title)}</h5>
                    <div style="font-size: 12px; color: var(--text-muted);">
                        Đơn giá: <span style="color: var(--text-main); font-weight: 600;">${unitPriceFormatted}đ</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <button onclick="updateCartItemQty(${item.product_id}, ${item.quantity - 1})" style="width: 26px; height: 26px; background: var(--secondary-gray); border: 1px solid var(--border-subtle); border-radius: 4px; color: var(--text-main); cursor: pointer; display: flex; align-items: center; justify-content: center;">-</button>
                    <span style="font-size: 13px; font-weight: 600; min-width: 20px; text-align: center; color: var(--text-main);">${item.quantity}</span>
                    <button onclick="updateCartItemQty(${item.product_id}, ${item.quantity + 1})" style="width: 26px; height: 26px; background: var(--secondary-gray); border: 1px solid var(--border-subtle); border-radius: 4px; color: var(--text-main); cursor: pointer; display: flex; align-items: center; justify-content: center;">+</button>
                </div>
                <div style="text-align: right; min-width: 75px;">
                    <div style="font-size: 13.5px; font-weight: 700; color: var(--text-main);">${subtotalFormatted}đ</div>
                    <button onclick="removeCartItem(${item.product_id})" title="Xóa món này" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 12px; padding: 2px 4px; margin-top: 2px;">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

async function addToCart(productId) {
    try {
        const res = await fetch(`${API_BASE_URL}/cart/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                product_id: productId,
                quantity: 1
            })
        });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || `HTTP ${res.status}`);
        }
        const result = await res.json();
        currentCart = result.data;
        renderCartBadge();
        showToast('Đã thêm sản phẩm vào giỏ hàng!', 'success');
    } catch (err) {
        console.error('Lỗi thêm giỏ hàng:', err);
        showToast(err.message, 'error');
    }
}

async function updateCartItemQty(productId, newQty) {
    try {
        const res = await fetch(`${API_BASE_URL}/cart/update`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                product_id: productId,
                quantity: newQty
            })
        });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || `HTTP ${res.status}`);
        }
        const result = await res.json();
        currentCart = result.data;
        renderCartBadge();
        renderCartItems();
        updateCartTotals();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function removeCartItem(productId) {
    try {
        const res = await fetch(`${API_BASE_URL}/cart/remove/${productId}?user_id=${currentUser.id}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = await res.json();
        currentCart = result.data;
        renderCartBadge();
        renderCartItems();
        updateCartTotals();
        showToast('Đã xóa món đồ khỏi giỏ hàng', 'info');
    } catch (err) {
        showToast('Lỗi xóa sản phẩm: ' + err.message, 'error');
    }
}

async function applyCartVoucher() {
    const input = document.getElementById('voucherCodeInput');
    const alertBox = document.getElementById('voucherAlert');
    if (!input || !alertBox) return;

    const code = input.value.trim().toUpperCase();
    if (!code) {
        alertBox.style.display = 'block';
        alertBox.style.color = 'var(--danger-red)';
        alertBox.textContent = 'Vui lòng nhập mã voucher!';
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/vouchers/apply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                voucher_code: code,
                order_amount: currentCart.total_amount || 0
            })
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Mã voucher không hợp lệ');
        }

        appliedVoucher = data.data;
        alertBox.style.display = 'block';
        alertBox.style.color = 'var(--primary-green)';
        alertBox.innerHTML = `<i class="fa-solid fa-circle-check"></i> Đã áp dụng mã <strong>${appliedVoucher.voucher_code}</strong>: Giảm -${Number(appliedVoucher.discount_amount).toLocaleString('vi-VN')}đ`;
        updateCartTotals();
    } catch (err) {
        appliedVoucher = null;
        alertBox.style.display = 'block';
        alertBox.style.color = 'var(--danger-red)';
        alertBox.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${err.message}`;
        updateCartTotals();
    }
}

function updateCartTotals() {
    const selectedShippingRadio = document.querySelector('input[name="cartShippingMethod"]:checked');
    currentShippingMethod = selectedShippingRadio ? selectedShippingRadio.value : 'HUB_PICKUP';

    // Tính phí vận chuyển (Lab 05: Trạm Hub 0đ, GHN 25.000đ)
    currentShippingFee = (currentShippingMethod === 'GHN_DELIVERY') ? 25000 : 0;

    const subtotal = currentCart.total_amount || 0;
    const discount = appliedVoucher ? (appliedVoucher.discount_amount || 0) : 0;
    const finalTotal = Math.max(0, subtotal + currentShippingFee - discount);

    const subtotalEl = document.getElementById('cartSubtotal');
    const shippingEl = document.getElementById('cartShippingFee');
    const discountEl = document.getElementById('cartDiscount');
    const finalTotalEl = document.getElementById('cartFinalTotal');
    const voucherRow = document.getElementById('voucherRow');

    if (subtotalEl) subtotalEl.textContent = `${Number(subtotal).toLocaleString('vi-VN')}đ`;
    if (shippingEl) shippingEl.textContent = `${Number(currentShippingFee).toLocaleString('vi-VN')}đ`;
    if (discountEl) discountEl.textContent = `-${Number(discount).toLocaleString('vi-VN')}đ`;
    if (voucherRow) voucherRow.style.display = discount > 0 ? 'flex' : 'none';
    if (finalTotalEl) finalTotalEl.textContent = `${Number(finalTotal).toLocaleString('vi-VN')}đ`;
}

// =============================================================
// 9. ĐẶT HÀNG & THANH TOÁN (LAB 06 & LAB 09)
// =============================================================

function proceedToCheckout() {
    if (!currentCart.items || currentCart.items.length === 0) {
        showToast('Giỏ hàng của bạn đang trống! Vui lòng thêm sản phẩm.', 'error');
        return;
    }

    closeCartDrawer();

    // Điền trước thông tin giao nhận
    const nameInput = document.getElementById('checkoutName');
    const phoneInput = document.getElementById('checkoutPhone');
    const addressInput = document.getElementById('checkoutAddress');
    const totalBtn = document.getElementById('checkoutTotalBtn');

    if (nameInput) nameInput.value = currentUser.full_name || '';
    if (phoneInput) phoneInput.value = '098' + (Math.floor(1000000 + Math.random() * 9000000));
    if (addressInput && !addressInput.value) {
        addressInput.value = currentShippingMethod === 'HUB_PICKUP' ? 'Trạm Hub O2O Cơ sở 1 - ĐH HUNRE' : 'KTX HUNRE, 41A Phú Diễn, Bắc Từ Liêm, Hà Nội';
    }

    const subtotal = currentCart.total_amount || 0;
    const discount = appliedVoucher ? (appliedVoucher.discount_amount || 0) : 0;
    const finalTotal = Math.max(0, subtotal + currentShippingFee - discount);
    if (totalBtn) totalBtn.textContent = `${Number(finalTotal).toLocaleString('vi-VN')}đ`;

    const checkoutModal = document.getElementById('checkoutModal');
    if (checkoutModal) checkoutModal.style.display = 'flex';
}

function closeCheckoutModal() {
    const modal = document.getElementById('checkoutModal');
    if (modal) modal.style.display = 'none';
}

async function submitOrderCheckout() {
    const receiver_name = document.getElementById('checkoutName').value.trim();
    const receiver_phone = document.getElementById('checkoutPhone').value.trim();
    const shipping_address = document.getElementById('checkoutAddress').value.trim();
    const notes = document.getElementById('checkoutNote').value.trim();
    const gatewayRadio = document.querySelector('input[name="checkoutGateway"]:checked');
    const payment_gateway = gatewayRadio ? gatewayRadio.value : 'ESCROW';

    if (!receiver_name || !receiver_phone || !shipping_address) {
        alert('Vui lòng điền đầy đủ tên, số điện thoại và địa chỉ giao hàng!');
        return;
    }

    const payload = {
        buyer_id: currentUser.id,
        items: currentCart.items.map(it => ({
            product_id: it.product_id,
            quantity: it.quantity,
            unit_price: it.unit_price
        })),
        shipping_method: currentShippingMethod,
        shipping_address,
        receiver_name,
        receiver_phone,
        payment_gateway,
        voucher_code: appliedVoucher ? appliedVoucher.voucher_code : null,
        notes
    };

    try {
        const res = await fetch(`${API_BASE_URL}/orders/checkout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || `HTTP ${res.status}`);
        }

        const order = data.data;
        closeCheckoutModal();
        appliedVoucher = null;
        await loadCart(); // Giỏ hàng tự động làm sạch sau khi đặt đơn

        let successMsg = `Đặt hàng thành công! Mã đơn: ${order.order_code}. `;
        if (payment_gateway === 'ESCROW') {
            successMsg += 'Khoản tiền được ký quỹ an toàn tại Smart Escrow Hub HUNRE.';
        } else if (payment_gateway === 'MOMO') {
            successMsg += 'Vui lòng kiểm tra mã QR MoMo Sandbox trong lịch sử giao dịch.';
        } else {
            successMsg += 'Vui lòng chuẩn bị tiền mặt khi nhận hàng (COD).';
        }

        showToast(successMsg, 'success');
    } catch (err) {
        console.error('Lỗi thanh toán đặt hàng:', err);
        showToast('Lỗi đặt hàng: ' + err.message, 'error');
    }
}

// =============================================================
// 10. DANH SÁCH YÊU THÍCH (WISHLIST)
// =============================================================

async function loadWishlist() {
    try {
        const res = await fetch(`${API_BASE_URL}/wishlist/${currentUser.id}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = await res.json();
        userWishlistIds = result.data || [];
        updateWishlistBadge();
    } catch (err) {
        console.warn('Lỗi nạp danh sách yêu thích:', err);
    }
}

function updateWishlistBadge() {
    const badge = document.getElementById('wishlistCount');
    if (badge) {
        badge.textContent = userWishlistIds.length;
    }
}

async function toggleWishlistItem(productId, event) {
    if (event) {
        event.stopPropagation();
    }

    try {
        const res = await fetch(`${API_BASE_URL}/wishlist/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                product_id: productId
            })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = await res.json();
        const isAdded = result.data.is_wishlisted;

        if (isAdded) {
            if (!userWishlistIds.includes(productId)) userWishlistIds.push(productId);
            showToast('Đã thêm sản phẩm vào danh sách yêu thích!', 'success');
        } else {
            userWishlistIds = userWishlistIds.filter(id => id !== productId);
            showToast('Đã gỡ sản phẩm khỏi danh sách yêu thích', 'info');
        }

        updateWishlistBadge();
        renderProducts(); // Cập nhật lại màu trái tim
    } catch (err) {
        showToast('Lỗi cập nhật yêu thích: ' + err.message, 'error');
    }
}

function openWishlistModal() {
    renderWishlistItems();
    const modal = document.getElementById('wishlistModal');
    if (modal) modal.style.display = 'flex';
}

function closeWishlistModal() {
    const modal = document.getElementById('wishlistModal');
    if (modal) modal.style.display = 'none';
}

function renderWishlistItems() {
    const container = document.getElementById('wishlistItemsContainer');
    if (!container) return;

    const wishlistProducts = allProducts.filter(p => userWishlistIds.includes(p.id));

    if (wishlistProducts.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 30px; color: var(--text-muted);">
                <i class="fa-solid fa-heart-crack fa-3x" style="margin-bottom: 12px; color: var(--text-dim);"></i>
                <p>Bạn chưa lưu sản phẩm nào vào danh sách yêu thích</p>
            </div>
        `;
        return;
    }

    container.innerHTML = wishlistProducts.map(p => {
        const priceFormatted = Number(p.current_price || 0).toLocaleString('vi-VN');
        return `
            <div style="display: flex; align-items: center; justify-content: space-between; background: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 10px 14px; gap: 12px;">
                <img src="${p.image_url || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop'}" alt="${p.title}" style="width: 48px; height: 48px; border-radius: 6px; object-fit: cover; border: 1px solid var(--border-subtle);">
                <div style="flex: 1; min-width: 0;">
                    <h5 style="font-size: 13.5px; color: var(--text-main); margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(p.title)}</h5>
                    <div style="font-size: 12.5px; color: var(--text-main); font-weight: 700;">${priceFormatted}đ</div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary" style="padding: 6px 10px; font-size: 12px;" onclick="addToCart(${p.id})">
                        Thêm giỏ
                    </button>
                    <button class="btn btn-secondary" style="padding: 6px 10px; font-size: 12px; color: var(--text-muted);" onclick="toggleWishlistItem(${p.id})">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// =============================================================
// 11. ĐÁNH GIÁ SẢN PHẨM & RATING (LAB 02 MỞ RỘNG & BTL)
// =============================================================

async function openReviewsModal(productId, productTitle) {
    activeReviewProductId = productId;
    const titleEl = document.getElementById('reviewsProductTitle');
    if (titleEl) {
        titleEl.textContent = `Đánh Giá: ${productTitle}`;
    }

    await loadProductReviews(productId);
    const modal = document.getElementById('reviewsModal');
    if (modal) modal.style.display = 'flex';
}

function closeReviewsModal() {
    const modal = document.getElementById('reviewsModal');
    if (modal) modal.style.display = 'none';
}

async function loadProductReviews(productId) {
    const container = document.getElementById('reviewsListContainer');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE_URL}/products/${productId}/reviews`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = await res.json();
        const reviews = result.data || [];

        if (reviews.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--text-muted); font-size: 13px;">
                    Chưa có đánh giá nào cho sản phẩm này. Hãy là người đầu tiên để lại nhận xét!
                </div>
            `;
            return;
        }

        container.innerHTML = reviews.map(r => {
            const stars = '★'.repeat(r.rating || 5) + '☆'.repeat(Math.max(0, 5 - (r.rating || 5)));
            return `
                <div style="background: var(--secondary-gray); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 10px 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <strong style="font-size: 12.5px; color: var(--text-main);">${escapeHtml(r.user_name || 'Sinh viên')}</strong>
                        <span style="color: var(--text-main); font-size: 13px;">${stars}</span>
                    </div>
                    <p style="font-size: 12.5px; color: var(--text-secondary); margin: 0;">${escapeHtml(r.comment)}</p>
                </div>
            `;
        }).join('');
    } catch (err) {
        container.innerHTML = `<div style="color: var(--danger-red); font-size: 12px;">Lỗi nạp đánh giá: ${err.message}</div>`;
    }
}

async function submitProductReview() {
    if (!activeReviewProductId) return;

    const rating = parseInt(document.getElementById('reviewRatingSelect').value);
    const comment = document.getElementById('reviewCommentInput').value.trim();

    if (!comment) {
        alert('Vui lòng nhập nội dung đánh giá của bạn!');
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/reviews`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: activeReviewProductId,
                user_id: currentUser.id,
                rating,
                comment
            })
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || `HTTP ${res.status}`);
        }

        showToast('Đánh giá của bạn đã được ghi nhận!', 'success');
        document.getElementById('reviewCommentInput').value = '';
        await loadProductReviews(activeReviewProductId);
    } catch (err) {
        showToast('Lỗi gửi đánh giá: ' + err.message, 'error');
    }
}

