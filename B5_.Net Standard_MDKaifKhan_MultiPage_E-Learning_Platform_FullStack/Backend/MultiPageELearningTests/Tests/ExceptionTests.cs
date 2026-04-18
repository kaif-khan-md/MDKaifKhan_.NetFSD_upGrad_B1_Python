using Xunit;
using MultiPageELearningApi.Data;
using MultiPageELearningApi.Repositories;
using MultiPageELearningApi.Controllers;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Threading.Tasks;
using System.Collections.Generic;

public class ExceptionTests
{
    [Fact]
    public async Task InvalidQuiz_ReturnsNotFound()
    {
        var context = TestDbContextFactory.Create();
        var mapper = TestMapper.GetMapper();
        var controller = new QuizController(context, mapper);

        var answers = new Dictionary<int, string>
            {
                {1, "A"} // dummy answer
            };

var result = await controller.SubmitQuiz(999, answers, 1);

        var notFound = Assert.IsType<NotFoundObjectResult>(result);
        var value = notFound.Value.ToString();
        Assert.Contains("Quiz not found", value);
    }
}