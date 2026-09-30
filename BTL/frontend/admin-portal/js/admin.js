/**
 * HUNRE ADMIN PORTAL JAVASCRIPT
 * Xử lý luồng nghiệp vụ Lab 08 (Quản lý 8 tabs đơn hàng) & Lab 09 (Tài chính & Đối soát COD)
 */

const API_BASE = '/api/v1';

let currentMainTab = 'orders';
let currentOrderTab = 'all';
let currentSearchKeyword = '';
let allOrders = [];
let allTransactions = [];
let selectedOrderForModal = null;

// Khởi chạy khi tài liệu sẵn sàng
document.addEventListener('DOMContentLoaded', () => {
    loadAdminOrders();
    loadFinanceData();
    loadAdminUsers();
    loadAdminProducts();
});

// =============================================================
// 1. ĐIỀU HƯỚNG TABS CHÍNH
// =============================================================

function switchTab(tabName, btnElement) {
    currentMainTab = tabName;
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => btn.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');

    document.querySelectorAll('.admin-view').forEach(view => view.classList.remove('active'));
    
    const targetMap = {
        'orders': { id: 'viewOrders', title: 'Quản Lý & Xử Lý Đơn Hàng (Lab 08)', sub: 'Theo dõi trạng thái đơn hàng theo 8 tabs quy chuẩn và điều phối luồng giao nhận' },
        'finance': { id: 'viewFinance', title: 'Báo Cáo Tài Chính & Giao Dịch (Lab 09)', sub: 'Đối soát dòng tiền, tiền COD đang chờ thu và quỹ ký quỹ bảo vệ người mua' },
        'users': { id: 'viewUsers', title: 'Quản Lý Sinh Viên & KYC (Lab 03)', sub: 'Kiểm soát tài khoản sinh viên trường, vai trò phân quyền và điểm uy tín' },
        'products': { id: 'viewProducts', title: 'Quản Lý Danh Mục & Sản Phẩm (Lab 02)', sub: 'Tổng quan bài đăng, danh mục giáo trình và tồn kho hàng hóa' }
    };

    const target = targetMap[tabName];
    if (target) {
        const viewEl = document.getElementById(target.id);
        if (viewEl) viewEl.classList.add('active');
        document.getElementById('pageTitle').textContent = target.title;
        document.getElementById('pageSubtitle').textContent = target.sub;
    }

    if (tabName === 'orders') loadAdminOrders();
    else if (tabName === 'finance') loadFinanceData();
    else if (tabName === 'users') loadAdminUsers();
    else if (tabName === 'products') loadAdminProducts();
}

function refreshCurrentView() {
    switchTab(currentMainTab);
    showToast('Đã làm mới dữ liệu thời gian thực!', 'success');
}

// =============================================================
// 2. TAB 1: XỬ LÝ ĐƠN HÀNG THEO 8 TABS (LAB 08)
// =============================================================

