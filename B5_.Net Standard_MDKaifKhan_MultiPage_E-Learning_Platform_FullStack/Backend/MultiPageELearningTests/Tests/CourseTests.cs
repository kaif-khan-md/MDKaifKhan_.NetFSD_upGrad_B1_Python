using Xunit;
using Microsoft.AspNetCore.Mvc;
using MultiPageELearningApi.Models;
using MultiPageELearningApi.Data;
using MultiPageELearningApi.Repositories;
using MultiPageELearningApi.Controllers;
using Microsoft.EntityFrameworkCore;
using System.Threading.Tasks;
using System.Collections.Generic;

public class CourseTests
{
    [Fact]
    public async Task CreateCourse_ReturnsSuccess()
    {
        var context = TestDbContextFactory.Create();

        var course = new Course
        {
            Title = "Test Course",
            Description = "Test Description",
            CreatedBy = 1,
            CreatedAt = DateTime.Now
        };

        context.Courses.Add(course);
        await context.SaveChangesAsync();

        Assert.True(course.CourseId > 0);
    }

    [Fact]
    public async Task GetCourses_ReturnsList()
    {
        var context = TestDbContextFactory.Create();

        context.Courses.Add(new Course
        {
            Title = "Course1",
            Description = "Desc1",
            CreatedBy = 1,
            CreatedAt = DateTime.Now
        });

        await context.SaveChangesAsync();

        var result = await context.Courses.ToListAsync();

        Assert.NotEmpty(result);
    }

    [Fact]
    public async Task DeleteCourse_RemovesCourse()
    {
        var context = TestDbContextFactory.Create();

        var course = new Course
        {
            Title = "DeleteMe",
            Description = "Desc",
            CreatedBy = 1,
            CreatedAt = DateTime.Now
        };

        context.Courses.Add(course);
        await context.SaveChangesAsync();

        context.Courses.Remove(course);
        await context.SaveChangesAsync();

        Assert.Empty(context.Courses);
    }

    [Fact]
public async Task GetCourses_ReturnsOk()
{
    var context = TestDbContextFactory.Create();
var mapper = TestMapper.GetMapper();

// 🔥 create fake repo
var repo = new GenericRepository<Course>(context);

var controller = new CoursesController(repo, mapper, context);

    var result = await controller.GetCourses();

    Assert.IsType<OkObjectResult>(result);
}
}