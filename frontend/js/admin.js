/* ==========================================
   Admin Dashboard — JavaScript
   ========================================== */

const API = window.location.hostname === "localhost"
    ? "http://localhost:5050/api"
    : `${window.location.origin}/api`;

// Get auth token from storage (same as main app)
let authToken = sessionStorage.getItem("jobpulse_token") || localStorage.getItem("jobpulse_token") || null;

// Current pagination state
let currentPage = 1;
const pageLimit = 20;

// DOM helpers
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ========== AUTH HELPERS ==========
function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`,
    };
}

// ========== INIT ==========
document.addEventListener("DOMContentLoaded", async () => {
    // Check if user is logged in
    if (!authToken) {
        showLoginRequired();
        return;
    }

    // Check if user is admin
    try {
        const res = await fetch(`${API}/admin/check`, {
            headers: getAuthHeaders()
        });

        if (!res.ok) {
            if (res.status === 401) {
                showLoginRequired();
            } else {
                showAccessDenied();
            }
            return;
        }

        const data = await res.json();
        
        if (!data.is_admin) {
            showAccessDenied();
            return;
        }

        // User is admin - show dashboard
        showDashboard(data.email);
        await loadStats();
        await loadUsers(1);

    } catch (error) {
        console.error("Error checking admin status:", error);
        showAccessDenied();
    }
});

// ========== SHOW/HIDE STATES ==========
function showLoginRequired() {
    $("#loadingState").style.display = "none";
    $("#loginRequired").style.display = "flex";
}

function showAccessDenied() {
    $("#loadingState").style.display = "none";
    $("#accessDenied").style.display = "flex";
}

function showDashboard(email) {
    $("#loadingState").style.display = "none";
    $("#adminDashboard").style.display = "block";
    $("#adminEmail").textContent = email;
}

// ========== LOAD STATS ==========
async function loadStats() {
    try {
        const res = await fetch(`${API}/admin/stats`, {
            headers: getAuthHeaders()
        });

        if (!res.ok) {
            throw new Error("Failed to load stats");
        }

        const data = await res.json();

        // Update stat cards
        $("#totalUsers").textContent = formatNumber(data.total_users);
        $("#verifiedUsers").textContent = formatNumber(data.verified_users);
        $("#recentUsers7d").textContent = formatNumber(data.recent_users_7d);
        $("#recentUsers30d").textContent = formatNumber(data.recent_users_30d);
        $("#totalApplications").textContent = formatNumber(data.total_applications);
        $("#gmailConnected").textContent = formatNumber(data.gmail_connected_users);

        // Update last updated timestamp
        const timestamp = new Date(data.timestamp);
        $("#lastUpdated").textContent = timestamp.toLocaleString();

    } catch (error) {
        console.error("Error loading stats:", error);
    }
}

// ========== LOAD USERS ==========
async function loadUsers(page = 1) {
    currentPage = page;
    
    const tbody = $("#usersTableBody");
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="loading-row">
                <div class="spinner small"></div>
                Loading users...
            </td>
        </tr>
    `;

    try {
        const res = await fetch(`${API}/admin/users?page=${page}&limit=${pageLimit}`, {
            headers: getAuthHeaders()
        });

        if (!res.ok) {
            throw new Error("Failed to load users");
        }

        const data = await res.json();

        // Render users table
        if (data.users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="loading-row">
                        No users found
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = data.users.map((user, index) => `
                <tr>
                    <td>${(page - 1) * pageLimit + index + 1}</td>
                    <td>${escapeHtml(user.name) || '-'}</td>
                    <td>${escapeHtml(user.email)}</td>
                    <td>
                        ${user.email_verified 
                            ? '<span class="badge success"><i class="fas fa-check"></i> Yes</span>'
                            : '<span class="badge warning"><i class="fas fa-times"></i> No</span>'}
                    </td>
                    <td>
                        <span class="badge info">${user.application_count}</span>
                    </td>
                    <td>
                        ${user.gmail_connected 
                            ? '<span class="badge success"><i class="fab fa-google"></i> Yes</span>'
                            : '<span class="badge warning">No</span>'}
                    </td>
                    <td>${formatDate(user.created_at)}</td>
                </tr>
            `).join('');
        }

        // Render pagination
        renderPagination(data.page, data.total_pages, data.total);

    } catch (error) {
        console.error("Error loading users:", error);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="loading-row">
                    Error loading users. Please try again.
                </td>
            </tr>
        `;
    }
}

// ========== PAGINATION ==========
function renderPagination(currentPage, totalPages, totalUsers) {
    const pagination = $("#pagination");
    
    if (totalPages <= 1) {
        pagination.innerHTML = `<span>Showing all ${totalUsers} users</span>`;
        return;
    }

    let html = '';
    
    // Previous button
    html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="loadUsers(${currentPage - 1})">
        <i class="fas fa-chevron-left"></i> Prev
    </button>`;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<button onclick="loadUsers(1)">1</button>`;
        if (startPage > 2) {
            html += `<span>...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="loadUsers(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<span>...</span>`;
        }
        html += `<button onclick="loadUsers(${totalPages})">${totalPages}</button>`;
    }
    
    // Next button
    html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="loadUsers(${currentPage + 1})">
        Next <i class="fas fa-chevron-right"></i>
    </button>`;
    
    // Total count
    html += `<span style="margin-left: 1rem;">Total: ${totalUsers} users</span>`;
    
    pagination.innerHTML = html;
}

// ========== REFRESH ==========
async function refreshStats() {
    await loadStats();
    await loadUsers(currentPage);
}

// ========== HELPERS ==========
function formatNumber(num) {
    if (num === undefined || num === null) return '-';
    return num.toLocaleString();
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return '-';
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return '-';
    }
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