async function loadAdminOrders() {
    const tbody = document.getElementById('adminOrdersTbody');
    if (!tbody) return;

    const gateway = document.getElementById('gatewayFilter') ? document.getElementById('gatewayFilter').value : '';
    const shipping = document.getElementById('shippingFilter') ? document.getElementById('shippingFilter').value : '';

    try {
        let url = `${API_BASE}/admin/orders?tab=${currentOrderTab}`;
        if (gateway) url += `&gateway=${gateway}`;
        if (currentSearchKeyword) url += `&search=${encodeURIComponent(currentSearchKeyword)}`;

        const res = await fetch(url);
        const data = await res.json();
        
        allOrders = data.orders || [];
        updateTabCounters(allOrders);
        renderOrdersTable(allOrders, shipping);
    } catch (err) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center" style="color: var(--danger-red); padding: 30px;">
                    <i class="fa-solid fa-triangle-exclamation"></i> Không thể kết nối đến Order API: ${err.message}
                </td>
            </tr>
        `;
    }
}

function updateTabCounters(orders) {
    const badge = document.getElementById('ordersCountBadge');
    if (badge) badge.textContent = orders.length;

    // Cập nhật số lượng của từng tab theo status
    const counts = {
        'all': orders.length,
        'pending': 0, 'ready': 0, 'picking': 0, 'delivering': 0,
        'delivered': 0, 'return': 0, 'cancelled': 0
    };

    orders.forEach(o => {
        const s = (o.status || 'pending').toLowerCase();
        if (['pending', 'not_shipped', 'processing', 'deposited'].includes(s)) counts['pending']++;
        else if (['ready', 'ready_to_pick'].includes(s)) counts['ready']++;
        else if (s === 'picking') counts['picking']++;
        else if (['delivering', 'picked', 'storing', 'transporting', 'sorting', 'stored_at_hub'].includes(s)) counts['delivering']++;
        else if (['delivered', 'released'].includes(s)) counts['delivered']++;
        else if (['return', 'returning', 'returned', 'disputed'].includes(s)) counts['return']++;
        else if (s === 'cancelled') counts['cancelled']++;
    });

    Object.keys(counts).forEach(k => {
        const el = document.getElementById(`count-${k}`);
        if (el) el.textContent = counts[k];
    });
}

function renderOrdersTable(orders, shippingFilter = '') {
    const tbody = document.getElementById('adminOrdersTbody');
    if (!tbody) return;

    let list = orders;
    if (shippingFilter) {
        list = list.filter(o => o.shipping_method === shippingFilter);
    }

    if (list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center" style="padding: 40px; color: var(--text-muted);">
                    <i class="fa-solid fa-inbox fa-2x" style="margin-bottom: 8px;"></i>
                    <p>Không có đơn hàng nào trong tab "${currentOrderTab.toUpperCase()}".</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = list.map(o => {
        const statusClass = `status-${(o.status || 'pending').toLowerCase()}`;
        const statusText = formatStatusText(o.status);
        const totalFormatted = Number(o.total_price || 0).toLocaleString('vi-VN');
        const shipBadge = o.shipping_method === 'HUB_PICKUP' 
            ? '<span class="badge-info"><i class="fa-solid fa-building-columns"></i> Trạm Hub CS1 (0đ)</span>'
            : '<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #F59E0B; padding: 3px 8px; border-radius: 6px;"><i class="fa-solid fa-truck"></i> GHN Express</span>';
        
        const gatewayBadge = formatGatewayBadge(o.gateway);
        const payStatusBadge = (o.payment_status === 'paid')
            ? '<span style="color: var(--primary-green); font-weight: 600;"><i class="fa-solid fa-circle-check"></i> Đã thanh toán</span>'
            : '<span style="color: var(--warning-amber); font-weight: 600;"><i class="fa-solid fa-clock"></i> Chờ thanh toán</span>';

        const isDelivering = ['delivering', 'picking', 'transporting', 'stored_at_hub'].includes((o.status || '').toLowerCase());

        return `
            <tr>
                <td>
                    <strong style="color: #60A5FA; cursor: pointer;" onclick="viewOrderDetail('${o.order_code}')">${o.order_code}</strong>
                    <div style="font-size: 11px; color: var(--text-muted);">${o.created_at || ''}</div>
                </td>
                <td>
                    <strong>${escapeHtml(o.customer_name || 'Khách hàng')}</strong>
                    <div style="font-size: 11.5px; color: var(--text-muted);"><i class="fa-solid fa-phone"></i> ${o.customer_phone || ''}</div>
                </td>
                <td>${shipBadge}</td>
                <td><strong style="color: #FFFFFF;">${totalFormatted}đ</strong></td>
                <td>${gatewayBadge}</td>
                <td><span class="status-pill ${statusClass}">${statusText}</span></td>
                <td>${payStatusBadge}</td>
                <td>
                    <button class="btn-table-action" onclick="openOrderStatusModal('${o.order_code}', '${o.status}', '${escapeHtml(o.customer_name)}')">
                        <i class="fa-solid fa-pen-to-square"></i> Cập nhật
                    </button>
                    ${isDelivering ? `
                        <span title="Quy tắc Lab 08: Đơn đang giao không thể hủy!" style="cursor: not-allowed; opacity: 0.5; margin-left: 4px;">
                            <button class="btn-table-action danger" disabled style="cursor: not-allowed;">
                                <i class="fa-solid fa-ban"></i> Chặn hủy
                            </button>
                        </span>
                    ` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function filterOrderTab(tabName, btnElement) {
    currentOrderTab = tabName;
    document.querySelectorAll('.order-tabs-bar .tab-btn').forEach(btn => btn.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');
    loadAdminOrders();
}

function handleOrderSearch(event) {
    currentSearchKeyword = (event.target.value || '').trim();
    loadAdminOrders();
}

function formatStatusText(s) {
    const map = {
        'pending': 'Chờ xử lý',
        'ready': 'Chờ lấy hàng',
        'ready_to_pick': 'Chờ lấy hàng',
        'picking': 'Đang lấy hàng',
        'delivering': 'Đang giao hàng',
        'delivered': 'Thành công',
        'return': 'Hoàn hàng',
        'cancelled': 'Đã hủy',
        'stored_at_hub': 'Đang lưu tại Hub',
        'deposited': 'Đã đặt cọc'
    };
    return map[(s || '').toLowerCase()] || s;
}

function formatGatewayBadge(gw) {
    const g = (gw || '').toUpperCase();
    if (g === 'ESCROW') {
        return '<span style="background: rgba(16, 185, 129, 0.15); color: var(--primary-green); padding: 3px 8px; border-radius: 6px; font-weight: 600;"><i class="fa-solid fa-shield-halved"></i> Smart Escrow</span>';
    } else if (g === 'MOMO') {
        return '<span style="background: rgba(236, 72, 153, 0.15); color: #F472B6; padding: 3px 8px; border-radius: 6px; font-weight: 600;"><i class="fa-solid fa-wallet"></i> Ví MoMo</span>';
    } else {
        return '<span style="background: rgba(148, 163, 184, 0.15); color: #CBD5E1; padding: 3px 8px; border-radius: 6px; font-weight: 600;"><i class="fa-solid fa-money-bill-wave"></i> COD Tiền mặt</span>';
    }
}

// Modal Cập Nhật Trạng Thái
function openOrderStatusModal(orderCode, currentStatus, customerName) {
    selectedOrderForModal = { orderCode, currentStatus };
    document.getElementById('modalOrderInfo').textContent = `Mã đơn: ${orderCode} | Khách hàng: ${customerName} | Hiện tại: ${currentStatus}`;
    document.getElementById('modalStatusSelect').value = currentStatus.toLowerCase();
    document.getElementById('modalAdminNote').value = '';
    checkCancelWarning();
    document.getElementById('orderStatusModal').style.display = 'flex';
}

function closeOrderStatusModal() {
    document.getElementById('orderStatusModal').style.display = 'none';
    selectedOrderForModal = null;
}

function checkCancelWarning() {
    const newStatus = document.getElementById('modalStatusSelect').value;
    const warning = document.getElementById('cancelWarningAlert');
    if (!selectedOrderForModal) return;

    const curr = (selectedOrderForModal.currentStatus || '').toLowerCase();
    const isDelivering = ['delivering', 'picking', 'transporting', 'stored_at_hub'].includes(curr);

    if (isDelivering && newStatus === 'cancelled') {
        warning.style.display = 'block';
    } else {
        warning.style.display = 'none';
    }
}

async function submitOrderStatusUpdate() {
    if (!selectedOrderForModal) return;
    const newStatus = document.getElementById('modalStatusSelect').value;
    const note = document.getElementById('modalAdminNote').value;

    const curr = (selectedOrderForModal.currentStatus || '').toLowerCase();
    const isDelivering = ['delivering', 'picking', 'transporting', 'stored_at_hub'].includes(curr);

    // Chặn ngay tại frontend theo quy chuẩn Lab 08
    if (isDelivering && newStatus === 'cancelled') {
        showToast('Quy định Lab 08: Đơn hàng đang vận chuyển, KHÔNG ĐƯỢC PHÉP HỦY!', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/admin/orders/${selectedOrderForModal.orderCode}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus, note })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Lỗi cập nhật trạng thái');

        showToast(data.message || 'Cập nhật thành công!', 'success');
        closeOrderStatusModal();
        loadAdminOrders();
        loadFinanceData();
    } catch (err) {
        showToast(`Thất bại: ${err.message}`, 'error');
    }
}

function viewOrderDetail(orderCode) {
    const order = allOrders.find(o => o.order_code === orderCode);
    if (!order) return;
    alert(`Chi tiết đơn hàng ${order.order_code}:\n- Khách: ${order.customer_name} (${order.customer_phone})\n- Địa chỉ: ${order.shipping_address}\n- Phương thức: ${order.shipping_method}\n- Cổng: ${order.gateway}\n- Tổng tiền: ${Number(order.total_price).toLocaleString('vi-VN')}đ\n- Trạng thái: ${order.status}`);
}

// =============================================================
// 3. TAB 2: TÀI CHÍNH & DOANH THU (LAB 09)
// =============================================================

async function loadFinanceData() {
    try {
        // Tải KPIs
        const kpiRes = await fetch(`${API_BASE}/admin/finance/kpis`);
        const kpiData = await kpiRes.json();
        if (kpiData.success && kpiData.kpis) {
            const k = kpiData.kpis;
            document.getElementById('kpiGrossRevenue').textContent = `${Number(k.gross_revenue || 0).toLocaleString('vi-VN')}đ`;
            document.getElementById('kpiNetRevenue').textContent = `${Number(k.net_revenue || 0).toLocaleString('vi-VN')}đ`;
            document.getElementById('kpiPendingCod').textContent = `${Number(k.pending_cod_amount || 0).toLocaleString('vi-VN')}đ`;
            document.getElementById('kpiEscrowHolding').textContent = `${Number(k.escrow_holding_amount || 0).toLocaleString('vi-VN')}đ`;
            document.getElementById('kpiRefunded').textContent = `${Number(k.refunded_amount || 0).toLocaleString('vi-VN')}đ`;
            document.getElementById('kpiAov').textContent = `${Number(k.average_order_value || 0).toLocaleString('vi-VN')}đ`;
        }

        // Tải Transactions
        const txRes = await fetch(`${API_BASE}/admin/finance/transactions`);
        const txData = await txRes.json();
        allTransactions = txData.transactions || [];
        renderFinanceTransactions(allTransactions);
    } catch (err) {
        console.error('Lỗi tải dữ liệu tài chính:', err);
    }
}

function renderFinanceTransactions(txs) {
    const tbody = document.getElementById('financeTransactionsTbody');
    if (!tbody) return;

    if (txs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 30px; color: var(--text-muted);">Chưa có giao dịch nào được ghi nhận.</td></tr>`;
        return;
    }

    tbody.innerHTML = txs.map(t => {
        const amtFormatted = Number(t.amount || 0).toLocaleString('vi-VN');
        const isCod = (t.gateway === 'cod');
        const statusPill = (t.status === 'paid')
            ? '<span class="status-pill status-delivered"><i class="fa-solid fa-check"></i> Đã thu tiền (paid)</span>'
            : (t.status === 'pending'
                ? '<span class="status-pill status-delivering"><i class="fa-solid fa-clock"></i> Chờ thu (pending)</span>'
                : `<span class="status-pill status-return">${t.status}</span>`);

        return `
            <tr>
                <td>#${t.id}</td>
                <td><strong style="color: #60A5FA;">${t.order_code}</strong></td>
                <td>${formatGatewayBadge(t.gateway)}</td>
                <td><strong style="color: #FFFFFF;">${amtFormatted}đ</strong></td>
                <td>${statusPill}</td>
                <td style="font-size: 11.5px; color: var(--text-muted);">${t.paid_at || t.created_at || 'Chưa thanh toán'}</td>
                <td>
                    ${isCod ? `
                        <div style="display: flex; gap: 6px;">
                            ${t.status === 'pending' ? `
                                <button class="btn-table-action" onclick="transitionCodStatus(${t.id}, 'paid')">
                                    <i class="fa-solid fa-check-double"></i> Đã Thu Tiền COD
                                </button>
                            ` : ''}
                            ${t.status === 'paid' ? `
                                <button class="btn-table-action danger" onclick="transitionCodStatus(${t.id}, 'refund_pending')">
                                    <i class="fa-solid fa-rotate-left"></i> Chờ Hoàn Tiền
                                </button>
                            ` : ''}
                            ${t.status === 'refund_pending' ? `
                                <button class="btn-table-action danger" onclick="transitionCodStatus(${t.id}, 'refunded')">
                                    <i class="fa-solid fa-circle-check"></i> Đã Hoàn Tiền
                                </button>
                            ` : ''}
                        </div>
                    ` : '<span style="color: var(--text-muted); font-size: 11px;">Tự động qua Gateway</span>'}
                </td>
            </tr>
        `;
    }).join('');
}

async function transitionCodStatus(txId, targetStatus) {
    if (!confirm(`Xác nhận chuyển trạng thái đối soát COD sang '${targetStatus.toUpperCase()}'?`)) return;

    try {
        const res = await fetch(`${API_BASE}/admin/finance/cod-transition`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_id: txId, new_status: targetStatus })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Lỗi đối soát COD');

        showToast(data.message || 'Cập nhật đối soát COD thành công!', 'success');
        loadFinanceData();
        loadAdminOrders();
    } catch (err) {
        showToast(`Lỗi: ${err.message}`, 'error');
    }
}

// =============================================================
// 4. TAB 3: NGƯỜI DÙNG & KYC (LAB 03)
// =============================================================

async function loadAdminUsers() {
    const tbody = document.getElementById('adminUsersTbody');
    if (!tbody) return;

    try {
        const res = await fetch(`${API_BASE}/admin/users`);
        const data = await res.json();
        const users = data.users || [];

        tbody.innerHTML = users.map(u => {
            const isKyc = u.email && u.email.endsWith('@hunre.edu.vn');
            const score = u.trust_score || 500;
            let tierBadge = '<span class="status-pill status-ready">Bạc</span>';
            if (score >= 800) tierBadge = '<span class="status-pill status-delivered">Kim Cương</span>';
            else if (score >= 600) tierBadge = '<span class="status-pill status-delivering">Vàng</span>';
            else if (score < 400) tierBadge = '<span class="status-pill status-return">Đồng</span>';

            const statusClass = (u.status === 'BLOCKED') ? 'status-cancelled' : 'status-delivered';
            const statusLabel = (u.status === 'BLOCKED') ? 'Đã khóa' : 'Hoạt động';

            return `
                <tr>
                    <td>#${u.id}</td>
                    <td><strong>${u.student_code}</strong></td>
                    <td>${escapeHtml(u.full_name)}</td>
                    <td>
                        ${u.email}
                        ${isKyc ? '<i class="fa-solid fa-circle-check" style="color: var(--primary-green); margin-left: 4px;" title="KYC Hợp Lệ"></i>' : ''}
                    </td>
                    <td>${u.faculty || 'CNTT'}</td>
                    <td><strong style="color: #60A5FA;">${score}</strong></td>
                    <td>${tierBadge}</td>
                    <td><span class="badge-info">${u.role || 'STUDENT'}</span></td>
                    <td><span class="status-pill ${statusClass}">${statusLabel}</span></td>
                    <td>
                        ${u.role !== 'ADMIN' ? `
                            <button class="btn-table-action ${u.status === 'BLOCKED' ? '' : 'danger'}" onclick="toggleUserStatus(${u.id}, '${u.status || 'ACTIVE'}')">
                                <i class="fa-solid ${u.status === 'BLOCKED' ? 'fa-lock-open' : 'fa-lock'}"></i>
                                ${u.status === 'BLOCKED' ? 'Mở Khóa' : 'Khóa TK'}
                            </button>
                        ` : '<span style="color: var(--text-muted); font-size: 11px;">Quản trị viên</span>'}
                    </td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error('Lỗi tải người dùng:', err);
    }
}

async function toggleUserStatus(userId, currentStatus) {
    const newStatus = (currentStatus === 'BLOCKED') ? 'ACTIVE' : 'BLOCKED';
    if (!confirm(`Bạn có chắc chắn muốn chuyển tài khoản #${userId} sang '${newStatus}'?`)) return;

    try {
        const res = await fetch(`${API_BASE}/admin/users/${userId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Lỗi cập nhật trạng thái');

        showToast(data.message, 'success');
        loadAdminUsers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// =============================================================
// 5. TAB 4: DANH MỤC & SẢN PHẨM (LAB 02)
// =============================================================

async function loadAdminProducts() {
    const tbody = document.getElementById('adminProductsTbody');
    if (!tbody) return;

    try {
        const res = await fetch(`${API_BASE}/products`);
        const data = await res.json();
        const prods = data.data || [];

        tbody.innerHTML = prods.map(p => `
            <tr>
                <td>#${p.id}</td>
                <td>
                    <img src="${p.image_url || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=100'}" alt="${p.title}" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover;">
                </td>
                <td><strong>${escapeHtml(p.title)}</strong></td>
                <td><span class="badge-info">${p.category_name || p.category_id}</span></td>
                <td><strong style="color: var(--primary-green);">${Number(p.current_price).toLocaleString('vi-VN')}đ</strong></td>
                <td>${Number(p.floor_price || 0).toLocaleString('vi-VN')}đ</td>
                <td><span class="status-pill status-delivered">${p.condition_grade || 'GRADE_A'}</span></td>
                <td>${escapeHtml(p.seller_name || 'Sinh viên')}</td>
                <td><span class="status-pill status-ready">${p.status || 'ACTIVE'}</span></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Lỗi tải sản phẩm admin:', err);
    }
}

// =============================================================
// 6. TIỆN ÍCH HỖ TRỢ
// =============================================================

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation';
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
