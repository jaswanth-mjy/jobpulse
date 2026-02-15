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

// Store users data for detail view
let usersData = [];

// Store stats data for recipient count
let statsData = null;

// Selected users for bulk email
let selectedUsers = new Map(); // userId -> {email, name}

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
    console.log("Admin page loaded");
    console.log("Auth token from sessionStorage:", sessionStorage.getItem("jobpulse_token") ? "exists" : "null");
    console.log("Auth token from localStorage:", localStorage.getItem("jobpulse_token") ? "exists" : "null");
    console.log("Final authToken:", authToken ? "exists" : "null");
    
    // Check if user is logged in
    if (!authToken) {
        console.log("No auth token - showing login required");
        showLoginRequired();
        return;
    }

    // Check if user is admin
    try {
        console.log("Checking admin status...");
        const res = await fetch(`${API}/admin/check`, {
            headers: getAuthHeaders()
        });

        console.log("Admin check response status:", res.status);

        if (!res.ok) {
            if (res.status === 401) {
                console.log("401 - showing login required");
                showLoginRequired();
            } else {
                console.log("Non-OK response - showing access denied");
                showAccessDenied();
            }
            return;
        }

        const data = await res.json();
        console.log("Admin check data:", data);
        
        if (!data.is_admin) {
            console.log("Not admin - showing access denied");
            showAccessDenied();
            return;
        }

        // User is admin - show dashboard
        console.log("User is admin - showing dashboard");
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
    console.log("Loading stats...");
    try {
        const res = await fetch(`${API}/admin/stats`, {
            headers: getAuthHeaders()
        });

        console.log("Stats response status:", res.status);

        if (!res.ok) {
            throw new Error("Failed to load stats");
        }

        const data = await res.json();
        console.log("Stats data:", data);
        
        // Store for recipient count
        statsData = data;

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
        
        // Update recipient count for bulk email
        updateRecipientCount();

        console.log("Stats loaded successfully");

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
            <td colspan="9" class="loading-row">
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
        usersData = data.users; // Store for detail view

        // Render users table
        if (data.users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="loading-row">
                        No users found
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = data.users.map((user, index) => `
                <tr class="${selectedUsers.has(user.id) ? 'selected-row' : ''}">
                    <td class="checkbox-col">
                        <input type="checkbox" 
                            class="user-checkbox" 
                            data-user-id="${user.id}"
                            data-user-email="${escapeHtml(user.email)}"
                            data-user-name="${escapeHtml(user.name || '')}"
                            ${selectedUsers.has(user.id) ? 'checked' : ''}
                            onchange="toggleUserSelection(this)">
                    </td>
                    <td>${(page - 1) * pageLimit + index + 1}</td>
                    <td>
                        <div class="user-cell">
                            ${user.picture 
                                ? `<img src="${escapeHtml(user.picture)}" class="user-avatar-small" alt="avatar">`
                                : '<i class="fas fa-user-circle user-avatar-icon"></i>'}
                            <div class="user-cell-info">
                                <span class="user-cell-name">${escapeHtml(user.name) || '-'}</span>
                                <span class="user-cell-email">${escapeHtml(user.email)}</span>
                            </div>
                        </div>
                    </td>
                    <td>
                        ${user.auth_provider === 'google' 
                            ? '<span class="badge google"><i class="fab fa-google"></i> Google</span>'
                            : '<span class="badge email"><i class="fas fa-envelope"></i> Email</span>'}
                    </td>
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
                            ? `<span class="badge success" title="${user.gmail_emails?.join(', ') || ''}"><i class="fab fa-google"></i> ${user.gmail_emails?.length || 1}</span>`
                            : '<span class="badge muted">-</span>'}
                    </td>
                    <td>${formatDate(user.created_at)}</td>
                    <td>
                        <button class="btn btn-sm btn-ghost" onclick="showUserDetail('${user.id}')" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        // Render pagination
        renderPagination(data.page, data.total_pages, data.total);

    } catch (error) {
        console.error("Error loading users:", error);
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="loading-row">
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

// ========== USER DETAIL MODAL ==========
function showUserDetail(userId) {
    const user = usersData.find(u => u.id === userId);
    if (!user) return;
    
    const content = $("#userDetailContent");
    content.innerHTML = `
        <div class="user-detail-header">
            ${user.picture 
                ? `<img src="${escapeHtml(user.picture)}" class="user-detail-avatar" alt="avatar">`
                : '<div class="user-detail-avatar-placeholder"><i class="fas fa-user"></i></div>'}
            <div class="user-detail-name-section">
                <h3>${escapeHtml(user.name) || 'No Name'}</h3>
                <p>${escapeHtml(user.email)}</p>
            </div>
        </div>
        
        <div class="user-detail-grid">
            <div class="detail-item">
                <label><i class="fas fa-id-badge"></i> User ID</label>
                <span class="detail-value mono">${user.id}</span>
            </div>
            
            <div class="detail-item">
                <label><i class="fas fa-sign-in-alt"></i> Auth Method</label>
                <span class="detail-value">
                    ${user.auth_provider === 'google' 
                        ? '<span class="badge google"><i class="fab fa-google"></i> Google OAuth</span>'
                        : '<span class="badge email"><i class="fas fa-envelope"></i> Email/Password</span>'}
                </span>
            </div>
            
            <div class="detail-item">
                <label><i class="fas fa-check-circle"></i> Email Verified</label>
                <span class="detail-value">
                    ${user.email_verified 
                        ? '<span class="badge success"><i class="fas fa-check"></i> Verified</span>'
                        : '<span class="badge warning"><i class="fas fa-times"></i> Not Verified</span>'}
                </span>
            </div>
            
            <div class="detail-item">
                <label><i class="fas fa-calendar-check"></i> Verified At</label>
                <span class="detail-value">${formatDateTime(user.email_verified_at)}</span>
            </div>
            
            <div class="detail-item">
                <label><i class="fas fa-calendar-plus"></i> Account Created</label>
                <span class="detail-value">${formatDateTime(user.created_at)}</span>
            </div>
            
            <div class="detail-item">
                <label><i class="fas fa-file-alt"></i> Applications</label>
                <span class="detail-value"><span class="badge info">${user.application_count} applications</span></span>
            </div>
            
            <div class="detail-item full-width">
                <label><i class="fab fa-google"></i> Gmail Connections</label>
                <span class="detail-value">
                    ${user.gmail_connected 
                        ? `<div class="gmail-list">${user.gmail_emails?.map(e => `<span class="badge success"><i class="fas fa-envelope"></i> ${escapeHtml(e)}</span>`).join('') || '<span class="badge success">Connected</span>'}</div>`
                        : '<span class="badge muted">Not Connected</span>'}
                </span>
            </div>
        </div>
    `;
    
    $("#userDetailModal").style.display = "flex";
}

function closeUserModal() {
    $("#userDetailModal").style.display = "none";
}

// Close modal on overlay click
document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.style.display = "none";
    }
});

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeUserModal();
    }
});

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return '-';
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return '-';
    }
}

// ========== BULK EMAIL ==========

// Selected users tracking
function toggleUserSelection(checkbox) {
    const userId = checkbox.dataset.userId;
    const userEmail = checkbox.dataset.userEmail;
    const userName = checkbox.dataset.userName;
    
    if (checkbox.checked) {
        selectedUsers.set(userId, { email: userEmail, name: userName });
        checkbox.closest('tr').classList.add('selected-row');
    } else {
        selectedUsers.delete(userId);
        checkbox.closest('tr').classList.remove('selected-row');
    }
    
    updateSelectionUI();
}

function toggleSelectAll(checked) {
    const checkboxes = $$('.user-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = checked;
        toggleUserSelection(checkbox);
    });
}

function clearSelection() {
    selectedUsers.clear();
    $$('.user-checkbox').forEach(cb => {
        cb.checked = false;
        cb.closest('tr').classList.remove('selected-row');
    });
    $('#selectAllUsers').checked = false;
    updateSelectionUI();
}

function updateSelectionUI() {
    const count = selectedUsers.size;
    const selectionInfo = $('#selectionInfo');
    const selectedOption = $('#selectedOption');
    const selectedUsersHint = $('#selectedUsersHint');
    
    if (count > 0) {
        selectionInfo.style.display = 'flex';
        $('#selectedCount').textContent = count;
        selectedOption.disabled = false;
        selectedOption.textContent = `Selected Users (${count})`;
    } else {
        selectionInfo.style.display = 'none';
        selectedOption.disabled = true;
        selectedOption.textContent = 'Selected Users (0)';
        // If was on "selected", switch back to "all"
        if ($('#emailRecipients').value === 'selected') {
            $('#emailRecipients').value = 'all';
        }
    }
    
    // Show/hide hint based on dropdown value
    if ($('#emailRecipients').value === 'selected') {
        selectedUsersHint.style.display = count > 0 ? 'none' : 'block';
    } else {
        selectedUsersHint.style.display = 'none';
    }
    
    updateRecipientCount();
}

// Update recipient count when filter changes
document.addEventListener("DOMContentLoaded", () => {
    const recipientSelect = $("#emailRecipients");
    if (recipientSelect) {
        recipientSelect.addEventListener("change", () => {
            updateRecipientCount();
            updateSelectionUI();
        });
    }
    
    const messageTextarea = $("#emailMessage");
    if (messageTextarea) {
        messageTextarea.addEventListener("input", () => {
            $("#charCount").textContent = messageTextarea.value.length;
        });
    }
    
    const bulkEmailForm = $("#bulkEmailForm");
    if (bulkEmailForm) {
        bulkEmailForm.addEventListener("submit", handleBulkEmailSubmit);
    }
});

function updateRecipientCount() {
    if (!statsData) return;
    
    const filter = $("#emailRecipients").value;
    let count = 0;
    
    switch (filter) {
        case "all":
            count = statsData.total_users;
            break;
        case "verified":
            count = statsData.verified_users;
            break;
        case "unverified":
            count = statsData.unverified_users;
            break;
        case "selected":
            count = selectedUsers.size;
            break;
    }
    
    $("#recipientCount").textContent = count;
    $("#sendCount").textContent = filter === "selected" ? `${count} Selected` : count;
}

async function handleBulkEmailSubmit(e) {
    e.preventDefault();
    previewEmail();
}

function previewEmail() {
    const subject = $("#emailSubject").value.trim();
    const message = $("#emailMessage").value.trim();
    
    if (!subject || !message) {
        showEmailResult("Please fill in subject and message", "error");
        return;
    }
    
    // Show preview
    $("#previewSubject").textContent = subject;
    $("#previewBody").innerHTML = message.replace(/\n/g, '<br>');
    $("#emailPreviewModal").style.display = "flex";
}

function closeEmailPreview() {
    $("#emailPreviewModal").style.display = "none";
}

async function confirmSendEmail() {
    const btn = document.querySelector("#emailPreviewModal .btn-primary");
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    
    const subject = $("#emailSubject").value.trim();
    const message = $("#emailMessage").value.trim();
    const filter = $("#emailRecipients").value;
    
    // Build request body
    const requestBody = { subject, message, filter };
    
    // If sending to selected users, include the user IDs
    if (filter === "selected") {
        if (selectedUsers.size === 0) {
            showEmailResult("❌ No users selected. Please select users from the table above.", "error");
            btn.disabled = false;
            btn.innerHTML = originalText;
            closeEmailPreview();
            return;
        }
        requestBody.selected_user_ids = Array.from(selectedUsers.keys());
    }
    
    try {
        const res = await fetch(`${API}/admin/send-bulk-email`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(requestBody)
        });
        
        const data = await res.json();
        
        closeEmailPreview();
        
        if (res.ok) {
            showEmailResult(
                `✅ Email sent successfully! ${data.success} delivered, ${data.failed} failed.`,
                data.failed > 0 ? "warning" : "success"
            );
            
            // Clear form on success
            if (data.failed === 0) {
                $("#emailSubject").value = "";
                $("#emailMessage").value = "";
                $("#charCount").textContent = "0";
            }
        } else {
            showEmailResult(`❌ ${data.error || "Failed to send email"}`, "error");
        }
        
    } catch (error) {
        closeEmailPreview();
        showEmailResult(`❌ Network error: ${error.message}`, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function showEmailResult(message, type) {
    const result = $("#emailResult");
    result.textContent = message;
    result.className = `email-result ${type}`;
    result.style.display = "block";
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        result.style.display = "none";
    }, 10000);
}
