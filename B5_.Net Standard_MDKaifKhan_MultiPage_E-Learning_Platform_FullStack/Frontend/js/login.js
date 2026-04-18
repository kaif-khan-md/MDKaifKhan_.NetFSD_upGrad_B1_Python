function showTab(tab) {
    document.getElementById("loginForm").style.display    = tab === "login"    ? "" : "none";``
    document.getElementById("registerForm").style.display = tab === "register" ? "" : "none";
    document.querySelectorAll("#authTabs .nav-link").forEach((btn, i) => {
        btn.classList.toggle("active", (i === 0 && tab === "login") || (i === 1 && tab === "register"));
    });
    document.getElementById("authMsg").innerHTML = "";
}

// Override register to use separate register-form fields
async function register() {
    const fullName = document.getElementById("name").value.trim();
    const email    = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value.trim();
    if (!fullName || !email || !password) {
        showMsg("Please fill in all fields.", "danger"); return;
    }
    try {
        const data = await registerUser({ fullName, email, password });
        localStorage.setItem("userId",    data.userId);
        localStorage.setItem("userEmail", data.email || email);
        localStorage.setItem("userName",  data.fullName || fullName);
        showMsg("Registered successfully! Redirecting…", "success");
        setTimeout(() => window.location.href = "dashboard.html", 1000);
    } catch (err) {
        showMsg("Registration failed: " + err.message, "danger");
    }
}

// Override login to use login-form email field
async function login() {
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    if (!email || !password) { showMsg("Enter email and password.", "danger"); return; }
    try {
        const data = await loginUser({ email, password });
        localStorage.setItem("userId",    data.userId);
        localStorage.setItem("userEmail", data.email || email);
        localStorage.setItem("userName",  data.fullName || "");
        localStorage.setItem("role", data.role);
        showMsg("Login successful! Redirecting…", "success");
         setTimeout(() => {
            if (data.role === "Admin") {
                window.location.href = "admin.html";
            } else {
                window.location.href = "dashboard.html";
            }
        }, 1000);
    } catch (err) {
        showMsg("Login failed: " + err.message, "danger");
    }
}

function showMsg(msg, type) {
    const el = document.getElementById("authMsg");
    el.className = `alert alert-${type}`;
    el.textContent = msg;
}