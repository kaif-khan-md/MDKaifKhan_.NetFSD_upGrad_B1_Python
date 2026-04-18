using System;

namespace MultiPageELearningApi.Models;

public class Course
{
    public int CourseId { get; set; }
    public string Title { get; set; }
    public string Description { get; set; }
    public int CreatedBy { get; set; }
    public DateTime CreatedAt { get; set; }

    public User User { get; set; }
    public ICollection<Lesson> Lessons { get; set; }
    public ICollection<Quiz> Quizzes { get; set; }
}
