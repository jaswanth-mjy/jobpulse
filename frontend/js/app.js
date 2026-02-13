/* ==========================================
   JobPulse — Frontend JavaScript
   With Auth, Landing Page, MongoDB
   ========================================== */

const API = window.location.hostname === "localhost"
    ? "http://localhost:5050/api"
    : `${window.location.origin}/api`;

// Google OAuth Client ID — replace with your own from Google Cloud Console
const GOOGLE_CLIENT_ID = "160223116353-vg7bu7da2t1ilb90uhd9h4o7qmirldf0.apps.googleusercontent.com";

// ========== STATE ==========
let allApplications = [];
let invalidApplications = []; // Track applications that failed validation
let platforms = [];
let statuses = [];
let authToken = localStorage.getItem("jobpulse_token") || null;
let currentUser = JSON.parse(localStorage.getItem("jobpulse_user") || "null");
let recentlyUpdatedIds = new Set(); // Track recently updated applications
let recentlyImportedIds = new Set(); // Track recently imported applications

// Pagination state
let currentOffset = 0;
let pageSize = 50;
let hasMoreData = true;
let isLoadingMore = false;
let totalApplications = 0;

// ========== DOM REFS ==========
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ========== AUTH HELPERS ==========
function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`,
    };
}

function authFetch(url, options = {}) {
    options.headers = { ...options.headers, ...getAuthHeaders() };
    return fetch(url, options).then(async (response) => {
        // If 403 (Forbidden) - email verification required
        if (response.status === 403) {
            const data = await response.json();
            if (data.error && data.error.includes("verification")) {
                console.warn("⚠️ Email verification required - showing verification modal");
                showVerification(currentUser?.email || g.user_email);
                showToast("📧 Please verify your email to continue", "warning");
            }
        }
        return response;
    });
}

// ========== PASSWORD VISIBILITY TOGGLE ==========
function togglePasswordVisibility(inputId, button) {
    const input = document.getElementById(inputId);
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// ========== INIT ==========
document.addEventListener("DOMContentLoaded", async () => {
    // Mobile menu for landing
    const menuBtn = $("#landingMenuBtn");
    if (menuBtn) {
        menuBtn.addEventListener("click", () => {
            $("#landingMobileMenu").classList.toggle("open");
        });
    }

    if (authToken && currentUser) {
        // Verify token is still valid
        try {
            const res = await authFetch(`${API}/auth/me`);
            if (res.ok) {
                const data = await res.json();
                currentUser = data.user;
                
                // Update localStorage with fresh user data
                localStorage.setItem("jobpulse_user", JSON.stringify(currentUser));
                
                // Show app - verification will be handled by 403 error if needed
                console.log("✅ Valid token - showing app");
                showApp();
                // Auto-scan on page load if Gmail connected
                triggerAutoScanIfConnected();
            } else {
                clearAuth();
                showLanding();
            }
        } catch {
            showLanding();
        }
    } else {
        showLanding();
    }
});

// ========== SHOW/HIDE PAGES ==========
function showLanding() {
    $("#landingPage").style.display = "block";
    $("#appContainer").style.display = "none";
}

function showApp() {
    $("#landingPage").style.display = "none";
    $("#appContainer").style.display = "flex";

    // Update user info in sidebar
    if (currentUser) {
        $("#userName").textContent = currentUser.name || currentUser.email;
        $("#userEmail").textContent = currentUser.email;
    }

    initApp();
}

// ========== ONBOARDING: Handle Actions ==========
function handleOnboardingAction(action) {
    switch (action) {
        case 'add-application':
            hideOnboarding();
            resetForm();
            setView("add");
            showToast("Add your first job application!", "info");
            break;
        case 'connect-gmail':
            hideOnboarding();
            setView("gmail");
            showToast("Connect Gmail to auto-import applications", "info");
            break;
        default:
            console.log("Unknown onboarding action:", action);
    }
}

async function initApp() {
    await loadMeta();
    await refreshData();
    setupEventListeners();
    checkGmailStatus();
    setView("dashboard");
    
    // Show onboarding guide for first-time users
    setTimeout(() => {
        if (typeof showOnboarding === 'function') {
            showOnboarding(handleOnboardingAction);
        }
    }, 800);
}

// ========== AUTH: Show/Hide Modal ==========
function showAuth(mode) {
    const overlay = $("#authOverlay");
    overlay.classList.add("active");
    $("#authError").style.display = "none";

    if (mode === "signup") {
        $("#signinForm").style.display = "none";
        $("#signupForm").style.display = "block";
    } else if (mode === "forgot") {
        hideAuth();
        showForgotPassword();
    } else {
        $("#signinForm").style.display = "block";
        $("#signupForm").style.display = "none";
    }
}

function hideAuth() {
    $("#authOverlay").classList.remove("active");
}

function showAuthError(msg) {
    const el = $("#authError");
    el.textContent = msg;
    el.style.display = "block";
}

// ========== GOOGLE SIGN-IN (OAuth 2.0 Popup Flow) ==========
function triggerGoogleSignIn() {
    if (!GOOGLE_CLIENT_ID) {
        showAuthError("Google Sign-In is not configured yet. Please use email/password.");
        return;
    }

    // Disable both buttons while processing
    const signinBtn = $("#googleSigninBtn");
    const signupBtn = $("#googleSignupBtn");
    if (signinBtn) { signinBtn.disabled = true; signinBtn.textContent = "Opening Google..."; }
    if (signupBtn) { signupBtn.disabled = true; signupBtn.textContent = "Opening Google..."; }

    // Build OAuth URL
    const redirectUri = `${window.location.origin}/google-callback.html`;
    const scope = "openid email profile";
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
        `client_id=${GOOGLE_CLIENT_ID}&` +
        `redirect_uri=${encodeURIComponent(redirectUri)}&` +
        `response_type=code&` +
        `scope=${encodeURIComponent(scope)}&` +
        `access_type=online&` +
        `prompt=select_account`;

    // Open popup window
    const width = 500;
    const height = 600;
    const left = (window.innerWidth - width) / 2 + window.screenX;
    const top = (window.innerHeight - height) / 2 + window.screenY;
    
    const popup = window.open(
        authUrl,
        "Google Sign In",
        `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no,location=no,status=no`
    );

    // Listen for message from popup
    window.addEventListener("message", handleGoogleCallback, false);

    // Check if popup was blocked
    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
        showAuthError("Popup was blocked. Please allow popups for this site.");
        if (signinBtn) { signinBtn.disabled = false; signinBtn.textContent = "Sign in with Google"; }
        if (signupBtn) { signupBtn.disabled = false; signupBtn.textContent = "Sign up with Google"; }
    }
}

async function handleGoogleCallback(event) {
    // Verify origin
    if (event.origin !== window.location.origin) return;
    
    const { code, error } = event.data;
    
    // Re-enable buttons
    const signinBtn = $("#googleSigninBtn");
    const signupBtn = $("#googleSignupBtn");
    if (signinBtn) { signinBtn.disabled = false; signinBtn.textContent = "Sign in with Google"; }
    if (signupBtn) { signupBtn.disabled = false; signupBtn.textContent = "Sign up with Google"; }

    if (error) {
        showAuthError(`Google Sign-In failed: ${error}`);
        return;
    }

    if (!code) return;

    // Remove event listener
    window.removeEventListener("message", handleGoogleCallback);

    // Disable buttons again while processing
    if (signinBtn) { signinBtn.disabled = true; signinBtn.textContent = "Signing in..."; }
    if (signupBtn) { signupBtn.disabled = true; signupBtn.textContent = "Signing in..."; }

    try {
        const res = await fetch(`${API}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                code,
                redirect_uri: `${window.location.origin}/google-callback.html`
            }),
        });
        const data = await res.json();

        if (res.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem("jobpulse_token", authToken);
            localStorage.setItem("jobpulse_user", JSON.stringify(currentUser));
            hideAuth();
            showApp();
            showToast(`Welcome, ${data.user.name}! 🎉`, "success");

            if (data.auto_scan) {
                showToast("📧 Auto-scanning Gmail for new applications...", "info");
                pollScanStatus();
            }
        } else {
            showAuthError(data.error || "Google sign-in failed.");
        }
    } catch (err) {
        showAuthError("Network error. Is the backend running?");
    } finally {
        if (signinBtn) { signinBtn.disabled = false; signinBtn.innerHTML = '<svg class="google-icon" viewBox="0 0 24 24" width="20" height="20"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg> Continue with Google'; }
        if (signupBtn) { signupBtn.disabled = false; signupBtn.innerHTML = '<svg class="google-icon" viewBox="0 0 24 24" width="20" height="20"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg> Sign up with Google'; }
    }
}

