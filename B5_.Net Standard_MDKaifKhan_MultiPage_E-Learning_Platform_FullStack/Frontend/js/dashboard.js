
// const role = localStorage.getItem("role");

if (!userId) window.location.href = "login.html";

// LOAD COURSES INTO TABLE
async function loadDashboardCourses() {
    try {
        const courses = await getCourses();
        const table = document.getElementById("courseTable");

        if (!courses.length) {
            table.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center text-muted">
                        No courses available
                    </td>
                </tr>
            `;
            return;
        }

        //GET PROGRESS FROM DB
        let progress = [];
        try {
            progress = await getUserProgress(userId);
        } catch {}

        const rows = await Promise.all(courses.map(async c => {

            let lessonCount = 0;

            try {
                const lessons = await getLessons(c.courseId);
                lessonCount = lessons.length;
            } catch {}

            const isDone = progress.some(p =>
                p.courseId === c.courseId && p.isCompleted
            );

            return `
                <tr style="cursor:pointer"
                    onclick="viewLessons(${c.courseId}, '${c.title.replace(/'/g, "\\'")}')">

                    <td>${c.title}</td>

                    <td>${lessonCount}</td>

                    <td>
                        <span class="badge ${isDone ? "bg-success" : "bg-warning"}">
                            ${isDone ? "Completed" : "In Progress"}
                        </span>
                    </td>
                </tr>
            `;
        }));

        table.innerHTML = rows.join("");

    } catch (err) {
        console.error("Dashboard error:", err);
    }
}

// PROGRESS BAR
async function updateDashboardProgress() {
    try {
        const courses = await getCourses();
        const progress = await getUserProgress(userId);

        const completed = progress.filter(p => p.isCompleted);

        const percent = courses.length
            ? (completed.length / courses.length) * 100
            : 0;

        const bar = document.getElementById("progressBarBootstrap");
        const text = document.getElementById("progressText");

        if (bar) {
            bar.style.width = percent + "%";
            bar.innerText = percent.toFixed(0) + "%";
        }

        if (text) {
            text.innerText = `${completed.length}/${courses.length} completed`;
        }

    } catch (err) {
        console.error("Progress error:", err);
    }
}

function renderChart(completed, total, avgScore) {
    const ctx = document.getElementById("progressChart");

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Remaining'],
            datasets: [{
                data: [completed, total - completed]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // 🔥 IMPORTANT
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}
// ANALYTICS
async function loadDashboardAnalytics() {
    const cards = document.getElementById("analyticsCards");

    try {
        const sortedData   = await getAnalyticsCoursesSorted().catch(()=>[]);
        const lessonsData  = await getAnalyticsCoursesWithLessons().catch(()=>[]);
        const aboveAvgData = await getAnalyticsAboveAverage().catch(()=>[]);
        const combinedData = await getAnalyticsCombinedResults().catch(()=>[]);

        cards.innerHTML = `
        <div class="col-md-3 col-6">
            <div class="card text-center p-3 border-primary">
                <h2>${sortedData.length}</h2>
                <p class="small">Total Courses</p>
            </div>
        </div>

        <div class="col-md-3 col-6">
            <div class="card text-center p-3 border-success">
                <h2>${lessonsData.length}</h2>
                <p class="small">Courses w/ Lessons</p>
            </div>
        </div>

        <div class="col-md-3 col-6">
            <div class="card text-center p-3 border-warning">
                <h2>${aboveAvgData.length}</h2>
                <p class="small">Above Avg Users</p>
            </div>
        </div>

        <div class="col-md-3 col-6">
            <div class="card text-center p-3 border-info">
                <h2>${combinedData.length}</h2>
                <p class="small">Combined Results</p>
            </div>
        </div>`;
    } catch (err) {
        cards.innerHTML = `<p class="text-danger">Analytics failed</p>`;
        console.error(err);
    }
}
async function loadUserAnalytics() {
    try {
        const courses = await getCourses();
        const progress = await getUserProgress(userId);
        const res = await fetch(`${BASE_URL}/results/user-analytics/${userId}`);
        const quizData = await res.json();

        const completed = progress.filter(p => p.isCompleted).length;
        const total = courses.length;
        const percent = total ? (completed / total) * 100 : 0;

        document.getElementById("userAnalytics").innerHTML = `
            <div class="col-md-3">
                <div class="card p-3 text-center">
                    <h5>${total}</h5>
                    <small>Courses</small>
                </div>
            </div>

            <div class="col-md-3">
                <div class="card p-3 text-center">
                    <h5>${completed}</h5>
                    <small>Completed</small>
                </div>
            </div>

            <div class="col-md-3">
                <div class="card p-3 text-center">
                    <h5>${percent.toFixed(0)}%</h5>
                    <small>Progress</small>
                </div>
            </div>

            <div class="col-md-3">
                <div class="card p-3 text-center">
                    <h5>${quizData.averageScore}</h5>
                    <small>Avg Quiz Score</small>
                </div>
            </div>
        `;

        renderChart(completed, total, quizData.averageScore);

    } catch (err) {
        console.error(err);
    }
}

function renderChart(completed, total, avgScore) {
    const ctx = document.getElementById("progressChart");

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Remaining'],
            datasets: [{
                data: [completed, total - completed]
            }]
        }
    });
}
// INIT
loadDashboardCourses();
updateDashboardProgress();
loadUserAnalytics();  