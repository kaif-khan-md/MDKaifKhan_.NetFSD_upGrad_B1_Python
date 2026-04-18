using System.ComponentModel.DataAnnotations;
namespace MultiPageELearningApi.Dtos;
public class QuizDto
{
     public int QuizId { get; set; }

    [Required(ErrorMessage = "Course ID is required")]
    [Range(1, int.MaxValue, ErrorMessage = "Invalid course ID")]
    public int CourseId { get; set; }

    [Required(ErrorMessage = "Quiz title is required")]
    [StringLength(100, ErrorMessage = "Title cannot exceed 100 characters")]
    public string Title { get; set; }
}