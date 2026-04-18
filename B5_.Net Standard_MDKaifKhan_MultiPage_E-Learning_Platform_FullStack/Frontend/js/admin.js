const userId = localStorage.getItem("userId");
const role   = localStorage.getItem("role");

if (!userId || role !== "Admin") {
    alert("Access denied");
    window.location.href = "login.html";
}

// COURSES
async function loadAdminCourses() {
    const courses = await getCourses();

    document.getElementById("adminCourses").innerHTML = courses.map(c => `
        <div class="card p-3 mb-2">
            <h5>${c.title}</h5>
            <p>${c.description}</p>
            <button onclick="deleteCourseAdmin(${c.courseId})" class="btn btn-danger btn-sm">Delete</button>
        </div>
    `).join("");
}

async function createCourseAdmin() {
    const title = document.getElementById("courseTitle").value;
    const description = document.getElementById("courseDesc").value;

    await createCourse({ title, description, createdBy: userId });
    document.getElementById("courseTitle").value = "";
    document.getElementById("courseDesc").value = "";
    loadAdminCourses();
}

async function deleteCourseAdmin(id) {
    await deleteCourse(id);
    loadAdminCourses();
}

// REAL RESULTS 
async function loadAllResults() {
    const container = document.getElementById("allResults");
    container.innerHTML = "Loading...";

    try {
        const res = await fetch(`${BASE_URL}/results/all`);
        const data = await res.json();

        if (!data.length) {
            container.innerHTML = "No results";
            return;
        }

        const rows = data.map(r => `
            <tr>
                <td>${r.userName}</td>
                <td>${r.quizName}</td>
                <td>${r.score}</td>
                <td>
                    <button onclick="deleteResultAdmin(${r.resultId})"
                        class="btn btn-danger btn-sm">
                        Allow Reattempt
                    </button>
                </td>
            </tr>
        `);

        container.innerHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Quiz</th>
                        <th>Score</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.join("")}
                </tbody>
            </table>
        `;

    } catch (err) {
        container.innerHTML = err.message;
    }
}

// DELETE RESULT
async function deleteResultAdmin(id) {
    if (!confirm("Allow reattempt?")) return;

    await fetch(`${BASE_URL}/results/delete/${id}?userId=${userId}`, {
        method: "DELETE"
    });

    alert("User can reattempt now");
    loadAllResults();
}

// LOGOUT
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

loadAdminCourses();
loadAllResults();