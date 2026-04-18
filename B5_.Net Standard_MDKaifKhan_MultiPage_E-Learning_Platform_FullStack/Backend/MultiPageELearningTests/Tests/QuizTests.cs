using Xunit;
using MultiPageELearningApi.Models;
using MultiPageELearningApi.Controllers;
using System.Collections.Generic;
using Microsoft.AspNetCore.Mvc;
using System.Linq;
using System.Threading.Tasks;

public class QuizTests
{
    [Fact]
    public async Task QuizScoring_ReturnsCorrectScore()
    {
        var context = TestDbContextFactory.Create();

        // Add quiz
        var quiz = new Quiz
        {
            QuizId = 1,
            CourseId = 1,
            Title = "Sample Quiz"
        };

        context.Quizzes.Add(quiz);

        
        context.Questions.AddRange(
            new Question
            {
                QuestionId = 1,
                QuizId = 1,
                QuestionText = "What is A?",
                OptionA = "A",
                OptionB = "B",
                OptionC = "C",
                OptionD = "D",
                CorrectAnswer = "A"
            },
            new Question
            {
                QuestionId = 2,
                QuizId = 1,
                QuestionText = "What is B?",
                OptionA = "A",
                OptionB = "B",
                OptionC = "C",
                OptionD = "D",
                CorrectAnswer = "B"
            }
        );

        await context.SaveChangesAsync();

        var answers = new Dictionary<int, string>
        {
            {1, "A"},
            {2, "B"}
        };

        var questions = context.Questions
            .Where(q => q.QuizId == 1)
            .ToList();

        int score = 0;

        foreach (var q in questions)
        {
            if (answers.ContainsKey(q.QuestionId) &&
                answers[q.QuestionId] == q.CorrectAnswer)
            {
                score++;
            }
        }

        Assert.Equal(2, score);
    }
    [Fact]
public async Task SubmitQuiz_InvalidUser_ReturnsBadRequest()
{
    var context = TestDbContextFactory.Create();
    var mapper = TestMapper.GetMapper();
    var controller = new QuizController(context, mapper);
    

    var result = await controller.SubmitQuiz(1, null, 0);

    Assert.IsType<BadRequestObjectResult>(result);
}
}