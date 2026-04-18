# 📘 Full-Stack E-Learning Platform

A complete **Full-Stack E-Learning Platform** built using **ASP.NET Core, SQL Server, and JavaScript**, supporting course management, quizzes, user progress tracking, and admin controls.

---

## Features

### 👤 User Features

* Register & Login (secure password hashing using BCrypt)
* Browse available courses
* View lessons within courses
* Attempt quizzes (only once per quiz)
* View quiz results with score, percentage, and grade
* Track course completion progress

---

### 👑 Admin Features

* Create, update, delete courses
* Add and manage lessons
* Create quizzes and questions
* Edit/delete quiz questions
* Delete quiz results (allow reattempt)

---

### 🧠 Quiz System

* Dynamic quiz loading per course
* Multiple choice questions (A/B/C/D)
* Auto scoring system
* Grade calculation (A–F)
* Attempt restriction (1 attempt per user)
* Admin-controlled reattempt

---

### 📊 Progress Tracking

* Mark course as completed
* Undo completion
* View user progress
* Admin can view all users' progress

---

## 🏗️ Tech Stack

### Backend

* ASP.NET Core 8
* Entity Framework Core
* SQL Server
* AutoMapper
* Repository Pattern
* DTO Layer

### Frontend

* HTML, CSS, Bootstrap
* Vanilla JavaScript

### Testing

* xUnit
* In-Memory Database (EF Core)

---

## 🧱 Project Structure

```
MultiPageELearning/
│
├── MultiPageELearningApi/       # Backend API
├── MultiPageELearningTests/     # Unit & API Tests
├── frontend/                    # HTML, CSS, JS
├── SQL_Queries.sql              # Required SQL queries
└── README.md
```

---

## 🔌 API Endpoints

### 📚 Courses

* GET `/api/courses`
* GET `/api/courses/{id}`
* POST `/api/courses`
* PUT `/api/courses/{id}`
* DELETE `/api/courses/{id}`

### 📖 Lessons

* GET `/api/courses/{courseId}/lessons`
* POST `/api/lessons`
* PUT `/api/lessons/{id}`
* DELETE `/api/lessons/{id}`

### 📝 Quiz

* GET `/api/quizzes/{courseId}`
* POST `/api/quizzes`
* GET `/api/quizzes/{quizId}/questions`
* POST `/api/questions`

### 🎯 Quiz Attempt

* POST `/api/quizzes/{quizId}/submit`
* GET `/api/results/{userId}`

### 👤 Users

* POST `/api/users/register`
* POST `/api/users/login`
* GET `/api/users/{id}`
* PUT `/api/users/{id}`
* DELETE `/api/users/{id}`

---

## 🛡️ Validation & Security

* Input validation using **DataAnnotations**
* Clean error handling (user-friendly messages)
* Password hashing using **BCrypt**
* Prevent duplicate registrations
* Strong password rules (uppercase, lowercase, number)

---

## 🧪 Testing

Test project includes:

* ✅ Course CRUD tests
* ✅ Quiz scoring logic test
* ✅ LINQ filtering test
* ✅ API response validation
* ✅ Exception handling

Run tests:

```bash
dotnet test
```

---

## 🗄️ Database Design

Tables:

* Users
* Courses
* Lessons
* Quizzes
* Questions
* Results

Relationships:

* One User → Many Courses
* One Course → Many Lessons
* One Course → Many Quizzes
* One Quiz → Many Questions
* One User → Many Results

---

## 🧾 SQL Queries

The project includes a `SQL_Queries.sql` file covering:

* SELECT, WHERE, ORDER BY
* INNER JOIN, LEFT JOIN
* GROUP BY, COUNT, AVG
* Subqueries
* UNION
* INSERT, UPDATE, DELETE

---

# ⚙️ Setup Instructions

---

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

---

## 2️⃣ Configure Database (IMPORTANT)

Open:

```
MultiPageELearningApi/appsettings.json
```

Update connection string:

```json
"ConnectionStrings": {
  "DefaultConnection": "Server=.;Database=ElearningDB;Trusted_Connection=True;TrustServerCertificate=True;"
}
```

> ⚠️ Replace `Server=.` with your SQL Server instance if needed.

---

## 3️⃣ Apply Database Migrations

```bash
cd MultiPageELearningApi
dotnet ef database update
```

👉 This will:

* Create database
* Create all required tables

---

## 4️⃣ If Migrations Are Missing (Optional)

```bash
dotnet ef migrations add InitialCreate
dotnet ef database update
```

---

## 5️⃣ Install EF Tool (if needed)

```bash
dotnet tool install --global dotnet-ef
```

---

## 6️⃣ Run Backend

```bash
dotnet run
```

👉 Backend will run on:

```
http://localhost:5000
```

---

## 7️⃣ Run Frontend

Open in browser:

```
frontend/index.html
```

---

## 8️⃣ Configure API URL (IMPORTANT)

Since this project uses plain JavaScript (no build tools), you must manually update API URLs.

👉 Open all frontend JS files (like `api.js`, `quiz.js`, etc.)

Replace API base URL wherever needed:

```js
const API_BASE = "http://localhost:5000/api";
```

👉 After deployment, replace with your live backend URL:

```js
const API_BASE = "https://your-backend-url/api";
```

---




## 🎯 Key Highlights

* Clean layered architecture (Controller → Repository → DB)
* DTO-based API design
* Fully tested backend
* Real-world features (quiz system, progress tracking)
* Production-ready validation

---

## 📌 Future Improvements

* JWT Authentication
* Role-based authorization middleware
* Dashboard analytics with charts
* Responsive UI enhancements
* Live notifications

---

## 👨‍💻 Author

Developed as part of a full-stack learning project to demonstrate real-world application architecture and backend engineering skills.

---

## ⭐ Final Note

This project demonstrates a **complete full-stack system** with backend architecture, API design, validation, testing, and database handling—ready for academic submission and portfolio use.
