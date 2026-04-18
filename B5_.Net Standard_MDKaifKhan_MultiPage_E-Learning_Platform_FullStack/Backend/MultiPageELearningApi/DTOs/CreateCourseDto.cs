using System.ComponentModel.DataAnnotations;
namespace MultiPageELearningApi.Dtos;
public class CreateCourseDto
{
   [Required(ErrorMessage = "Course title is required")]
    [StringLength(100, ErrorMessage = "Title cannot exceed 100 characters")]
    public string Title { get; set; }

    [Required(ErrorMessage = "Course description is required")]
    public string Description { get; set; }

    [Required(ErrorMessage = "Creator ID is required")]
    [Range(1, int.MaxValue, ErrorMessage = "Invalid user ID")]
    public int CreatedBy { get; set; }
}