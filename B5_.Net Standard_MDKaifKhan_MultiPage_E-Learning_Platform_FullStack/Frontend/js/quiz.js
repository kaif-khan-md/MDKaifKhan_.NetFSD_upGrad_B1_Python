const userId = localStorage.getItem("userId");
if (!userId) window.location.href = "login.html";
const role = localStorage.getItem("role");


let questionsData = [];
let userAnswers   = {};
let currentQuizId = null;

// ─── INIT ────────────────────────────────────────────────
window.onload = async () => {
    await loadCourseSelector();
};

// ─── STEP 1: Pick a course ───────────────────────────────
async function loadCourseSelector() {
    const container = document.getElementById("quizContainer");
    if (!container) return;

    container.innerHTML = `<div class="spinner-border text-primary"></div><p class="mt-2">Loading courses…</p>`;

    try {
        const courses = await getCourses();

        if (!courses.length) {
            container.innerHTML = `<p class="text-muted">No courses available.</p>`;
            return;
        }

        container.innerHTML = `
            <p class="text-muted mb-2">Select a course to load its quiz:</p>
            <div class="row g-3">
                ${courses.map(c => `
                <div class="col-md-4">
                    <div class="card p-3 h-100 d-flex flex-column justify-content-between shadow-sm">
                        <div>
                            <h6 class="mb-1">${c.title}</h6>
                            <p class="text-muted small">${c.description || ""}</p>
                        </div>
                       ${role === "Admin" ? `
                            <button onclick="openQuizBuilder(${c.courseId})" class="btn btn-success btn-sm mt-2">
                                Create / Manage Quiz
                            </button>
                        ` : `
                            <button onclick="checkAndStartQuiz(${c.courseId})" class="btn btn-primary btn-sm mt-2">
                                Start Quiz
                            </button>
                        `}
                    </div>
                </div>`).join("")}
            </div>`;
    } catch (err) {
        container.innerHTML = `<p class="text-danger">Error loading courses: ${err.message}</p>`;
    }
}

// ─── STEP 2: Load quiz for chosen course ─────────────────
async function loadQuizForCourse(courseId) {
    resetQuizState();
    const container = document.getElementById("quizContainer");
    container.innerHTML = `<div class="spinner-border text-primary"></div><p class="mt-2">Loading quiz…</p>`;
    userAnswers = {};

    try {
        // Get quiz metadata for this course
        const quiz = await getQuizByCourse(courseId);

        // quiz may be an object or array depending on backend
        const quizId = Array.isArray(quiz) ? quiz[0]?.quizId : quiz.quizId;
        if (!quizId) {
            container.innerHTML = `<p class="text-muted">No quiz found for this course.</p>
                <button onclick="loadCourseSelector()" class="btn btn-secondary btn-sm mt-2">← Back</button>`;
            return;
        }

        currentQuizId = quizId;
        const questions = await getQuestions(quizId);
        questionsData   = questions;

        if (!questions.length) {
            container.innerHTML = `<p class="text-muted">This quiz has no questions yet.</p>
                <button onclick="loadCourseSelector()" class="btn btn-secondary btn-sm mt-2">← Back</button>`;
            return;
        }

        renderQuiz(questions);
    } catch (err) {
        container.innerHTML = `<p class="text-danger">Error loading quiz: ${err.message}</p>
            <button onclick="loadCourseSelector()" class="btn btn-secondary btn-sm mt-2">← Back</button>`;
    }
}

// ─── RENDER QUESTIONS ────────────────────────────────────
function renderQuiz(questions) {
    const container = document.getElementById("quizContainer");
    if (!container) return;

    container.innerHTML = `
        <button onclick="goBackToCourses()" class="btn btn-outline-secondary btn-sm mb-3">← Back to Courses</button>
        ${questions.map((q, i) => `
        <div class="card p-3 mb-3 shadow-sm">
            <h6 class="mb-3"><span class="badge bg-primary me-2">Q${i + 1}</span>${q.questionText}</h6>
            ${["A", "B", "C", "D"].filter(opt => q["option" + opt]).map(opt => `
            <div class="form-check mb-1">
                <input class="form-check-input" type="radio"
                    name="q${i}"
                    id="q${i}${opt}"
                    onchange="selectAnswer(${q.questionId}, '${escHtml(q['option' + opt])}')">
                <label class="form-check-label" for="q${i}${opt}">
                    <span class="badge bg-light text-dark border me-1">${opt}</span>
                    ${q["option" + opt]}
                </label>
            </div>`).join("")}
        </div>`).join("")}`;

    document.getElementById("result").innerHTML = "";
}

