// ─── REGISTER ────────────────────────────────────────────
async function register() {
    const fullName = document.getElementById("name").value.trim();
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!fullName || !email || !password) {
        showMsg("Please fill in all fields.", "danger");
        return;
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

// LOGIN 
async function login() {
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
        showMsg("Please enter email and password.", "danger");
        return;
    }

    try {
        const data = await loginUser({ email, password });

        localStorage.setItem("userId",    data.userId);
        localStorage.setItem("userEmail", data.email || email);
        localStorage.setItem("userName",  data.fullName || "");

        showMsg("Login successful! Redirecting…", "success");
        setTimeout(() => window.location.href = "dashboard.html", 1000);

    } catch (err) {
        showMsg("Login failed: " + err.message, "danger");
    }
}

//  HELPERS 
function showMsg(msg, type = "info") {
    let el = document.getElementById("authMsg");
    if (!el) {
        el = document.createElement("div");
        el.id = "authMsg";
        document.body.appendChild(el);
    }
    el.className = `alert alert-${type} mt-3`;
    el.textContent = msg;
}