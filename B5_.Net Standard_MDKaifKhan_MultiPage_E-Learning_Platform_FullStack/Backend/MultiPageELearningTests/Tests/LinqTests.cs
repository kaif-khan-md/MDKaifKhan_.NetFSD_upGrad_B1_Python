using Xunit;
using MultiPageELearningApi.Data;
using Microsoft.AspNetCore.Mvc;
using MultiPageELearningApi.Models;
using Microsoft.EntityFrameworkCore;
using System.Linq;
using System.Threading.Tasks;

public class LinqTests
{
    [Fact]
    public async Task FilterCourses_ByUser()
    {
        var context = TestDbContextFactory.Create();

        context.Courses.AddRange(
            new Course
            {
                Title = "C1",
                Description = "Desc1",
                CreatedBy = 1,
                CreatedAt = DateTime.Now
            },
            new Course
            {
                Title = "C2",
                Description = "Desc2",
                CreatedBy = 2,
                CreatedAt = DateTime.Now
            }
        );

        await context.SaveChangesAsync();

        var result = context.Courses
            .Where(c => c.CreatedBy == 1)
            .ToList();

        Assert.Single(result);
    }
}