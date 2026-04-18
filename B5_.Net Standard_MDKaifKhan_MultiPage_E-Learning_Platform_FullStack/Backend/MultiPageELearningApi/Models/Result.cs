using System;

namespace MultiPageELearningApi.Models;

public class Result
{
    public int ResultId { get; set; }
    public int UserId { get; set; }
    public int QuizId { get; set; }
    public int Score { get; set; }
    public DateTime AttemptDate { get; set; }

    public User User { get; set; }
    public Quiz Quiz { get; set; }
}