// ========== AUTH: Sign Up ==========
async function handleSignUp(e) {
    e.preventDefault();
    const btn = $("#signupBtn");
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
    $("#authError").style.display = "none";

    const name = $("#signupName").value.trim();
    const email = $("#signupEmail").value.trim();
    const password = $("#signupPassword").value;

    try {
        const res = await fetch(`${API}/auth/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password }),
        });
        const data = await res.json();

        if (res.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem("jobpulse_token", authToken);
            localStorage.setItem("jobpulse_user", JSON.stringify(currentUser));
            
            // Check if email verification is pending (only on signup)
            if (data.pending_verification) {
                hideAuth();
                showVerification(email);
                if (data.email_sent) {
                    showToast("📧 Verification code sent to your email!", "info");
                } else {
                    showToast("⚠️ Email sending is not configured. Contact admin.", "warning");
                }
            } else {
                // Legacy flow - skip verification
                hideAuth();
                showApp();
                showToast("Account created! Welcome to JobPulse 🎉 Connect your Gmail to auto-import applications.", "success");
            }
        } else {
            showAuthError(data.error || "Signup failed");
        }
    } catch (err) {
        showAuthError("Network error. Is the backend running?");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
    }
}

// ========== AUTH: Sign In ==========
async function handleSignIn(e) {
    e.preventDefault();
    const btn = $("#signinBtn");
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
    $("#authError").style.display = "none";

    const email = $("#signinEmail").value.trim();
    const password = $("#signinPassword").value;

    try {
        const res = await fetch(`${API}/auth/signin`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        const data = await res.json();

        if (res.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem("jobpulse_token", authToken);
            localStorage.setItem("jobpulse_user", JSON.stringify(currentUser));
            
            // Check if email verification is pending (backend explicitly requires it)
            console.log("🔍 Sign-in response:", { pending_verification: data.pending_verification, email_sent: data.email_sent });
            if (data.pending_verification) {
                console.log("⚠️ Verification required - showing verification modal");
                hideAuth();
                showVerification(email);
                if (data.email_sent) {
                    showToast("📧 Verification code sent to your email!", "info");
                } else {
                    showToast("⚠️ Email sending is not configured. Contact admin.", "warning");
                }
            } else {
                console.log("✅ Already verified or Google user - showing app");
                // Legacy flow - already verified or old accounts
                hideAuth();
                showApp();
                showToast("Welcome back! 👋", "success");

                // Auto-scan Gmail if connected
                if (data.auto_scan) {
                    showToast("📧 Auto-scanning Gmail for new applications...", "info");
                    pollScanStatus();
                }
            }
        } else {
            showAuthError(data.error || "Invalid credentials");
        }
    } catch (err) {
        showAuthError("Network error. Is the backend running?");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
    }
}

// ========== AUTH: Logout ==========
function handleLogout() {
    clearAuth();
    showLanding();
    showToast("Signed out successfully", "info");
}

function clearAuth() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem("jobpulse_token");
    localStorage.removeItem("jobpulse_user");
}

// ========== PROFILE SETTINGS ==========
function toggleProfileMenu() {
    const dropdown = $("#profileDropdown");
    const icon = $("#profileMenuIcon");
    
    if (dropdown.style.display === "none") {
        dropdown.style.display = "block";
        icon.classList.add("rotated");
    } else {
        dropdown.style.display = "none";
        icon.classList.remove("rotated");
    }
}

async function showProfileSettings() {
    const overlay = $("#profileSettingsOverlay");
    overlay.classList.add("active");
    
    // Hide profile dropdown
    $("#profileDropdown").style.display = "none";
    $("#profileMenuIcon").classList.remove("rotated");
    
    // Load user data
    if (currentUser) {
        $("#profileName").textContent = currentUser.name || "N/A";
        $("#profileEmail").textContent = currentUser.email || "N/A";
        
        try {
            const res = await authFetch(`${API}/auth/me`);
            if (res.ok) {
                const data = await res.json();
                
                // Update verification status
                if (data.user.email_verified || data.verified) {
                    $("#profileVerified").innerHTML = '<span class="badge badge-success"><i class="fas fa-check-circle"></i> Verified</span>';
                } else {
                    $("#profileVerified").innerHTML = '<span class="badge" style="background: #fff3cd; color: #856404;"><i class="fas fa-exclamation-triangle"></i> Not Verified</span>';
                }
                
                // Show created date if available
                if (data.user.created_at) {
                    const createdDate = new Date(data.user.created_at);
                    const formatted = createdDate.toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                    });
                    $("#profileCreatedAt").textContent = formatted;
                } else {
                    $("#profileCreatedAt").textContent = "N/A";
                }
            }
        } catch (err) {
            console.error("Failed to load profile data:", err);
        }
    }
}

function hideProfileSettings() {
    $("#profileSettingsOverlay").classList.remove("active");
    $("#profileError").style.display = "none";
}

function restartOnboardingTutorial() {
    hideProfileSettings();
    if (typeof resetOnboarding === 'function') {
        resetOnboarding();
        setTimeout(() => {
            if (typeof showOnboarding === 'function') {
                showOnboarding(handleOnboardingAction);
                showToast("Tutorial restarted! Let's go through it again.", "info");
            }
        }, 500);
    } else {
        showToast("Onboarding feature not available", "error");
    }
}

function showProfileError(msg) {
    const el = $("#profileError");
    el.textContent = msg;
    el.style.display = "block";
}

async function confirmDeleteAccount() {
    // First close the profile settings modal
    hideProfileSettings();
    
    // Small delay to let the profile modal close animation complete
    setTimeout(() => {
        showConfirmDialog(
            "⚠️ Delete Account",
            `<strong>WARNING: This action cannot be undone!</strong><br><br>
            This will permanently delete:<br>
            • All your job applications<br>
            • Your profile information<br>
            • All connected Gmail accounts<br>
            • All your data<br><br>
            <span style="color: var(--accent-red); font-weight: 600;">
            This action is irreversible and immediate.
            </span>`,
            "DELETE",
            async () => {
                try {
                    const res = await authFetch(`${API}/auth/delete-account`, {
                        method: "DELETE",
                    });
                    const data = await res.json();
                    
                    if (res.ok) {
                        showToast("Account deleted successfully", "success");
                        
                        // Sign out after 2 seconds
                        setTimeout(() => {
                            handleLogout();
                        }, 2000);
                    } else {
                        showProfileError(data.error || "Failed to delete account");
                    }
                } catch (err) {
                    showProfileError("Network error. Please try again.");
                }
            },
            () => {
                showToast("Account deletion cancelled", "info");
            }
        );
    }, 100);
}

// ========== EMAIL VERIFICATION ==========
async function requestVerificationCode(email) {
    try {
        const res = await authFetch(`${API}/auth/resend-verification`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });
        
        if (res.ok) {
            console.log("✅ Verification code sent to", email);
            return true;
        } else {
            console.warn("⚠️ Failed to send verification code");
            return false;
        }
    } catch (err) {
        console.error("❌ Error sending verification code:", err);
        return false;
    }
}

function showVerification(email) {
    console.log("🔍 showVerification() called with email:", email);
    const overlay = $("#verificationOverlay");
    if (!overlay) {
        console.error("❌ verificationOverlay element not found!");
        return;
    }
    
    console.log("✅ Adding 'active' class to verification overlay");
    overlay.classList.add("active");
    $("#verificationError").style.display = "none";
    $("#verificationSuccess").style.display = "none";
    $("#verificationCode").value = "";
    $("#verificationEmail").textContent = email || "your email";
    
    if (email) {
        $("#verificationEmailText").textContent = `We've sent a 6-digit code to ${email}`;
    }
    
    // Auto-focus on code input
    setTimeout(() => {
        const codeInput = $("#verificationCode");
        if (codeInput) codeInput.focus();
        console.log("📧 Verification modal should now be visible");
    }, 100);
}

function hideVerification() {
    // Only hide if user is verified - prevent bypassing verification
    console.log("⚠️ Attempting to hide verification modal");
    $("#verificationOverlay").classList.remove("active");
}

function showVerificationError(msg) {
    const el = $("#verificationError");
    el.textContent = msg;
    el.style.display = "block";
    $("#verificationSuccess").style.display = "none";
}

function showVerificationSuccess(msg) {
    const el = $("#verificationSuccess");
    el.textContent = msg;
    el.style.display = "block";
    $("#verificationError").style.display = "none";
}

async function handleVerifyEmail() {
    const btn = $("#verifyBtn");
    const code = $("#verificationCode").value.trim();
    
    if (!code) {
        showVerificationError("Please enter the verification code");
        return;
    }
    
    if (code.length !== 6 || !/^\d{6}$/.test(code)) {
        showVerificationError("Code must be 6 digits");
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
    $("#verificationError").style.display = "none";
    
    try {
        const res = await authFetch(`${API}/auth/verify-email`, {
            method: "POST",
            body: JSON.stringify({ code }),
        });
        const data = await res.json();
        
        if (res.ok) {
            // Update token with verified status
            authToken = data.token;
            localStorage.setItem("jobpulse_token", authToken);
            
            // Update currentUser with verified status
            if (currentUser) {
                currentUser.email_verified = true;
                localStorage.setItem("jobpulse_user", JSON.stringify(currentUser));
            }
            
            showVerificationSuccess("✅ Email verified successfully!");
            showToast("Email verified! Welcome to JobPulse! 🎉", "success");
            
            // Close verification modal and show app
            setTimeout(() => {
                hideVerification();
                showApp();
                
                // Auto-scan if Gmail connected
                if (data.auto_scan) {
                    showToast("📧 Auto-scanning Gmail for new applications...", "info");
                    pollScanStatus();
                }
            }, 1500);
        } else {
            showVerificationError(data.error || "Verification failed");
        }
    } catch (err) {
        showVerificationError("Network error. Please try again.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check-circle"></i> Verify Email';
    }
}

async function handleResendCode() {
    const btn = $("#resendBtn");
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    $("#verificationError").style.display = "none";
    
    try {
        const res = await authFetch(`${API}/auth/resend-verification`, {
            method: "POST",
        });
        const data = await res.json();
        
        if (res.ok) {
            showVerificationSuccess("📧 New verification code sent to your email!");
            showToast("New code sent!", "success");
            $("#verificationCode").value = "";
            $("#verificationCode").focus();
        } else {
            showVerificationError(data.error || "Failed to resend code");
        }
    } catch (err) {
        showVerificationError("Network error. Please try again.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Resend Code';
    }
}

// ========== FORGOT PASSWORD ==========
let forgotPasswordEmail = "";

function showForgotPassword() {
    const overlay = $("#forgotPasswordOverlay");
    overlay.classList.add("active");
    $("#forgotPasswordForm").style.display = "block";
    $("#resetPasswordForm").style.display = "none";
    $("#forgotError").style.display = "none";
    $("#forgotSuccess").style.display = "none";
    $("#resetError").style.display = "none";
    $("#forgotEmail").value = "";
    
    setTimeout(() => $("#forgotEmail").focus(), 100);
}

function hideForgotPassword() {
    $("#forgotPasswordOverlay").classList.remove("active");
    forgotPasswordEmail = "";
}

function showForgotError(msg) {
    const el = $("#forgotError");
    el.textContent = msg;
    el.style.display = "block";
    $("#forgotSuccess").style.display = "none";
}

function showForgotSuccess(msg) {
    const el = $("#forgotSuccess");
    el.textContent = msg;
    el.style.display = "block";
    $("#forgotError").style.display = "none";
}

function showResetError(msg) {
    const el = $("#resetError");
    el.textContent = msg;
    el.style.display = "block";
}

async function handleForgotPassword() {
    const btn = $("#forgotBtn");
    const email = $("#forgotEmail").value.trim();
    
    if (!email) {
        showForgotError("Please enter your email address");
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    $("#forgotError").style.display = "none";
    
    try {
        const res = await fetch(`${API}/auth/forgot-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        const data = await res.json();
        
        if (res.ok) {
            forgotPasswordEmail = email;
            showForgotSuccess("📧 Reset code sent! Check your email.");
            showToast("Check your email for reset code", "info");
            
            // Switch to reset form after 2 seconds
            setTimeout(() => {
                $("#forgotPasswordForm").style.display = "none";
                $("#resetPasswordForm").style.display = "block";
                $("#resetEmailText").textContent = `Code sent to ${email}`;
                $("#resetCode").focus();
            }, 2000);
        } else {
            showForgotError(data.error || "Failed to send reset code");
        }
    } catch (err) {
        showForgotError("Network error. Please try again.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Reset Code';
    }
}

async function handleResetPassword() {
    const btn = $("#resetBtn");
    const code = $("#resetCode").value.trim();
    const newPassword = $("#newPassword").value;
    const confirmPassword = $("#confirmPassword").value;
    
    if (!code) {
        showResetError("Please enter the reset code");
        return;
    }
    
    if (code.length !== 6 || !/^\d{6}$/.test(code)) {
        showResetError("Code must be 6 digits");
        return;
    }
    
    if (!newPassword) {
        showResetError("Please enter a new password");
        return;
    }
    
    if (newPassword.length < 6) {
        showResetError("Password must be at least 6 characters");
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showResetError("Passwords do not match");
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
    $("#resetError").style.display = "none";
    
    try {
        const res = await fetch(`${API}/auth/reset-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                email: forgotPasswordEmail, 
                code, 
                new_password: newPassword 
            }),
        });
        const data = await res.json();
        
        if (res.ok) {
            showToast("✅ Password reset successfully! You can now sign in.", "success");
            
            // Close modal and show sign-in form
            setTimeout(() => {
                hideForgotPassword();
                showAuth("signin");
            }, 1500);
        } else {
            showResetError(data.error || "Failed to reset password");
        }
    } catch (err) {
        showResetError("Network error. Please try again.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check-circle"></i> Reset Password';
    }
}

async function handleResendResetCode() {
    if (!forgotPasswordEmail) {
        showResetError("Please start over from the email step");
        return;
    }
    
    showResetError("");
    
    try {
        const res = await fetch(`${API}/auth/forgot-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: forgotPasswordEmail }),
        });
        
        if (res.ok) {
            showToast("📧 New reset code sent!", "success");
            $("#resetCode").value = "";
            $("#resetCode").focus();
        } else {
            showResetError("Failed to resend code");
        }
    } catch (err) {
        showResetError("Network error. Please try again.");
    }
}

// ========== LOAD METADATA ==========
async function loadMeta() {
    try {
        const [pRes, sRes] = await Promise.all([
            fetch(`${API}/platforms`),
            fetch(`${API}/statuses`),
        ]);
        platforms = await pRes.json();
        statuses = await sRes.json();

        populateSelect($("#platform"), platforms);
        populateSelect($("#status"), statuses);
        populateSelect($("#filterPlatform"), platforms, true);
        populateSelect($("#filterStatus"), statuses, true);
    } catch (e) {
        console.error("Failed to load metadata:", e);
        showToast("Cannot connect to server. Is the backend running?", "error");
    }
}

function populateSelect(el, items, hasAll = false) {
    if (!el) return;
    const existing = hasAll ? '<option value="">All</option>' : "";
    el.innerHTML = existing + items.map((i) => `<option value="${i}">${i}</option>`).join("");
}

// ========== REFRESH DATA ==========
async function refreshData(resetPagination = true) {
    try {
        if (resetPagination) {
            currentOffset = 0;
            hasMoreData = true;
            allApplications = [];
        }
        
        const params = new URLSearchParams();
        const platform = $("#filterPlatform")?.value;
        const status = $("#filterStatus")?.value;
        const search = $("#globalSearch")?.value;
        const sortBy = $("#sortBy")?.value;
        const order = $("#sortOrder")?.value;

        if (platform) params.set("platform", platform);
        if (status) params.set("status", status);
        if (search) params.set("search", search);
        if (sortBy) params.set("sort_by", sortBy);
        if (order) params.set("order", order);
        
        // Add pagination parameters
        params.set("limit", pageSize);
        params.set("offset", currentOffset);

        const res = await authFetch(`${API}/applications?${params}`);
        if (res.status === 401) {
            clearAuth();
            showLanding();
            return;
        }
        const data = await res.json();
        
        // Handle both paginated and legacy response formats
        const newApps = data.applications || data;
        hasMoreData = data.has_more !== undefined ? data.has_more : false;
        totalApplications = data.total || newApps.length;
        
        // Separate valid and invalid applications, auto-fix status mismatches
        if (resetPagination) {
            invalidApplications = [];
        }
        
        const validNewApps = [];
        newApps.forEach(app => {
            // Try to auto-fix status mismatches before validation
            if (app.status_history && Array.isArray(app.status_history) && app.status_history.length > 0) {
                const sortedHistory = [...app.status_history].sort((a, b) => {
                    return new Date(b.date) - new Date(a.date);
                });
                const latestHistoryStatus = sortedHistory[0].status;
                
                // If there's a mismatch, auto-fix it
                if (app.status !== latestHistoryStatus) {
                    console.log(`🔧 Auto-fixing status mismatch for ${app.company} - ${app.role}: "${app.status}" → "${latestHistoryStatus}"`);
                    autoFixApplication(app.id, latestHistoryStatus);
                    app.status = latestHistoryStatus; // Update locally for immediate display
                }
            }
            
            const isValid = validateApplication(app);
            if (!isValid) {
                invalidApplications.push(app);
            } else {
                validNewApps.push(app);
            }
        });
        
        // Append new apps to existing list or replace if resetting
        if (resetPagination) {
            allApplications = validNewApps;
        } else {
            allApplications = [...allApplications, ...validNewApps];
        }
        
        // Update offset for next load
        currentOffset = allApplications.length;
        
        // Show warning if there are invalid applications, otherwise clear it
        if (invalidApplications.length > 0 && resetPagination) {
            console.warn(`⚠️ ${invalidApplications.length} applications failed validation and are hidden from dashboard`);
            console.warn("Invalid applications:", invalidApplications.map(app => `${app.company} - ${app.role}`));
            showValidationWarning(invalidApplications.length);
        } else if (resetPagination) {
            // Clear any existing validation warning
            const existing = $("#validationWarning");
            if (existing) existing.remove();
            console.log("✅ All applications passed validation");
        }

        renderDashboard();
        renderApplicationsTable();
        updatePaginationUI();
    } catch (e) {
        console.error("Failed to refresh data:", e);
    } finally {
        isLoadingMore = false;
    }
}

// ========== LOAD MORE (INFINITE SCROLL) ==========
async function loadMoreApplications() {
    if (isLoadingMore || !hasMoreData) return;
    
    isLoadingMore = true;
    $("#loadingMore").style.display = "flex";
    
    try {
        await refreshData(false); // false = don't reset pagination
    } catch (e) {
        console.error("Failed to load more:", e);
        showToast("Failed to load more applications", "error");
    } finally {
        $("#loadingMore").style.display = "none";
    }
}

// Update pagination UI indicators
function updatePaginationUI() {
    const loadingMore = $("#loadingMore");
    const allLoaded = $("#allLoaded");
    
    if (loadingMore) loadingMore.style.display = "none";
    
    if (allLoaded) {
        allLoaded.style.display = hasMoreData ? "none" : "flex";
    }
}

// Setup infinite scroll
function setupInfiniteScroll() {
    const applicationsView = $("#applicationsView");
    if (!applicationsView) return;
    
    let scrollTimeout;
    applicationsView.addEventListener("scroll", () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            const scrollTop = applicationsView.scrollTop;
            const scrollHeight = applicationsView.scrollHeight;
            const clientHeight = applicationsView.clientHeight;
            
            // Load more when 300px from bottom
            if (scrollHeight - scrollTop - clientHeight < 300 && hasMoreData && !isLoadingMore) {
                loadMoreApplications();
            }
        }, 100);
    });
}

// ========== VALIDATION WARNING ==========
function showValidationWarning(count) {
    const existing = $("#validationWarning");
    if (existing) existing.remove();
    
    const warning = document.createElement("div");
    warning.id = "validationWarning";
    warning.className = "validation-warning";
    warning.innerHTML = `
        <div class="validation-warning-content">
            <i class="fas fa-exclamation-triangle"></i>
            <span>${count} application${count > 1 ? 's' : ''} hidden due to incomplete data</span>
            <button class="btn btn-sm btn-ghost" onclick="showInvalidApplications()">
                <i class="fas fa-eye"></i> View & Fix
            </button>
        </div>
    `;
    
    const dashboard = $("#dashboardView");
    if (dashboard) {
        dashboard.insertBefore(warning, dashboard.firstChild);
    }
}

// Show invalid applications modal
window.showInvalidApplications = function() {
    const modal = $("#appModal");
    const overlay = $("#modalOverlay");
    const title = $("#modalTitle");
    const body = $("#modalBody");
    
    title.innerHTML = '<i class="fas fa-exclamation-triangle" style="color:var(--accent-yellow)"></i> Applications Needing Review';
    
    let html = `
        <div class="invalid-apps-info">
            <p>These applications have incomplete or invalid data and won't appear on your dashboard until fixed:</p>
        </div>
        <div class="invalid-apps-list">
    `;
    
    invalidApplications.forEach(app => {
        const issues = [];
        if (!app.company || !app.company.trim()) issues.push("Missing company name");
        if (!app.role || !app.role.trim()) issues.push("Missing role/position");
        if (!app.status || !app.status.trim()) issues.push("Missing status");
        if (!app.platform || !app.platform.trim()) issues.push("Missing platform");
        if (!app.applied_date) issues.push("Missing application date");
        
        // Check for status mismatch
        if (app.status_history && Array.isArray(app.status_history) && app.status_history.length > 0) {
            const sortedHistory = [...app.status_history].sort((a, b) => {
                return new Date(b.date) - new Date(a.date);
            });
            const latestHistoryStatus = sortedHistory[0].status;
            if (app.status !== latestHistoryStatus) {
                issues.push(`Status mismatch: Shows "${app.status}" but latest is "${latestHistoryStatus}"`);
            }
        }
        
        html += `
            <div class="invalid-app-card">
                <div class="invalid-app-header">
                    <h4>${esc(app.company || 'Unknown Company')} - ${esc(app.role || 'Unknown Role')}</h4>
                    <button class="btn btn-sm btn-primary" onclick="fixApplication('${app.id}')">
                        <i class="fas fa-pen"></i> Fix Now
                    </button>
                </div>
                <div class="invalid-app-issues">
                    ${issues.map(issue => `<span class="issue-tag"><i class="fas fa-times-circle"></i> ${issue}</span>`).join('')}
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    body.innerHTML = html;
    
    overlay.style.display = "flex";
    setTimeout(() => {
        overlay.classList.add("active");
        modal.classList.add("active");
    }, 10);
}

// Fix invalid application - close modal and open edit form
window.fixApplication = function(id) {
    // Properly close the invalid apps modal
    const overlay = $("#modalOverlay");
    const modal = $("#appModal");
    
    overlay.classList.remove("active");
    modal.classList.remove("active");
    
    // Wait for animation, then hide and open edit form
    setTimeout(() => {
        overlay.style.display = "none";
        editApplication(id);
    }, 300);
}

// Auto-fix status mismatch by updating status to match latest history
async function autoFixApplication(id, correctStatus) {
    try {
        await authFetch(`${API}/applications/${id}`, {
            method: "PUT",
            body: JSON.stringify({ status: correctStatus }),
        });
        console.log(`✅ Auto-fixed application ${id} status to "${correctStatus}"`);
    } catch (e) {
        console.warn(`❌ Failed to auto-fix application ${id}:`, e);
    }
}

// ========== APPLICATION VALIDATION ==========
function validateApplication(app) {
    // Essential fields must be present and non-empty
    if (!app.company || !app.company.trim()) {
        console.warn(`Invalid application: missing company`, app);
        return false;
    }
    
    if (!app.role || !app.role.trim()) {
        console.warn(`Invalid application: missing role for ${app.company}`, app);
        return false;
    }
    
    if (!app.status || !app.status.trim()) {
        console.warn(`Invalid application: missing status for ${app.company} - ${app.role}`, app);
        return false;
    }
    
    if (!app.platform || !app.platform.trim()) {
        console.warn(`Invalid application: missing platform for ${app.company} - ${app.role}`, app);
        return false;
    }
    
    if (!app.applied_date) {
        console.warn(`Invalid application: missing applied_date for ${app.company} - ${app.role}`, app);
        return false;
    }
    
    // Validate date format
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(app.applied_date)) {
        console.warn(`Invalid application: invalid date format for ${app.company} - ${app.role}`, app);
        return false;
    }
    
    // Validate status is from allowed list
    const validStatuses = [
        "Applied", "Viewed", "In Review", "Phone Screen", 
        "Interview Scheduled", "Interviewed", "Technical Round", 
        "HR Round", "Assessment", "Offer Received", "Accepted", 
        "Rejected", "Withdrawn", "Ghosted"
    ];
    if (!validStatuses.includes(app.status)) {
        console.warn(`Invalid application: unknown status "${app.status}" for ${app.company} - ${app.role}`, app);
        return false;
    }
    
    // CRITICAL: Check status_history consistency
    if (app.status_history && Array.isArray(app.status_history) && app.status_history.length > 0) {
        // Get the most recent status from history
        const sortedHistory = [...app.status_history].sort((a, b) => {
            return new Date(b.date) - new Date(a.date);
        });
        
        const latestHistoryStatus = sortedHistory[0].status;
        
        // If current status doesn't match latest history, it's outdated/inconsistent
        if (app.status !== latestHistoryStatus) {
            console.warn(
                `⚠️ Status mismatch for ${app.company} - ${app.role}: ` +
                `Current="${app.status}", Latest in history="${latestHistoryStatus}". ` +
                `This application needs manual review.`
            );
            return false;
        }
    }
    
    // All validations passed
    return true;
}

// ========== EVENT LISTENERS ==========
let _listenersSetup = false;
function setupEventListeners() {
    if (_listenersSetup) return;
    _listenersSetup = true;

    // Navigation
    $$(".nav-item").forEach((item) => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            setView(item.dataset.view);
        });
    });

    // Quick add
    $("#quickAddBtn").addEventListener("click", () => {
        resetForm();
        setView("add");
    });

    // Form submit
    $("#applicationForm").addEventListener("submit", handleFormSubmit);

    // Cancel
    $("#cancelBtn").addEventListener("click", () => setView("applications"));

    // Filters (reset pagination when filters change)
    ["filterPlatform", "filterStatus", "sortBy", "sortOrder"].forEach((id) => {
        $(`#${id}`)?.addEventListener("change", () => refreshData(true));
    });

    // Search (debounced, reset pagination)
    let searchTimer;
    $("#globalSearch").addEventListener("input", () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => refreshData(true), 350);
    });

    // Modal close
    $("#modalClose").addEventListener("click", closeModal);
    $("#modalOverlay").addEventListener("click", (e) => {
        if (e.target === $("#modalOverlay")) closeModal();
    });

    // Mobile menu
    $("#menuToggle").addEventListener("click", () => {
        const sidebar = $(".sidebar");
        const overlay = $("#sidebarOverlay");
        sidebar.classList.toggle("open");
        overlay.classList.toggle("active");
    });

    // Close sidebar when clicking overlay
    const sidebarOverlay = $("#sidebarOverlay");
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", () => {
            $(".sidebar").classList.remove("open");
            sidebarOverlay.classList.remove("active");
        });
    }

    // Close sidebar when clicking nav items on mobile
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            if (window.innerWidth <= 768) {
                $(".sidebar").classList.remove("open");
                $("#sidebarOverlay").classList.remove("active");
            }
        });
    });

    // Gmail
    $("#scanGmailBtn").addEventListener("click", () => setView("gmail"));
    $("#startScanBtn").addEventListener("click", startGmailScan);
    $("#viewImportedAppsBtn").addEventListener("click", () => {
        setView("applications");
        showToast("Showing imported applications", "info");
    });
    setupGmailForm();
    
    // Setup infinite scroll for applications view
    setupInfiniteScroll();
}

