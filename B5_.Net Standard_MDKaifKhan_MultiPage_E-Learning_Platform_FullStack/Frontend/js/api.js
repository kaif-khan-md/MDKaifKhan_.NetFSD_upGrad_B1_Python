const BASE_URL = "http://localhost:5190/api";

// USERS 
async function registerUser(data) {
    const res = await fetch(`${BASE_URL}/users/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function registerAdmin(data) {
    const res = await fetch(`${BASE_URL}/users/register-admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function loginUser(data) {
    const res = await fetch(`${BASE_URL}/users/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getUser(id) {
    const res = await fetch(`${BASE_URL}/users/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function updateUser(id, data) {
    const res = await fetch(`${BASE_URL}/users/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
}

async function deleteUser(id) {
    const res = await fetch(`${BASE_URL}/users/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await res.text());
}

// COURSES
async function getCourses() {
    const res = await fetch(`${BASE_URL}/courses`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getCourse(id) {
    const res = await fetch(`${BASE_URL}/courses/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function createCourse(data) {
    const res = await fetch(`${BASE_URL}/courses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function updateCourse(id, data) {
    const res = await fetch(`${BASE_URL}/courses/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
}

async function deleteCourse(id) {
    const res = await fetch(`${BASE_URL}/courses/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await res.text());
}

// LESSONS
async function getLessons(courseId) {
    const res = await fetch(`${BASE_URL}/courses/${courseId}/lessons`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function createLesson(userId, data) {
    const res = await fetch(`${BASE_URL}/lessons?userId=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function updateLesson(id, data) {
    const res = await fetch(`${BASE_URL}/lessons/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
}

async function deleteLesson(id) {
    const res = await fetch(`${BASE_URL}/lessons/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await res.text());
}

//  QUIZZES 
async function getQuizByCourse(courseId) {
    const res = await fetch(`${BASE_URL}/quizzes/${courseId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getQuestions(quizId) {
    const res = await fetch(`${BASE_URL}/quizzes/${quizId}/questions`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function createQuiz(userId, data) {
    const res = await fetch(`${BASE_URL}/quizzes?userId=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function createQuestion(userId, data) {
    const res = await fetch(`${BASE_URL}/questions?userId=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function updateQuestion(id, data) {
    const res = await fetch(`${BASE_URL}/questions/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
}

async function deleteQuestion(id) {
    const res = await fetch(`${BASE_URL}/questions/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await res.text());
}

async function submitQuizAPI(quizId, userId, answers) {
    const res = await fetch(`${BASE_URL}/quizzes/${quizId}/submit?userId=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(answers)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

// RESULTS 
async function getResults(userId) {
    const res = await fetch(`${BASE_URL}/results/${userId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getResult(id) {
    const res = await fetch(`${BASE_URL}/results/single/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function deleteResult(id) {
    const res = await fetch(`${BASE_URL}/results/delete/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await res.text());
}

// ANALYTICS 
async function getAnalyticsCoursesByUser(userId) {
    const res = await fetch(`${BASE_URL}/analytics/courses-by-user/${userId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getAnalyticsCoursesSorted() {
    const res = await fetch(`${BASE_URL}/analytics/courses-sorted`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getAnalyticsCoursesWithLessons() {
    const res = await fetch(`${BASE_URL}/analytics/courses-with-lessons`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getAnalyticsUserPerformance() {
    const res = await fetch(`${BASE_URL}/analytics/user-performance`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getAnalyticsAboveAverage() {
    const res = await fetch(`${BASE_URL}/analytics/above-average`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function getAnalyticsCombinedResults() {
    const res = await fetch(`${BASE_URL}/analytics/combined-results`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function markCourseComplete(userId, courseId) {
    await fetch(`${BASE_URL}/progress?userId=${userId}&courseId=${courseId}`, {
        method: "POST"
    });
}

async function undoCourseComplete(userId, courseId) {
    await fetch(`${BASE_URL}/progress/undo?userId=${userId}&courseId=${courseId}`, {
        method: "PUT"
    });
}

async function getUserProgress(userId) {
    const res = await fetch(`${BASE_URL}/progress/${userId}`);
    return res.json();
}

async function getAllProgress() {
    const res = await fetch(`${BASE_URL}/progress/all`);
    return res.json();
}

async function getQuiz(id) {
    const res = await fetch(`${BASE_URL}/quizzes/single/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}