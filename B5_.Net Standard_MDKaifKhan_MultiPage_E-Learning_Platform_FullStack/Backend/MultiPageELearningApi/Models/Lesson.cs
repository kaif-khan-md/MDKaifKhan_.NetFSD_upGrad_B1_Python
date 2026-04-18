using System;

namespace MultiPageELearningApi.Models;

public class Lesson
{
    public int LessonId { get; set; }
    public int CourseId { get; set; }
    public string Title { get; set; }
    public string Content { get; set; }
    public int OrderIndex { get; set; }

    public Course Course { get; set; }
}