function goBackToCourses() {
    resetQuizState();  
    loadCourseSelector();
}

// ─── SELECT ANSWER ───────────────────────────────────────
function selectAnswer(id, answer) {
    userAnswers[id] = answer;
}

// ─── SUBMIT ──────────────────────────────────────────────
async function submitQuiz() {
    if (!currentQuizId) { alert("Please select a quiz first."); return; }

    if (Object.keys(userAnswers).length !== questionsData.length) {
        alert(`Please answer all ${questionsData.length} question(s) before submitting.`);
        return;
    }

    try {
        const res = await submitQuizAPI(currentQuizId, userId, userAnswers);

        const score   = res.score   ?? res.Score   ?? "N/A";
        const total   = res.total   ?? res.Total   ?? questionsData.length;
        const percent = total ? Math.round((score / total) * 100) : 0;
        const grade   = calculateGrade(percent);

        document.getElementById("result").innerHTML = `
            <div class="text-center">
                <h4 class="mb-1">Quiz Submitted! 🎉</h4>
                <p class="mb-1">Score: <strong>${score} / ${total}</strong></p>
                <p class="mb-1">Percentage: <strong>${percent}%</strong></p>
                <p class="mb-0">Grade: <span class="badge bg-${gradeColor(grade)} fs-6">${grade}</span></p>
                
            </div>`;
    } catch (err) {
        document.getElementById("result").innerHTML =
            `<p class="text-danger">Submission failed: ${err.message}</p>`;
    }
}

// ─── GRADE HELPERS ───────────────────────────────────────
function calculateGrade(percent) {
    if (percent >= 90) return "A";
    if (percent >= 80) return "B";
    if (percent >= 70) return "C";
    if (percent >= 60) return "D";
    return "F";
}

function gradeColor(grade) {
    return { A: "success", B: "primary", C: "warning", D: "warning", F: "danger" }[grade] || "secondary";
}

// ─── LOGOUT ──────────────────────────────────────────────
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

