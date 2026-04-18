const userId = localStorage.getItem("userId");
if (!userId) window.location.href = "login.html";

const role = localStorage.getItem("role");

let courses = [];

// window.addEventListener("DOMContentLoaded", () => {
//     if (role !== "Admin") {
//         document.getElementById("addCourseSection")?.remove();
//     }
// });

// COMPLETED 
function getCompleted() {
    return JSON.parse(localStorage.getItem("completed_" + userId)) || [];
}

function saveCompleted(data) {
    localStorage.setItem("completed_" + userId, JSON.stringify(data));
}

// ─── LOAD COURSES ────────────────────────────────────────
async function loadCourses() {
    try {
        courses = await getCourses();
        console.log("Courses:", courses);

        renderCourses();
        renderProgress();

    } catch (err) {
        console.error("Load courses error:", err);
    }
}

// ─── ADD COURSE ──────────────────────────────────────────
async function addCourse() {
    const title = document.getElementById("courseTitle")?.value.trim();
    const description = document.getElementById("courseDesc")?.value.trim();

    if (!title || !description) {
        alert("Enter title and description");
        return;
    }

    try {
        await createCourse({
            title,
            description,
            createdBy: parseInt(userId)
        });

        document.getElementById("courseTitle").value = "";
        document.getElementById("courseDesc").value = "";

        await loadCourses();
    } catch (err) {
        alert("Error adding course: " + err.message);
    }
}

// ─── UPDATE COURSE ───────────────────────────────────────
async function editCourse(id) {
    const course = courses.find(c => c.courseId === id);
    if (!course) return;

    const newTitle = prompt("New title:", course.title);
    const newDesc = prompt("New description:", course.description);
    if (!newTitle) return;

    try {
        await updateCourse(id, {
            title: newTitle,
            description: newDesc || course.description,
            createdBy: parseInt(userId)
        });

        await loadCourses();
    } catch (err) {
        alert("Error updating course: " + err.message);
    }
}

// ─── DELETE COURSE ───────────────────────────────────────
async function deleteCourseUI(id) {
    if (!confirm("Delete this course?")) return;

    try {
        await deleteCourse(id);
        await loadCourses();
    } catch (err) {
        alert("Error deleting course: " + err.message);
    }
}

// ─── COMPLETE COURSE ─────────────────────────────────────
async function toggleCourse(id, isCompleted) {
    try {
        if (isCompleted) {
            await undoCourseComplete(userId, id);
        } else {
            await markCourseComplete(userId, id);
        }

        loadCourses();

    } catch (err) {
        alert(err.message);
    }
}

// ─── LESSONS MODAL ───────────────────────────────────────
async function viewLessons(courseId, courseTitle) {
    const modal = document.getElementById("lessonsModal");
    const body = document.getElementById("lessonsBody");
    const title = document.getElementById("lessonsModalTitle");

    if (!modal) return;

    title.textContent = `Lessons — ${courseTitle}`;
    body.innerHTML = `<div class="spinner-border text-primary"></div>`;

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();

    try {
        const lessons = await getLessons(courseId);

        if (lessons.length === 0) {
            body.innerHTML = `<p class="text-muted">No lessons yet.</p>`;
        } else {
            body.innerHTML = lessons.map(l => `
                <div class="card mb-3 border-0 shadow-sm">
                    <div class="card-body">

                        <h5 class="fw-bold text-primary">${escHtml(l.title)}</h5>

                        <pre style="
                            white-space: pre-wrap;
                            background: #f8f9fa;
                            padding: 12px;
                            border-radius: 8px;
                            font-size: 14px;
                        ">
${escHtml(l.content || "")}
                        </pre>

                        ${role === "Admin" ? `
                            <div class="mt-2 d-flex gap-2">
                                <button 
                                    class="btn btn-warning btn-sm edit-lesson-btn"
                                    data-id="${l.lessonId}"
                                    data-title="${escHtml(l.title)}"
                                    data-content="${escHtml(l.content || "")}"
                                    data-course="${l.courseId}">
                                    ✏️ Edit
                                </button>

                                <button onclick="deleteLessonUI(${l.lessonId}, ${l.courseId})"
                                    class="btn btn-danger btn-sm">
                                    🗑 Delete
                                </button>
                            </div>
                        ` : ''}

                    </div>
                </div>
            `).join("");
        }

        setTimeout(() => {
            document.querySelectorAll(".edit-lesson-btn").forEach(btn => {
                btn.addEventListener("click", () => {
                    editLessonUI(
                        btn.dataset.id,
                        btn.dataset.title,
                        btn.dataset.content,
                        btn.dataset.course
                    );
                });
            });
        }, 0);

        // ➕ ADD LESSON FORM
        if (role === "Admin") {
            body.innerHTML += `
                <hr>
                <div class="card p-3 mt-3 shadow-sm">
                    <h5 class="mb-3 text-success">Add Lesson</h5>

                    <input id="newLessonTitle"
                        class="form-control mb-2"
                        placeholder="Lesson title">

                    <textarea id="newLessonContent"
                        class="form-control mb-3"
                        rows="5"
                        placeholder="Write lesson content here..."></textarea>

                    <button onclick="addLesson(${courseId})"
                        class="btn btn-success w-100">
                        Add Lesson
                    </button>
                </div>
            `;
        }

    } catch (err) {
        body.innerHTML = `<p class="text-danger">${err.message}</p>`;
    }
}

