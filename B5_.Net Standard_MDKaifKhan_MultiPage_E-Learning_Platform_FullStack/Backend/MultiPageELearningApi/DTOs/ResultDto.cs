namespace MultiPageELearningApi.Dtos;
public class ResultDto
{
    public int ResultId { get; set; }
    public int UserId { get; set; }
    public int QuizId { get; set; }
    public int Score { get; set; }
    public DateTime AttemptDate { get; set; }

}