namespace MultiPageELearningApi.Models;
public class CourseProgress
{
    public int Id { get; set; }

    public int UserId { get; set; }
    public int CourseId { get; set; }

    public bool IsCompleted { get; set; }

    public User User { get; set; }
    public Course Course { get; set; }
}