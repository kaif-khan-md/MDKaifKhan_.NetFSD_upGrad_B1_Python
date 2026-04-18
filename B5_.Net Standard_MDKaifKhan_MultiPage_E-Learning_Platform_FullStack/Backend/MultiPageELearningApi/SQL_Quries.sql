
-- BASIC QUERIES

-- SELECT
SELECT * FROM Users;

-- WHERE
SELECT * FROM Courses WHERE CreatedBy = 1;

-- ORDER BY
SELECT * FROM Lessons ORDER BY OrderIndex;


-- JOINS

-- INNER JOIN
SELECT u.FullName, r.Score
FROM Users u
INNER JOIN Results r ON u.UserId = r.UserId;

-- LEFT JOIN
SELECT c.Title AS Course, l.Title AS Lesson
FROM Courses c
LEFT JOIN Lessons l ON c.CourseId = l.CourseId;

-- AGGREGATION

-- COUNT
SELECT UserId, COUNT(*) AS TotalAttempts
FROM Results
GROUP BY UserId;

-- AVG
SELECT AVG(Score) AS AverageScore
FROM Results;


-- SUBQUERY


SELECT *
FROM Results
WHERE Score > (SELECT AVG(Score) FROM Results);

-- SET OPERATORS


SELECT Email FROM Users
UNION
SELECT Title FROM Courses;


-- DML OPERATIONS

-- INSERT
INSERT INTO Courses (Title, Description, CreatedBy, CreatedAt)
VALUES ('Sample Course', 'Test Description', 1, GETDATE());

-- UPDATE
UPDATE Courses
SET Title = 'Updated Course'
WHERE CourseId = 1;

-- DELETE
DELETE FROM Courses
WHERE CourseId = 1;