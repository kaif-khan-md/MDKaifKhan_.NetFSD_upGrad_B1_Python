using Microsoft.EntityFrameworkCore;
using MultiPageELearningApi.Models;
namespace MultiPageELearningApi.Data; 
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) {}

    public DbSet<User> Users { get; set; }
    public DbSet<Course> Courses { get; set; }
    public DbSet<CourseProgress> CourseProgresses { get; set; }
    public DbSet<Lesson> Lessons { get; set; }
    public DbSet<Quiz> Quizzes { get; set; }
    public DbSet<Question> Questions { get; set; }
    public DbSet<Result> Results { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    modelBuilder.Entity<User>()
        .HasMany(u => u.Courses)
        .WithOne(c => c.User)
        .HasForeignKey(c => c.CreatedBy)
        .OnDelete(DeleteBehavior.Cascade);

    modelBuilder.Entity<Course>()
        .HasMany(c => c.Lessons)
        .WithOne(l => l.Course)
        .HasForeignKey(l => l.CourseId)
        .OnDelete(DeleteBehavior.Cascade);

    modelBuilder.Entity<Course>()
        .HasMany(c => c.Quizzes)
        .WithOne(q => q.Course)
        .HasForeignKey(q => q.CourseId)
        .OnDelete(DeleteBehavior.Cascade);
    modelBuilder.Entity<CourseProgress>()
        .HasOne(cp => cp.User)
        .WithMany()
        .HasForeignKey(cp => cp.UserId)
        .OnDelete(DeleteBehavior.NoAction);

    modelBuilder.Entity<CourseProgress>()
        .HasOne(cp => cp.Course)
        .WithMany()
        .HasForeignKey(cp => cp.CourseId)
        .OnDelete(DeleteBehavior.NoAction);

    modelBuilder.Entity<Quiz>()
        .HasMany(q => q.Questions)
        .WithOne(qn => qn.Quiz)
        .HasForeignKey(qn => qn.QuizId)
        .OnDelete(DeleteBehavior.Cascade);

    modelBuilder.Entity<User>()
        .HasMany(u => u.Results)
        .WithOne(r => r.User)
        .HasForeignKey(r => r.UserId)
        .OnDelete(DeleteBehavior.NoAction); 
}
}