// ─── UTIL ────────────────────────────────────────────────
function escHtml(str) {
    return (str || "").replace(/'/g, "\\'");
}
async function openQuizBuilder(courseId) {
    const container = document.getElementById("quizContainer");

    try {
        const quizzes = await getQuizByCourse(courseId);

        if (!quizzes || (Array.isArray(quizzes) && quizzes.length === 0)) {
            container.innerHTML = `
                <h4>Create First Quiz</h4>

                <input id="quizTitle" class="form-control mb-2" placeholder="Enter Quiz Title">

                <button onclick="createQuizForCourse(${courseId})" class="btn btn-success">
                    ➕ Create Quiz
                </button>
            `;
            return;
        }

        const quizList = Array.isArray(quizzes) ? quizzes : [quizzes];

        container.innerHTML = `
            <h4>Manage Quizzes</h4>

            <div class="mb-3">
                <input id="quizTitle" class="form-control mb-2" placeholder="New Quiz Title">
                <button onclick="createQuizForCourse(${courseId})" class="btn btn-success btn-sm">
                    ➕ Add New Quiz
                </button>
            </div>

            <div class="list-group mb-3">
                ${quizList.map(q => `
                    <button class="list-group-item list-group-item-action"
                        onclick="selectQuiz(${q.quizId}, '${q.title}')">
                        📘 ${q.title}
                    </button>
                `).join("")}
            </div>

            <div id="selectedQuizSection"></div>
        `;
    } catch (err) {
        container.innerHTML = `<p class="text-danger">${err.message}</p>`;
    }
}
async function createQuizForCourse(courseId) {
    const title = document.getElementById("quizTitle").value.trim();

    if (!title) {
        alert("Enter quiz title");
        return;
    }

    try {
        await createQuiz(userId, {
            courseId,
            title
        });

        alert("Quiz created!");

        openQuizBuilder(courseId); // refresh list

    } catch (err) {
        alert(err.message);
    }
}

function renderQuestionForm() {
    const el = document.getElementById("questionBuilder");

    el.innerHTML = `
        <div class="card p-3">
            <h5>Add Question</h5>

            <input id="qText" class="form-control mb-2" placeholder="Question">

            <input id="optA" class="form-control mb-2" placeholder="Option A">
            <input id="optB" class="form-control mb-2" placeholder="Option B">
            <input id="optC" class="form-control mb-2" placeholder="Option C">
            <input id="optD" class="form-control mb-2" placeholder="Option D">

            <select id="correct" class="form-control mb-3">
                <option value="">Select Correct Answer</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
            </select>

            <button onclick="addQuestion()" class="btn btn-primary w-100">
                Add Question
            </button>
        </div>
    `;
}

async function addQuestion() {
    const questionText = document.getElementById("qText").value.trim();
    const optionA = document.getElementById("optA").value.trim();
    const optionB = document.getElementById("optB").value.trim();
    const optionC = document.getElementById("optC").value.trim();
    const optionD = document.getElementById("optD").value.trim();
    const correct = document.getElementById("correct").value;

    if (!questionText || !optionA || !optionB || !optionC || !optionD || !correct) {
        alert("Fill all fields");
        return;
    }

    const correctAnswer =
        correct === "A" ? optionA :
        correct === "B" ? optionB :
        correct === "C" ? optionC :
        optionD;

    try {
        await createQuestion(userId, {
            quizId: currentQuizId,
            questionText,
            optionA,
            optionB,
            optionC,
            optionD,
            correctAnswer
        });

        alert("Question added");

        renderQuestionForm();
        document.getElementById("qText").value = "";
        document.getElementById("optA").value = "";
        document.getElementById("optB").value = "";
        document.getElementById("optC").value = "";
        document.getElementById("optD").value = "";
        document.getElementById("correct").value = "";
        loadExistingQuestions();
    } catch (err) {
        alert(err.message);
    }
}
async function loadExistingQuestions() {
    const container = document.getElementById("questionsList");

    const questions = await getQuestions(currentQuizId);

    if (!questions.length) {
        container.innerHTML = `<p class="text-muted">No questions yet</p>`;
        return;
    }

    container.innerHTML = questions.map(q => `
        <div class="card p-3 mb-2">
            <strong>${q.questionText}</strong>

            <ul>
                <li>A: ${q.optionA}</li>
                <li>B: ${q.optionB}</li>
                <li>C: ${q.optionC}</li>
                <li>D: ${q.optionD}</li>
            </ul>

            <p><strong>Correct:</strong> ${q.correctAnswer}</p>

            <div class="d-flex gap-2">
                <button onclick="editQuestionUI(${q.questionId})" class="btn btn-warning btn-sm">Edit</button>
                <button onclick="deleteQuestionUI(${q.questionId})" class="btn btn-danger btn-sm">Delete</button>
            </div>
        </div>
    `).join("");
}

async function editQuestionUI(id) {
    const text = prompt("New Question:");
    const optionA = prompt("Option A:");
    const optionB = prompt("Option B:");
    const optionC = prompt("Option C:");
    const optionD = prompt("Option D:");
    const correct = prompt("Correct Answer:");

    if (!text) return;

    try {
        await updateQuestion(id, {
            questionId: id,
            quizId: currentQuizId,
            questionText: text,
            optionA,
            optionB,
            optionC,
            optionD,
            correctAnswer: correct
        });

        alert("Updated!");
        loadExistingQuestions();

    } catch (err) {
        alert(err.message);
    }
}

async function deleteQuestionUI(id) {
    if (!confirm("Delete this question?")) return;

    try {
        await deleteQuestion(id);
        loadExistingQuestions();
    } catch (err) {
        alert(err.message);
    }
}

async function selectQuiz(quizId, title) {
    currentQuizId = quizId;

    const section = document.getElementById("selectedQuizSection");

    const questions = await getQuestions(quizId);

    section.innerHTML = `
        <div class="card p-3">
            <h5>📘 ${title}</h5>
            <p class="text-muted">Total Questions: ${questions.length}</p>

            <div id="questionBuilder"></div>

            <hr>
            <h6>📋 Questions</h6>
            <div id="questionsList"></div>
        </div>
    `;

    renderQuestionForm();
    loadExistingQuestions();
}

async function checkAndStartQuiz(courseId) {
    try {
        const quiz = await getQuizByCourse(courseId);
        const quizId = Array.isArray(quiz) ? quiz[0]?.quizId : quiz.quizId;

        const results = await getResults(userId);
        const already = results.some(r => r.quizId === quizId);

        if (already) {
            alert("You have already attempted this quiz.");
            return;
        }

        loadQuizForCourse(courseId);
    } catch (err) {
        loadQuizForCourse(courseId);
    }
}

function resetQuizState() {
    questionsData = [];
    userAnswers = {};
    currentQuizId = null;

    const result = document.getElementById("result");
    if (result) result.innerHTML = "";

    const submit = document.getElementById("submitSection");
    if (submit) submit.style.display = "none";
}