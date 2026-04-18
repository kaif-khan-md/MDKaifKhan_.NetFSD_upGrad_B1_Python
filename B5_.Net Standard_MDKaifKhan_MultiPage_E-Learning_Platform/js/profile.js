const userId = localStorage.getItem("userId");
if (!userId) window.location.href = "login.html";

// ─── LOAD PROFILE ────────────────────────────────────────
async function loadProfile() {
    try {
        const user = await getUser(userId);
        document.getElementById("displayName").textContent    = user.fullName || "—";
        document.getElementById("usernameInput").value        = user.fullName || "";
        document.getElementById("displayEmail").textContent   = user.email    || "—";
    } catch (err) {
        console.error("User load error:", err);
    }
}

// ─── UPDATE PROFILE ──────────────────────────────────────
async function handleName() {
    const name  = document.getElementById("usernameInput").value.trim();
    const email = document.getElementById("emailInput").value.trim();

    if (!name) { alert("Enter a valid name"); return; }

    try {
        const currentUser = await getUser(userId);
        await updateUser(userId, {
            userId:   parseInt(userId),
            fullName: name,
            email:    email || currentUser.email
        });

        localStorage.setItem("userName", name);
        alert("Profile updated successfully ✓");
        loadProfile();
    } catch (err) {
        alert("Update error: " + err.message);
    }
}

// ─── DELETE ACCOUNT ──────────────────────────────────────
async function deleteAccount() {
    if (!confirm("Are you sure you want to delete your account?")) return;
    try {
        await deleteUser(userId);
        localStorage.clear();
        window.location.href = "login.html";
    } catch (err) {
        alert("Delete error: " + err.message);
    }
}

// ─── RESULTS  ─────────────────────────────────────
async function loadResultsUI() {
    const scoreEl   = document.getElementById("quizScore");
    const historyEl = document.getElementById("resultsHistory");
    if (!scoreEl) return;

    try {
        const results = await getResults(userId);

        if (!results.length) {
            scoreEl.textContent = "No quiz attempted yet.";
            historyEl.innerHTML = `<li class="list-group-item text-muted">No results yet</li>`;
            return;
        }

        // LAST SCORE
        const last = results[results.length - 1];

        let lastQuizName = "Quiz";
        let lastTotal = 0;

        try {
            const quiz = await getQuiz(last.quizId);   // 🔥 NEW API
            lastQuizName = quiz.title;

            const questions = await getQuestions(last.quizId);
            lastTotal = questions.length;
        } catch {}

        scoreEl.innerHTML = `
            Last: ${lastQuizName} 
            <span class="badge bg-primary">
                ${last.score} / ${lastTotal}
            </span>
        `;

        historyEl.innerHTML = await Promise.all(results.map(async r => {

            let quizName = "Quiz";
            let total = 0;

            try {
                const quiz = await getQuiz(r.quizId);   // 🔥 IMPORTANT
                quizName = quiz.title;

                const questions = await getQuestions(r.quizId);
                total = questions.length;
            } catch {}

            return `
                <li class="list-group-item">
                    ${quizName} — 
                    <strong>${r.score} / ${total}</strong>
                    <br>
                    <small class="text-muted">
                        Attempted on: ${new Date(r.attemptDate).toLocaleString()}
                    </small>
                </li>
            `;
        })).then(arr => arr.join(""));

    } catch (err) {
        console.error("Results error:", err);
        scoreEl.textContent = "Could not load results.";
    }
}

// ─── COMPLETED COURSES ───────────────────────────────────
async function loadCompletedCourses() {
    const list = document.getElementById("completedList");
    if (!list) return;

    try {
        const progress = await getUserProgress(userId);
        const courses = await getCourses();

        const completed = progress.filter(p => p.isCompleted);

        if (!completed.length) {
            list.innerHTML = `<li class="list-group-item text-muted">No courses completed yet.</li>`;
            return;
        }

        document.getElementById("completedTitle").innerText =
            `📚 Completed Courses (${completed.length})`;

        list.innerHTML = completed.map(p => {
            const course = courses.find(c => c.courseId == p.courseId);

            return `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <span>📗 ${course ? course.title : "Unknown Course"}</span>
                    <span class="badge bg-success">Completed</span>
                </li>
            `;
        }).join("");

    } catch (err) {
        list.innerHTML = `<li class="text-danger">Error loading completed courses</li>`;
    }
}

// ─── LOGOUT ──────────────────────────────────────────────
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

// ─── INIT ────────────────────────────────────────────────
window.onload = () => {
    loadProfile();

    const role = localStorage.getItem("role");

    if (role !== "Admin") {
        loadResultsUI();
    } else {
        document.getElementById("quizScore").innerHTML =
            `<span class="text-muted">Admins do not have quiz results</span>`;
        document.getElementById("resultsHistory").innerHTML = "";
    }

    loadCompletedCourses();
};