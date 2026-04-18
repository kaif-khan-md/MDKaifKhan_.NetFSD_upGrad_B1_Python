// NAV ACTIVE LINK
const links = document.querySelectorAll(".nav-item-link");
const currentPage = window.location.pathname.split("/").pop();

links.forEach(link => {
    if (link.getAttribute("href") === currentPage) {
        link.classList.add("fw-bold", "text-warning");
    }
});

// ADMIN LINK
window.addEventListener("DOMContentLoaded", () => {
    const role = localStorage.getItem("role");

    if (role === "Admin") {
        const adminLink = document.getElementById("adminLink");
        if (adminLink) adminLink.style.display = "inline";
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const page = window.location.pathname.split("/").pop();

    const title = document.getElementById("pageTitle");
    const subtitle = document.getElementById("pageSubtitle");

    if (!title || !subtitle) return;

    switch (page) {
        case "dashboard.html":
            title.innerText = "Dashboard";
            subtitle.innerText = "Welcome back";
            break;

        case "courses.html":
            title.innerText = "Courses";
            subtitle.innerText = "Explore your learning";
            break;

        case "quiz.html":
            title.innerText = "Quiz";
            subtitle.innerText = "Test your knowledge";
            break;

        case "profile.html":
            title.innerText = "Profile";
            subtitle.innerText = "Manage your account";
            break;

        case "admin.html":
            title.innerText = "Admin Panel";
            subtitle.innerText = "Manage platform data";
            break;

        default:
            title.innerText = "E-Learning";
            subtitle.innerText = "Learning platform";
    }
});