// ─── ADD LESSON ──────────────────────────────────────────
async function addLesson(courseId) {
    const title = document.getElementById("newLessonTitle")?.value.trim();
    const content = document.getElementById("newLessonContent")?.value.trim();

    if (!title) return alert("Enter title");

    try {
        await createLesson(parseInt(userId), { courseId, title, content });

        const course = courses.find(c => c.courseId === courseId);
        viewLessons(courseId, course?.title || "");
    } catch (err) {
        alert(err.message);
    }
}

// ─── EDIT LESSON ─────────────────────────────────────────
async function editLessonUI(id, oldTitle, oldContent, courseId) {
    const newTitle = prompt("Edit Title:", oldTitle);
    const newContent = prompt("Edit Content:", oldContent);

    if (!newTitle) return;

    await updateLesson(id, {
        lessonId: id,
        courseId,
        title: newTitle,
        content: newContent
    });

    alert("Updated!");

    const course = courses.find(c => c.courseId == courseId);
    viewLessons(courseId, course?.title || "");
}

// ─── DELETE LESSON ───────────────────────────────────────
async function deleteLessonUI(id, courseId) {
    if (!confirm("Delete lesson?")) return;

    try {
        await deleteLesson(id);

        // reload lessons properly
        const course = courses.find(c => c.courseId == courseId);
        viewLessons(courseId, course?.title || "");

    } catch (err) {
        alert(err.message);
    }
}

// ─── RENDER COURSES ──────────────────────────────────────
async function renderCourses() {
    const container = document.getElementById("courses");
    if (!container) return;

    let progress = [];
    try {
        progress = await getUserProgress(userId);
    } catch { }

    const completed = progress.filter(p => p.isCompleted).map(p => p.courseId);
    container.innerHTML = "";

    courses.forEach(c => {
        const done = completed.includes(c.courseId);
        const isAdmin = role === "Admin";

        container.innerHTML += `
        <div class="card p-3 mb-3 shadow">
            <h5>${escHtml(c.title)}</h5>
            <p class="text-muted">${escHtml(c.description)}</p>

            <div class="d-flex gap-2 flex-wrap">
                <button onclick="viewLessons(${c.courseId},'${escHtml(c.title)}')" class="btn btn-info btn-sm">Lessons</button>

                <button onclick="toggleCourse(${c.courseId}, ${done})"
                class="btn ${done ? 'btn-secondary' : 'btn-success'} btn-sm">
                ${done ? 'Undo' : 'Mark Complete'}
                </button>

                ${isAdmin ? `
                    <button onclick="editCourse(${c.courseId})" class="btn btn-warning btn-sm">Edit</button>
                    <button onclick="deleteCourseUI(${c.courseId})" class="btn btn-danger btn-sm">Delete</button>
                ` : ''}
            </div>
        </div>`;
    });
}

// ─── PROGRESS ────────────────────────────────────────────
async function renderProgress() {
    const bar = document.getElementById("progressBarBootstrap");
    const text = document.getElementById("progressText");

    let progress = [];
    try {
        progress = await getUserProgress(userId);
    } catch { }

    const completed = progress.filter(p => p.isCompleted).map(p => p.courseId);
    const percent = courses.length ? (completed.length / courses.length) * 100 : 0;

    if (bar) {
        bar.style.width = percent + "%";
        bar.innerText = percent.toFixed(0) + "%";
    }

    if (text) {
        text.innerText = `${completed.length}/${courses.length} completed`;
    }
}

// ─── LOGOUT ──────────────────────────────────────────────
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

// ─── UTIL ────────────────────────────────────────────────
function escHtml(str) {
    return (str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// INIT
loadCourses();