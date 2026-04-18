using System.ComponentModel.DataAnnotations;
namespace MultiPageELearningApi.Dtos;
public class QuestionDto
{
    public int QuestionId { get; set; }

    [Required(ErrorMessage = "Quiz ID is required")]
    [Range(1, int.MaxValue, ErrorMessage = "Invalid quiz ID")]
    public int QuizId { get; set; }

    [Required(ErrorMessage = "Question text is required")]
    public string QuestionText { get; set; }

    [Required(ErrorMessage = "Option A is required")]
    public string OptionA { get; set; }

    [Required(ErrorMessage = "Option B is required")]
    public string OptionB { get; set; }

    [Required(ErrorMessage = "Option C is required")]
    public string OptionC { get; set; }

    [Required(ErrorMessage = "Option D is required")]
    public string OptionD { get; set; }

    [Required(ErrorMessage = "Correct answer is required")]
    [RegularExpression("A|B|C|D", ErrorMessage = "Correct answer must be A, B, C or D")]
    public string CorrectAnswer { get; set; }
}