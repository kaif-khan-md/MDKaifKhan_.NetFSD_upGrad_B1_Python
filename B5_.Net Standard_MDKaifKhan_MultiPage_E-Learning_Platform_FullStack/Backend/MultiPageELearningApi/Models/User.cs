using System;

namespace MultiPageELearningApi.Models;

public class User
{
    public int UserId { get; set; }
    public string FullName { get; set; }
    public string Email { get; set; }
    public string PasswordHash { get; set; }

    public string Role { get; set; } = "User";
    public DateTime CreatedAt { get; set; }

    public ICollection<Course> Courses { get; set; }
    public ICollection<Result> Results { get; set; }
}