// ========== VIEW SWITCHING ==========
const views = {};
function setView(name) {
    // Lazy-cache view references
    if (!views.dashboard) {
        views.dashboard = $("#dashboardView");
        views.applications = $("#applicationsView");
        views.add = $("#addView");
        views.gmail = $("#gmailView");
    }

    Object.values(views).forEach((v) => v?.classList.remove("active"));
    views[name]?.classList.add("active");

    $$(".nav-item").forEach((n) => n.classList.remove("active"));
    $(`.nav-item[data-view="${name}"]`)?.classList.add("active");

    const titles = { dashboard: "Dashboard", applications: "Applications", add: "Add Application", gmail: "Gmail Import" };
    $("#pageTitle").textContent = titles[name] || "";

    $(".sidebar").classList.remove("open");
}

// ========== DASHBOARD ==========
async function renderDashboard() {
    try {
        const res = await authFetch(`${API}/stats`);
        if (!res.ok) return;
        const stats = await res.json();

        $("#statTotal").textContent = stats.total;
        const interviewCount =
            (stats.by_status["Interview Scheduled"] || 0) +
            (stats.by_status["Interviewed"] || 0) +
            (stats.by_status["Phone Screen"] || 0) +
            (stats.by_status["Technical Round"] || 0) +
            (stats.by_status["HR Round"] || 0);
        $("#statInterviews").textContent = interviewCount;
        $("#statOffers").textContent = (stats.by_status["Offer Received"] || 0) + (stats.by_status["Accepted"] || 0);
        $("#statRejected").textContent = stats.by_status["Rejected"] || 0;
        $("#statResponseRate").textContent = stats.response_rate + "%";
        $("#statGhosted").textContent = stats.by_status["Ghosted"] || 0;

        renderPlatformChart(stats.by_platform);
        renderStatusChart(stats.by_status);
        renderRecentTable();
    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

// ========== PLATFORM BAR CHART ==========
function renderPlatformChart(data) {
    const container = $("#platformChart");
    if (!container) return;
    if (Object.keys(data).length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px;">No data yet</p>';
        return;
    }
    const max = Math.max(...Object.values(data));
    const colors = ["var(--accent-blue)", "var(--accent-purple)", "var(--accent-green)", "var(--accent-orange)", "var(--accent-pink)", "var(--accent-yellow)", "var(--accent-red)"];

    let html = '<div class="bar-chart">';
    Object.entries(data).forEach(([name, count], i) => {
        const pct = (count / max) * 100;
        const color = colors[i % colors.length];
        html += `
            <div class="bar-item">
                <span class="bar-label">${name}</span>
                <div class="bar-track">
                    <div class="bar-fill" style="width:${pct}%;background:${color}">${count}</div>
                </div>
            </div>`;
    });
    html += "</div>";
    container.innerHTML = html;
}

// ========== STATUS CHART ==========
function renderStatusChart(data) {
    const container = $("#statusChart");
    if (!container) return;
    if (Object.keys(data).length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px;">No data yet</p>';
        return;
    }
    const colorMap = {
        Applied: "var(--accent-blue)", Viewed: "var(--accent-purple)", "In Review": "var(--accent-yellow)",
        "Phone Screen": "var(--accent-pink)", "Interview Scheduled": "#7c3aed", Interviewed: "#8b5cf6",
        "Technical Round": "var(--accent-orange)", "HR Round": "#d946ef",
        "Offer Received": "var(--accent-green)", Accepted: "#34d399",
        Rejected: "var(--accent-red)", Withdrawn: "#6b7280", Ghosted: "#9ca3af",
    };

    let html = '<div class="donut-chart">';
    Object.entries(data).forEach(([name, count]) => {
        const color = colorMap[name] || "var(--text-muted)";
        html += `
            <div class="donut-item">
                <span class="donut-color" style="background:${color}"></span>
                <span class="donut-count">${count}</span>
                <span class="donut-name">${name}</span>
            </div>`;
    });
    html += "</div>";
    container.innerHTML = html;
}

// ========== RECENT TABLE ==========
function renderRecentTable() {
    const tbody = $("#recentTable tbody");
    if (!tbody) return;
    
    // Sort by updated_date to show most recently changed applications first
    const sortedApps = [...allApplications].sort((a, b) => {
        const dateA = new Date(a.updated_date || a.applied_date);
        const dateB = new Date(b.updated_date || b.applied_date);
        return dateB - dateA;
    });
    
    const recent = sortedApps.slice(0, 5);

    if (recent.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:30px;">No applications yet</td></tr>';
        return;
    }

    tbody.innerHTML = recent.map((app) => {
        const isUpdated = recentlyUpdatedIds.has(app.id);
        const isNew = recentlyImportedIds.has(app.id);
        const rowStyle = isUpdated ? 'background: rgba(245, 158, 11, 0.08); cursor:pointer; transition: all 0.3s ease;' : 
                         isNew ? 'background: rgba(16, 185, 129, 0.08); cursor:pointer; transition: all 0.3s ease;' : 'cursor:pointer; transition: all 0.3s ease;';
        const updateBadge = isUpdated ? ' <span class="update-badge updated"><i class="fas fa-sync-alt"></i>Updated</span>' : 
                           isNew ? ' <span class="update-badge new"><i class="fas fa-check-circle"></i>New</span>' : '';
        
        // Show when it was last updated
        const lastUpdate = app.updated_date && app.updated_date !== app.applied_date 
            ? `<span style="color:var(--text-muted);font-size:0.85rem;display:block;margin-top:2px;">Updated ${formatDate(app.updated_date)}</span>`
            : '';
        
        return `
        <tr style="${rowStyle}" onclick="viewApplication('${app.id}')">
            <td class="company-cell">${esc(app.company)}</td>
            <td>${esc(app.role)}</td>
            <td>${platformBadge(app.platform)}</td>
            <td>${statusBadge(app.status)}${updateBadge}</td>
            <td>${formatDate(app.applied_date)}${lastUpdate}</td>
        </tr>`;
    }).join("");
}

// ========== APPLICATIONS TABLE ==========
function renderApplicationsTable() {
    const tbody = $("#applicationsTable tbody");
    const empty = $("#emptyState");
    if (!tbody) return;

    if (allApplications.length === 0) {
        tbody.innerHTML = "";
        if (empty) empty.style.display = "block";
        return;
    }

    if (empty) empty.style.display = "none";
    tbody.innerHTML = allApplications.map((app) => {
        const isUpdated = recentlyUpdatedIds.has(app.id);
        const isNew = recentlyImportedIds.has(app.id);
        const rowStyle = isUpdated ? 'background: rgba(245, 158, 11, 0.08); transition: all 0.3s ease;' : 
                         isNew ? 'background: rgba(16, 185, 129, 0.08); transition: all 0.3s ease;' : 'transition: all 0.3s ease;';
        const updateBadge = isUpdated ? ' <span class="update-badge updated"><i class="fas fa-sync-alt"></i>Updated</span>' : 
                           isNew ? ' <span class="update-badge new"><i class="fas fa-check-circle"></i>New</span>' : '';
        return `
        <tr style="${rowStyle}">
            <td class="company-cell">${esc(app.company)}</td>
            <td>${esc(app.role)}</td>
            <td>${platformBadge(app.platform)}</td>
            <td>${statusBadge(app.status)}${updateBadge}</td>
            <td>${esc(app.location || "—")}</td>
            <td>${esc(app.salary || "—")}</td>
            <td>${formatDate(app.applied_date)}</td>
            <td>
                <div class="action-btns">
                    <button class="action-btn" title="View" onclick="viewApplication('${app.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="action-btn" title="Edit" onclick="editApplication('${app.id}')">
                        <i class="fas fa-pen"></i>
                    </button>
                    <button class="action-btn delete" title="Delete" onclick="deleteApplication('${app.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>`;
    }).join("");
}

// ========== FORM HANDLING ==========
async function handleFormSubmit(e) {
    e.preventDefault();

    const data = {
        company: $("#company").value.trim(),
        role: $("#role").value.trim(),
        platform: $("#platform").value,
        status: $("#status").value,
        salary: $("#salary").value.trim(),
        location: $("#location").value.trim(),
        job_url: $("#jobUrl").value.trim(),
        notes: $("#notes").value.trim(),
        applied_date: $("#appliedDate").value || new Date().toISOString().split("T")[0],
        interview_date: $("#interviewDate").value,
        response_date: $("#responseDate").value,
    };

    const editId = $("#editId").value;

    try {
        let res;
        if (editId) {
            res = await authFetch(`${API}/applications/${editId}`, {
                method: "PUT",
                body: JSON.stringify(data),
            });
        } else {
            res = await authFetch(`${API}/applications`, {
                method: "POST",
                body: JSON.stringify(data),
            });
        }

        const result = await res.json();
        if (res.ok) {
            showToast(editId ? "Application updated!" : "Application added!", "success");
            resetForm();
            await refreshData();
            setView("applications");
        } else {
            showToast(result.error || "Something went wrong", "error");
        }
    } catch (e) {
        showToast("Network error. Is the server running?", "error");
    }
}

function resetForm() {
    $("#applicationForm").reset();
    $("#editId").value = "";
    $("#formTitle").innerHTML = '<i class="fas fa-plus-circle"></i> Add New Application';
    $("#submitBtn").innerHTML = '<i class="fas fa-save"></i> Save Application';
    $("#appliedDate").value = new Date().toISOString().split("T")[0];
}

// ========== EDIT ==========
async function editApplication(id) {
    try {
        const res = await authFetch(`${API}/applications/${id}`);
        const app = await res.json();

        $("#editId").value = app.id;
        $("#company").value = app.company;
        $("#role").value = app.role;
        $("#platform").value = app.platform;
        $("#status").value = app.status;
        $("#salary").value = app.salary || "";
        $("#location").value = app.location || "";
        $("#jobUrl").value = app.job_url || "";
        $("#notes").value = app.notes || "";
        $("#appliedDate").value = app.applied_date || "";
        $("#interviewDate").value = app.interview_date || "";
        $("#responseDate").value = app.response_date || "";

        $("#formTitle").innerHTML = '<i class="fas fa-edit"></i> Edit Application';
        $("#submitBtn").innerHTML = '<i class="fas fa-save"></i> Update Application';

        setView("add");
    } catch (e) {
        showToast("Failed to load application", "error");
    }
}

// ========== DELETE ==========
async function deleteApplication(id) {
    if (!confirm("Are you sure you want to delete this application?")) return;

    try {
        const res = await authFetch(`${API}/applications/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast("Application deleted!", "success");
            await refreshData();
        } else {
            showToast("Failed to delete", "error");
        }
    } catch (e) {
        showToast("Network error", "error");
    }
}

// ========== VIEW MODAL ==========
async function viewApplication(id) {
    try {
        const res = await authFetch(`${API}/applications/${id}`);
        const app = await res.json();

        $("#modalTitle").textContent = `${app.company} — ${app.role}`;

        const fields = [
            ["Company", app.company],
            ["Role", app.role],
            ["Platform", platformBadge(app.platform)],
            ["Status", statusBadge(app.status)],
            ["Location", app.location || "—"],
            ["Salary", app.salary || "—"],
            ["Job URL", app.job_url ? `<a href="${esc(app.job_url)}" target="_blank">${esc(app.job_url)}</a>` : "—"],
            ["Applied Date", formatDate(app.applied_date)],
            ["Interview Date", app.interview_date ? formatDate(app.interview_date) : "—"],
            ["Response Date", app.response_date ? formatDate(app.response_date) : "—"],
            ["Last Updated", formatDate(app.updated_date)],
            ["Notes", app.notes || "—"],
        ];

        let detailsHTML = fields.map(([label, value]) => `
            <div class="modal-detail">
                <span class="modal-detail-label">${label}</span>
                <span class="modal-detail-value">${value}</span>
            </div>`).join("");
        
        // Add status history timeline if available
        if (app.status_history && app.status_history.length > 0) {
            detailsHTML += `
                <div class="modal-detail" style="margin-top:24px;border-top:1px solid var(--border-color);padding-top:20px;">
                    <span class="modal-detail-label" style="font-size:1rem;color:var(--text-primary);margin-bottom:16px;display:block;">
                        <i class="fas fa-history"></i> Status Timeline
                    </span>
                    <div class="status-timeline">
                        ${app.status_history.map((entry, index) => {
                            const icon = entry.source === 'gmail_scan' ? 'fa-envelope' : 'fa-edit';
                            const isLatest = index === app.status_history.length - 1;
                            return `
                                <div class="timeline-item ${isLatest ? 'latest' : ''}">
                                    <div class="timeline-marker">
                                        <i class="fas ${icon}"></i>
                                    </div>
                                    <div class="timeline-content">
                                        <div class="timeline-status">${statusBadge(entry.status)}</div>
                                        <div class="timeline-date">${formatDate(entry.date)}</div>
                                        <div class="timeline-source">${entry.source === 'gmail_scan' ? 'Gmail Scan' : 'Manual Update'}</div>
                                    </div>
                                </div>
                            `;
                        }).reverse().join('')}
                    </div>
                </div>
            `;
        }

        $("#modalBody").innerHTML = detailsHTML;

        $("#modalOverlay").classList.add("active");
    } catch (e) {
        showToast("Failed to load details", "error");
    }
}

function closeModal() {
    $("#modalOverlay").classList.remove("active");
}

// ========== CLEAR FILTERS ==========
function clearFilters() {
    $("#filterPlatform").value = "";
    $("#filterStatus").value = "";
    $("#sortBy").value = "applied_date";
    $("#sortOrder").value = "desc";
    refreshData(true); // Reset pagination when clearing filters
    showToast("Filters cleared", "info");
}

// ========== CLEAR ALL APPLICATIONS ==========
async function clearAllApplications() {
    const count = allApplications.length;
    
    if (count === 0) {
        showToast("No applications to delete", "info");
        return;
    }
    
    // Show custom confirmation dialog
    showConfirmDialog(
        `⚠️ Delete ALL ${count} Applications?`,
        `This will permanently delete all your applications. This action cannot be undone.<br><br>Type <strong>DELETE ALL</strong> to confirm:`,
        'DELETE ALL',
        async () => {
            // Confirmed - proceed with deletion
            try {
                const btn = document.querySelector('.btn-danger[onclick*="clearAllApplications"]');
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
                }

                const res = await authFetch(`${API}/applications/clear/all`, { 
                    method: "DELETE" 
                });

                const result = await res.json();

                if (res.ok) {
                    showToast(`✅ Successfully deleted ${result.deleted_count} applications!`, "success");
                    await refreshData();
                } else {
                    showToast(result.error || "Failed to delete applications", "error");
                }

                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-trash-alt"></i> Clear All Data';
                }
            } catch (e) {
                showToast("Failed to delete applications. Please try again.", "error");
                console.error("Clear all error:", e);
                
                const btn = document.querySelector('.btn-danger[onclick*="clearAllApplications"]');
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-trash-alt"></i> Clear All Data';
                }
            }
        }
    );
}

// ========== CUSTOM CONFIRMATION DIALOG ==========
function showConfirmDialog(title, message, requiredText = null, onConfirm = null, onCancel = null) {
    const dialog = $("#confirmDialog");
    const titleEl = $("#confirmTitle");
    const messageEl = $("#confirmMessage");
    const inputWrapper = $("#confirmInputWrapper");
    const input = $("#confirmInput");
    const hint = $("#confirmHint");
    const okBtn = $("#confirmOkBtn");
    const cancelBtn = $("#confirmCancelBtn");
    
    // Set content
    titleEl.textContent = title;
    messageEl.innerHTML = message;
    
    // Handle input requirement
    if (requiredText) {
        inputWrapper.style.display = "block";
        input.value = "";
        input.placeholder = `Type "${requiredText}" to confirm...`;
        hint.textContent = `You must type exactly: ${requiredText}`;
        okBtn.disabled = true;
        okBtn.style.opacity = "0.5";
        
        // Validate input
        input.oninput = () => {
            if (input.value === requiredText) {
                input.classList.add("valid");
                okBtn.disabled = false;
                okBtn.style.opacity = "1";
            } else {
                input.classList.remove("valid");
                okBtn.disabled = true;
                okBtn.style.opacity = "0.5";
            }
        };
    } else {
        inputWrapper.style.display = "none";
        okBtn.disabled = false;
        okBtn.style.opacity = "1";
    }
    
    // Handle confirm
    okBtn.onclick = () => {
        if (requiredText && input.value !== requiredText) {
            return;
        }
        hideConfirmDialog();
        if (onConfirm) onConfirm();
    };
    
    // Handle cancel
    cancelBtn.onclick = () => {
        hideConfirmDialog();
        if (onCancel) onCancel();
    };
    
    // Show dialog
    dialog.classList.add("active");
    
    // Focus input if required
    if (requiredText) {
        setTimeout(() => input.focus(), 100);
    }
}

function hideConfirmDialog() {
    const dialog = $("#confirmDialog");
    dialog.classList.remove("active");
}

// ========== HELPERS ==========
function esc(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return "—";
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
    } catch {
        return dateStr;
    }
}

function statusBadge(status) {
    const cls = status.toLowerCase().replace(/\s+/g, "-");
    return `<span class="status-badge status-${cls}">${status}</span>`;
}

function platformBadge(platform) {
    const icons = {
        LinkedIn: "fab fa-linkedin", Naukri: "fas fa-briefcase", Glassdoor: "fas fa-door-open",
        Indeed: "fas fa-search", AngelList: "fas fa-rocket", Wellfound: "fas fa-rocket",
        Instahyre: "fas fa-user-check", Internshala: "fas fa-graduation-cap",
        Monster: "fas fa-dragon", CareerBuilder: "fas fa-hard-hat", ZipRecruiter: "fas fa-bolt",
        Hired: "fas fa-handshake", "Company Website": "fas fa-globe", Referral: "fas fa-user-friends",
        Other: "fas fa-ellipsis-h",
    };
    const icon = icons[platform] || "fas fa-briefcase";
    return `<span class="platform-badge"><i class="${icon}"></i> ${platform}</span>`;
}

// ========== TOAST ==========
function showToast(message, type = "info") {
    const icons = { 
        success: "fa-check-circle", 
        error: "fa-exclamation-circle", 
        info: "fa-info-circle",
        warning: "fa-exclamation-triangle"
    };
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas ${icons[type]}"></i><span>${message}</span>`;
    $("#toastContainer").appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100px) scale(0.9)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ========== ALERT HELPER ==========
function showAlert(title, message, type = "info", containerId = null) {
    const icons = {
        success: "fa-check-circle",
        error: "fa-times-circle",
        warning: "fa-exclamation-triangle",
        info: "fa-info-circle"
    };
    
    const alert = document.createElement("div");
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="fas ${icons[type]} alert-icon"></i>
        <div class="alert-content">
            <div class="alert-title">${title}</div>
            <div class="alert-message">${message}</div>
        </div>
    `;
    
    if (containerId) {
        const container = $(containerId);
        if (container) {
            container.insertBefore(alert, container.firstChild);
        }
    }
    
    return alert;
}

// ==========================================
//  AUTO-SCAN ON LOGIN
// ==========================================

async function triggerAutoScanIfConnected() {
    try {
        const res = await authFetch(`${API}/gmail/status`);
        const data = await res.json();
        if (data.is_authenticated) {
            // Trigger a background scan via signin already did it,
            // but if page was refreshed, we check status
            pollScanStatus();
        }
    } catch (e) {
        // Silently ignore
    }
}

async function pollScanStatus() {
    let attempts = 0;
    const maxAttempts = 60; // poll for up to ~2 minutes

    const poll = async () => {
        try {
            const res = await authFetch(`${API}/scan/status`);
            const data = await res.json();

            if (data.status === "scanning") {
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(poll, 2000);
                }
            } else if (data.status === "done" && data.result) {
                const r = data.result;
                if (r.imported > 0 || r.updated > 0) {
                    showToast(`✅ Auto-scan: ${r.imported} new, ${r.updated || 0} updated applications imported!`, "success");
                    
                    // Track which apps were updated/imported from auto-scan
                    recentlyUpdatedIds.clear();
                    recentlyImportedIds.clear();
                    
                    if (r.applications) {
                        r.applications.forEach(app => {
                            if (app._action === "updated") {
                                recentlyUpdatedIds.add(app.id);
                            } else if (app._action === "new") {
                                recentlyImportedIds.add(app.id);
                            }
                        });
                    }
                    
                    await refreshData();  // Refresh dashboard with new data
                    
                    // Clear highlights after 10 seconds
                    setTimeout(() => {
                        recentlyUpdatedIds.clear();
                        recentlyImportedIds.clear();
                        renderDashboard();
                        renderApplicationsTable();
                    }, 10000);
                } else if (r.found > 0) {
                    showToast("Auto-scan complete — all applications already up to date.", "info");
                }
                // else: no Gmail accounts, stay silent
            } else if (data.status === "error") {
                console.error("Auto-scan error:", data.result?.error);
                // Don't show error toast — don't alarm the user on auto-scan
            }
            // status === "idle" means no scan was triggered, do nothing
        } catch (e) {
            // Silently ignore network errors during polling
        }
    };

    // Start polling after a short delay
    setTimeout(poll, 3000);
}

// ==========================================
//  GMAIL INTEGRATION (Multi-Account)
// ==========================================

async function checkGmailStatus() {
    try {
        const res = await authFetch(`${API}/gmail/accounts`);
        const data = await res.json();
        const accounts = data.accounts || [];

        renderAccountsList(accounts);

        if (accounts.length > 0) {
            $("#gmailScanCard").style.display = "block";
            $("#scanGmailBtn").innerHTML = '<i class="fas fa-envelope"></i> Scan Gmail';
        } else {
            $("#gmailScanCard").style.display = "none";
        }
    } catch (e) {
        console.error("Gmail status check failed:", e);
    }
}

function renderAccountsList(accounts) {
    const container = $("#connectedAccountsList");
    if (!container) return;

    if (!accounts.length) {
        container.innerHTML = `
            <p class="no-accounts-msg">
                <i class="fas fa-info-circle"></i> No Gmail accounts connected yet. Click <strong>"Add Account"</strong> to get started.
            </p>`;
        return;
    }

    container.innerHTML = accounts.map(acct => {
        const initials = acct.email.charAt(0).toUpperCase();
        const authBadge = acct.auth_type === 'oauth' 
            ? '<span class="auth-type-badge oauth"><i class="fab fa-google"></i> OAuth</span>'
            : '<span class="auth-type-badge app-password"><i class="fas fa-key"></i> App Password</span>';
        return `
            <div class="account-row" data-id="${acct.id}">
                <div class="account-info">
                    <div class="account-icon">${esc(initials)}</div>
                    <span class="account-email">${esc(acct.email)}</span>
                    ${authBadge}
                    <span class="account-badge"><i class="fas fa-check"></i> Connected</span>
                </div>
                <button class="account-remove-btn" data-id="${acct.id}" title="Remove account">
                    <i class="fas fa-trash-alt"></i> Remove
                </button>
            </div>`;
    }).join("");

    container.querySelectorAll(".account-remove-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const id = btn.dataset.id;
            const row = btn.closest(".account-row");
            const email = row.querySelector(".account-email").textContent;
            if (!confirm(`Remove ${email}?`)) return;

            try {
                const res = await authFetch(`${API}/gmail/accounts/${id}`, { method: "DELETE" });
                if (res.ok) {
                    showToast(`${email} removed.`, "info");
                    await checkGmailStatus();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to remove", "error");
                }
            } catch (e) {
                showToast("Failed to remove account.", "error");
            }
        });
    });
}

// Track if OAuth is available on the server
let oauthAvailable = false;

async function checkOAuthStatus() {
    try {
        const res = await fetch(`${API}/gmail/oauth/status`);
        const data = await res.json();
        oauthAvailable = data.oauth_available === true;
        
        // Show/hide OAuth option based on availability
        const oauthCard = $("#oauthMethodCard");
        if (oauthCard) {
            oauthCard.style.display = oauthAvailable ? "flex" : "none";
            if (!oauthAvailable) {
                oauthCard.innerHTML = `
                    <div class="auth-method-icon" style="opacity: 0.5;">
                        <i class="fab fa-google"></i>
                    </div>
                    <h3 style="opacity: 0.5;">Sign in with Google</h3>
                    <p class="auth-method-desc" style="color: #888;">
                        OAuth not configured on server. Use App Password method instead.
                    </p>
                `;
            }
        }
    } catch (e) {
        console.log("OAuth status check failed, defaulting to App Password only");
        oauthAvailable = false;
    }
}

function setupGmailForm() {
    const authMethodCard = $("#gmailAuthMethodCard");
    const setupCard = $("#gmailSetupCard");
    if (!authMethodCard || !setupCard) return;
    
    // Check OAuth availability on load
    checkOAuthStatus();

    // Show auth method selection when clicking "Add Account"
    $("#showAddAccountBtn")?.addEventListener("click", async () => {
        await checkOAuthStatus(); // Refresh OAuth status
        authMethodCard.style.display = "block";
        setupCard.style.display = "none";
    });

    // Cancel from auth method selection
    $("#cancelAuthMethodBtn")?.addEventListener("click", () => {
        authMethodCard.style.display = "none";
    });

    // Start OAuth flow
    $("#startOAuthBtn")?.addEventListener("click", async () => {
        if (!oauthAvailable) {
            showToast("OAuth is not configured on the server. Please use App Password.", "error");
            return;
        }
        
        const btn = $("#startOAuthBtn");
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        
        try {
            const res = await authFetch(`${API}/gmail/oauth/start`, { method: "POST" });
            const data = await res.json();
            
            if (res.ok && data.authorization_url) {
                // Open OAuth window
                const width = 600, height = 700;
                const left = (screen.width - width) / 2;
                const top = (screen.height - height) / 2;
                
                const oauthWindow = window.open(
                    data.authorization_url,
                    'Gmail OAuth',
                    `width=${width},height=${height},left=${left},top=${top},scrollbars=yes`
                );
                
                // Listen for OAuth completion
                const handleMessage = async (event) => {
                    if (event.data?.type === 'oauth_success') {
                        showToast(`✅ ${event.data.email} connected via OAuth!`, "success");
                        authMethodCard.style.display = "none";
                        await checkGmailStatus();
                        window.removeEventListener('message', handleMessage);
                    } else if (event.data?.type === 'oauth_error') {
                        showToast(`OAuth failed: ${event.data.error}`, "error");
                        window.removeEventListener('message', handleMessage);
                    }
                };
                window.addEventListener('message', handleMessage);
                
                // Check if window was closed without completing
                const checkClosed = setInterval(() => {
                    if (oauthWindow?.closed) {
                        clearInterval(checkClosed);
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fab fa-google"></i> Continue with Google';
                    }
                }, 500);
                
            } else {
                showToast(data.error || "Failed to start OAuth", "error");
            }
        } catch (e) {
            showToast("Failed to start OAuth flow", "error");
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fab fa-google"></i> Continue with Google';
        }
    });

    // Show App Password form
    $("#showAppPasswordFormBtn")?.addEventListener("click", () => {
        authMethodCard.style.display = "none";
        setupCard.style.display = "block";
        $("#gmailEmail").value = "";
        $("#gmailAppPassword").value = "";
        $("#gmailEmail").focus();
    });

    // Back to auth method selection
    $("#backToAuthMethodBtn")?.addEventListener("click", () => {
        setupCard.style.display = "none";
        authMethodCard.style.display = "block";
    });

    // Cancel from App Password form
    $("#cancelAddAccountBtn")?.addEventListener("click", () => {
        setupCard.style.display = "none";
    });

    // App Password form submission
    $("#gmailConnectForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();

        const emailAddr = $("#gmailEmail").value.trim();
        const appPassword = $("#gmailAppPassword").value.trim().replace(/\s/g, "");
        const btn = $("#connectGmailBtn");

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';

        try {
            const res = await authFetch(`${API}/gmail/accounts`, {
                method: "POST",
                body: JSON.stringify({ email: emailAddr, app_password: appPassword }),
            });
            const data = await res.json();

            if (res.ok) {
                showToast(data.message || "Account connected! 🎉", "success");
                setupCard.style.display = "none";
                await checkGmailStatus();
            } else {
                showToast(data.error || "Failed to connect", "error");
            }
        } catch (e) {
            showToast("Connection failed. Is the backend running?", "error");
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-link"></i> Connect Account';
        }
    });
}

async function startGmailScan() {
    const btn = $("#startScanBtn");
    const progress = $("#scanProgress");
    const results = $("#scanResults");
    const daysBack = $("#scanDaysBack").value;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
    progress.style.display = "block";
    results.style.display = "none";

    const fill = $("#progressFill");
    fill.style.width = "10%";
    setTimeout(() => fill.style.width = "30%", 500);
    setTimeout(() => fill.style.width = "60%", 1500);
    setTimeout(() => fill.style.width = "80%", 3000);

    try {
        const res = await authFetch(`${API}/gmail/scan`, {
            method: "POST",
            body: JSON.stringify({ days_back: parseInt(daysBack), max_results: 100 }),
        });

        const data = await res.json();

        fill.style.width = "100%";
        $("#scanProgressText").textContent = "Scan complete!";

        setTimeout(() => {
            progress.style.display = "none";

            if (res.ok) {
                results.style.display = "block";
                $("#resultFound").textContent = data.found;
                $("#resultImported").textContent = data.imported;
                $("#resultUpdated").textContent = data.updated || 0;
                $("#resultSkipped").textContent = data.skipped;

                const tbody = $("#scanResultsTable tbody");
                if (data.applications && data.applications.length > 0) {
                    tbody.innerHTML = data.applications.map(app => {
                        const action = app._action === "updated" ? '<span style="color:#f59e0b">↻ Updated</span>' : '<span style="color:#10b981">✓ New</span>';
                        return `
                            <tr>
                                <td class="company-cell">${esc(app.company)}</td>
                                <td>${esc(app.role)}</td>
                                <td>${platformBadge(app.platform)}</td>
                                <td>${statusBadge(app.status)} ${action}</td>
                                <td>${formatDate(app.applied_date)}</td>
                            </tr>`;
                    }).join("");
                } else {
                    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:20px;">
                        ${data.found === 0 ? "No job application emails found in this period." : "All found applications were already imported."}
                    </td></tr>`;
                }

                showToast(data.message, (data.imported > 0 || data.updated > 0) ? "success" : "info");

                if (data.imported > 0 || data.updated > 0) {
                    // Track which apps were updated/imported
                    recentlyUpdatedIds.clear();
                    recentlyImportedIds.clear();
                    
                    if (data.applications) {
                        data.applications.forEach(app => {
                            if (app._action === "updated") {
                                recentlyUpdatedIds.add(app.id);
                            } else if (app._action === "new") {
                                recentlyImportedIds.add(app.id);
                            }
                        });
                    }
                    
                    refreshData();
                    
                    // Clear highlights after 10 seconds
                    setTimeout(() => {
                        recentlyUpdatedIds.clear();
                        recentlyImportedIds.clear();
                        renderDashboard();
                        renderApplicationsTable();
                    }, 10000);
                }
            } else {
                showToast(data.error || "Scan failed", "error");
            }
        }, 600);

    } catch (e) {
        showToast("Scan failed. Is the backend running?", "error");
        progress.style.display = "none";
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-search"></i> Scan All Accounts';
    }
}
