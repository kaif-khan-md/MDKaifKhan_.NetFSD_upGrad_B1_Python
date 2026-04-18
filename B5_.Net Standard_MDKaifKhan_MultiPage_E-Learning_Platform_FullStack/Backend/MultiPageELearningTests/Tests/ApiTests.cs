using Xunit;
using MultiPageELearningApi.Controllers;
using Microsoft.AspNetCore.Mvc;
using MultiPageELearningApi.Repositories;
using MultiPageELearningApi.Models;
using MultiPageELearningApi.Dtos;


public class ApiTests
{
    [Fact]
    public async Task Register_InvalidModel_ReturnsBadRequest()
    {
        var context = TestDbContextFactory.Create();
        var repo = new GenericRepository<User>(context);

        var controller = new UsersController(repo);

        controller.ModelState.AddModelError("Email", "Required");

        var dto = new RegisterUserDto
        {
            FullName = "Test",
            Email = "test@test.com",
            Password = "123456"
        };

        controller.ModelState.AddModelError("Email", "Required");

        var result = await controller.Register(dto);

        Assert.IsType<BadRequestObjectResult>(result);
    }
}